from __future__ import annotations

import gzip
import logging
import tarfile
from dataclasses import dataclass
from pathlib import Path
from typing import Generator, Iterable

LOGGER = logging.getLogger("legifrance_ingestion.archive_reader")


@dataclass
class ArchiveMember:
    archive_path: Path
    member_name: str
    content: bytes

    @property
    def suffix(self) -> str:
        if "." not in self.member_name:
            return ""
        return self.member_name.rsplit(".", 1)[-1].lower()


def is_supported_member(member_name: str) -> bool:
    lower_name = member_name.lower()
    return lower_name.endswith(".xml") or lower_name.endswith(".pdf")


def iter_archive_members(archive_path: Path) -> Generator[ArchiveMember, None, None]:
    LOGGER.info("Opening archive stream | archive=%s", archive_path)

    with archive_path.open("rb") as raw_fp:
        with gzip.GzipFile(fileobj=raw_fp, mode="rb") as gz_fp:
            with tarfile.open(fileobj=gz_fp, mode="r|") as tar:
                for member in tar:
                    if not member.isfile():
                        continue
                    if not is_supported_member(member.name):
                        continue

                    extracted = tar.extractfile(member)
                    if extracted is None:
                        continue

                    content = extracted.read()
                    yield ArchiveMember(
                        archive_path=archive_path,
                        member_name=member.name,
                        content=content,
                    )


def filter_xml_members(members: Iterable[ArchiveMember]) -> Generator[ArchiveMember, None, None]:
    for member in members:
        if member.member_name.lower().endswith(".xml"):
            yield member


def filter_pdf_members(members: Iterable[ArchiveMember]) -> Generator[ArchiveMember, None, None]:
    for member in members:
        if member.member_name.lower().endswith(".pdf"):
            yield member
