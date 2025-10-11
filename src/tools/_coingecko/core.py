"""
CoinGecko core business logic
"""
from .services.api_client import make_request
from .utils import format_price_data, format_coin_info, format_market_data


def get_price(params):
    """Get simple price for a coin"""
    coin_id = params['coin_id']
    vs_currency = params['vs_currency']
    
    query_params = {
        'ids': coin_id,
        'vs_currencies': vs_currency,
        'include_market_cap': str(params['include_market_cap']).lower(),
        'include_24hr_vol': str(params['include_24hr_vol']).lower(),
        'include_24hr_change': str(params['include_24hr_change']).lower()
    }
    
    data = make_request('simple/price', query_params)
    
    if coin_id not in data:
        return {
            'success': False,
            'error': f"Coin '{coin_id}' not found. Use list_coins to find valid coin IDs."
        }
    
    return {
        'success': True,
        'operation': 'get_price',
        'coin_id': coin_id,
        'vs_currency': vs_currency,
        'data': format_price_data(data[coin_id], vs_currency)
    }


def get_coin_info(params):
    """Get comprehensive coin information"""
    coin_id = params['coin_id']
    
    query_params = {
        'localization': 'false',
        'tickers': 'false',
        'market_data': 'true',
        'community_data': 'true',
        'developer_data': 'true'
    }
    
    data = make_request(f'coins/{coin_id}', query_params)
    
    return {
        'success': True,
        'operation': 'get_coin_info',
        'coin_id': coin_id,
        'data': format_coin_info(data, params['vs_currency'])
    }


def search_coins(params):
    """Search coins by name or symbol"""
    query = params['query']
    
    data = make_request('search', {'query': query})
    
    coins = data.get('coins', [])[:params['limit']]
    
    return {
        'success': True,
        'operation': 'search_coins',
        'query': query,
        'results': [
            {
                'id': coin.get('id'),
                'name': coin.get('name'),
                'symbol': coin.get('symbol'),
                'market_cap_rank': coin.get('market_cap_rank'),
                'thumb': coin.get('thumb'),
                'large': coin.get('large')
            }
            for coin in coins
        ],
        'total_count': len(data.get('coins', [])),
        'returned_count': len(coins)
    }


def get_market_chart(params):
    """Get historical market data (price, market cap, volume)"""
    coin_id = params['coin_id']
    vs_currency = params['vs_currency']
    days = params['days']
    
    query_params = {
        'vs_currency': vs_currency,
        'days': days
    }
    
    data = make_request(f'coins/{coin_id}/market_chart', query_params)
    
    prices = data.get('prices', [])
    market_caps = data.get('market_caps', [])
    volumes = data.get('total_volumes', [])
    
    return {
        'success': True,
        'operation': 'get_market_chart',
        'coin_id': coin_id,
        'vs_currency': vs_currency,
        'days': days,
        'data_points': len(prices),
        'prices': [{'timestamp': p[0], 'price': p[1]} for p in prices],
        'market_caps': [{'timestamp': m[0], 'market_cap': m[1]} for m in market_caps],
        'volumes': [{'timestamp': v[0], 'volume': v[1]} for v in volumes]
    }


def get_trending(params):
    """Get trending coins (top 7)"""
    data = make_request('search/trending')
    
    coins = data.get('coins', [])
    
    return {
        'success': True,
        'operation': 'get_trending',
        'trending_coins': [
            {
                'id': coin['item'].get('id'),
                'name': coin['item'].get('name'),
                'symbol': coin['item'].get('symbol'),
                'market_cap_rank': coin['item'].get('market_cap_rank'),
                'price_btc': coin['item'].get('price_btc'),
                'thumb': coin['item'].get('thumb'),
                'score': coin['item'].get('score')
            }
            for coin in coins
        ],
        'count': len(coins)
    }


def get_global_data(params):
    """Get global cryptocurrency market data"""
    data = make_request('global')
    
    global_data = data.get('data', {})
    
    return {
        'success': True,
        'operation': 'get_global_data',
        'data': {
            'active_cryptocurrencies': global_data.get('active_cryptocurrencies'),
            'markets': global_data.get('markets'),
            'total_market_cap': global_data.get('total_market_cap', {}),
            'total_volume': global_data.get('total_volume', {}),
            'market_cap_percentage': global_data.get('market_cap_percentage', {}),
            'market_cap_change_percentage_24h_usd': global_data.get('market_cap_change_percentage_24h_usd'),
            'updated_at': global_data.get('updated_at')
        }
    }


def list_coins(params):
    """List all coins with ID, name, symbol"""
    limit = params['limit']
    
    data = make_request('coins/list')
    
    coins = data[:limit]
    
    return {
        'success': True,
        'operation': 'list_coins',
        'coins': [
            {
                'id': coin.get('id'),
                'name': coin.get('name'),
                'symbol': coin.get('symbol')
            }
            for coin in coins
        ],
        'total_available': len(data),
        'returned_count': len(coins),
        'truncated': len(data) > limit
    }


def get_exchanges(params):
    """Get list of exchanges"""
    limit = params['limit']
    
    query_params = {
        'per_page': limit,
        'page': 1
    }
    
    data = make_request('exchanges', query_params)
    
    return {
        'success': True,
        'operation': 'get_exchanges',
        'exchanges': [
            {
                'id': ex.get('id'),
                'name': ex.get('name'),
                'year_established': ex.get('year_established'),
                'country': ex.get('country'),
                'url': ex.get('url'),
                'trust_score': ex.get('trust_score'),
                'trade_volume_24h_btc': ex.get('trade_volume_24h_btc'),
                'trade_volume_24h_btc_normalized': ex.get('trade_volume_24h_btc_normalized')
            }
            for ex in data
        ],
        'returned_count': len(data)
    }


def get_coin_history(params):
    """Get historical coin data for a specific date"""
    coin_id = params['coin_id']
    date = params['date']
    
    query_params = {
        'date': date,
        'localization': 'false'
    }
    
    data = make_request(f'coins/{coin_id}/history', query_params)
    
    market_data = data.get('market_data', {})
    
    return {
        'success': True,
        'operation': 'get_coin_history',
        'coin_id': coin_id,
        'date': date,
        'name': data.get('name'),
        'symbol': data.get('symbol'),
        'market_data': {
            'current_price': market_data.get('current_price', {}),
            'market_cap': market_data.get('market_cap', {}),
            'total_volume': market_data.get('total_volume', {})
        }
    }


def compare_coins(params):
    """Compare multiple coins side by side"""
    coin_ids = params['coin_ids']
    vs_currency = params['vs_currency']
    
    query_params = {
        'ids': ','.join(coin_ids),
        'vs_currencies': vs_currency,
        'include_market_cap': 'true',
        'include_24hr_vol': 'true',
        'include_24hr_change': 'true'
    }
    
    data = make_request('simple/price', query_params)
    
    comparison = []
    for coin_id in coin_ids:
        if coin_id in data:
            comparison.append({
                'coin_id': coin_id,
                'data': format_price_data(data[coin_id], vs_currency)
            })
        else:
            comparison.append({
                'coin_id': coin_id,
                'error': 'Not found'
            })
    
    return {
        'success': True,
        'operation': 'compare_coins',
        'vs_currency': vs_currency,
        'comparison': comparison,
        'count': len(comparison)
    }
