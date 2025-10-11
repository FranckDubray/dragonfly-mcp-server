"""
Reddit Intelligence Tool - Advanced Reddit analysis and insights
Search, analyze sentiment, find experts, track trends across Reddit
"""

from typing import Dict, Any
from pathlib import Path
import json

from ._reddit import (
    RedditIntelligence, 
    analyze_sentiment, 
    find_experts, 
    find_trending_topics, 
    multi_subreddit_search
)

_SPEC_DIR = Path(__file__).resolve().parent.parent / "tool_specs"


def _load_spec_override(name: str) -> Dict[str, Any] | None:
    try:
        p = _SPEC_DIR / f"{name}.json"
        if p.is_file():
            with open(p, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception:
        pass
    return None


def run(operation: str, **params) -> Dict[str, Any]:
    """Execute Reddit intelligence operations"""
    reddit = RedditIntelligence()
    
    if operation == "search_subreddit":
        subreddit = params.get('subreddit')
        query = params.get('query', '')
        sort = params.get('sort', 'hot')
        limit = params.get('limit', 25)
        time_filter = params.get('time_filter', 'all')
        
        if not subreddit:
            return {"error": "subreddit required for search_subreddit operation"}
        
        return reddit.search_subreddit(subreddit, query, sort, limit, time_filter)
    
    elif operation == "get_comments":
        subreddit = params.get('subreddit')
        post_id = params.get('post_id')
        limit = params.get('limit', 50)
        
        if not subreddit or not post_id:
            return {"error": "subreddit and post_id required for get_comments operation"}
        
        return reddit.get_post_comments(subreddit, post_id, limit)
    
    elif operation == "analyze_sentiment":
        subreddit = params.get('subreddit')
        query = params.get('query', '')
        limit = params.get('limit', 25)
        
        if not subreddit:
            return {"error": "subreddit required for analyze_sentiment operation"}
        
        # Get posts first
        posts_result = reddit.search_subreddit(subreddit, query, "hot", limit)
        
        if not posts_result.get('success'):
            return posts_result
        
        # Extract texts for sentiment analysis
        texts = []
        for post in posts_result['posts']:
            texts.append(post['title'])
            if post['selftext']:
                texts.append(post['selftext'])
        
        sentiment_result = analyze_sentiment(texts)
        sentiment_result['subreddit'] = subreddit
        sentiment_result['query'] = query
        sentiment_result['posts_analyzed'] = len(posts_result['posts'])
        
        return sentiment_result
    
    elif operation == "find_trending":
        subreddit = params.get('subreddit', 'all')
        time_filter = params.get('time_filter', 'day')
        limit = params.get('limit', 50)
        
        return find_trending_topics(reddit, subreddit, time_filter, limit)
    
    elif operation == "find_experts":
        subreddit = params.get('subreddit')
        topic = params.get('topic', '')
        min_karma = params.get('min_karma_threshold', 1000)
        
        if not subreddit:
            return {"error": "subreddit required for find_experts operation"}
        
        return find_experts(reddit, subreddit, topic, min_karma)
    
    elif operation == "multi_search":
        subreddits = params.get('subreddits', [])
        query = params.get('query')
        limit_per_sub = params.get('limit_per_sub', 10)
        
        if not subreddits or not query:
            return {"error": "subreddits and query required for multi_search operation"}
        
        return multi_subreddit_search(reddit, subreddits, query, limit_per_sub)
    
    else:
        return {
            "error": f"Unknown operation: {operation}. Available: search_subreddit, get_comments, analyze_sentiment, find_trending, find_experts, multi_search"
        }


def spec() -> Dict[str, Any]:
    """Return the MCP function specification for Reddit Intelligence"""
    
    override = _load_spec_override("reddit_intelligence")
    if override and isinstance(override, dict):
        return override

    # Fallback minimal, should not be used if JSON exists
    return {
        "type": "function",
        "function": {
            "name": "reddit_intelligence",
            "displayName": "Reddit",
            "parameters": {
                "type": "object",
                "properties": {"operation": {"type": "string"}},
                "required": ["operation"],
                "additionalProperties": False
            }
        }
    }
