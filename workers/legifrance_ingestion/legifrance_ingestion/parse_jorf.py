from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any
from xml.etree import ElementTree as ET

from .archive_reader import ArchiveMember

LOGGER = logging.getLogger("legifrance_ingestion.parse_jorf")


@dataclass
class ParsedJorfObject:
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

    if '/texte/' in name or tag in {'TEXTELR', 'TEXTE_VERSION'}:
        return 'texte'
    raise ValueError(f"Unsupported JORF kind for V1: member={member_name} root_tag={root_tag}")


def _parse_links(root: ET.Element) -> list[dict[str, Any]]:
    links: list[dict[str, Any]] = []
    for link in root.findall('.//LIENS/LIEN'):
        target_id = link.attrib.get('id') or None
        link_type = link.attrib.get('typelien') or None
        direction = link.attrib.get('sens') or None
        surface = (link.text or '').strip() or None

        if not (target_id or link_type or surface):
            continue

        item: dict[str, Any] = {
            "link_type": link_type or "UNKNOWN",
            "direction": direction or "unknown",
            "target": {},
        }
        if target_id:
            item["target"]["id"] = target_id
        if link.attrib.get('cidtexte'):
            item["target"]["cid"] = link.attrib.get('cidtexte')
        if link.attrib.get('naturetexte'):
            item["target"]["nature"] = link.attrib.get('naturetexte')
        if link.attrib.get('nortexte'):
            item["target"]["nor"] = link.attrib.get('nortexte')
        if link.attrib.get('num'):
            item["target"]["num"] = link.attrib.get('num')
        if link.attrib.get('numtexte'):
            item["target"]["num_text"] = link.attrib.get('numtexte')
        if link.attrib.get('datesignatexte'):
            item["target"]["date_signature"] = link.attrib.get('datesignatexte')
        if surface:
            item["surface"] = surface
        links.append(item)
    return links


def parse_jorf_member(member: ArchiveMember) -> list[dict[str, Any]]:
    root = ET.fromstring(member.content)
    kind = _detect_kind(member.member_name, root.tag)

    if kind == 'texte':
        return [parse_jorf_texte(root).to_raw_obj()]

    raise ValueError(f"Unsupported parsed JORF kind: {kind}")


def parse_jorf_texte(root: ET.Element) -> ParsedJorfObject:
    texte_id = _text_or_none(root, './/META/META_COMMUN/ID') or 'UNKNOWN_JORF_TEXTE_ID'
    nature = _text_or_none(root, './/META/META_COMMUN/NATURE') or 'Texte'
    title = (
        _text_or_none(root, './/META/META_SPEC/META_TEXTE_CHRONICLE/TITRE')
        or _text_or_none(root, './/TITRE')
        or texte_id
    )
    title_full = _text_or_none(root, './/META/META_SPEC/META_TEXTE_CHRONICLE/TITREFULL')
    cid = _text_or_none(root, './/META/META_SPEC/META_TEXTE_CHRONICLE/CID')
    nor = _text_or_none(root, './/META/META_SPEC/META_TEXTE_CHRONICLE/NOR')
    eli = _text_or_none(root, './/META/META_COMMUN/ID_ELI')
    date_signature = _text_or_none(root, './/META/META_SPEC/META_TEXTE_CHRONICLE/DATE_TEXTE')
    date_publication = _text_or_none(root, './/META/META_SPEC/META_TEXTE_CHRONICLE/DATE_PUBLI')
    etat = _text_or_none(root, './/META/META_SPEC/META_TEXTE_VERSION/ETAT')
    date_debut = _text_or_none(root, './/META/META_SPEC/META_TEXTE_VERSION/DATE_DEBUT')
    date_fin = _text_or_none(root, './/META/META_SPEC/META_TEXTE_VERSION/DATE_FIN')

    contenu_node = root.find('.//BLOC_TEXTUEL/CONTENU')
    content_html = _inner_xml(contenu_node)
    content_text = ''.join(contenu_node.itertext()).strip() if contenu_node is not None else None
    links = _parse_links(root)

    # In JORF V1 we may only know the JORF text itself; bridge to LEGI can come later
    return ParsedJorfObject(
        entity_type='texte',
        corpus='JORF',
        id=texte_id,
        title=title,
        nature=nature,
        content={
            'text': content_text,
            'html': content_html,
        },
        context={},
        extra={
            'cid': cid,
            'jorf_id': texte_id,
            'nor': nor,
            'eli': eli,
            'title_full': title_full,
            'date_signature': date_signature,
            'date_publication': date_publication,
            'date_debut': date_debut,
            'date_fin': date_fin,
            'etat': etat,
            'document_kind': 'regulatory_publication',
            'links_explicit': links,
        },
    )
