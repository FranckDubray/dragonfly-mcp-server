from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any
from xml.etree import ElementTree as ET

from .archive_reader import ArchiveMember

LOGGER = logging.getLogger("legifrance_ingestion.parse_kali")


@dataclass
class ParsedKaliObject:
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


def _context_texte_node(root: ET.Element) -> ET.Element | None:
    return root.find('.//CONTEXTE/TEXTE')


def _extract_context_ids(root: ET.Element) -> dict[str, str | None]:
    texte_node = _context_texte_node(root)
    if texte_node is None:
        return {
            "cid": None,
            "nor": None,
            "text_nature": None,
            "texte_titre": None,
        }

    cid = texte_node.attrib.get('cid') or None
    nor = texte_node.attrib.get('nor') or None
    text_nature = texte_node.attrib.get('nature') or None
    texte_titre = _text_or_none(texte_node, './TITRE_TXT')

    return {
        "cid": cid,
        "nor": nor,
        "text_nature": text_nature,
        "texte_titre": texte_titre,
    }


def _detect_kind(member_name: str, root_tag: str) -> str:
    name = member_name.lower()
    tag = root_tag.upper()

    if tag == 'ARTICLE':
        return 'article'
    if tag == 'SECTION_TA':
        return 'section'
    if tag in {'TEXTEKALI', 'TEXTE_VERSION'}:
        return 'texte'

    if '/article/' in name:
        return 'article'
    if '/section_ta/' in name or '/section/' in name:
        return 'section'
    if '/texte/' in name:
        return 'texte'

    raise ValueError(f"Unsupported KALI kind for member={member_name} root_tag={root_tag}")


def parse_kali_article(root: ET.Element) -> ParsedKaliObject:
    article_id = _text_or_none(root, './/META/META_COMMUN/ID') or 'UNKNOWN_ARTICLE_ID'
    article_num = _text_or_none(root, './/META/META_SPEC/META_ARTICLE/NUM') or article_id
    article_title = _text_or_none(root, './/META/META_SPEC/META_ARTICLE/TITRE') or article_num
    nature = _text_or_none(root, './/META/META_COMMUN/NATURE') or 'Article'
    etat = _text_or_none(root, './/META/META_SPEC/META_ARTICLE/ETAT')
    date_debut = _text_or_none(root, './/META/META_SPEC/META_ARTICLE/DATE_DEBUT')
    date_fin = _text_or_none(root, './/META/META_SPEC/META_ARTICLE/DATE_FIN')

    context_data = _extract_context_ids(root)
    contenu_node = root.find('.//BLOC_TEXTUEL/CONTENU')
    content_html = _inner_xml(contenu_node)
    content_text = ''.join(contenu_node.itertext()).strip() if contenu_node is not None else None

    return ParsedKaliObject(
        entity_type='article',
        corpus='KALI',
        id=article_id,
        title=article_title,
        nature=nature,
        content={
            'text': content_text,
            'html': content_html,
        },
        context={
            'parent_text_id': context_data['cid'],
            'parent_section_id': None,
            'code_id': context_data['cid'],
            'code_title': context_data['texte_titre'],
        },
        extra={
            'cid': context_data['cid'],
            'nor': context_data['nor'],
            'article_num': article_num,
            'etat': etat,
            'date_debut': date_debut,
            'date_fin': date_fin,
            'document_kind': context_data['text_nature'],
        },
    )


def parse_kali_section(root: ET.Element, member_name: str) -> ParsedKaliObject:
    section_id = _text_or_none(root, './/META/META_COMMUN/ID')
    if not section_id:
        lower_name = member_name.lower()
        if lower_name.endswith('.xml'):
            section_id = member_name.rsplit('/', 1)[-1].replace('.xml', '')
    if not section_id:
        section_id = 'UNKNOWN_SECTION_ID'

    section_title = _text_or_none(root, './/TITRE_TA') or section_id
    nature = _text_or_none(root, './/META/META_COMMUN/NATURE') or 'Section'
    context_data = _extract_context_ids(root)

    return ParsedKaliObject(
        entity_type='section',
        corpus='KALI',
        id=section_id,
        title=section_title,
        nature=nature,
        content={},
        context={
            'parent_text_id': context_data['cid'],
            'parent_section_id': None,
        },
        extra={
            'cid': context_data['cid'],
            'nor': context_data['nor'],
            'section_title': section_title,
        },
    )


def parse_kali_texte(root: ET.Element) -> ParsedKaliObject:
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
    date_debut = _text_or_none(root, './/META/META_SPEC/META_TEXTE_VERSION/DATE_DEBUT')
    date_fin = _text_or_none(root, './/META/META_SPEC/META_TEXTE_VERSION/DATE_FIN')
    etat = _text_or_none(root, './/META/META_SPEC/META_TEXTE_VERSION/ETAT')

    return ParsedKaliObject(
        entity_type='texte',
        corpus='KALI',
        id=texte_id,
        title=title,
        nature=nature,
        content={},
        context={},
        extra={
            'cid': cid,
            'nor': nor,
            'title_full': title_full,
            'date_signature': date_signature,
            'date_debut': date_debut,
            'date_fin': date_fin,
            'etat': etat,
            'document_kind': 'conventional_text',
        },
    )


def parse_kali_member(member: ArchiveMember) -> list[dict[str, Any]]:
    root = ET.fromstring(member.content)
    kind = _detect_kind(member.member_name, root.tag)

    if kind == 'article':
        return [parse_kali_article(root).to_raw_obj()]
    if kind == 'section':
        return [parse_kali_section(root, member.member_name).to_raw_obj()]
    if kind == 'texte':
        return [parse_kali_texte(root).to_raw_obj()]

    raise ValueError(f"Unsupported parsed kind: {kind}")
