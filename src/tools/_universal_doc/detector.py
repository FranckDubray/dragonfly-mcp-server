"""Universal Documentation Scraper - Platform Detection"""


class DocPlatformDetector:
    """Detect documentation platform and return appropriate scraping strategy"""
    
    @staticmethod
    def detect_platform(url: str, content: str = None) -> str:
        """Detect the documentation platform based on URL and content"""
        url_lower = url.lower()
        
        # URL-based detection first
        if 'gitbook.io' in url_lower or 'gitbook.com' in url_lower:
            return 'gitbook'
        elif 'notion.so' in url_lower or 'notion.site' in url_lower:
            return 'notion'
        elif 'confluence' in url_lower or 'atlassian' in url_lower:
            return 'confluence'
        elif 'readthedocs.io' in url_lower:
            return 'readthedocs'
        elif 'github.io' in url_lower and '/docs' in url_lower:
            return 'github_pages'
        elif 'vercel.app' in url_lower or 'netlify.app' in url_lower:
            return 'static_site'
        
        # Content-based detection if content provided
        if content:
            content_lower = content.lower()
            
            # GitBook indicators
            if any(indicator in content_lower for indicator in [
                'gitbook', '__gitbook', 'data-testid="page-content"'
            ]):
                return 'gitbook'
            
            # Notion indicators
            if any(indicator in content_lower for indicator in [
                'notion-page', 'notion-block', 'notion.so'
            ]):
                return 'notion'
            
            # Docusaurus indicators
            if any(indicator in content_lower for indicator in [
                'docusaurus', 'data-theme="light"', 'theme-doc-sidebar'
            ]):
                return 'docusaurus'
            
            # Confluence indicators
            if any(indicator in content_lower for indicator in [
                'confluence', 'atlassian', 'ajs-page-panel'
            ]):
                return 'confluence'
            
            # ReadTheDocs indicators
            if any(indicator in content_lower for indicator in [
                'readthedocs', 'sphinx_rtd_theme', 'rst-content'
            ]):
                return 'readthedocs'
        
        return 'generic'