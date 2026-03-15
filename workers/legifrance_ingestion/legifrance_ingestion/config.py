from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()


def _as_bool(value: str | None, default: bool = False) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class Settings:
    dragonfly_api_base_url: str
    dragonfly_api_key: str
    datasource_name: str

    workdir: Path

    http_timeout: int
    http_max_retries: int
    http_retry_backoff: int

    log_level: str

    enable_legi: bool
    enable_jorf: bool
    enable_kali: bool
    enable_cass: bool
    enable_jade: bool
    enable_constit: bool

    dila_base_url: str
    dila_legi_url: str
    dila_jorf_url: str
    dila_kali_url: str
    dila_cass_url: str
    dila_jade_url: str
    dila_constit_url: str

    @property
    def ingestion_state_prefix(self) -> str:
        return "_meta/ingestion/state/"

    @property
    def ingestion_runs_prefix(self) -> str:
        return "_meta/ingestion/runs/"

    @property
    def manifests_prefix(self) -> str:
        return "_meta/manifests/"

    @property
    def mappings_prefix(self) -> str:
        return "_meta/mappings/"

    @property
    def schema_prefix(self) -> str:
        return "_meta/schema/"


def load_settings() -> Settings:
    workdir = Path(os.getenv("LEGI_WORKDIR", "/tmp/legifrance_ingestion")).resolve()
    workdir.mkdir(parents=True, exist_ok=True)

    api_base_url = os.getenv("DRAGONFLY_API_BASE_URL", "").strip()
    api_key = os.getenv("DRAGONFLY_API_KEY", "").strip()
    datasource_name = os.getenv("DRAGONFLY_DATASOURCE_NAME", "legifrance").strip()

    if not api_base_url:
        raise ValueError("Missing DRAGONFLY_API_BASE_URL")
    if not api_key:
        raise ValueError("Missing DRAGONFLY_API_KEY")
    if not datasource_name:
        raise ValueError("Missing DRAGONFLY_DATASOURCE_NAME")

    return Settings(
        dragonfly_api_base_url=api_base_url.rstrip("/"),
        dragonfly_api_key=api_key,
        datasource_name=datasource_name,
        workdir=workdir,
        http_timeout=int(os.getenv("LEGI_HTTP_TIMEOUT", "60")),
        http_max_retries=int(os.getenv("LEGI_HTTP_MAX_RETRIES", "3")),
        http_retry_backoff=int(os.getenv("LEGI_HTTP_RETRY_BACKOFF", "2")),
        log_level=os.getenv("LEGI_LOG_LEVEL", "INFO").upper(),
        enable_legi=_as_bool(os.getenv("LEGI_ENABLE_LEGI"), True),
        enable_jorf=_as_bool(os.getenv("LEGI_ENABLE_JORF"), True),
        enable_kali=_as_bool(os.getenv("LEGI_ENABLE_KALI"), True),
        enable_cass=_as_bool(os.getenv("LEGI_ENABLE_CASS"), True),
        enable_jade=_as_bool(os.getenv("LEGI_ENABLE_JADE"), True),
        enable_constit=_as_bool(os.getenv("LEGI_ENABLE_CONSTIT"), True),
        dila_base_url=os.getenv("DILA_BASE_URL", "https://echanges.dila.gouv.fr/OPENDATA"),
        dila_legi_url=os.getenv("DILA_LEGI_URL", "https://echanges.dila.gouv.fr/OPENDATA/LEGI/"),
        dila_jorf_url=os.getenv("DILA_JORF_URL", "https://echanges.dila.gouv.fr/OPENDATA/JORF/"),
        dila_kali_url=os.getenv("DILA_KALI_URL", "https://echanges.dila.gouv.fr/OPENDATA/KALI/"),
        dila_cass_url=os.getenv("DILA_CASS_URL", "https://echanges.dila.gouv.fr/OPENDATA/CASS/"),
        dila_jade_url=os.getenv("DILA_JADE_URL", "https://echanges.dila.gouv.fr/OPENDATA/JADE/"),
        dila_constit_url=os.getenv("DILA_CONSTIT_URL", "https://echanges.dila.gouv.fr/OPENDATA/CONSTIT/"),
    )
