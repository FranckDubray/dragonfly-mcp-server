"""GitBook Enhanced - Modular implementation"""

from .discovery import guess_gitbook_urls, test_gitbook_url, extract_base_url_from_page
from .sitemap import discover_sitemap, discover_navigation  
from .content import extract_page_content, search_in_pages
from .utils import clean_text

__all__ = [
    'guess_gitbook_urls',
    'test_gitbook_url', 
    'extract_base_url_from_page',
    'discover_sitemap',
    'discover_navigation',
    'extract_page_content',
    'search_in_pages',
    'clean_text'
]