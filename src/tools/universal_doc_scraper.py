"""
Universal Documentation Scraper - Support for multiple doc platforms
Scrapes and searches across GitBook, Notion, Confluence, ReadTheDocs, Docusaurus, etc.
"""

import requests
from typing import Dict, Any, List
from pathlib import Path
import json

from ._universal_doc import UniversalDocScraper

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


def run(operation: str, **params) -> Dict[str, Any]:
    """Execute universal documentation scraper operations"""
    scraper = UniversalDocScraper()
    
    if operation == "discover_docs":
        base_url = params.get('base_url')
        
        if not base_url:
            return {"error": "base_url required for discover_docs operation"}
        
        return scraper.discover_documentation(base_url)
    
    elif operation == "extract_page":
        url = params.get('url')
        
        if not url:
            return {"error": "url required for extract_page operation"}
        
        return scraper.extract_page_content(url)
    
    elif operation == "search_across_sites":
        sites = params.get('sites', [])
        query = params.get('query')
        max_results = params.get('max_results', 20)
        
        if not sites or not query:
            return {"error": "sites and query required for search_across_sites operation"}
        
        return scraper.search_across_sites(sites, query, max_results)
    
    elif operation == "detect_platform":
        url = params.get('url')
        
        if not url:
            return {"error": "url required for detect_platform operation"}
        
        try:
            response = requests.get(url, headers=scraper.headers, timeout=10)
            platform = scraper.detector.detect_platform(url, response.text)
            
            return {
                'success': True,
                'url': url,
                'platform_detected': platform,
                'confidence': 'high' if platform != 'generic' else 'low'
            }
        except Exception as e:
            return {
                'success': False,
                'url': url,
                'error': str(e)
            }
    
    else:
        return {
            "error": f"Unknown operation: {operation}. Available: discover_docs, extract_page, search_across_sites, detect_platform"
        }


def spec() -> Dict[str, Any]:
    """Return the MCP function specification for Universal Doc Scraper"""
    
    base = {
        "type": "function",
        "function": {
            "name": "universal_doc_scraper",
            "description": "Universal documentation scraper supporting GitBook, Notion, Confluence, ReadTheDocs, Docusaurus, and other doc platforms. Discover, extract, and search across multiple documentation sites.",
            "parameters": {
                "type": "object",
                "properties": {
                    "operation": {
                        "type": "string",
                        "enum": [
                            "discover_docs",
                            "extract_page", 
                            "search_across_sites",
                            "detect_platform"
                        ],
                        "description": "Operation: discover_docs (find all pages in a doc site), extract_page (get content from specific page), search_across_sites (search multiple doc sites), detect_platform (identify doc platform type)"
                    }
                },
                "required": ["operation"],
                "additionalProperties": False
            }
        }
    }
    
    override = _load_spec_override("universal_doc_scraper")
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