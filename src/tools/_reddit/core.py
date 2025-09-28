"""Reddit Intelligence - Core functionality"""

import requests
from typing import Dict, Any, List, Optional
import re
from datetime import datetime, timedelta
import time


class RedditIntelligence:
    """Reddit intelligence and analysis tool - Core functionality"""
    
    def __init__(self):
        self.base_url = "https://www.reddit.com"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (compatible; Reddit-Intelligence-Tool/1.0)',
            'Accept': 'application/json, text/html'
        }
    
    def clean_text(self, text: str) -> str:
        """Clean Reddit text content"""
        if not text:
            return ""
        
        # Remove Reddit markdown
        text = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', text)  # Links
        text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)  # Bold
        text = re.sub(r'\*(.*?)\*', r'\1', text)  # Italic
        text = re.sub(r'~~(.*?)~~', r'\1', text)  # Strikethrough
        text = re.sub(r'^&gt;(.+)', r'> \1', text, flags=re.MULTILINE)  # Quotes
        
        # Clean extra whitespace
        text = re.sub(r'\s+', ' ', text.strip())
        
        return text
    
    def get_json_data(self, url: str) -> Optional[Dict]:
        """Get JSON data from Reddit API"""
        try:
            # Add .json to URL if not present
            if not url.endswith('.json'):
                url += '.json'
            
            response = requests.get(url, headers=self.headers, timeout=15)
            response.raise_for_status()
            
            return response.json()
            
        except Exception as e:
            return None
    
    def search_subreddit(self, subreddit: str, query: str = "", sort: str = "hot", 
                        limit: int = 25, time_filter: str = "all") -> Dict[str, Any]:
        """Search within a specific subreddit"""
        try:
            if query:
                # Search with query
                url = f"{self.base_url}/r/{subreddit}/search.json"
                params = {
                    'q': query,
                    'restrict_sr': 'on',
                    'sort': sort,
                    'limit': limit,
                    't': time_filter
                }
                
                response = requests.get(url, headers=self.headers, params=params, timeout=15)
            else:
                # Get subreddit posts
                url = f"{self.base_url}/r/{subreddit}/{sort}.json"
                params = {
                    'limit': limit,
                    't': time_filter
                }
                
                response = requests.get(url, headers=self.headers, params=params, timeout=15)
            
            response.raise_for_status()
            data = response.json()
            
            if 'data' not in data or 'children' not in data['data']:
                return {"error": "Invalid response format", "subreddit": subreddit}
            
            posts = []
            for post in data['data']['children']:
                post_data = post['data']
                
                posts.append({
                    'id': post_data.get('id', ''),
                    'title': self.clean_text(post_data.get('title', '')),
                    'author': post_data.get('author', '[deleted]'),
                    'score': post_data.get('score', 0),
                    'upvote_ratio': post_data.get('upvote_ratio', 0),
                    'num_comments': post_data.get('num_comments', 0),
                    'created_utc': post_data.get('created_utc', 0),
                    'url': post_data.get('url', ''),
                    'permalink': f"{self.base_url}{post_data.get('permalink', '')}",
                    'selftext': self.clean_text(post_data.get('selftext', '')),
                    'flair': post_data.get('link_flair_text', ''),
                    'is_video': post_data.get('is_video', False),
                    'over_18': post_data.get('over_18', False),
                    'subreddit': post_data.get('subreddit', '')
                })
            
            return {
                'success': True,
                'subreddit': subreddit,
                'query': query,
                'sort': sort,
                'posts_found': len(posts),
                'posts': posts
            }
            
        except Exception as e:
            return {
                'success': False,
                'subreddit': subreddit,
                'error': str(e)
            }
    
    def get_post_comments(self, subreddit: str, post_id: str, limit: int = 50) -> Dict[str, Any]:
        """Get comments from a specific post"""
        try:
            url = f"{self.base_url}/r/{subreddit}/comments/{post_id}.json"
            params = {'limit': limit}
            
            response = requests.get(url, headers=self.headers, params=params, timeout=15)
            response.raise_for_status()
            data = response.json()
            
            if len(data) < 2:
                return {"error": "Invalid post or no comments", "post_id": post_id}
            
            # First element is the post, second is comments
            post_info = data[0]['data']['children'][0]['data']
            comments_data = data[1]['data']['children']
            
            def extract_comment(comment_data, depth=0):
                if 'data' not in comment_data:
                    return None
                
                c_data = comment_data['data']
                
                comment = {
                    'id': c_data.get('id', ''),
                    'author': c_data.get('author', '[deleted]'),
                    'body': self.clean_text(c_data.get('body', '')),
                    'score': c_data.get('score', 0),
                    'created_utc': c_data.get('created_utc', 0),
                    'depth': depth,
                    'replies': []
                }
                
                # Get replies
                if 'replies' in c_data and c_data['replies'] and depth < 3:  # Limit depth
                    if isinstance(c_data['replies'], dict) and 'data' in c_data['replies']:
                        for reply in c_data['replies']['data'].get('children', []):
                            reply_comment = extract_comment(reply, depth + 1)
                            if reply_comment:
                                comment['replies'].append(reply_comment)
                
                return comment
            
            comments = []
            for comment_data in comments_data[:limit]:
                comment = extract_comment(comment_data)
                if comment and comment['body']:  # Skip deleted/empty comments
                    comments.append(comment)
            
            return {
                'success': True,
                'post_id': post_id,
                'post_title': self.clean_text(post_info.get('title', '')),
                'post_author': post_info.get('author', ''),
                'post_score': post_info.get('score', 0),
                'comments_found': len(comments),
                'comments': comments
            }
            
        except Exception as e:
            return {
                'success': False,
                'post_id': post_id,
                'error': str(e)
            }