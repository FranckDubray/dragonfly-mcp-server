from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urljoin

import requests

from .config import Settings

LOGGER = logging.getLogger("legifrance_ingestion.acquisition")

HREF_RE = re.compile(r'href="([^"]+\.tar\.gz)"', re.IGNORECASE)


@dataclass(frozen=True)
class ArchiveInfo:
    corpus: str
    name: str
    url: str


def _fetch_index(url: str, timeout: int) -> str:
    response = requests.get(url, timeout=timeout)
    response.raise_for_status()
    return response.text


def _extract_archive_names(html: str) -> list[str]:
    names = HREF_RE.findall(html)
    deduped = sorted(set(names))
    return deduped


def _build_archives(corpus: str, base_url: str, settings: Settings) -> list[ArchiveInfo]:
    html = _fetch_index(base_url, settings.http_timeout)
    archive_names = _extract_archive_names(html)
    archives: list[ArchiveInfo] = []
    for name in archive_names:
        archives.append(
            ArchiveInfo(
                corpus=corpus,
                name=name,
                url=urljoin(base_url, name),
            )
        )
    return archives


def list_legi_archives(settings: Settings) -> list[ArchiveInfo]:
    return _build_archives("legi", settings.dila_legi_url, settings)


def list_jorf_archives(settings: Settings) -> list[ArchiveInfo]:
    return _build_archives("jorf", settings.dila_jorf_url, settings)


def list_kali_archives(settings: Settings) -> list[ArchiveInfo]:
    return _build_archives("kali", settings.dila_kali_url, settings)


def list_cass_archives(settings: Settings) -> list[ArchiveInfo]:
    return _build_archives("cass", settings.dila_cass_url, settings)


def list_jade_archives(settings: Settings) -> list[ArchiveInfo]:
    return _build_archives("jade", settings.dila_jade_url, settings)


def list_constit_archives(settings: Settings) -> list[ArchiveInfo]:
    return _build_archives("constit", settings.dila_constit_url, settings)


def download_archive(settings: Settings, archive: ArchiveInfo) -> Path:
    target_dir = settings.workdir / archive.corpus / "archives"
    target_dir.mkdir(parents=True, exist_ok=True)
    target_path = target_dir / archive.name

    if target_path.exists():
        LOGGER.info("Archive already present locally | path=%s", target_path)
        return target_path

    LOGGER.info("Downloading archive | corpus=%s url=%s", archive.corpus, archive.url)
    with requests.get(archive.url, stream=True, timeout=settings.http_timeout) as response:
        response.raise_for_status()
        with target_path.open("wb") as fp:
            for chunk in response.iter_content(chunk_size=1024 * 1024):
                if not chunk:
                    continue
                fp.write(chunk)

    LOGGER.info("Archive downloaded | path=%s", target_path)
    return target_path


def select_latest_archive(archives: list[ArchiveInfo]) -> ArchiveInfo:
    if not archives:
        raise RuntimeError("No archive found")
    return sorted(archives, key=lambda a: a.name)[-1]
