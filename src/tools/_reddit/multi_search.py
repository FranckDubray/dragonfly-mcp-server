"""Reddit Intelligence - Multi-Subreddit Search"""

import time
from typing import Dict, Any, List


def multi_subreddit_search(reddit_instance, subreddits: List[str], query: str, limit_per_sub: int = 10) -> Dict[str, Any]:
    """Search across multiple subreddits"""
    all_results = []
    subreddit_stats = []
    
    for subreddit in subreddits:
        result = reddit_instance.search_subreddit(subreddit, query, "hot", limit_per_sub)
        
        if result.get('success'):
            posts = result['posts']
            all_results.extend(posts)
            
            subreddit_stats.append({
                'subreddit': subreddit,
                'posts_found': len(posts),
                'avg_score': round(sum(p['score'] for p in posts) / len(posts), 1) if posts else 0,
                'total_comments': sum(p['num_comments'] for p in posts)
            })
        else:
            subreddit_stats.append({
                'subreddit': subreddit,
                'error': result.get('error', 'Unknown error')
            })
        
        # Small delay between requests
        time.sleep(0.5)
    
    # Sort all results by score
    all_results.sort(key=lambda x: x['score'], reverse=True)
    
    return {
        'success': True,
        'query': query,
        'subreddits_searched': len(subreddits),
        'total_posts_found': len(all_results),
        'results': all_results,
        'subreddit_breakdown': subreddit_stats
    }