from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any

from .http_writer import DragonflyWriter


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
                self.rows_by_mapping["text_to_articles"].append(
                    {"source_id": parent_text_id, "target_id": object_id, "corpus": corpus}
                )

            parent_section_id = context.get("parent_section_id")
            if parent_section_id:
                self.rows_by_mapping["section_to_articles"].append(
                    {"source_id": parent_section_id, "target_id": object_id, "corpus": corpus}
                )

        if entity_type == "section":
            parent_text_id = context.get("parent_text_id")
            if parent_text_id:
                self.rows_by_mapping["section_to_text"].append(
                    {"source_id": object_id, "target_id": parent_text_id, "corpus": corpus}
                )

            parent_section_id = context.get("parent_section_id")
            if parent_section_id:
                self.rows_by_mapping["section_to_children"].append(
                    {"source_id": parent_section_id, "target_id": object_id, "corpus": corpus}
                )

        jorf_id = source_ids.get("jorf_id")
        legi_id = source_ids.get("legi_id")
        if corpus == "LEGI" and jorf_id:
            self.rows_by_mapping["legi_to_jorf"].append(
                {"source_id": object_id, "target_id": jorf_id, "corpus": corpus}
            )
        if corpus == "JORF" and legi_id:
            self.rows_by_mapping["jorf_to_legi"].append(
                {"source_id": object_id, "target_id": legi_id, "corpus": corpus}
            )

    def flush(self, writer: DragonflyWriter) -> list[str]:
        written_paths: list[str] = []
        for mapping_name, rows in self.rows_by_mapping.items():
            path = f"_meta/mappings/{mapping_name}.jsonl"
            writer.write_jsonl(path, rows)
            written_paths.append(path)
        return written_paths
