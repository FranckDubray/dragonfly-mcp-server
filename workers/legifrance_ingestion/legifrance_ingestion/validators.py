from __future__ import annotations

from typing import Any


class CanonicalValidationError(ValueError):
    """Raised when a canonical object does not meet minimal invariants."""


SUPPORTED_ENTITY_TYPES = {"texte", "article", "section", "conteneur", "decision"}
SUPPORTED_CORPORA = {
    "LEGI",
    "JORF",
    "KALI",
    "CASS",
    "INCA",
    "CAPP",
    "JADE",
    "CONSTIT",
    "CNIL",
    "CIRCULAIRES",
}


def validate_canonical(obj: dict[str, Any]) -> None:
    if not obj.get("schema_version"):
        raise CanonicalValidationError("Missing schema_version")

    entity_type = obj.get("entity_type")
    if entity_type not in SUPPORTED_ENTITY_TYPES:
        raise CanonicalValidationError(f"Unsupported entity_type: {entity_type}")

    corpus = obj.get("corpus")
    if corpus not in SUPPORTED_CORPORA:
        raise CanonicalValidationError(f"Unsupported corpus: {corpus}")

    if not obj.get("id"):
        raise CanonicalValidationError("Missing id")

    provenance = obj.get("provenance") or {}
    if not provenance.get("source_xml_path"):
        raise CanonicalValidationError("Missing provenance.source_xml_path")
    if not provenance.get("archive_name"):
        raise CanonicalValidationError("Missing provenance.archive_name")
    if not provenance.get("ingested_at"):
        raise CanonicalValidationError("Missing provenance.ingested_at")

    source_ids = obj.get("source_ids") or {}
    if not source_ids.get("primary"):
        raise CanonicalValidationError("Missing source_ids.primary")

    titles = obj.get("titles") or {}
    if not titles.get("title"):
        raise CanonicalValidationError("Missing titles.title")

    if entity_type == "article":
        article_metadata = obj.get("article_metadata") or {}
        if not article_metadata.get("article_num"):
            raise CanonicalValidationError("Missing article_metadata.article_num")
        context = obj.get("context") or {}
        if not context.get("parent_text_id"):
            raise CanonicalValidationError("Missing context.parent_text_id for article")

    if entity_type == "section":
        section_metadata = obj.get("section_metadata") or {}
        if not section_metadata.get("section_title"):
            raise CanonicalValidationError("Missing section_metadata.section_title")
        context = obj.get("context") or {}
        if not context.get("parent_text_id"):
            raise CanonicalValidationError("Missing context.parent_text_id for section")

    if entity_type == "conteneur":
        container_metadata = obj.get("container_metadata") or {}
        if not container_metadata.get("container_kind"):
            raise CanonicalValidationError("Missing container_metadata.container_kind")
        if not container_metadata.get("container_title"):
            raise CanonicalValidationError("Missing container_metadata.container_title")

    if entity_type == "decision":
        decision_metadata = obj.get("decision_metadata") or {}
        # Minimal CASS/CNIL/JADE/... V1: jurisdiction is desirable but not strictly blocking.
        # Keep decision objects publishable as long as the core canonical invariants are present.
        if not decision_metadata:
            raise CanonicalValidationError("Missing decision_metadata")
