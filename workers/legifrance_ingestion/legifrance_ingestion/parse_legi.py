from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any
from xml.etree import ElementTree as ET

from .archive_reader import ArchiveMember

LOGGER = logging.getLogger("legifrance_ingestion.parse_legi")


@dataclass
class ParsedLegiObject:
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

    if "/article/" in name or tag == "ARTICLE":
        return "article"
    if "/section_ta/" in name or tag == "SECTION_TA":
        return "section"
    if "/texte/" in name or tag in {"TEXTELR", "TEXTE_VERSION"}:
        return "texte"
    raise ValueError(f"Unsupported LEGI kind for member={member_name} root_tag={root_tag}")


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


def parse_legi_member(member: ArchiveMember) -> list[dict[str, Any]]:
    root = ET.fromstring(member.content)
    kind = _detect_kind(member.member_name, root.tag)

    if kind == "article":
        return [parse_legi_article(root).to_raw_obj()]
    if kind == "section":
        return [parse_legi_section(root).to_raw_obj()]
    if kind == "texte":
        return [parse_legi_texte(root).to_raw_obj()]

    raise ValueError(f"Unsupported parsed kind: {kind}")


def parse_legi_article(root: ET.Element) -> ParsedLegiObject:
    article_id = _text_or_none(root, './/META/META_COMMUN/ID') or 'UNKNOWN_ARTICLE_ID'
    article_num = _text_or_none(root, './/META/META_SPEC/META_ARTICLE/NUM') or article_id
    nature = _text_or_none(root, './/META/META_COMMUN/NATURE') or 'Article'
    etat = _text_or_none(root, './/META/META_SPEC/META_ARTICLE/ETAT')
    date_debut = _text_or_none(root, './/META/META_SPEC/META_ARTICLE/DATE_DEBUT')
    date_fin = _text_or_none(root, './/META/META_SPEC/META_ARTICLE/DATE_FIN')
    cid = _text_or_none(root, './/CONTEXTE/TEXTE/@cid')
    if cid is None:
        texte_node = root.find('.//CONTEXTE/TEXTE')
        cid = texte_node.attrib.get('cid') if texte_node is not None else None
        jorf_id = texte_node.attrib.get('cid') if texte_node is not None else None
        nor = texte_node.attrib.get('nor') if texte_node is not None else None
        text_nature = texte_node.attrib.get('nature') if texte_node is not None else None
    else:
        jorf_id = None
        nor = None
        text_nature = None

    texte_titre = _text_or_none(root, './/CONTEXTE/TEXTE/TITRE_TXT')
    contenu_node = root.find('.//BLOC_TEXTUEL/CONTENU')
    content_html = _inner_xml(contenu_node)
    content_text = ''.join(contenu_node.itertext()).strip() if contenu_node is not None else None
    links = _parse_links(root)

    return ParsedLegiObject(
        entity_type='article',
        corpus='LEGI',
        id=article_id,
        title=article_num,
        nature=nature,
        content={
            'text': content_text,
            'html': content_html,
        },
        context={
            'parent_text_id': cid,
            'code_id': cid,
            'code_title': texte_titre,
        },
        extra={
            'cid': cid,
            'jorf_id': jorf_id,
            'nor': nor,
            'article_num': article_num,
            'etat': etat,
            'date_debut': date_debut,
            'date_fin': date_fin,
            'document_kind': text_nature,
            'links_explicit': links,
        },
    )


def parse_legi_section(root: ET.Element) -> ParsedLegiObject:
    section_id = _text_or_none(root, './/META/META_COMMUN/ID') or 'UNKNOWN_SECTION_ID'
    section_title = _text_or_none(root, './/TITRE_TA') or section_id
    nature = _text_or_none(root, './/META/META_COMMUN/NATURE') or 'Section'
    texte_node = root.find('.//CONTEXTE/TEXTE')
    cid = texte_node.attrib.get('cid') if texte_node is not None else None

    parent_section_id = None
    # parent section is not directly available in all XMLs; left absent for V1 minimal parser

    return ParsedLegiObject(
        entity_type='section',
        corpus='LEGI',
        id=section_id,
        title=section_title,
        nature=nature,
        content={},
        context={
            'parent_text_id': cid,
            'parent_section_id': parent_section_id,
        },
        extra={
            'cid': cid,
            'section_title': section_title,
        },
    )


def parse_legi_texte(root: ET.Element) -> ParsedLegiObject:
    texte_id = _text_or_none(root, './/META/META_COMMUN/ID') or 'UNKNOWN_TEXTE_ID'
    title = (
        _text_or_none(root, './/META/META_SPEC/META_TEXTE_VERSION/TITRE')
        or _text_or_none(root, './/TITRE')
        or texte_id
    )
    title_full = _text_or_none(root, './/META/META_SPEC/META_TEXTE_VERSION/TITREFULL')
    nature = _text_or_none(root, './/META/META_COMMUN/NATURE') or 'Texte'
    cid = _text_or_none(root, './/META/META_SPEC/META_TEXTE_CHRONICLE/CID')
    nor = _text_or_none(root, './/META/META_SPEC/META_TEXTE_CHRONICLE/NOR')
    date_signature = _text_or_none(root, './/META/META_SPEC/META_TEXTE_CHRONICLE/DATE_TEXTE')
    date_publication = _text_or_none(root, './/META/META_SPEC/META_TEXTE_CHRONICLE/DATE_PUBLI')
    date_debut = _text_or_none(root, './/META/META_SPEC/META_TEXTE_VERSION/DATE_DEBUT')
    date_fin = _text_or_none(root, './/META/META_SPEC/META_TEXTE_VERSION/DATE_FIN')
    etat = _text_or_none(root, './/META/META_SPEC/META_TEXTE_VERSION/ETAT')
    links = _parse_links(root)

    return ParsedLegiObject(
        entity_type='texte',
        corpus='LEGI',
        id=texte_id,
        title=title,
        nature=nature,
        content={},
        context={},
        extra={
            'cid': cid,
            'legi_id': texte_id,
            'nor': nor,
            'title_full': title_full,
            'date_signature': date_signature,
            'date_publication': date_publication,
            'date_debut': date_debut,
            'date_fin': date_fin,
            'etat': etat,
            'document_kind': 'normative_text',
            'links_explicit': links,
        },
    )
