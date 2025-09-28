"""Reddit Intelligence - Trending Topics Analysis"""

import re
from typing import Dict, Any
from collections import Counter


def find_trending_topics(reddit_instance, subreddit: str = "all", time_filter: str = "day", limit: int = 50) -> Dict[str, Any]:
    """Find trending topics in a subreddit"""
    try:
        posts_result = reddit_instance.search_subreddit(subreddit, "", "hot", limit, time_filter)
        
        if not posts_result.get('success'):
            return posts_result
        
        posts = posts_result['posts']
        
        # Extract keywords from titles
        all_words = []
        for post in posts:
            title = post['title'].lower()
            # Remove common words and extract meaningful terms
            words = re.findall(r'\b[a-zA-Z]{3,}\b', title)
            
            # Filter out common words
            stop_words = {
                'the', 'and', 'for', 'are', 'but', 'not', 'you', 'all', 'can', 'had', 'her', 'was', 'one', 'our', 'out', 'day', 'get', 'has', 'him', 'his', 'how', 'its', 'may', 'new', 'now', 'old', 'see', 'two', 'way', 'who', 'boy', 'did', 'she', 'use', 'your', 'about', 'would', 'there', 'could', 'other', 'after', 'first', 'never', 'these', 'think', 'where', 'being', 'every', 'great', 'might', 'shall', 'still', 'those', 'under', 'while', 'this', 'that', 'with', 'have', 'from', 'they', 'know', 'want', 'been', 'good', 'much', 'some', 'time', 'very', 'when', 'come', 'here', 'just', 'like', 'long', 'make', 'many', 'over', 'such', 'take', 'than', 'them', 'well', 'were', 'what'
            }
            
            filtered_words = [word for word in words if word not in stop_words and len(word) > 2]
            all_words.extend(filtered_words)
        
        # Count word frequency
        word_counts = Counter(all_words)
        trending_words = word_counts.most_common(20)
        
        # Analyze post metrics
        total_score = sum(post['score'] for post in posts)
        avg_score = total_score / len(posts) if posts else 0
        total_comments = sum(post['num_comments'] for post in posts)
        
        # Find top posts
        top_posts = sorted(posts, key=lambda x: x['score'], reverse=True)[:5]
        
        return {
            'success': True,
            'subreddit': subreddit,
            'time_filter': time_filter,
            'posts_analyzed': len(posts),
            'trending_keywords': [{'word': word, 'frequency': count} for word, count in trending_words],
            'metrics': {
                'total_score': total_score,
                'average_score': round(avg_score, 1),
                'total_comments': total_comments,
                'average_comments': round(total_comments / len(posts), 1) if posts else 0
            },
            'top_posts': [{
                'title': post['title'],
                'score': post['score'],
                'comments': post['num_comments'],
                'author': post['author'],
                'permalink': post['permalink']
            } for post in top_posts]
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }