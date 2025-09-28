"""
Enhanced GitBook Tool - Smart discovery and global search
Automatically find all pages and search across entire documentation
"""

from typing import Dict, Any
from pathlib import Path
import json
import time
from urllib.parse import urlparse

from ._gitbook import (
    guess_gitbook_urls, test_gitbook_url, extract_base_url_from_page,
    discover_sitemap, discover_navigation,
    extract_page_content, search_in_pages
)

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
    """Execute GitBook operations with enhanced discovery and search."""
    
    if operation == "find_docs":
        company = params.get('company')
        
        if not company:
            return {"error": "company name required for find_docs operation"}
        
        # Generate possible URLs
        possible_urls = guess_gitbook_urls(company)
        
        # Test each URL
        found_docs = []
        for url in possible_urls:
            result = test_gitbook_url(url)
            if result["is_gitbook"]:
                found_docs.append(result)
        
        return {
            "success": True,
            "company": company,
            "urls_tested": len(possible_urls),
            "docs_found": len(found_docs),
            "results": found_docs
        }
    
    elif operation == "extract_base_url":
        page_url = params.get('page_url')
        
        if not page_url:
            return {"error": "page_url required for extract_base_url operation"}
        
        base_url = extract_base_url_from_page(page_url)
        
        return {
            "success": True,
            "original_url": page_url,
            "base_url": base_url
        }
    
    elif operation == "discover_site":
        base_url = params.get('base_url')
        
        if not base_url:
            return {"error": "base_url required for discover_site operation"}
        
        # Try multiple discovery methods
        pages = []
        methods_used = []
        
        # Method 1: Sitemap
        sitemap_pages = discover_sitemap(base_url)
        if sitemap_pages:
            pages.extend(sitemap_pages)
            methods_used.append("sitemap")
        
        # Method 2: Navigation crawling
        nav_pages = discover_navigation(base_url)
        if nav_pages:
            # Merge and deduplicate
            pages_set = set(pages)
            new_pages = [p for p in nav_pages if p not in pages_set]
            pages.extend(new_pages)
            if new_pages:
                methods_used.append("navigation")
        
        # Remove duplicates and filter
        unique_pages = list(set(pages))
        
        # Filter to keep only relevant GitBook pages
        filtered_pages = []
        base_domain = urlparse(base_url).netloc
        
        for page_url in unique_pages:
            parsed = urlparse(page_url)
            if (parsed.netloc == base_domain and 
                not page_url.endswith('.xml') and
                not page_url.endswith('.json')):
                filtered_pages.append(page_url)
        
        return {
            "success": True,
            "base_url": base_url,
            "pages_found": len(filtered_pages),
            "discovery_methods": methods_used,
            "pages": filtered_pages[:50],  # Limit to first 50 for display
            "total_discovered": len(unique_pages)
        }
    
    elif operation == "search_site":
        base_url = params.get('base_url')
        query = params.get('query')
        max_results = params.get('max_results', 10)
        max_pages = params.get('max_pages', 20)
        
        if not base_url or not query:
            return {"error": "base_url and query required for search_site operation"}
        
        # First discover pages
        discovery = run("discover_site", base_url=base_url)
        if "error" in discovery:
            return discovery
        
        pages_to_search = discovery["pages"][:max_pages]
        
        # Extract content from each page
        pages_data = []
        processed = 0
        
        for page_url in pages_to_search:
            page_data = extract_page_content(page_url)
            pages_data.append(page_data)
            processed += 1
            
            # Add small delay to be respectful
            time.sleep(0.1)
        
        # Search across all pages
        search_results = search_in_pages(pages_data, query, max_results)
        
        return {
            "success": True,
            "query": query,
            "base_url": base_url,
            "pages_searched": processed,
            "results_found": len(search_results),
            "results": search_results
        }
    
    elif operation == "read_page":
        # Keep the original functionality
        url = params.get('url')
        
        if not url:
            return {"error": "URL required for read_page operation"}
        
        result = extract_page_content(url)
        return result
    
    else:
        return {"error": f"Unknown operation: {operation}. Available: find_docs, extract_base_url, discover_site, search_site, read_page"}


def spec() -> Dict[str, Any]:
    """Return the enhanced MCP function specification."""
    
    base = {
        "type": "function",
        "function": {
            "name": "gitbook",
            "description": "Enhanced GitBook tool with smart discovery and global search. Automatically find all pages in a GitBook site and search across entire documentation without knowing specific URLs.",
            "parameters": {
                "type": "object",
                "properties": {
                    "operation": {
                        "type": "string",
                        "enum": [
                            "find_docs",
                            "extract_base_url", 
                            "discover_site",
                            "search_site",
                            "read_page"
                        ],
                        "description": "Operation: find_docs (find GitBook docs for company), extract_base_url (get base URL from page), discover_site (find all pages), search_site (search across entire documentation), read_page (read specific page)"
                    }
                },
                "required": ["operation"],
                "additionalProperties": False
            }
        }
    }
    
    override = _load_spec_override("gitbook")
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