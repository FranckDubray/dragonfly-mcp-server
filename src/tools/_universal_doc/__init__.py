"""Universal Documentation Scraper - Modular implementation"""

from .detector import DocPlatformDetector
from .scraper import UniversalDocScraper

__all__ = [
    'DocPlatformDetector',
    'UniversalDocScraper'
]