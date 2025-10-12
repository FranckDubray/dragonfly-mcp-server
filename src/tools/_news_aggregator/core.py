"""Core handlers for news aggregator operations."""
from typing import Dict, Any, List
from concurrent.futures import ThreadPoolExecutor, as_completed
from .providers.newsapi_client import NewsAPIClient
from .providers.nyt_client import NYTClient
from .providers.guardian_client import GuardianClient
from .validators import (
    validate_query_required,
    validate_country_required,
    validate_limit,
    validate_page,
    validate_date_format
)
from .utils import (
    get_available_providers,
    normalize_article,
    deduplicate_articles,
    sort_articles,
    truncate_with_warning
)


# Initialize clients
newsapi_client = NewsAPIClient()
nyt_client = NYTClient()
guardian_client = GuardianClient()


def _query_provider(provider_name: str, client, method: str, **kwargs) -> Dict[str, Any]:
    """Query a single provider (used for parallel execution)."""
    try:
        if method == "search":
            result = client.search(**kwargs)
        elif method == "top_headlines":
            result = client.top_headlines(**kwargs)
        else:
            result = {"success": False, "error": f"Unknown method: {method}"}
        
        if result.get("success"):
            articles = result.get("articles", [])
            normalized = [normalize_article(a, provider_name) for a in articles]
            
            response = {
                "provider": provider_name,
                "status": "success",
                "articles": normalized,
                "count": len(normalized)
            }
            
            # Propagate debug info if present
            if "debug_info" in result:
                response["debug_info"] = result["debug_info"]
            
            return response
        else:
            return {
                "provider": provider_name,
                "status": "error",
                "error": result.get("error", "Unknown error"),
                "articles": []
            }
    except Exception as e:
        return {
            "provider": provider_name,
            "status": "error",
            "error": str(e),
            "articles": []
        }


def handle_search_news(
    query: str = None,
    from_date: str = None,
    to_date: str = None,
    language: str = None,
    sort_by: str = "publishedAt",
    sources: list = None,
    providers: list = None,
    limit: int = 20,
    page: int = 1,
    **params
) -> Dict[str, Any]:
    """Search news across multiple providers with PARALLEL requests."""
    
    # Validate required parameters
    query_validation = validate_query_required(query)
    if not query_validation["valid"]:
        return {"error": query_validation["error"]}
    
    limit_validation = validate_limit(limit)
    if not limit_validation["valid"]:
        return {"error": limit_validation["error"]}
    
    page_validation = validate_page(page)
    if not page_validation["valid"]:
        return {"error": page_validation["error"]}
    
    # Validate dates
    from_date_validation = validate_date_format(from_date, "from_date")
    if not from_date_validation["valid"]:
        return {"error": from_date_validation["error"]}
    
    to_date_validation = validate_date_format(to_date, "to_date")
    if not to_date_validation["valid"]:
        return {"error": to_date_validation["error"]}
    
    # Determine which providers to use
    available = get_available_providers()
    
    if not providers:
        # Use all available providers
        active_providers = [p for p, avail in available.items() if avail]
    else:
        # Validate requested providers
        active_providers = []
        for p in providers:
            if p not in available:
                return {"error": f"Unknown provider '{p}'. Available: {list(available.keys())}"}
            if not available[p]:
                return {"error": f"Provider '{p}' not configured. Set {p.upper()}_API_KEY environment variable."}
            active_providers.append(p)
    
    if not active_providers:
        return {
            "error": "No providers available. Configure at least one API key: NEWS_API_KEY, NYT_API_KEY, or GUARDIAN_API_KEY",
            "help": {
                "newsapi": "https://newsapi.org/register",
                "nyt": "https://developer.nytimes.com/get-started",
                "guardian": "https://open-platform.theguardian.com/access/"
            }
        }
    
    # Calculate per-provider limit (optimize distribution)
    # Give more to providers with higher limits
    provider_limits = {
        "newsapi": min(100, limit),  # NewsAPI can return up to 100
        "nyt": min(10, limit),        # NYT returns 10 by default
        "guardian": min(50, limit)    # Guardian max 50
    }
    
    # Prepare parallel queries
    query_tasks = []
    
    if "newsapi" in active_providers:
        query_tasks.append({
            "provider": "newsapi",
            "client": newsapi_client,
            "method": "search",
            "kwargs": {
                "query": query,
                "from_date": from_date,
                "to_date": to_date,
                "language": language,
                "sort_by": sort_by,
                "sources": sources,
                "page": page,
                "page_size": provider_limits["newsapi"]
            }
        })
    
    if "nyt" in active_providers:
        query_tasks.append({
            "provider": "nyt",
            "client": nyt_client,
            "method": "search",
            "kwargs": {
                "query": query,
                "from_date": from_date,
                "to_date": to_date,
                "page": page - 1,  # NYT uses 0-based pages
                "page_size": provider_limits["nyt"]
            }
        })
    
    if "guardian" in active_providers:
        query_tasks.append({
            "provider": "guardian",
            "client": guardian_client,
            "method": "search",
            "kwargs": {
                "query": query,
                "from_date": from_date,
                "to_date": to_date,
                "page": page,
                "page_size": provider_limits["guardian"]
            }
        })
    
    # Execute queries in PARALLEL
    all_articles = []
    provider_stats = {}
    debug_infos = {}
    
    with ThreadPoolExecutor(max_workers=len(query_tasks)) as executor:
        # Submit all tasks
        future_to_task = {
            executor.submit(
                _query_provider,
                task["provider"],
                task["client"],
                task["method"],
                **task["kwargs"]
            ): task["provider"]
            for task in query_tasks
        }
        
        # Collect results as they complete
        for future in as_completed(future_to_task):
            result = future.result()
            provider_name = result["provider"]
            
            if result["status"] == "success":
                all_articles.extend(result["articles"])
                provider_stats[provider_name] = {
                    "status": "ok",
                    "articles": result["count"]
                }
                # Capture debug info if present
                if "debug_info" in result:
                    debug_infos[provider_name] = result["debug_info"]
            else:
                provider_stats[provider_name] = {
                    "status": "error",
                    "reason": result.get("error", "Unknown")[:100]  # Truncate error
                }
    
    # Check if we got any results
    if not all_articles:
        errors = {p: s.get("reason") for p, s in provider_stats.items() if s.get("status") == "error"}
        response = {
            "success": True,
            "articles": [],
            "returned_count": 0,
            "total_available": 0,
            "providers": provider_stats
        }
        
        # Add debug infos if any
        if debug_infos:
            response["debug"] = debug_infos
        
        if errors:
            response["provider_errors"] = errors
        
        return response
    
    # Deduplicate and sort
    unique_articles = deduplicate_articles(all_articles)
    sorted_articles = sort_articles(unique_articles, sort_by)
    
    # Apply pagination and truncation
    total_available = len(sorted_articles)
    start_idx = (page - 1) * limit
    end_idx = start_idx + limit
    paginated = sorted_articles[start_idx:end_idx]
    
    # Build response with anti-flood protection
    response = {
        "success": True,
        "articles": paginated,
        "returned_count": len(paginated),
        "total_available": total_available,
        "page": page,
        "limit": limit,
        "providers": provider_stats  # Simplified metadata
    }
    
    # Add debug info if present
    if debug_infos:
        response["debug"] = debug_infos
    
    # Add truncation warning if needed
    if total_available > limit:
        response["truncated"] = True
        response["warning"] = f"Results limited to {limit} articles per page (anti-flood policy). Use 'page' parameter to see more. Total: {total_available}"
    
    return response


