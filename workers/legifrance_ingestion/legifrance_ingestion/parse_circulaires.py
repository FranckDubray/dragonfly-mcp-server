from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any
from xml.etree import ElementTree as ET

from .archive_reader import ArchiveMember

LOGGER = logging.getLogger("legifrance_ingestion.parse_circulaires")


@dataclass
class ParsedCirculairesObject:
    entity_type: str
    corpus: str
    id: str
    title: str
    nature: str
    content: dict[str, Any]
    context: dict[str, Any]
    extra: dict[str, Any]

    def to_raw_obj(self) -> dict[str, Any]:
        raw = {
            "entity_type": self.entity_type,
            "corpus": self.corpus,
            "id": self.id,
            "title": self.title,
            "nature": self.nature,
            "content": self.content,
            "context": self.context,
        }
        raw.update(self.extra)
        return raw


def _text_or_none(node: ET.Element | None, xpath: str) -> str | None:
    if node is None:
        return None
    found = node.find(xpath)
    if found is None or found.text is None:
        return None
    value = found.text.strip()
    return value or None


def _inner_xml(node: ET.Element | None) -> str | None:
    if node is None:
        return None
    parts: list[str] = []
    if node.text and node.text.strip():
        parts.append(node.text.strip())
    for child in node:
        parts.append(ET.tostring(child, encoding="unicode"))
    joined = "".join(parts).strip()
    return joined or None


def _detect_kind(member_name: str, root_tag: str) -> str:
    name = member_name.lower()
    tag = root_tag.upper()

    if tag in {"CIRCULAIRE", "TEXTE_CIRCULAIRE"}:
        return "texte"

    if "/circulaires/" in name and name.endswith(".xml"):
        return "texte"

    raise ValueError(
        f"Unsupported CIRCULAIRES kind for member={member_name} root_tag={root_tag}"
    )


def parse_circulaire_texte(root: ET.Element) -> ParsedCirculairesObject:
    circulaire_id = (
        _text_or_none(root, ".//ID")
        or _text_or_none(root, ".//META/META_COMMUN/ID")
        or _text_or_none(root, ".//ID_CIRCULAIRE")
        or "UNKNOWN_CIRCULAIRE_ID"
    )

    title = (
        _text_or_none(root, ".//TITRE")
        or _text_or_none(root, ".//META/META_SPEC/TITRE")
        or circulaire_id
    )

    nature = _text_or_none(root, ".//NATURE") or "Circulaire"

    date_signature = _text_or_none(root, ".//DATE_SIGNATURE")
    date_depot = _text_or_none(root, ".//DATE_DEPOT")
    date_mise_en_application = _text_or_none(root, ".//DATE_MISE_EN_APPLICATION")
    author = _text_or_none(root, ".//AUTEUR")
    signataire = _text_or_none(root, ".//SIGNATAIRE")
    destinataire = _text_or_none(root, ".//DESTINATAIRE")
    resume = _text_or_none(root, ".//RESUME")
    nor = _text_or_none(root, ".//NUMERO_NOR")

    pdf_path = (
        _text_or_none(root, ".//NOM_FICHIER_PDF")
        or _text_or_none(root, ".//PDF")
    )

    content_node = root.find(".//CONTENU")
    content_text = "".join(content_node.itertext()).strip() if content_node is not None else None
    content_html = _inner_xml(content_node) if content_node is not None else None

    return ParsedCirculairesObject(
        entity_type="texte",
        corpus="CIRCULAIRES",
        id=circulaire_id,
        title=title,
        nature=nature,
        content={
            **({"text": content_text} if content_text else {}),
            **({"html": content_html} if content_html else {}),
            **({"abstract": resume} if resume else {}),
        },
        context={},
        extra={
            "nor": nor,
            "date_signature": date_signature,
            "date_depot": date_depot,
            "date_mise_en_application": date_mise_en_application,
            "author": author,
            "signataire": signataire,
            "destinataire": destinataire,
            "pdf_path": pdf_path,
            "document_kind": "administrative_circular",
        },
    )


def parse_circulaires_member(member: ArchiveMember) -> list[dict[str, Any]]:
    root = ET.fromstring(member.content)
    kind = _detect_kind(member.member_name, root.tag)

    if kind == "texte":
        return [parse_circulaire_texte(root).to_raw_obj()]

    raise ValueError(f"Unsupported parsed kind: {kind}")
