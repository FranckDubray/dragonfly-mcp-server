from __future__ import annotations

import logging
from pathlib import Path

from .archive_reader import filter_xml_members, iter_archive_members
from .config import load_settings
from .http_writer import DragonflyWriter
from .manifests import ManifestCollector
from .map_canonical import map_to_canonical_json
from .mappings import MappingCollector
from .parse_kali import parse_kali_member
from .validators import validate_canonical

LOGGER = logging.getLogger("legifrance_ingestion.bootstrap_kali_minimal")

TARGET_ENTITY_TYPES = {"texte", "article", "section"}
DEFAULT_MAX_TEXTS = 5
DEFAULT_MAX_ARTICLES = 20
DEFAULT_MAX_SECTIONS = 20


def compute_datasource_path(obj: dict) -> str:
    return f"kali/{obj['entity_type']}/{obj['id']}.json"


def _can_publish(entity_type: str, published_counts: dict[str, int], max_texts: int, max_articles: int, max_sections: int) -> bool:
    if entity_type == "texte":
        return published_counts["texte"] < max_texts
    if entity_type == "article":
        return published_counts["article"] < max_articles
    if entity_type == "section":
        return published_counts["section"] < max_sections
    return False


def _quotas_reached(published_counts: dict[str, int], max_texts: int, max_articles: int, max_sections: int) -> bool:
    return (
        published_counts["texte"] >= max_texts
        and published_counts["article"] >= max_articles
        and published_counts["section"] >= max_sections
    )


def run_minimal_kali_roundtrip(
    archive_path: str,
    max_texts: int = DEFAULT_MAX_TEXTS,
    max_articles: int = DEFAULT_MAX_ARTICLES,
    max_sections: int = DEFAULT_MAX_SECTIONS,
) -> dict:
    settings = load_settings()
    writer = DragonflyWriter(settings)
    manifests = ManifestCollector()
    mappings = MappingCollector()

    archive = Path(archive_path).resolve()
    if not archive.exists():
        raise FileNotFoundError(f"Archive not found: {archive}")

    published: list[str] = []
    selected_members: list[str] = []
    published_counts = {"texte": 0, "article": 0, "section": 0}

    for member in filter_xml_members(iter_archive_members(archive)):
        try:
            raw_objects = parse_kali_member(member)
        except Exception as exc:
            LOGGER.warning("Skipping member due to parse error | member=%s error=%s", member.member_name, exc)
            continue

        for raw_obj in raw_objects:
            entity_type = raw_obj["entity_type"]
            if entity_type not in TARGET_ENTITY_TYPES:
                continue
            if not _can_publish(entity_type, published_counts, max_texts, max_articles, max_sections):
                continue

            canonical = map_to_canonical_json(raw_obj, archive.name, member.member_name)
            validate_canonical(canonical)

            path = compute_datasource_path(canonical)
            writer.write_json(path, canonical)
            manifests.add(canonical, path)
            mappings.collect_from_object(canonical)

            published.append(path)
            selected_members.append(member.member_name)
            published_counts[entity_type] += 1
            LOGGER.info("Published KALI object | type=%s path=%s", entity_type, path)

        if _quotas_reached(published_counts, max_texts, max_articles, max_sections):
            break

    if published_counts["texte"] == 0:
        raise RuntimeError("No KALI text object could be parsed and published from archive")
    if published_counts["article"] == 0:
        raise RuntimeError("No KALI article object could be parsed and published from archive")
    if published_counts["section"] == 0:
        raise RuntimeError("No KALI section object could be parsed and published from archive")

    run_name = f"kali_bootstrap_minimal_{archive.stem.replace('.', '_')}"
    manifest_paths = manifests.flush(writer, run_name)
    mapping_paths = mappings.flush(writer)

    return {
        "archive": str(archive),
        "selected_members": selected_members,
        "published_paths": published,
        "manifest_paths": manifest_paths,
        "mapping_paths": mapping_paths,
        "published_counts": published_counts,
        "limits": {
            "max_texts": max_texts,
            "max_articles": max_articles,
            "max_sections": max_sections,
        },
    }
