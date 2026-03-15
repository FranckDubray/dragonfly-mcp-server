from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path
from typing import Literal

from .acquisition import (
    download_archive,
    list_cass_archives,
    list_jorf_archives,
    list_kali_archives,
    list_legi_archives,
    select_latest_archive,
)
from .bootstrap_cass_minimal import run_minimal_cass_roundtrip
from .bootstrap_jorf_minimal import run_minimal_jorf_roundtrip
from .bootstrap_kali_minimal import run_minimal_kali_roundtrip
from .bootstrap_legi_minimal import run_minimal_legi_roundtrip
from .config import Settings, load_settings
from .state_store import LocalStateStore, RunState

Mode = Literal["bootstrap", "replay", "daily"]
Corpus = Literal["legi", "jorf", "kali", "cass"]

LOGGER = logging.getLogger("legifrance_ingestion")
DEFAULT_REPLAY_LIMIT = 3
DEFAULT_DAILY_LIMIT = 2


def configure_logging(level: str) -> None:
    logging.basicConfig(
        level=getattr(logging, level, logging.INFO),
        format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="legifrance_ingestion",
        description="Worker d'ingestion DILA → Dragonfly API → S3 datasource legifrance",
    )
    parser.add_argument(
        "--mode",
        required=True,
        choices=["bootstrap", "replay", "daily"],
        help="Mode d'exécution",
    )
    parser.add_argument(
        "--corpus",
        required=True,
        choices=["legi", "jorf", "kali", "cass"],
        help="Corpus à traiter",
    )
    parser.add_argument(
        "--archive-path",
        required=False,
        help="Chemin local d'une archive à utiliser explicitement pour un bootstrap minimal",
    )
    return parser


def _update_state_begin(state_store: LocalStateStore, corpus: Corpus, mode: Mode, archive_path: str | None) -> None:
    state = state_store.load(corpus, mode)
    state.status = "running"
    state.last_processed_archive = archive_path
    extra = state.extra or {}
    extra["last_started_mode"] = mode
    state.extra = extra
    state_store.save(state)


def _update_state_success(state_store: LocalStateStore, corpus: Corpus, mode: Mode, archive_path: str | None, result: dict) -> None:
    state = RunState(
        corpus=corpus,
        mode=mode,
        last_processed_archive=archive_path,
        status="success",
        updated_at=result.get("archive"),
        extra={
            "published_paths": result.get("published_paths", []),
            "manifest_paths": result.get("manifest_paths", []),
            "mapping_paths": result.get("mapping_paths", []),
        },
    )
    state_store.save(state)


def _resolve_bootstrap_archive(settings: Settings, corpus: Corpus, archive_path: str | None) -> str:
    if archive_path:
        path = Path(archive_path).resolve()
        if not path.exists():
            raise FileNotFoundError(f"Archive not found: {path}")
        return str(path)

    LOGGER.info("No archive path provided, resolving latest remote archive | corpus=%s", corpus)

    if corpus == "legi":
        latest = select_latest_archive(list_legi_archives(settings))
        return str(download_archive(settings, latest))

    if corpus == "jorf":
        latest = select_latest_archive(list_jorf_archives(settings))
        return str(download_archive(settings, latest))

    if corpus == "kali":
        latest = select_latest_archive(list_kali_archives(settings))
        return str(download_archive(settings, latest))

    if corpus == "cass":
        latest = select_latest_archive(list_cass_archives(settings))
        return str(download_archive(settings, latest))

    raise RuntimeError(f"Unsupported corpus for bootstrap archive resolution: {corpus}")


def _run_single_archive(corpus: Corpus, archive_path: str) -> dict:
    if corpus == "legi":
        return run_minimal_legi_roundtrip(archive_path)
    if corpus == "jorf":
        return run_minimal_jorf_roundtrip(archive_path)
    if corpus == "kali":
        return run_minimal_kali_roundtrip(archive_path)
    if corpus == "cass":
        return run_minimal_cass_roundtrip(archive_path)
    raise RuntimeError(f"Unsupported corpus for single archive run: {corpus}")


def _list_archives_for_corpus(settings: Settings, corpus: Corpus):
    if corpus == "legi":
        return list_legi_archives(settings)
    if corpus == "jorf":
        return list_jorf_archives(settings)
    if corpus == "kali":
        return list_kali_archives(settings)
    if corpus == "cass":
        return list_cass_archives(settings)
    raise RuntimeError(f"Unsupported corpus for archive listing: {corpus}")


def run_bootstrap(settings: Settings, corpus: Corpus, archive_path: str | None = None) -> int:
    resolved_archive = _resolve_bootstrap_archive(settings, corpus, archive_path)
    LOGGER.info("BOOTSTRAP start | corpus=%s archive=%s", corpus, resolved_archive)
    state_store = LocalStateStore(settings)
    _update_state_begin(state_store, corpus, "bootstrap", resolved_archive)
    result = _run_single_archive(corpus, resolved_archive)
    _update_state_success(state_store, corpus, "bootstrap", resolved_archive, result)
    LOGGER.info("BOOTSTRAP done | result=%s", result)
    return 0


