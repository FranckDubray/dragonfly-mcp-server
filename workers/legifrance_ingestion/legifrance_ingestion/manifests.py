from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any

from .http_writer import DragonflyWriter


@dataclass
class ManifestCollector:
    entries_by_corpus: dict[str, list[dict[str, Any]]] = field(default_factory=lambda: defaultdict(list))

    def add(self, obj: dict[str, Any], path: str) -> None:
        corpus = obj["corpus"].lower()
        self.entries_by_corpus[corpus].append(
            {
                "id": obj["id"],
                "entity_type": obj["entity_type"],
                "corpus": obj["corpus"],
                "path": path,
                "archive_name": obj["provenance"]["archive_name"],
                "ingested_at": obj["provenance"]["ingested_at"],
            }
        )

    def flush(self, writer: DragonflyWriter, run_name: str) -> list[str]:
        written_paths: list[str] = []
        for corpus, rows in self.entries_by_corpus.items():
            path = f"_meta/manifests/{corpus}/{run_name}.jsonl"
            writer.write_jsonl(path, rows)
            written_paths.append(path)
        return written_paths
