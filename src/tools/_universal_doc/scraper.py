"""Universal Documentation Scraper - Main scraping functionality"""

import requests
from bs4 import BeautifulSoup
from typing import Dict, Any, List, Set, Optional
import re
from urllib.parse import urljoin, urlparse, parse_qs
import time
from xml.etree import ElementTree

from .detector import DocPlatformDetector


class UniversalDocScraper:
    """Universal documentation scraper supporting multiple platforms"""
    
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (compatible; Universal-Doc-Scraper/1.0)',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
        }
        self.detector = DocPlatformDetector()
    
    def clean_text(self, text: str) -> str:
        """Clean and normalize text"""
        if not text:
            return ""
        
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text.strip())
        # Remove common navigation elements
        text = re.sub(r'Table of contents|On this page|Previous|Next|Edit on GitHub', '', text, flags=re.IGNORECASE)
        
        return text
    
    def discover_sitemap(self, base_url: str) -> List[str]:
        """Discover pages via sitemap.xml"""
        sitemap_urls = [
            f"{base_url.rstrip('/')}/sitemap.xml",
            f"{base_url.rstrip('/')}/sitemap_index.xml",
            f"{base_url.rstrip('/')}/robots.txt"  # Often contains sitemap reference
        ]
        
        pages = []
        
        for sitemap_url in sitemap_urls:
            try:
                if sitemap_url.endswith('robots.txt'):
                    # Parse robots.txt for sitemap references
                    response = requests.get(sitemap_url, timeout=10)
                    if response.status_code == 200:
                        for line in response.text.split('\n'):
                            if line.lower().startswith('sitemap:'):
                                actual_sitemap = line.split(':', 1)[1].strip()
                                sitemap_urls.append(actual_sitemap)
                    continue
                
                response = requests.get(sitemap_url, timeout=10)
                if response.status_code == 200:
                    # Parse XML sitemap
                    root = ElementTree.fromstring(response.content)
                    
                    # Handle namespaces
                    namespaces = {'': 'http://www.sitemaps.org/schemas/sitemap/0.9'}
                    
                    # Extract URLs
                    for url_elem in root.findall('.//url', namespaces) or root.findall('.//url'):
                        loc_elem = url_elem.find('loc', namespaces) or url_elem.find('loc')
                        if loc_elem is not None and loc_elem.text:
                            pages.append(loc_elem.text.strip())
                    
                    if pages:
                        break
                        
            except Exception:
                continue
        
        return pages
    
    def scrape_gitbook_style(self, base_url: str, content: str, soup: BeautifulSoup) -> Dict:
        """GitBook-specific scraping logic"""
        # Extract navigation links
        pages = set()
        
        for link in soup.select('a[href]'):
            href = link.get('href')
            if href and not href.startswith('#') and not href.startswith('mailto:'):
                full_url = urljoin(base_url, href)
                parsed = urlparse(full_url)
                
                if parsed.netloc == urlparse(base_url).netloc:
                    pages.add(full_url)
        
        # Extract main content
        content_selectors = [
            '[data-testid="page-content"]',
            '.page-body',
            'main article',
            '.content'
        ]
        
        main_content = ""
        for selector in content_selectors:
            content_elem = soup.select_one(selector)
            if content_elem:
                main_content = self.clean_text(content_elem.get_text())
                break
        
        return {
            'pages': list(pages),
            'content_extraction_method': 'gitbook',
            'main_content': main_content
        }
    
    def scrape_notion_style(self, base_url: str, content: str, soup: BeautifulSoup) -> Dict:
        """Notion-specific scraping logic"""
        pages = set()
        
        # Notion uses different link patterns
        for link in soup.select('a[href*="notion.so"], a[href*="notion.site"]'):
            href = link.get('href')
            if href:
                pages.add(href)
        
        # Notion content extraction
        main_content = ""
        notion_content = soup.select_one('.notion-page-content, [data-block-id]')
        if notion_content:
            main_content = self.clean_text(notion_content.get_text())
        
        return {
            'pages': list(pages),
            'content_extraction_method': 'notion',
            'main_content': main_content
        }
    
    def scrape_docusaurus_style(self, base_url: str, content: str, soup: BeautifulSoup) -> Dict:
        """Docusaurus-specific scraping logic"""
        pages = set()
        
        # Docusaurus navigation
        for link in soup.select('.theme-doc-sidebar a, nav a, .navbar__item a'):
            href = link.get('href')
            if href:
                full_url = urljoin(base_url, href)
                pages.add(full_url)
        
        # Docusaurus content
        main_content = ""
        doc_content = soup.select_one('main article, .theme-doc-markdown, .markdown')
        if doc_content:
            main_content = self.clean_text(doc_content.get_text())
        
        return {
            'pages': list(pages),
            'content_extraction_method': 'docusaurus',
            'main_content': main_content
        }
    
    def scrape_generic(self, base_url: str, content: str, soup: BeautifulSoup) -> Dict:
        """Generic scraping logic for unknown platforms"""
        pages = set()
        
        # Generic link extraction
        base_domain = urlparse(base_url).netloc
        for link in soup.select('a[href]'):
            href = link.get('href')
            if href and not href.startswith('#') and not href.startswith('mailto:'):
                full_url = urljoin(base_url, href)
                parsed = urlparse(full_url)
                
                if parsed.netloc == base_domain:
                    pages.add(full_url)
        
        # Generic content extraction
        main_content = ""
        
        # Try common content selectors
        content_selectors = [
            'main', 'article', '.content', '.documentation', '.docs',
            '#content', '.main-content', '.page-content'
        ]
        
        for selector in content_selectors:
            content_elem = soup.select_one(selector)
            if content_elem:
                # Remove navigation
                for nav in content_elem.select('nav, .nav, .navigation, .sidebar'):
                    nav.decompose()
                main_content = self.clean_text(content_elem.get_text())
                break
        
        return {
            'pages': list(pages),
            'content_extraction_method': 'generic',
            'main_content': main_content
        }
    
    def discover_documentation(self, base_url: str) -> Dict[str, Any]:
        """Discover all pages in a documentation site"""
        try:
            response = requests.get(base_url, headers=self.headers, timeout=15)
            response.raise_for_status()
            
            content = response.text
            soup = BeautifulSoup(content, 'html.parser')
            
            # Detect platform
            platform = self.detector.detect_platform(base_url, content)
            
            # Get title
            title = ""
            title_elem = soup.select_one('title')
            if title_elem:
                title = self.clean_text(title_elem.get_text())
            
            # Platform-specific scraping
            result = {}
            if platform == 'gitbook':
                result = self.scrape_gitbook_style(base_url, content, soup)
            elif platform == 'notion':
                result = self.scrape_notion_style(base_url, content, soup)
            elif platform == 'docusaurus':
                result = self.scrape_docusaurus_style(base_url, content, soup)
            else:
                result = self.scrape_generic(base_url, content, soup)
            
            # Try sitemap discovery as well
            sitemap_pages = self.discover_sitemap(base_url)
            
            # Merge results
            all_pages = list(set(result.get('pages', []) + sitemap_pages))
            
            # Filter and clean pages
            filtered_pages = []
            base_domain = urlparse(base_url).netloc
            
            for page_url in all_pages:
                parsed = urlparse(page_url)
                if (parsed.netloc == base_domain and 
                    not page_url.endswith(('.pdf', '.zip', '.tar.gz')) and
                    '/api/' not in page_url):
                    filtered_pages.append(page_url)
            
            return {
                'success': True,
                'base_url': base_url,
                'platform_detected': platform,
                'title': title,
                'pages_found': len(filtered_pages),
                'pages': filtered_pages[:100],  # Limit for performance
                'discovery_methods': ['navigation', 'sitemap'] if sitemap_pages else ['navigation'],
                'total_discovered': len(all_pages)
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f"Failed to discover documentation: {str(e)}",
                'base_url': base_url
            }
    
    def extract_page_content(self, url: str) -> Dict[str, Any]:
        """Extract content from a single documentation page"""
        try:
            response = requests.get(url, headers=self.headers, timeout=15)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            platform = self.detector.detect_platform(url, response.text)
            
            # Extract title
            title = ""
            for selector in ['h1', '[data-testid="page-title"]', 'title']:
                title_elem = soup.select_one(selector)
                if title_elem:
                    title = self.clean_text(title_elem.get_text())
                    break
            
            # Platform-specific content extraction
            content = ""
            if platform == 'gitbook':
                content_elem = soup.select_one('[data-testid="page-content"], .page-body, main')
            elif platform == 'notion':
                content_elem = soup.select_one('.notion-page-content, [data-block-id]')
            elif platform == 'docusaurus':
                content_elem = soup.select_one('main article, .theme-doc-markdown')
            else:
                content_elem = soup.select_one('main, article, .content')
            
            if content_elem:
                # Remove navigation and TOC
                for nav in content_elem.select('nav, .toc, .table-of-contents, .pagination, .sidebar'):
                    nav.decompose()
                content = self.clean_text(content_elem.get_text())
            
            # Extract headings
            headings = []
            for heading in soup.select('h1, h2, h3, h4, h5, h6'):
                headings.append({
                    'level': int(heading.name[1]),
                    'text': self.clean_text(heading.get_text())
                })
            
            # Extract code blocks
            code_blocks = []
            for code in soup.select('pre code, .highlight code'):
                code_text = code.get_text()
                if code_text.strip():
                    code_blocks.append(code_text.strip())
            
            return {
                'success': True,
                'url': url,
                'platform': platform,
                'title': title,
                'content': content,
                'headings': headings,
                'code_blocks': code_blocks,
                'word_count': len(content.split()) if content else 0
            }
            
        except Exception as e:
            return {
                'success': False,
                'url': url,
                'error': str(e)
            }
    
    def search_across_sites(self, sites: List[str], query: str, max_results: int = 20) -> Dict[str, Any]:
        """Search across multiple documentation sites"""
        all_results = []
        processed_sites = []
        
        for site_url in sites:
            try:
                # Discover pages
                discovery = self.discover_documentation(site_url)
                if not discovery['success']:
                    continue
                
                # Search pages (limit to avoid timeout)
                pages_to_search = discovery['pages'][:10]  # Limit per site
                site_results = []
                
                for page_url in pages_to_search:
                    page_data = self.extract_page_content(page_url)
                    if page_data['success']:
                        content = page_data['content'].lower()
                        title = page_data['title'].lower()
                        
                        # Calculate relevance score
                        score = 0
                        query_lower = query.lower()
                        
                        if query_lower in title:
                            score += 10
                        
                        score += content.count(query_lower)
                        
                        if score > 0:
                            # Extract snippet
                            words = page_data['content'].split()
                            snippet = ""
                            
                            for i, word in enumerate(words):
                                if query_lower in word.lower():
                                    start = max(0, i - 15)
                                    end = min(len(words), i + 15)
                                    snippet = ' '.join(words[start:end])
                                    break
                            
                            site_results.append({
                                'url': page_url,
                                'title': page_data['title'],
                                'platform': page_data['platform'],
                                'score': score,
                                'snippet': snippet,
                                'word_count': page_data['word_count']
                            })
                
                # Sort by score
                site_results.sort(key=lambda x: x['score'], reverse=True)
                all_results.extend(site_results[:5])  # Top 5 per site
                
                processed_sites.append({
                    'url': site_url,
                    'platform': discovery['platform_detected'],
                    'pages_searched': len(pages_to_search),
                    'results_found': len(site_results)
                })
                
                # Small delay between sites
                time.sleep(0.5)
                
            except Exception as e:
                processed_sites.append({
                    'url': site_url,
                    'error': str(e)
                })
        
        # Sort all results by score
        all_results.sort(key=lambda x: x['score'], reverse=True)
        
        return {
            'success': True,
            'query': query,
            'sites_processed': len(processed_sites),
            'total_results': len(all_results),
            'results': all_results[:max_results],
            'sites_details': processed_sites
        }