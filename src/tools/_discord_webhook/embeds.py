from __future__ import annotations
from typing import Any, Dict, List, Optional
import re

EMBED_DESC_MAX = 4000
EMBEDS_PER_MESSAGE_MAX = 10
CONTENT_MAX = 2000

def make_embeds_from_article(article: Dict[str, Any], *, split_long_messages: bool = True) -> List[Dict[str, Any]]:
    title = article.get("title")
    url = article.get("url")
    if not title or not url:
        raise ValueError("article.title and article.url are required")

    color = article.get("color")
    excerpt = article.get("excerpt")
    body = article.get("body") or ""

    embeds: List[Dict[str, Any]] = []

    main_embed: Dict[str, Any] = {"title": title, "url": url}
    if excerpt:
        main_embed["description"] = excerpt[:4096]
    if color is not None:
        main_embed["color"] = int(color)
    author_name = article.get("author_name")
    if author_name:
        main_embed["author"] = {"name": author_name[:256]}
    image_url = article.get("image_url")
    if image_url:
        main_embed["image"] = {"url": image_url}
    thumb_url = article.get("thumbnail_url")
    if thumb_url:
        main_embed["thumbnail"] = {"url": thumb_url}

    fields = []
    tags = article.get("tags") or []
    if isinstance(tags, list) and tags:
        tag_text = " ".join(f"#{t}" for t in tags[:32])
        fields.append({"name": "Tags", "value": tag_text[:1024]})
    published_at = article.get("published_at")
    if published_at:
        fields.append({"name": "Publié", "value": str(published_at)[:1024]})
    if fields:
        main_embed["fields"] = fields[:25]

    embeds.append(main_embed)

    if body.strip():
        if split_long_messages:
            body_embeds = split_body_to_embeds(body, color=color)
            embeds.extend(body_embeds)
        else:
            e: Dict[str, Any] = {"description": body[:EMBED_DESC_MAX]}
            if color is not None:
                e["color"] = int(color)
            embeds.append(e)

    return embeds


def split_body_to_embeds(body: str, color: Optional[int] = None) -> List[Dict[str, Any]]:
    chunks: List[str] = []

    def is_in_code_block(s: str) -> bool:
        return s.count("```") % 2 == 1

    paragraphs = re.split(r"\n\n+", body)
    buf = ""
    for p in paragraphs:
        candidate = (buf + ("\n\n" if buf else "") + p) if buf else p
        if len(candidate) <= EMBED_DESC_MAX and not is_in_code_block(candidate):
            buf = candidate
        else:
            if buf:
                chunks.append(buf)
            chunks.extend(split_paragraph(p))
            buf = ""
    if buf:
        chunks.append(buf)

    normalized: List[str] = []
    for c in chunks:
        if len(c) <= EMBED_DESC_MAX and not is_in_code_block(c):
            normalized.append(c)
        else:
            normalized.extend(force_split_text(c))

    embeds: List[Dict[str, Any]] = []
    for part in normalized:
        e: Dict[str, Any] = {"description": part[:EMBED_DESC_MAX]}
        if color is not None:
            e["color"] = int(color)
        embeds.append(e)
    return embeds


def split_paragraph(p: str) -> List[str]:
    parts: List[str] = []
    current = ""
    for line in p.splitlines():
        candidate = (current + "\n" + line) if current else line
        if len(candidate) <= EMBED_DESC_MAX:
            current = candidate
        else:
            if current:
                parts.append(current)
            parts.extend(split_line(line))
            current = ""
    if current:
        parts.append(current)
    return parts


def split_line(line: str) -> List[str]:
    parts: List[str] = []
    current = ""
    for word in re.split(r"(\s+)", line):
        candidate = current + word
        if len(candidate) <= EMBED_DESC_MAX:
            current = candidate
        else:
            if current:
                parts.append(current)
            if len(word) > EMBED_DESC_MAX:
                parts.extend([word[i : i + EMBED_DESC_MAX] for i in range(0, len(word), EMBED_DESC_MAX)])
                current = ""
            else:
                current = word
    if current:
        parts.append(current)
    return parts


def force_split_text(text: str) -> List[str]:
    out: List[str] = []
    start = 0
    while start < len(text):
        end = min(start + EMBED_DESC_MAX, len(text))
        out.append(text[start:end])
        start = end
    return out


def batch_embeds(embeds: List[Dict[str, Any]]) -> List[List[Dict[str, Any]]]:
    return [embeds[i : i + EMBEDS_PER_MESSAGE_MAX] for i in range(0, len(embeds), EMBEDS_PER_MESSAGE_MAX)]
