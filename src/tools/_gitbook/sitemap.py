"""GitBook Enhanced - Sitemap and Navigation Discovery"""

import requests
from bs4 import BeautifulSoup
from typing import List
from urllib.parse import urljoin, urlparse
from xml.etree import ElementTree


def discover_sitemap(base_url: str) -> List[str]:
    """Try to discover pages via sitemap.xml."""
    sitemap_urls = [
        f"{base_url.rstrip('/')}/sitemap.xml",
        f"{base_url.rstrip('/')}/sitemap_index.xml"
    ]
    
    pages = []
    
    for sitemap_url in sitemap_urls:
        try:
            response = requests.get(sitemap_url, timeout=10)
            if response.status_code == 200:
                # Parse XML sitemap
                root = ElementTree.fromstring(response.content)
                
                # Handle namespaces
                namespaces = {
                    '': 'http://www.sitemaps.org/schemas/sitemap/0.9'
                }
                
                # Extract URLs
                for url_elem in root.findall('.//url', namespaces) or root.findall('.//url'):
                    loc_elem = url_elem.find('loc', namespaces) or url_elem.find('loc')
                    if loc_elem is not None and loc_elem.text:
                        pages.append(loc_elem.text.strip())
                
                if pages:
                    break  # Found sitemap, stop trying others
                    
        except Exception as e:
            continue
    
    return pages


def discover_navigation(base_url: str) -> List[str]:
    """Discover pages by crawling navigation from base URL."""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (compatible; GitBook-Enhanced-Tool/1.0)',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
        }
        
        response = requests.get(base_url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Extract all internal links
        pages = set()
        base_domain = f"{urlparse(base_url).scheme}://{urlparse(base_url).netloc}"
        
        for link in soup.select('a[href]'):
            href = link.get('href')
            if href:
                full_url = urljoin(base_url, href)
                parsed = urlparse(full_url)
                
                # Only include internal links that look like GitBook pages
                if (parsed.netloc == urlparse(base_url).netloc and 
                    not href.startswith('#') and 
                    not href.startswith('mailto:') and
                    not href.endswith('.pdf') and
                    not href.endswith('.zip') and
                    '/api/' not in href):
                    pages.add(full_url)
        
        return list(pages)
        
    except Exception as e:
        return []