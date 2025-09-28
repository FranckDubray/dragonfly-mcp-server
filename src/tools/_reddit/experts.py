"""Reddit Intelligence - Expert Users Analysis"""

from typing import Dict, Any


def find_experts(reddit_instance, subreddit: str, topic: str = "", min_karma_threshold: int = 1000) -> Dict[str, Any]:
    """Find expert users in a subreddit based on activity and karma"""
    try:
        # Search for topic or get general posts
        posts_result = reddit_instance.search_subreddit(subreddit, topic, "top", 50, "month")
        
        if not posts_result.get('success'):
            return posts_result
        
        posts = posts_result['posts']
        
        # Analyze authors
        author_stats = {}
        
        for post in posts:
            author = post['author']
            if author == '[deleted]':
                continue
            
            if author not in author_stats:
                author_stats[author] = {
                    'posts': 0,
                    'total_score': 0,
                    'total_comments': 0,
                    'avg_score': 0,
                    'posts_list': []
                }
            
            author_stats[author]['posts'] += 1
            author_stats[author]['total_score'] += post['score']
            author_stats[author]['total_comments'] += post['num_comments']
            author_stats[author]['posts_list'].append({
                'title': post['title'],
                'score': post['score'],
                'comments': post['num_comments']
            })
        
        # Calculate averages and filter experts
        experts = []
        for author, stats in author_stats.items():
            if stats['posts'] >= 2:  # At least 2 posts
                stats['avg_score'] = stats['total_score'] / stats['posts']
                
                # Score expert based on multiple factors
                expert_score = (
                    stats['avg_score'] * 0.4 +
                    stats['posts'] * 10 +
                    stats['total_comments'] * 0.1
                )
                
                experts.append({
                    'username': author,
                    'expert_score': round(expert_score, 1),
                    'posts_count': stats['posts'],
                    'avg_post_score': round(stats['avg_score'], 1),
                    'total_karma_earned': stats['total_score'],
                    'engagement_generated': stats['total_comments'],
                    'top_posts': sorted(stats['posts_list'], key=lambda x: x['score'], reverse=True)[:3]
                })
        
        # Sort by expert score
        experts.sort(key=lambda x: x['expert_score'], reverse=True)
        
        return {
            'success': True,
            'subreddit': subreddit,
            'topic': topic or 'general',
            'posts_analyzed': len(posts),
            'experts_found': len(experts),
            'experts': experts[:10]  # Top 10 experts
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }