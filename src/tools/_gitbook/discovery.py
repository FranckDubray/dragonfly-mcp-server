"""GitBook Enhanced - URL Discovery"""

import requests
from bs4 import BeautifulSoup
from typing import Dict, Any, List
import re
from urllib.parse import urlparse

from .utils import clean_text

# Constants
DEFAULT_TIMEOUT = 10


def guess_gitbook_urls(company_name: str) -> List[str]:
    """Generate possible GitBook URLs for a company/organization."""
    if not company_name:
        return []
    
    # Clean company name
    name = company_name.lower().strip()
    name = re.sub(r'[^a-z0-9-]', '', name)  # Keep only alphanumeric and hyphens
    
    # Generate possible URLs
    possible_urls = [
        f"https://{name}.gitbook.io",
        f"https://docs.{name}.com",
        f"https://doc.{name}.com", 
        f"https://help.{name}.com",
        f"https://support.{name}.com",
        f"https://{name}.gitbook.com",
        f"https://{name}-docs.gitbook.io",
        f"https://{name}docs.gitbook.io"
    ]
    
    return possible_urls


def test_gitbook_url(url: str, timeout: int = DEFAULT_TIMEOUT) -> Dict[str, Any]:
    """Test if a URL is a valid GitBook documentation."""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (compatible; GitBook-Discovery-Tool/1.0)',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
        }
        
        response = requests.get(url, headers=headers, timeout=timeout, allow_redirects=True)
        
        if response.status_code == 200:
            # Check if it's actually GitBook
            content = response.text.lower()
            gitbook_indicators = [
                'gitbook',
                'data-testid="page-content"',
                'gitbook.io',
                'gitbook.com',
                '__gitbook'
            ]
            
            is_gitbook = any(indicator in content for indicator in gitbook_indicators)
            
            if is_gitbook:
                soup = BeautifulSoup(response.text, 'html.parser')
                title = ""
                
                # Try to get page title
                title_elem = soup.select_one('title')
                if title_elem:
                    title = clean_text(title_elem.get_text())
                
                return {
                    "url": response.url,  # Final URL after redirects
                    "status": "valid",
                    "title": title,
                    "is_gitbook": True
                }
        
        return {
            "url": url,
            "status": "not_found",
            "is_gitbook": False
        }
        
    except requests.RequestException:
        return {
            "url": url,
            "status": "error",
            "is_gitbook": False
        }


def extract_base_url_from_page(page_url: str) -> str:
    """Extract GitBook base URL from any page URL."""
    if not page_url:
        return ""
    
    parsed = urlparse(page_url)
    
    # For GitBook URLs, the base is usually just the domain
    if 'gitbook.io' in parsed.netloc or 'gitbook.com' in parsed.netloc:
        return f"{parsed.scheme}://{parsed.netloc}"
    
    # For custom domains, try to find the root
    # Usually GitBook docs are at the root or /docs
    base_candidates = [
        f"{parsed.scheme}://{parsed.netloc}",
        f"{parsed.scheme}://{parsed.netloc}/docs",
    ]
    
    for candidate in base_candidates:
        test_result = test_gitbook_url(candidate)
        if test_result["is_gitbook"]:
            return candidate
    
    # Fallback to domain root
    return f"{parsed.scheme}://{parsed.netloc}"
