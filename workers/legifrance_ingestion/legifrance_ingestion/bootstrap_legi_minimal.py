from __future__ import annotations

import logging
from pathlib import Path

from .archive_reader import filter_xml_members, iter_archive_members
from .config import load_settings
from .http_writer import DragonflyWriter
from .manifests import ManifestCollector
from .map_canonical import map_to_canonical_json
from .mappings import MappingCollector
from .parse_legi import parse_legi_member
from .validators import validate_canonical

LOGGER = logging.getLogger("legifrance_ingestion.bootstrap_legi_minimal")


TARGET_ENTITY_TYPES = {"texte", "article", "section"}


def compute_datasource_path(obj: dict) -> str:
    return f"legi/{obj['entity_type']}/{obj['id']}.json"


def _rewrite_parent_to_legi(canonical: dict, cid_to_legi: dict[str, str]) -> dict:
    if canonical.get("corpus") != "LEGI":
        return canonical

    context = canonical.get("context") or {}
    source_ids = canonical.get("source_ids") or {}

    parent_text_id = context.get("parent_text_id")
    if isinstance(parent_text_id, str) and parent_text_id.startswith("JORFTEXT"):
        legi_parent = cid_to_legi.get(parent_text_id)
        if legi_parent:
            context["parent_text_id"] = legi_parent

    code_id = context.get("code_id")
    if isinstance(code_id, str) and code_id.startswith("JORFTEXT"):
        legi_parent = cid_to_legi.get(code_id)
        if legi_parent:
            context["code_id"] = legi_parent

    cid = source_ids.get("cid")
    if isinstance(cid, str) and cid.startswith("JORFTEXT"):
        legi_parent = cid_to_legi.get(cid)
        if legi_parent and "legi_id" not in source_ids and canonical.get("entity_type") != "texte":
            source_ids["legi_id"] = legi_parent

    canonical["context"] = context
    canonical["source_ids"] = source_ids
    return canonical


def run_minimal_legi_roundtrip(archive_path: str) -> dict:
    settings = load_settings()
    writer = DragonflyWriter(settings)
    manifests = ManifestCollector()
    mappings = MappingCollector()

    archive = Path(archive_path).resolve()
    if not archive.exists():
        raise FileNotFoundError(f"Archive not found: {archive}")

    published: list[str] = []
    selected_members: list[str] = []
    entity_types_seen: set[str] = set()
    cid_to_legi: dict[str, str] = {}
    pending_children: list[tuple[dict, str, str]] = []

    for member in filter_xml_members(iter_archive_members(archive)):
        try:
            raw_objects = parse_legi_member(member)
        except Exception as exc:
            LOGGER.warning("Skipping member due to parse error | member=%s error=%s", member.member_name, exc)
            continue

        for raw_obj in raw_objects:
            entity_type = raw_obj["entity_type"]
            if entity_type not in TARGET_ENTITY_TYPES:
                continue
            if entity_type in entity_types_seen:
                continue

            canonical = map_to_canonical_json(raw_obj, archive.name, member.member_name)

            if entity_type == "texte":
                source_ids = canonical.get("source_ids") or {}
                cid = source_ids.get("cid")
                if cid and canonical.get("id"):
                    cid_to_legi[cid] = canonical["id"]
                canonical = _rewrite_parent_to_legi(canonical, cid_to_legi)
                validate_canonical(canonical)
                path = compute_datasource_path(canonical)
                writer.write_json(path, canonical)
                manifests.add(canonical, path)
                mappings.collect_from_object(canonical)
                published.append(path)
                selected_members.append(member.member_name)
                entity_types_seen.add(entity_type)
                LOGGER.info("Published minimal LEGI object | type=%s path=%s", entity_type, path)
                continue

            # Delay children until we have seen the parent text mapping if needed
            pending_children.append((canonical, archive.name, member.member_name))

        if entity_types_seen == TARGET_ENTITY_TYPES:
            break

    still_pending: list[tuple[dict, str, str]] = []
    for canonical, archive_name, member_name in pending_children:
        entity_type = canonical["entity_type"]
        if entity_type in entity_types_seen:
            continue

        canonical = _rewrite_parent_to_legi(canonical, cid_to_legi)
        try:
            validate_canonical(canonical)
        except Exception:
            still_pending.append((canonical, archive_name, member_name))
            continue

        path = compute_datasource_path(canonical)
        writer.write_json(path, canonical)
        manifests.add(canonical, path)
        mappings.collect_from_object(canonical)
        published.append(path)
        selected_members.append(member_name)
        entity_types_seen.add(entity_type)
        LOGGER.info("Published minimal LEGI object | type=%s path=%s", entity_type, path)

        if entity_types_seen == TARGET_ENTITY_TYPES:
            break

    if "texte" not in entity_types_seen:
        raise RuntimeError("No LEGI text object could be parsed and published from archive")
    if "article" not in entity_types_seen:
        raise RuntimeError("No LEGI article object could be parsed and published from archive")
    if "section" not in entity_types_seen:
        raise RuntimeError("No LEGI section object could be parsed and published from archive")

    run_name = f"legi_bootstrap_minimal_{archive.stem.replace('.', '_')}"
    manifest_paths = manifests.flush(writer, run_name)
    mapping_paths = mappings.flush(writer)

    return {
        "archive": str(archive),
        "selected_members": selected_members,
        "published_paths": published,
        "manifest_paths": manifest_paths,
        "mapping_paths": mapping_paths,
    }
