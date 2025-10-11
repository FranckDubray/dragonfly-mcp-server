"""
Utility functions for CoinGecko
"""


def format_price_data(data, vs_currency):
    """Format simple price data"""
    formatted = {
        'price': data.get(vs_currency)
    }
    
    # Add market cap if present
    market_cap_key = f'{vs_currency}_market_cap'
    if market_cap_key in data:
        formatted['market_cap'] = data[market_cap_key]
    
    # Add 24h volume if present
    vol_key = f'{vs_currency}_24h_vol'
    if vol_key in data:
        formatted['volume_24h'] = data[vol_key]
    
    # Add 24h change if present
    change_key = f'{vs_currency}_24h_change'
    if change_key in data:
        formatted['change_24h'] = data[change_key]
    
    return formatted


def format_coin_info(data, vs_currency):
    """Format comprehensive coin information - TRUNCATED for LLM"""
    market_data = data.get('market_data', {})
    
    # Get description and truncate to 300 chars max
    description = data.get('description', {}).get('en', '')
    if len(description) > 300:
        description = description[:297] + '...'
    
    return {
        'id': data.get('id'),
        'symbol': data.get('symbol'),
        'name': data.get('name'),
        'description': description,
        'categories': data.get('categories', [])[:5],  # Limit to 5 categories
        'links': {
            'homepage': data.get('links', {}).get('homepage', [])[:1],  # Only first homepage
            'blockchain_site': [s for s in data.get('links', {}).get('blockchain_site', []) if s][:2]  # Only 2 non-empty
        },
        'image': {
            'thumb': data.get('image', {}).get('thumb'),
            'small': data.get('image', {}).get('small')
        },
        'market_cap_rank': data.get('market_cap_rank'),
        'market_data': {
            'current_price': market_data.get('current_price', {}).get(vs_currency),
            'market_cap': market_data.get('market_cap', {}).get(vs_currency),
            'total_volume': market_data.get('total_volume', {}).get(vs_currency),
            'high_24h': market_data.get('high_24h', {}).get(vs_currency),
            'low_24h': market_data.get('low_24h', {}).get(vs_currency),
            'price_change_percentage_24h': market_data.get('price_change_percentage_24h'),
            'price_change_percentage_7d': market_data.get('price_change_percentage_7d'),
            'price_change_percentage_30d': market_data.get('price_change_percentage_30d'),
            'circulating_supply': market_data.get('circulating_supply'),
            'total_supply': market_data.get('total_supply'),
            'max_supply': market_data.get('max_supply'),
            'ath': market_data.get('ath', {}).get(vs_currency),
            'ath_change_percentage': market_data.get('ath_change_percentage', {}).get(vs_currency),
            'atl': market_data.get('atl', {}).get(vs_currency),
            'atl_change_percentage': market_data.get('atl_change_percentage', {}).get(vs_currency)
        },
        'community_data': {
            'twitter_followers': data.get('community_data', {}).get('twitter_followers'),
            'reddit_subscribers': data.get('community_data', {}).get('reddit_subscribers')
        },
        'last_updated': data.get('last_updated')
    }


def format_market_data(data):
    """Format market data for charts"""
    return {
        'timestamp': data[0],
        'value': data[1]
    }
