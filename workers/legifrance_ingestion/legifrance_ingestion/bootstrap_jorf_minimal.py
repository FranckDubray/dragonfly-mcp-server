from __future__ import annotations

import logging
from pathlib import Path

from .archive_reader import filter_xml_members, iter_archive_members
from .config import load_settings
from .http_writer import DragonflyWriter
from .manifests import ManifestCollector
from .map_canonical import map_to_canonical_json
from .mappings import MappingCollector
from .parse_jorf import parse_jorf_member
from .validators import validate_canonical

LOGGER = logging.getLogger("legifrance_ingestion.bootstrap_jorf_minimal")


def compute_datasource_path(obj: dict) -> str:
    return f"jorf/{obj['entity_type']}/{obj['id']}.json"


def run_minimal_jorf_roundtrip(archive_path: str) -> dict:
    settings = load_settings()
    writer = DragonflyWriter(settings)
    manifests = ManifestCollector()
    mappings = MappingCollector()

    archive = Path(archive_path).resolve()
    if not archive.exists():
        raise FileNotFoundError(f"Archive not found: {archive}")

    published: list[str] = []
    selected_members: list[str] = []

    for member in filter_xml_members(iter_archive_members(archive)):
        try:
            raw_objects = parse_jorf_member(member)
        except Exception:
            continue

        for raw_obj in raw_objects:
            canonical = map_to_canonical_json(raw_obj, archive.name, member.member_name)
            validate_canonical(canonical)

            path = compute_datasource_path(canonical)
            writer.write_json(path, canonical)
            manifests.add(canonical, path)
            mappings.collect_from_object(canonical)

            published.append(path)
            selected_members.append(member.member_name)
            LOGGER.info("Published minimal JORF object | path=%s", path)
            break

        if published:
            break

    if not published:
        raise RuntimeError("No JORF text object could be parsed and published from archive")

    run_name = f"jorf_bootstrap_minimal_{archive.stem.replace('.', '_')}"
    manifest_paths = manifests.flush(writer, run_name)
    mapping_paths = mappings.flush(writer)

    return {
        "archive": str(archive),
        "selected_members": selected_members,
        "published_paths": published,
        "manifest_paths": manifest_paths,
        "mapping_paths": mapping_paths,
    }