def run_replay(settings: Settings, corpus: Corpus) -> int:
    LOGGER.info("REPLAY start | corpus=%s", corpus)
    state_store = LocalStateStore(settings)
    state = state_store.load(corpus, "replay")

    archives = sorted(_list_archives_for_corpus(settings, corpus), key=lambda a: a.name)
    processed_archives = list((state.extra or {}).get("processed_archives", []))
    processed_set = set(processed_archives)
    pending_archives = [a for a in archives if a.name not in processed_set]
    replay_batch = pending_archives[:DEFAULT_REPLAY_LIMIT]

    LOGGER.info(
        "REPLAY planning | corpus=%s total_archives=%s already_processed=%s pending=%s selected=%s",
        corpus,
        len(archives),
        len(processed_archives),
        len(pending_archives),
        len(replay_batch),
    )

    if not replay_batch:
        LOGGER.info("REPLAY nothing to do | corpus=%s", corpus)
        state.status = "success"
        extra = state.extra or {}
        extra["last_replay_count"] = 0
        state.extra = extra
        state_store.save(state)
        return 0

    replay_results: list[dict] = []
    for archive in replay_batch:
        local_archive = str(download_archive(settings, archive))
        _update_state_begin(state_store, corpus, "replay", local_archive)
        LOGGER.info("REPLAY archive start | corpus=%s archive=%s", corpus, archive.name)
        result = _run_single_archive(corpus, local_archive)
        replay_results.append({
            "archive_name": archive.name,
            "archive_path": local_archive,
            "published_paths": result.get("published_paths", []),
            "manifest_paths": result.get("manifest_paths", []),
            "mapping_paths": result.get("mapping_paths", []),
        })
        processed_archives.append(archive.name)
        state = RunState(
            corpus=corpus,
            mode="replay",
            last_processed_archive=local_archive,
            status="success",
            updated_at=result.get("archive"),
            extra={
                "processed_archives": processed_archives,
                "last_replay_count": len(replay_results),
                "replay_results": replay_results,
            },
        )
        state_store.save(state)
        LOGGER.info("REPLAY archive done | corpus=%s archive=%s", corpus, archive.name)

    LOGGER.info("REPLAY done | corpus=%s replayed=%s", corpus, len(replay_results))
    return 0


def run_daily(settings: Settings, corpus: Corpus) -> int:
    LOGGER.info("DAILY start | corpus=%s", corpus)
    state_store = LocalStateStore(settings)
    state = state_store.load(corpus, "daily")

    archives = sorted(_list_archives_for_corpus(settings, corpus), key=lambda a: a.name)
    processed_archives = list((state.extra or {}).get("processed_archives", []))
    processed_set = set(processed_archives)
    new_archives = [a for a in archives if a.name not in processed_set]
    daily_batch = new_archives[:DEFAULT_DAILY_LIMIT]

    LOGGER.info(
        "DAILY planning | corpus=%s total_archives=%s already_processed=%s new=%s selected=%s",
        corpus,
        len(archives),
        len(processed_archives),
        len(new_archives),
        len(daily_batch),
    )

    if not daily_batch:
        LOGGER.info("DAILY nothing to do | corpus=%s", corpus)
        state.status = "success"
        extra = state.extra or {}
        extra["last_daily_count"] = 0
        state.extra = extra
        state_store.save(state)
        return 0

    daily_results: list[dict] = []
    for archive in daily_batch:
        local_archive = str(download_archive(settings, archive))
        _update_state_begin(state_store, corpus, "daily", local_archive)
        LOGGER.info("DAILY archive start | corpus=%s archive=%s", corpus, archive.name)
        result = _run_single_archive(corpus, local_archive)
        daily_results.append({
            "archive_name": archive.name,
            "archive_path": local_archive,
            "published_paths": result.get("published_paths", []),
            "manifest_paths": result.get("manifest_paths", []),
            "mapping_paths": result.get("mapping_paths", []),
        })
        processed_archives.append(archive.name)
        state = RunState(
            corpus=corpus,
            mode="daily",
            last_processed_archive=local_archive,
            status="success",
            updated_at=result.get("archive"),
            extra={
                "processed_archives": processed_archives,
                "last_daily_count": len(daily_results),
                "daily_results": daily_results,
            },
        )
        state_store.save(state)
        LOGGER.info("DAILY archive done | corpus=%s archive=%s", corpus, archive.name)

    LOGGER.info("DAILY done | corpus=%s processed=%s", corpus, len(daily_results))
    return 0


def dispatch(settings: Settings, mode: Mode, corpus: Corpus, archive_path: str | None = None) -> int:
    if corpus == "legi" and not settings.enable_legi:
        raise RuntimeError("Corpus LEGI is disabled by configuration")
    if corpus == "jorf" and not settings.enable_jorf:
        raise RuntimeError("Corpus JORF is disabled by configuration")
    if corpus == "kali" and not settings.enable_kali:
        raise RuntimeError("Corpus KALI is disabled by configuration")
    if corpus == "cass" and not settings.enable_cass:
        raise RuntimeError("Corpus CASS is disabled by configuration")

    if mode == "bootstrap":
        return run_bootstrap(settings, corpus, archive_path)
    if mode == "replay":
        return run_replay(settings, corpus)
    if mode == "daily":
        return run_daily(settings, corpus)

    raise RuntimeError(f"Unsupported mode: {mode}")


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    settings = load_settings()
    configure_logging(settings.log_level)

    LOGGER.info(
        "Worker start | mode=%s corpus=%s datasource=%s api=%s archive=%s",
        args.mode,
        args.corpus,
        settings.datasource_name,
        settings.dragonfly_api_base_url,
        args.archive_path,
    )

    try:
        return dispatch(settings, args.mode, args.corpus, args.archive_path)
    except Exception:
        LOGGER.exception("Worker failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
