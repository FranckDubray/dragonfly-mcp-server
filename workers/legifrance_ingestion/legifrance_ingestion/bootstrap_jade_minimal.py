from __future__ import annotations

import logging
from pathlib import Path

from .archive_reader import filter_xml_members, iter_archive_members
from .config import load_settings
from .http_writer import DragonflyWriter
from .manifests import ManifestCollector
from .map_canonical import map_to_canonical_json
from .parse_jade import parse_jade_member
from .validators import validate_canonical

LOGGER = logging.getLogger("legifrance_ingestion.bootstrap_jade_minimal")

DEFAULT_MAX_DECISIONS = 20


def compute_datasource_path(obj: dict) -> str:
    return f"jade/{obj['entity_type']}/{obj['id']}.json"


def run_minimal_jade_roundtrip(
    archive_path: str,
    max_decisions: int = DEFAULT_MAX_DECISIONS,
) -> dict:
    settings = load_settings()
    writer = DragonflyWriter(settings)
    manifests = ManifestCollector()

    archive = Path(archive_path).resolve()
    if not archive.exists():
        raise FileNotFoundError(f"Archive not found: {archive}")

    published: list[str] = []
    selected_members: list[str] = []
    published_count = 0

    for member in filter_xml_members(iter_archive_members(archive)):
        try:
            raw_objects = parse_jade_member(member)
        except Exception as exc:
            LOGGER.warning("Skipping member due to parse error | member=%s error=%s", member.member_name, exc)
            continue

        for raw_obj in raw_objects:
            if raw_obj["entity_type"] != "decision":
                continue
            if published_count >= max_decisions:
                break

            canonical = map_to_canonical_json(raw_obj, archive.name, member.member_name)
            validate_canonical(canonical)

            path = compute_datasource_path(canonical)
            writer.write_json(path, canonical)
            manifests.add(canonical, path)

            published.append(path)
            selected_members.append(member.member_name)
            published_count += 1
            LOGGER.info("Published JADE decision | path=%s", path)

        if published_count >= max_decisions:
            break

    if published_count == 0:
        raise RuntimeError("No JADE decision object could be parsed and published from archive")

    run_name = f"jade_bootstrap_minimal_{archive.stem.replace('.', '_')}"
    manifest_paths = manifests.flush(writer, run_name)

    return {
        "archive": str(archive),
        "selected_members": selected_members,
        "published_paths": published,
        "manifest_paths": manifest_paths,
        "mapping_paths": [],
        "published_counts": {"decision": published_count},
        "limits": {
            "max_decisions": max_decisions,
        },
    }