def handle_top_headlines(
    country: str = None,
    category: str = None,
    query: str = None,
    sources: list = None,
    limit: int = 20,
    page: int = 1,
    **params
) -> Dict[str, Any]:
    """Get top headlines (NewsAPI only)."""
    
    # Validate parameters
    if not country and not category and not sources:
        country_validation = validate_country_required(None)
        return {"error": "At least one of 'country', 'category', or 'sources' is required for top_headlines"}
    
    limit_validation = validate_limit(limit)
    if not limit_validation["valid"]:
        return {"error": limit_validation["error"]}
    
    page_validation = validate_page(page)
    if not page_validation["valid"]:
        return {"error": page_validation["error"]}
    
    # Check NewsAPI availability
    if not newsapi_client.is_available():
        return {
            "error": "NEWS_API_KEY not configured. Get free key at https://newsapi.org/register"
        }
    
    # Query NewsAPI
    try:
        result = newsapi_client.top_headlines(
            country=country,
            category=category,
            query=query,
            sources=sources,
            page=page,
            page_size=limit
        )
        
        if not result.get("success"):
            return result
        
        articles = result.get("articles", [])
        normalized = [normalize_article(a, "newsapi") for a in articles]
        total_available = result.get("totalResults", len(normalized))
        
        # Build response with anti-flood protection
        response = {
            "success": True,
            "articles": normalized,
            "returned_count": len(normalized),
            "total_available": total_available,
            "page": page,
            "limit": limit
        }
        
        # Add debug info if present and no articles found
        if "debug_info" in result and total_available == 0:
            response["debug"] = result["debug_info"]
        
        if total_available > limit:
            response["truncated"] = True
            response["warning"] = f"Results limited to {limit} articles per page. Use 'page' parameter to see more. Total: {total_available}"
        
        return response
        
    except Exception as e:
        return {"error": f"Failed to fetch top headlines: {str(e)}"}


def handle_list_sources(
    category: str = None,
    language: str = None,
    country: str = None,
    **params
) -> Dict[str, Any]:
    """List available news sources (NewsAPI only)."""
    
    # Check NewsAPI availability
    if not newsapi_client.is_available():
        return {
            "error": "NEWS_API_KEY not configured. Get free key at https://newsapi.org/register"
        }
    
    try:
        result = newsapi_client.sources(
            category=category,
            language=language,
            country=country
        )
        
        if not result.get("success"):
            return result
        
        sources = result.get("sources", [])
        
        # Anti-flood: limit sources list
        if len(sources) > 100:
            return {
                "success": True,
                "sources": sources[:100],
                "count": len(sources[:100]),
                "total_available": len(sources),
                "truncated": True,
                "warning": f"Sources list truncated to 100 (out of {len(sources)} total)"
            }
        
        return {
            "success": True,
            "sources": sources,
            "count": len(sources)
        }
        
    except Exception as e:
        return {"error": f"Failed to fetch sources: {str(e)}"}
