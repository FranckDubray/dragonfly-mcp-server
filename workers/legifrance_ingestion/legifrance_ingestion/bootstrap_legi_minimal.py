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
DEFAULT_MAX_TEXTS = 5
DEFAULT_MAX_ARTICLES = 25
DEFAULT_MAX_SECTIONS = 25
DEFAULT_MAX_ARTICLES_PER_TEXT = 5
DEFAULT_MAX_SECTIONS_PER_TEXT = 5


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


def _normalize_target_text_ids(target_text_ids: set[str] | None) -> set[str]:
    return {item.strip().upper() for item in (target_text_ids or set()) if item and item.strip()}


def _has_minimum_triplet(published_counts: dict[str, int]) -> bool:
    return (
        published_counts["texte"] >= 1
        and published_counts["article"] >= 1
        and published_counts["section"] >= 1
    )


def _quotas_reached(published_counts: dict[str, int], max_texts: int, max_articles: int, max_sections: int) -> bool:
    return (
        published_counts["texte"] >= max_texts
        and published_counts["article"] >= max_articles
        and published_counts["section"] >= max_sections
    )


def _can_stop_scan(published_counts: dict[str, int], max_texts: int, max_articles: int, max_sections: int) -> bool:
    return _has_minimum_triplet(published_counts) and _quotas_reached(
        published_counts, max_texts, max_articles, max_sections
    )


def _is_selected_text(parent_text_id: str | None, selected_text_ids: set[str]) -> bool:
    return bool(parent_text_id and parent_text_id in selected_text_ids)


def _can_publish_text(canonical_text_id: str, normalized_target_text_ids: set[str], published_counts: dict[str, int], max_texts: int) -> bool:
    if normalized_target_text_ids and canonical_text_id not in normalized_target_text_ids:
        return False
    return published_counts["texte"] < max_texts


def _can_publish_article(
    parent_text_id: str | None,
    selected_text_ids: set[str],
    published_counts: dict[str, int],
    published_articles_per_text: dict[str, int],
    max_articles: int,
    max_articles_per_text: int,
) -> bool:
    if not _is_selected_text(parent_text_id, selected_text_ids):
        return False
    if published_counts["article"] >= max_articles:
        return False
    return published_articles_per_text.get(parent_text_id, 0) < max_articles_per_text


def _can_publish_section(
    parent_text_id: str | None,
    selected_text_ids: set[str],
    published_counts: dict[str, int],
    published_sections_per_text: dict[str, int],
    max_sections: int,
    max_sections_per_text: int,
) -> bool:
    if not _is_selected_text(parent_text_id, selected_text_ids):
        return False
    if published_counts["section"] >= max_sections:
        return False
    return published_sections_per_text.get(parent_text_id, 0) < max_sections_per_text


