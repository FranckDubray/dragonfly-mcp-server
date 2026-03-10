from __future__ import annotations

from datetime import datetime, timezone
from typing import Any


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def normalize_open_end_date(value: str | None) -> str | None:
    if not value:
        return None
    if value == "2999-01-01":
        return None
    return value


def add_if_present(target: dict[str, Any], key: str, value: Any) -> None:
    if value is None:
        return
    if value == "":
        return
    if value == []:
        return
    if value == {}:
        return
    target[key] = value


def build_provenance(raw_obj: dict[str, Any], archive_name: str, source_xml_path: str) -> dict[str, Any]:
    return {
        "archive_name": archive_name,
        "source_xml_path": source_xml_path,
        "ingested_at": now_iso(),
    }


def build_common_base(raw_obj: dict[str, Any], archive_name: str, source_xml_path: str) -> dict[str, Any]:
    obj = {
        "schema_version": "1.1",
        "entity_type": raw_obj["entity_type"],
        "corpus": raw_obj["corpus"],
        "id": raw_obj["id"],
        "source_ids": {
            "primary": raw_obj["id"],
        },
        "titles": {
            "title": raw_obj.get("title") or raw_obj["id"],
        },
        "nature": {
            "nature": raw_obj.get("nature", "UNKNOWN"),
        },
        "content": raw_obj.get("content", {}),
        "context": raw_obj.get("context", {}),
        "provenance": build_provenance(raw_obj, archive_name, source_xml_path),
    }

    source_ids = obj["source_ids"]
    add_if_present(source_ids, "cid", raw_obj.get("cid"))
    add_if_present(source_ids, "nor", raw_obj.get("nor"))
    add_if_present(source_ids, "eli", raw_obj.get("eli"))
    add_if_present(source_ids, "ecli", raw_obj.get("ecli"))
    add_if_present(source_ids, "jorf_id", raw_obj.get("jorf_id"))
    add_if_present(source_ids, "legi_id", raw_obj.get("legi_id"))

    titles = obj["titles"]
    add_if_present(titles, "title_full", raw_obj.get("title_full"))

    dates: dict[str, Any] = {}
    add_if_present(dates, "date_signature", raw_obj.get("date_signature"))
    add_if_present(dates, "date_publication", raw_obj.get("date_publication"))
    add_if_present(dates, "date_decision", raw_obj.get("date_decision"))
    add_if_present(dates, "date_debut", normalize_open_end_date(raw_obj.get("date_debut")))
    add_if_present(dates, "date_fin", normalize_open_end_date(raw_obj.get("date_fin")))
    if dates:
        obj["dates"] = dates

    status: dict[str, Any] = {}
    add_if_present(status, "etat", raw_obj.get("etat"))
    if raw_obj.get("etat"):
        status["is_in_force"] = raw_obj.get("etat") == "VIGUEUR"
    if status:
        obj["status"] = status

    explicit_links = raw_obj.get("links_explicit") or []
    if explicit_links:
        obj["links_explicit"] = explicit_links

    return obj


def build_canonical_article(raw_obj: dict[str, Any], archive_name: str, source_xml_path: str) -> dict[str, Any]:
    obj = build_common_base(raw_obj, archive_name, source_xml_path)
    obj["article_metadata"] = {
        "article_num": raw_obj["article_num"],
    }
    return obj


def build_canonical_section(raw_obj: dict[str, Any], archive_name: str, source_xml_path: str) -> dict[str, Any]:
    obj = build_common_base(raw_obj, archive_name, source_xml_path)
    obj["section_metadata"] = {
        "section_title": raw_obj["section_title"],
    }
    add_if_present(obj["section_metadata"], "section_kind", raw_obj.get("section_kind"))
    add_if_present(obj["section_metadata"], "section_level", raw_obj.get("section_level"))
    return obj


def build_canonical_texte(raw_obj: dict[str, Any], archive_name: str, source_xml_path: str) -> dict[str, Any]:
    obj = build_common_base(raw_obj, archive_name, source_xml_path)
    metadata: dict[str, Any] = {}
    add_if_present(metadata, "num", raw_obj.get("num"))
    add_if_present(metadata, "document_kind", raw_obj.get("document_kind"))
    if metadata:
        obj["text_metadata"] = metadata
    return obj


def map_to_canonical_json(raw_obj: dict[str, Any], archive_name: str, source_xml_path: str) -> dict[str, Any]:
    entity_type = raw_obj["entity_type"]

    if entity_type == "article":
        return build_canonical_article(raw_obj, archive_name, source_xml_path)
    if entity_type == "section":
        return build_canonical_section(raw_obj, archive_name, source_xml_path)
    if entity_type == "texte":
        return build_canonical_texte(raw_obj, archive_name, source_xml_path)

    raise ValueError(f"Unsupported entity_type for V1 mapper: {entity_type}")
