from __future__ import annotations

import argparse
import logging
import sys
from typing import Literal

from .config import Settings, load_settings

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
    return parser


def run_bootstrap(settings: Settings, corpus: Corpus) -> int:
    LOGGER.info("BOOTSTRAP start | corpus=%s", corpus)
    LOGGER.info("TODO: implement bootstrap pipeline for corpus=%s", corpus)
    return 0


def run_replay(settings: Settings, corpus: Corpus) -> int:
    LOGGER.info("REPLAY start | corpus=%s", corpus)
    LOGGER.info("TODO: implement historical incremental replay for corpus=%s", corpus)
    return 0


def run_daily(settings: Settings, corpus: Corpus) -> int:
    LOGGER.info("DAILY start | corpus=%s", corpus)
    LOGGER.info("TODO: implement daily incremental ingestion for corpus=%s", corpus)
    return 0


def dispatch(settings: Settings, mode: Mode, corpus: Corpus) -> int:
    if corpus == "legi" and not settings.enable_legi:
        raise RuntimeError("Corpus LEGI is disabled by configuration")
    if corpus == "jorf" and not settings.enable_jorf:
        raise RuntimeError("Corpus JORF is disabled by configuration")

    if mode == "bootstrap":
        return run_bootstrap(settings, corpus)
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
        "Worker start | mode=%s corpus=%s datasource=%s api=%s",
        args.mode,
        args.corpus,
        settings.datasource_name,
        settings.dragonfly_api_base_url,
    )

    try:
        return dispatch(settings, args.mode, args.corpus)
    except Exception:
        LOGGER.exception("Worker failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
