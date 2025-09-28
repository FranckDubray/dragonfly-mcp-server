"""Reddit Intelligence - Modular implementation"""

from .core import RedditIntelligence
from .sentiment import analyze_sentiment
from .experts import find_experts
from .trends import find_trending_topics
from .multi_search import multi_subreddit_search

__all__ = [
    'RedditIntelligence',
    'analyze_sentiment', 
    'find_experts',
    'find_trending_topics',
    'multi_subreddit_search'
]