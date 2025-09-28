"""GitBook Enhanced - Content extraction and search"""

import requests
from bs4 import BeautifulSoup
from typing import Dict, Any, List
import re

from .utils import clean_text


def extract_page_content(url: str) -> Dict[str, Any]:
    """Extract content from a single GitBook page."""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (compatible; GitBook-Enhanced-Tool/1.0)',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Extract title
        title = ""
        for selector in ['h1', '[data-testid="page-title"]', 'title']:
            title_elem = soup.select_one(selector)
            if title_elem:
                title = clean_text(title_elem.get_text())
                break
        
        # Extract main content
        content = ""
        content_selectors = [
            '[data-testid="page-content"]',
            '.page-body',
            'main article',
            '.content',
            'main'
        ]
        
        for selector in content_selectors:
            content_elem = soup.select_one(selector)
            if content_elem:
                # Remove navigation and TOC elements
                for nav in content_elem.select('nav, .toc, .table-of-contents, .pagination'):
                    nav.decompose()
                
                content = clean_text(content_elem.get_text())
                break
        
        # If no structured content found, get body text
        if not content:
            for element in soup(['script', 'style', 'nav', 'header', 'footer']):
                element.decompose()
            content = clean_text(soup.get_text())
        
        # Extract headings for structure
        headings = []
        for heading in soup.select('h1, h2, h3, h4, h5, h6'):
            headings.append({
                "level": int(heading.name[1]),
                "text": clean_text(heading.get_text())
            })
        
        return {
            "url": url,
            "title": title,
            "content": content,
            "headings": headings,
            "word_count": len(content.split()) if content else 0,
            "success": True
        }
        
    except Exception as e:
        return {
            "url": url,
            "error": str(e),
            "success": False
        }


def search_in_pages(pages_data: List[Dict], query: str, max_results: int = 10) -> List[Dict]:
    """Search for query across all pages and return ranked results."""
    if not query:
        return []
    
    query_lower = query.lower()
    results = []
    
    for page in pages_data:
        if not page.get("success") or not page.get("content"):
            continue
        
        content = page["content"]
        title = page.get("title", "")
        
        # Calculate relevance score
        score = 0
        
        # Title matches are very important
        if query_lower in title.lower():
            score += 10
        
        # Count occurrences in content
        content_lower = content.lower()
        occurrences = content_lower.count(query_lower)
        score += occurrences
        
        # Bonus for exact phrase matches
        if query_lower in content_lower:
            score += 5
        
        if score > 0:
            # Extract snippets with context
            snippets = []
            words = content.split()
            
            for i, word in enumerate(words):
                if query_lower in word.lower():
                    start = max(0, i - 10)
                    end = min(len(words), i + 10)
                    snippet = ' '.join(words[start:end])
                    
                    # Highlight the match
                    snippet_highlighted = re.sub(
                        f'({re.escape(query)})', 
                        f'**{query}**', 
                        snippet, 
                        flags=re.IGNORECASE
                    )
                    
                    snippets.append(f"...{snippet_highlighted}...")
                    
                    if len(snippets) >= 3:  # Max 3 snippets per page
                        break
            
            results.append({
                "url": page["url"],
                "title": title,
                "score": score,
                "occurrences": occurrences,
                "snippets": snippets,
                "word_count": page.get("word_count", 0)
            })
    
    # Sort by score (relevance)
    results.sort(key=lambda x: x["score"], reverse=True)
    
    return results[:max_results]