from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any
from xml.etree import ElementTree as ET

from .archive_reader import ArchiveMember

LOGGER = logging.getLogger("legifrance_ingestion.parse_jade")


@dataclass
class ParsedJadeObject:
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

    if tag in {"TEXTE_JURI_ADMIN", "DECISION", "CETA"}:
        return "decision"

    if "/jade/" in name and name.endswith('.xml'):
        return "decision"

    raise ValueError(f"Unsupported JADE kind for member={member_name} root_tag={root_tag}")


def parse_jade_decision(root: ET.Element) -> ParsedJadeObject:
    decision_id = _text_or_none(root, './/META/META_COMMUN/ID') or 'UNKNOWN_DECISION_ID'
    title = _text_or_none(root, './/META/META_SPEC/META_JURI/TITRE') or decision_id
    nature = _text_or_none(root, './/META/META_COMMUN/NATURE') or 'Decision'

    date_decision = _text_or_none(root, './/META/META_SPEC/META_JURI/DATE_DEC')
    jurisdiction = _text_or_none(root, './/META/META_SPEC/META_JURI/JURIDICTION')
    formation = _text_or_none(root, './/META/META_SPEC/META_JURI_ADMIN/FORMATION')
    decision_number = _text_or_none(root, './/META/META_SPEC/META_JURI/NUMERO')
    solution = _text_or_none(root, './/META/META_SPEC/META_JURI/SOLUTION')
    ecli = _text_or_none(root, './/META/META_SPEC/META_JURI_ADMIN/ECLI')

    contenu_node = root.find('.//TEXTE/BLOC_TEXTUEL/CONTENU')
    content_html = _inner_xml(contenu_node)
    content_text = ''.join(contenu_node.itertext()).strip() if contenu_node is not None else None

    summary = _text_or_none(root, './/TEXTE/SOMMAIRE/ANA')

    return ParsedJadeObject(
        entity_type='decision',
        corpus='JADE',
        id=decision_id,
        title=title,
        nature=nature,
        content={
            'text': content_text,
            'html': content_html,
            **({'summary': summary} if summary else {}),
        },
        context={
            'jurisdiction': jurisdiction,
            'formation': formation,
        },
        extra={
            'date_decision': date_decision,
            'decision_number': decision_number,
            'solution': solution,
            'ecli': ecli,
            'document_kind': 'decision',
        },
    )


def parse_jade_member(member: ArchiveMember) -> list[dict[str, Any]]:
    root = ET.fromstring(member.content)
    kind = _detect_kind(member.member_name, root.tag)

    if kind == 'decision':
        return [parse_jade_decision(root).to_raw_obj()]

    raise ValueError(f"Unsupported parsed kind: {kind}")
