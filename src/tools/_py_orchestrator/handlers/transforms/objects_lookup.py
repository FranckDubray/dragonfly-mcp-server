# TRANSFORM_META_START
{
  "io_type": "any->object",
  "description": "Normalize an input string and map it via a provided dictionary (domain_to_company, entity_synonyms...). Returns mapped result + hit flag + normalized key.",
  "inputs": [
    "- value: any (string recommended)",
    "- mapping: object (normalizedKey -> any)",
    "- default: any (optional, default null)",
    "- case_insensitive: boolean (default true)",
    "- trim: boolean (default true)",
    "- remove_accents: boolean (default true)",
    "- pre_strip_suffixes: list[string] (optional; removed from end before lookup)",
    "- normalize_spaces: boolean (default true)"
  ],
  "outputs": [
    "- result: any",
    "- hit: boolean",
    "- normalized: string"
  ]
}
# TRANSFORM_META_END

import unicodedata
from typing import Any, Dict

from ..base import AbstractHandler, HandlerError


def _strip_accents(s: str) -> str:
    return "".join(ch for ch in unicodedata.normalize("NFD", s) if unicodedata.category(ch) != "Mn")


def _collapse_spaces(s: str) -> str:
    return " ".join(s.split())


def _normalize(s: Any, *, trim: bool, remove_accents: bool, case_insensitive: bool, normalize_spaces: bool) -> str:
    if s is None:
        return ""
    if not isinstance(s, str):
        s = str(s)
    if trim:
        s = s.strip()
    if normalize_spaces:
        s = _collapse_spaces(s)
    if remove_accents:
        s = _strip_accents(s)
    if case_insensitive:
        s = s.lower()
    return s


def _strip_suffixes(s: str, suffixes: list) -> str:
    if not suffixes:
        return s
    base = s
    done = False
    # supprimer récursivement les suffixes si présents en fin de chaîne
    while not done and base:
        done = True
        for suf in suffixes:
            suf_n = suf.strip().lower()
            if suf_n and base.endswith(suf_n):
                base = base[: -len(suf_n)].rstrip()
                done = False
    return base


class ObjectsLookupHandler(AbstractHandler):
    @property
    def kind(self) -> str:
        return "objects_lookup"

    def run(self, value=None, mapping=None, default=None, case_insensitive=True, trim=True,
            remove_accents=True, pre_strip_suffixes=None, normalize_spaces=True, **kwargs) -> Dict[str, Any]:
        mapping = mapping or {}
        pre_strip_suffixes = pre_strip_suffixes or []

        # Normaliser les clés du mapping
        norm_map: Dict[str, Any] = {}
        for k, v in mapping.items():
            nk = _normalize(str(k), trim=True, remove_accents=remove_accents,
                            case_insensitive=case_insensitive, normalize_spaces=True)
            norm_map[nk] = v

        # Normaliser la valeur d'entrée
        nv = _normalize(value, trim=trim, remove_accents=remove_accents,
                        case_insensitive=case_insensitive, normalize_spaces=normalize_spaces)

        # strip suffixes légers si fournis
        nv_stripped = _strip_suffixes(nv, pre_strip_suffixes) if pre_strip_suffixes else nv

        # Lookup
        result = norm_map.get(nv_stripped)
        hit = result is not None
        if not hit:
            return {"result": default, "hit": False, "normalized": nv_stripped}
        return {"result": result, "hit": True, "normalized": nv_stripped}
