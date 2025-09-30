"""
🎓 Academic Research Tool Super - Version multi-sources optimisée

Sources intégrées: PubMed, arXiv, HAL, CrossRef
Réponses compactes pour préserver le contexte LLM
"""

import json
import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET
import re
import time
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from collections import Counter
from pathlib import Path

@dataclass
class Author:
    name: str
    affiliation: str = ""

@dataclass
class ResearchResult:
    title: str
    authors: List[Author]
    abstract: str
    doi: str
    url: str
    publication_date: str
    journal: str
    source: str
    citations_count: int = 0
    full_text_url: str = ""

class AcademicResearchSuper:
    def __init__(self):
        self.headers = {
            'User-Agent': 'Academic-Research-Super/1.0 (Python; Educational Use)'
        }
        self.last_request = {}
    # ... (code inchangé du run et des méthodes de recherche)

_tool = AcademicResearchSuper()

_SPEC_DIR = Path(__file__).resolve().parent.parent / "tool_specs"

def _load_spec_override(name: str) -> Dict[str, Any] | None:
    try:
        p = _SPEC_DIR / f"{name}.json"
        if p.is_file():
            with open(p, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception:
        pass
    return None

def run(**params) -> Dict[str, Any]:
    try:
        operation = params.get('operation', 'search_papers')
        # ... (code de routage original, inchangé)
        return {"success": False, "error": "Not implemented in this snippet"}
    except Exception as e:
        return {"success": False, "error": str(e)}

def spec() -> Dict[str, Any]:
    base = {
        "type": "function",
        "function": {
            "name": "academic_research_super",
            "displayName": "Research",
            "description": "Recherche académique multi-sources (PubMed, arXiv, HAL, CrossRef).",
            "parameters": {
                "type": "object",
                "additionalProperties": True
            }
        }
    }
    override = _load_spec_override("academic_research_super")
    if override and isinstance(override, dict):
        fn = base.get("function", {})
        ofn = override.get("function", {})
        if ofn.get("displayName"):
            fn["displayName"] = ofn["displayName"]
        if ofn.get("description"):
            fn["description"] = ofn["description"]
        if ofn.get("parameters"):
            fn["parameters"] = ofn["parameters"]
    return base
