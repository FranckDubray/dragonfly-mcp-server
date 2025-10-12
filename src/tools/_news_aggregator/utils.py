"""Utilities for news aggregator."""
import os
from typing import Dict, Any, List


def get_available_providers() -> Dict[str, bool]:
    """Check which providers have API keys configured."""
    return {
        "newsapi": bool(os.getenv("NEWS_API_KEY")),
        "nyt": bool(os.getenv("NYT_API_KEY")),
        "guardian": bool(os.getenv("GUARDIAN_API_KEY"))
    }


def normalize_article(raw: Dict[str, Any], provider: str) -> Dict[str, Any]:
    """Normalize article from any provider to unified format.
    
    Returns only essential fields to avoid LLM context flooding.
    """
    
    if provider == "newsapi":
        return {
            "title": raw.get("title", "").strip(),
            "description": raw.get("description", "").strip()[:300],  # Limit to 300 chars
            "url": raw.get("url", ""),
            "source": raw.get("source", {}).get("name", "Unknown"),
            "provider": "newsapi",
            "author": raw.get("author"),
            "published_at": raw.get("publishedAt", ""),
            "image_url": raw.get("urlToImage")
        }
    
    elif provider == "nyt":
        # NYT has nested structure
        headline = raw.get("headline", {})
        byline = raw.get("byline", {})
        
        # Byline can be dict or string - handle both
        author = None
        if isinstance(byline, dict):
            author = byline.get("original")
        elif isinstance(byline, str):
            author = byline
        
        # Extract image if available
        image_url = None
        multimedia = raw.get("multimedia", [])
        if multimedia and isinstance(multimedia, list):
            # Find first image
            for media in multimedia:
                if isinstance(media, dict) and media.get("type") == "image":
                    media_url = media.get("url", "")
                    if media_url:
                        image_url = f"https://www.nytimes.com/{media_url}"
                    break
        
        # Headline can be dict or string
        title = ""
        if isinstance(headline, dict):
            title = headline.get("main", "").strip()
        elif isinstance(headline, str):
            title = headline.strip()
        
        return {
            "title": title,
            "description": raw.get("abstract", "").strip()[:300],  # Limit to 300 chars
            "url": raw.get("web_url", ""),
            "source": "The New York Times",
            "provider": "nyt",
            "author": author,
            "published_at": raw.get("pub_date", ""),
            "image_url": image_url
        }
    
    elif provider == "guardian":
        fields = raw.get("fields", {})
        
        return {
            "title": raw.get("webTitle", "").strip(),
            "description": fields.get("trailText", "").strip()[:300],  # Limit to 300 chars
            "url": raw.get("webUrl", ""),
            "source": "The Guardian",
            "provider": "guardian",
            "author": fields.get("byline"),
            "published_at": raw.get("webPublicationDate", ""),
            "image_url": fields.get("thumbnail")
        }
    
    # Fallback for unknown provider
    return {
        "title": str(raw.get("title", ""))[:200],
        "description": str(raw.get("description", ""))[:300],
        "url": str(raw.get("url", "")),
        "source": "Unknown",
        "provider": provider,
        "author": None,
        "published_at": "",
        "image_url": None
    }


def deduplicate_articles(articles: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Remove duplicate articles by URL."""
    seen_urls = set()
    unique_articles = []
    
    for article in articles:
        url = article.get("url", "")
        if url and url not in seen_urls:
            seen_urls.add(url)
            unique_articles.append(article)
    
    return unique_articles


def sort_articles(articles: List[Dict[str, Any]], sort_by: str = "publishedAt") -> List[Dict[str, Any]]:
    """Sort articles by specified criteria."""
    if sort_by == "publishedAt":
        # Sort by date, most recent first
        return sorted(
            articles,
            key=lambda x: x.get("published_at", ""),
            reverse=True
        )
    # Add other sort methods if needed
    return articles


def truncate_with_warning(articles: List[Dict[str, Any]], limit: int, total_available: int) -> Dict[str, Any]:
    """Truncate results with anti-flood warning."""
    truncated = articles[:limit]
    
    result = {
        "articles": truncated,
        "returned_count": len(truncated),
        "total_available": total_available
    }
    
    if total_available > limit:
        result["truncated"] = True
        result["warning"] = f"Results truncated: showing {len(truncated)} of {total_available} articles (limit={limit}). Use 'page' parameter to see more."
    
    return result
