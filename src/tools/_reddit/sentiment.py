"""Reddit Intelligence - Sentiment Analysis"""

from typing import Dict, Any, List


def analyze_sentiment(texts: List[str]) -> Dict[str, Any]:
    """Basic sentiment analysis of text list"""
    if not texts:
        return {"error": "No texts provided for sentiment analysis"}
    
    # Simple keyword-based sentiment analysis
    positive_words = [
        'good', 'great', 'excellent', 'amazing', 'awesome', 'love', 'like', 
        'best', 'perfect', 'wonderful', 'fantastic', 'brilliant', 'outstanding',
        'helpful', 'useful', 'easy', 'simple', 'clear', 'works', 'solved'
    ]
    
    negative_words = [
        'bad', 'terrible', 'awful', 'horrible', 'hate', 'dislike', 'worst',
        'broken', 'useless', 'confusing', 'difficult', 'hard', 'problem',
        'issue', 'bug', 'error', 'fails', 'doesnt work', "doesn't work"
    ]
    
    sentiments = []
    positive_count = 0
    negative_count = 0
    neutral_count = 0
    
    for text in texts:
        text_lower = text.lower()
        
        pos_score = sum(1 for word in positive_words if word in text_lower)
        neg_score = sum(1 for word in negative_words if word in text_lower)
        
        if pos_score > neg_score:
            sentiment = 'positive'
            positive_count += 1
        elif neg_score > pos_score:
            sentiment = 'negative'
            negative_count += 1
        else:
            sentiment = 'neutral'
            neutral_count += 1
        
        sentiments.append({
            'text': text[:100] + '...' if len(text) > 100 else text,
            'sentiment': sentiment,
            'positive_score': pos_score,
            'negative_score': neg_score
        })
    
    total = len(texts)
    return {
        'success': True,
        'total_analyzed': total,
        'positive_count': positive_count,
        'negative_count': negative_count,
        'neutral_count': neutral_count,
        'positive_percentage': round((positive_count / total) * 100, 1),
        'negative_percentage': round((negative_count / total) * 100, 1),
        'neutral_percentage': round((neutral_count / total) * 100, 1),
        'overall_sentiment': 'positive' if positive_count > negative_count else 'negative' if negative_count > positive_count else 'neutral',
        'detailed_results': sentiments[:10]  # Show first 10 detailed results
    }