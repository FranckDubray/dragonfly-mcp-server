from __future__ import annotations

import argparse
import logging
import sys
from typing import Literal

from .bootstrap_jorf_minimal import run_minimal_jorf_roundtrip
from .bootstrap_legi_minimal import run_minimal_legi_roundtrip
from .config import Settings, load_settings
from .state_store import LocalStateStore, RunState

Mode = Literal["bootstrap", "replay", "daily"]
Corpus = Literal["legi", "jorf"]

LOGGER = logging.getLogger("legifrance_ingestion")


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
        choices=["legi", "jorf"],
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
    state.extra = {"last_started_mode": mode}
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


def run_bootstrap(settings: Settings, corpus: Corpus, archive_path: str | None = None) -> int:
    LOGGER.info("BOOTSTRAP start | corpus=%s archive=%s", corpus, archive_path)
    state_store = LocalStateStore(settings)
    _update_state_begin(state_store, corpus, "bootstrap", archive_path)

    if corpus == "legi":
        if not archive_path:
            raise RuntimeError("For now, LEGI bootstrap requires --archive-path")
        result = run_minimal_legi_roundtrip(archive_path)
        _update_state_success(state_store, corpus, "bootstrap", archive_path, result)
        LOGGER.info("BOOTSTRAP done | result=%s", result)
        return 0

    if corpus == "jorf":
        if not archive_path:
            raise RuntimeError("For now, JORF bootstrap requires --archive-path")
        result = run_minimal_jorf_roundtrip(archive_path)
        _update_state_success(state_store, corpus, "bootstrap", archive_path, result)
        LOGGER.info("BOOTSTRAP done | result=%s", result)
        return 0

    raise RuntimeError(f"Unsupported corpus for bootstrap: {corpus}")


def run_replay(settings: Settings, corpus: Corpus) -> int:
    LOGGER.info("REPLAY start | corpus=%s", corpus)
    LOGGER.info("TODO: implement historical incremental replay for corpus=%s", corpus)
    return 0


def run_daily(settings: Settings, corpus: Corpus) -> int:
    LOGGER.info("DAILY start | corpus=%s", corpus)
    LOGGER.info("TODO: implement daily incremental ingestion for corpus=%s", corpus)
    return 0


def dispatch(settings: Settings, mode: Mode, corpus: Corpus, archive_path: str | None = None) -> int:
    if corpus == "legi" and not settings.enable_legi:
        raise RuntimeError("Corpus LEGI is disabled by configuration")
    if corpus == "jorf" and not settings.enable_jorf:
        raise RuntimeError("Corpus JORF is disabled by configuration")

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
