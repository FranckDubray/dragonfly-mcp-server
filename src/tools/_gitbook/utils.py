"""GitBook Enhanced - Utility functions"""

import re


def clean_text(text: str) -> str:
    """Clean and format text from HTML."""
    if not text:
        return ""
    
    # Remove extra whitespace and normalize
    text = re.sub(r'\s+', ' ', text.strip())
    # Remove common GitBook navigation elements
    text = re.sub(r'Table of contents|On this page|Previous|Next', '', text, flags=re.IGNORECASE)
    
    return text