def run_minimal_legi_roundtrip(
    archive_path: str,
    max_texts: int = DEFAULT_MAX_TEXTS,
    max_articles: int = DEFAULT_MAX_ARTICLES,
    max_sections: int = DEFAULT_MAX_SECTIONS,
    max_articles_per_text: int = DEFAULT_MAX_ARTICLES_PER_TEXT,
    max_sections_per_text: int = DEFAULT_MAX_SECTIONS_PER_TEXT,
    target_text_ids: set[str] | None = None,
) -> dict:
    settings = load_settings()
    writer = DragonflyWriter(settings)
    manifests = ManifestCollector()
    mappings = MappingCollector()

    archive = Path(archive_path).resolve()
    if not archive.exists():
        raise FileNotFoundError(f"Archive not found: {archive}")

    normalized_target_text_ids = _normalize_target_text_ids(target_text_ids)

    published: list[str] = []
    selected_members: list[str] = []
    cid_to_legi: dict[str, str] = {}
    pending_children: list[tuple[dict, str, str]] = []
    published_counts = {"texte": 0, "article": 0, "section": 0}
    selected_text_ids: set[str] = set()
    selected_text_paths_seen: set[str] = set()
    published_articles_per_text: dict[str, int] = {}
    published_sections_per_text: dict[str, int] = {}

    if normalized_target_text_ids:
        LOGGER.info(
            "Starting targeted LEGI roundtrip | archive=%s target_text_ids=%s limits=texts:%s articles:%s sections:%s per_text_articles:%s per_text_sections:%s",
            archive,
            sorted(normalized_target_text_ids),
            max_texts,
            max_articles,
            max_sections,
            max_articles_per_text,
            max_sections_per_text,
        )
    else:
        LOGGER.info(
            "Starting generic LEGI roundtrip | archive=%s limits=texts:%s articles:%s sections:%s per_text_articles:%s per_text_sections:%s",
            archive,
            max_texts,
            max_articles,
            max_sections,
            max_articles_per_text,
            max_sections_per_text,
        )

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

            canonical = map_to_canonical_json(raw_obj, archive.name, member.member_name)

            if entity_type == "texte":
                current_text_id = canonical["id"]
                if normalized_target_text_ids and current_text_id in normalized_target_text_ids:
                    LOGGER.info(
                        "Target text candidate seen | id=%s member=%s",
                        current_text_id,
                        member.member_name,
                    )
                if member.member_name in selected_text_paths_seen:
                    LOGGER.debug(
                        "Skipping duplicate text variant by path | id=%s member=%s",
                        current_text_id,
                        member.member_name,
                    )
                    continue
                if current_text_id in selected_text_ids:
                    LOGGER.debug(
                        "Skipping duplicate text variant by id | id=%s member=%s",
                        current_text_id,
                        member.member_name,
                    )
                    continue
                if not _can_publish_text(current_text_id, normalized_target_text_ids, published_counts, max_texts):
                    if normalized_target_text_ids and current_text_id in normalized_target_text_ids:
                        LOGGER.debug("Skipping targeted text due to quota | id=%s", current_text_id)
                    continue
                source_ids = canonical.get("source_ids") or {}
                cid = source_ids.get("cid")
                if cid and canonical.get("id"):
                    cid_to_legi[cid] = canonical["id"]
                canonical = _rewrite_parent_to_legi(canonical, cid_to_legi)
                validate_canonical(canonical)
                path = compute_datasource_path(canonical)
                writer.write_json(path, canonical)
                manifests.add(canonical, path)
                current_member_name = member.member_name
                LOGGER.info(
                    "Collecting mapping candidate | type=%s id=%s parent_text_id=%s code_id=%s cid=%s legi_id=%s member=%s",
                    canonical.get("entity_type"),
                    canonical.get("id"),
                    (canonical.get("context") or {}).get("parent_text_id"),
                    (canonical.get("context") or {}).get("code_id"),
                    (canonical.get("source_ids") or {}).get("cid"),
                    (canonical.get("source_ids") or {}).get("legi_id"),
                    current_member_name,
                )
                mappings.collect_from_object(canonical)
                published.append(path)
                selected_members.append(member.member_name)
                published_counts["texte"] += 1
                selected_text_ids.add(canonical["id"])
                selected_text_paths_seen.add(member.member_name)
                LOGGER.info("Published LEGI text pivot | id=%s path=%s", canonical["id"], path)
                continue

            pending_children.append((canonical, archive.name, member.member_name))

        if _can_stop_scan(published_counts, max_texts, max_articles, max_sections):
            break

    if normalized_target_text_ids:
        LOGGER.info(
            "Text pass complete | selected_text_ids=%s cid_to_legi=%s pending_children=%s",
            sorted(selected_text_ids),
            cid_to_legi,
            len(pending_children),
        )

    for canonical, archive_name, member_name in pending_children:
        entity_type = canonical["entity_type"]
        canonical = _rewrite_parent_to_legi(canonical, cid_to_legi)
        parent_text_id = (canonical.get("context") or {}).get("parent_text_id")

        if entity_type == "article":
            if not _can_publish_article(
                parent_text_id,
                selected_text_ids,
                published_counts,
                published_articles_per_text,
                max_articles,
                max_articles_per_text,
            ):
                if normalized_target_text_ids and parent_text_id in normalized_target_text_ids:
                    LOGGER.debug(
                        "Skipping targeted article due to quota | article=%s parent_text_id=%s count_for_parent=%s",
                        canonical.get("id"),
                        parent_text_id,
                        published_articles_per_text.get(parent_text_id, 0),
                    )
                continue
        elif entity_type == "section":
            if not _can_publish_section(
                parent_text_id,
                selected_text_ids,
                published_counts,
                published_sections_per_text,
                max_sections,
                max_sections_per_text,
            ):
                if normalized_target_text_ids and parent_text_id in normalized_target_text_ids:
                    LOGGER.debug(
                        "Skipping targeted section due to quota | section=%s parent_text_id=%s count_for_parent=%s",
                        canonical.get("id"),
                        parent_text_id,
                        published_sections_per_text.get(parent_text_id, 0),
                    )
                continue
        else:
            continue

        try:
            validate_canonical(canonical)
        except Exception:
            continue

        path = compute_datasource_path(canonical)
        writer.write_json(path, canonical)
        manifests.add(canonical, path)
        current_member_name = member_name
        LOGGER.info(
            "Collecting mapping candidate | type=%s id=%s parent_text_id=%s code_id=%s cid=%s legi_id=%s member=%s",
            canonical.get("entity_type"),
            canonical.get("id"),
            (canonical.get("context") or {}).get("parent_text_id"),
            (canonical.get("context") or {}).get("code_id"),
            (canonical.get("source_ids") or {}).get("cid"),
            (canonical.get("source_ids") or {}).get("legi_id"),
            current_member_name,
        )
        mappings.collect_from_object(canonical)
        published.append(path)
        selected_members.append(member_name)
        published_counts[entity_type] += 1

        if entity_type == "article" and parent_text_id:
            published_articles_per_text[parent_text_id] = published_articles_per_text.get(parent_text_id, 0) + 1
        if entity_type == "section" and parent_text_id:
            published_sections_per_text[parent_text_id] = published_sections_per_text.get(parent_text_id, 0) + 1

        LOGGER.info("Published LEGI child | type=%s parent_text_id=%s path=%s", entity_type, parent_text_id, path)

        if _can_stop_scan(published_counts, max_texts, max_articles, max_sections):
            break

    if normalized_target_text_ids:
        missing_target_texts = sorted(normalized_target_text_ids - selected_text_ids)
        if missing_target_texts:
            raise RuntimeError(f"Some target LEGI text IDs were not found/published: {missing_target_texts}")

    if published_counts["texte"] == 0:
        raise RuntimeError("No LEGI text object could be parsed and published from archive")
    if published_counts["article"] == 0:
        raise RuntimeError("No LEGI article object could be parsed and published from archive")
    if published_counts["section"] == 0:
        raise RuntimeError("No LEGI section object could be parsed and published from archive")

    run_name = f"legi_bootstrap_minimal_{archive.stem.replace('.', '_')}"
    manifest_paths = manifests.flush(writer, run_name)
    mapping_paths = mappings.flush(writer)

    result = {
        "archive": str(archive),
        "selected_members": selected_members,
        "published_paths": published,
        "manifest_paths": manifest_paths,
        "mapping_paths": mapping_paths,
        "published_counts": published_counts,
        "target_text_ids": sorted(normalized_target_text_ids),
        "selected_text_ids": sorted(selected_text_ids),
        "published_articles_per_text": published_articles_per_text,
        "published_sections_per_text": published_sections_per_text,
        "limits": {
            "max_texts": max_texts,
            "max_articles": max_articles,
            "max_sections": max_sections,
            "max_articles_per_text": max_articles_per_text,
            "max_sections_per_text": max_sections_per_text,
        },
    }

    LOGGER.info("LEGI roundtrip complete | result=%s", result)
    return result
