from __future__ import annotations

import logging
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any

from .http_writer import DragonflyWriter

LOGGER = logging.getLogger("legifrance_ingestion.mappings")


@dataclass
class MappingCollector:
    rows_by_mapping: dict[str, list[dict[str, Any]]] = field(default_factory=lambda: defaultdict(list))

    def collect_from_object(self, obj: dict[str, Any]) -> None:
        entity_type = obj["entity_type"]
        corpus = obj["corpus"]
        object_id = obj["id"]
        context = obj.get("context") or {}
        source_ids = obj.get("source_ids") or {}

        if entity_type == "article":
            parent_text_id = context.get("parent_text_id")
            if parent_text_id:
                self.rows_by_mapping["article_to_text"].append(
                    {"source_id": object_id, "target_id": parent_text_id, "corpus": corpus}
                )
                LOGGER.info(
                    "Mapping append | mapping=article_to_text source_id=%s target_id=%s corpus=%s",
                    object_id,
                    parent_text_id,
                    corpus,
                )

                self.rows_by_mapping["text_to_articles"].append(
                    {"source_id": parent_text_id, "target_id": object_id, "corpus": corpus}
                )
                LOGGER.info(
                    "Mapping append | mapping=text_to_articles source_id=%s target_id=%s corpus=%s",
                    parent_text_id,
                    object_id,
                    corpus,
                )
            else:
                LOGGER.warning(
                    "Mapping skip | type=article id=%s reason=no_parent_text_id context=%s source_ids=%s",
                    object_id,
                    context,
                    source_ids,
                )

            parent_section_id = context.get("parent_section_id")
            if parent_section_id:
                self.rows_by_mapping["section_to_articles"].append(
                    {"source_id": parent_section_id, "target_id": object_id, "corpus": corpus}
                )
                LOGGER.info(
                    "Mapping append | mapping=section_to_articles source_id=%s target_id=%s corpus=%s",
                    parent_section_id,
                    object_id,
                    corpus,
                )

        if entity_type == "section":
            parent_text_id = context.get("parent_text_id")
            if parent_text_id:
                self.rows_by_mapping["section_to_text"].append(
                    {"source_id": object_id, "target_id": parent_text_id, "corpus": corpus}
                )
                LOGGER.info(
                    "Mapping append | mapping=section_to_text source_id=%s target_id=%s corpus=%s",
                    object_id,
                    parent_text_id,
                    corpus,
                )

                self.rows_by_mapping["text_to_sections"].append(
                    {"source_id": parent_text_id, "target_id": object_id, "corpus": corpus}
                )
                LOGGER.info(
                    "Mapping append | mapping=text_to_sections source_id=%s target_id=%s corpus=%s",
                    parent_text_id,
                    object_id,
                    corpus,
                )
            else:
                LOGGER.warning(
                    "Mapping skip | type=section id=%s reason=no_parent_text_id context=%s source_ids=%s",
                    object_id,
                    context,
                    source_ids,
                )

            parent_section_id = context.get("parent_section_id")
            if parent_section_id:
                self.rows_by_mapping["section_to_children"].append(
                    {"source_id": parent_section_id, "target_id": object_id, "corpus": corpus}
                )
                LOGGER.info(
                    "Mapping append | mapping=section_to_children source_id=%s target_id=%s corpus=%s",
                    parent_section_id,
                    object_id,
                    corpus,
                )

        # Minimal LEGI -> JORF bridge
        if corpus == "LEGI":
            bridge_target = (
                source_ids.get("jorf_id")
                or (source_ids.get("cid") if str(source_ids.get("cid", "")).startswith("JORFTEXT") else None)
                or (context.get("parent_text_id") if str(context.get("parent_text_id", "")).startswith("JORFTEXT") else None)
            )
            if bridge_target:
                self.rows_by_mapping["legi_to_jorf"].append(
                    {"source_id": object_id, "target_id": bridge_target, "corpus": corpus}
                )
                LOGGER.info(
                    "Mapping append | mapping=legi_to_jorf source_id=%s target_id=%s corpus=%s",
                    object_id,
                    bridge_target,
                    corpus,
                )
                self.rows_by_mapping["jorf_to_legi"].append(
                    {"source_id": bridge_target, "target_id": object_id, "corpus": corpus}
                )
                LOGGER.info(
                    "Mapping append | mapping=jorf_to_legi source_id=%s target_id=%s corpus=%s",
                    bridge_target,
                    object_id,
                    corpus,
                )

        # Direct JORF -> LEGI bridge if already known in the object
        if corpus == "JORF":
            legi_id = source_ids.get("legi_id")
            if legi_id:
                self.rows_by_mapping["jorf_to_legi"].append(
                    {"source_id": object_id, "target_id": legi_id, "corpus": corpus}
                )
                LOGGER.info(
                    "Mapping append | mapping=jorf_to_legi source_id=%s target_id=%s corpus=%s",
                    object_id,
                    legi_id,
                    corpus,
                )
                self.rows_by_mapping["legi_to_jorf"].append(
                    {"source_id": legi_id, "target_id": object_id, "corpus": corpus}
                )
                LOGGER.info(
                    "Mapping append | mapping=legi_to_jorf source_id=%s target_id=%s corpus=%s",
                    legi_id,
                    object_id,
                    corpus,
                )

    def flush(self, writer: DragonflyWriter) -> list[str]:
        written_paths: list[str] = []
        for mapping_name, rows in self.rows_by_mapping.items():
            LOGGER.info(
                "Flushing mapping | mapping=%s raw_rows=%s",
                mapping_name,
                len(rows),
            )
            deduped_rows = _dedupe_rows(rows)
            LOGGER.info(
                "Flushing mapping | mapping=%s deduped_rows=%s",
                mapping_name,
                len(deduped_rows),
            )
            path = f"_meta/mappings/{mapping_name}.jsonl"
            writer.write_jsonl(path, deduped_rows)
            LOGGER.info(
                "Flushed mapping | mapping=%s path=%s",
                mapping_name,
                path,
            )
            written_paths.append(path)
        return written_paths


def _dedupe_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen: set[tuple[str, str, str]] = set()
    deduped: list[dict[str, Any]] = []
    for row in rows:
        key = (
            str(row.get("source_id")),
            str(row.get("target_id")),
            str(row.get("corpus")),
        )
        if key in seen:
            continue
        seen.add(key)
        deduped.append(row)
    return deduped
