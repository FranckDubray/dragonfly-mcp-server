"""
CoinGecko API routing
"""
from .validators import validate_params
from .core import (
    get_price,
    get_coin_info,
    search_coins,
    get_market_chart,
    get_trending,
    get_global_data,
    list_coins,
    get_exchanges,
    get_coin_history,
    compare_coins
)


def route_operation(**params):
    """Route to appropriate handler based on operation"""
    try:
        # Validate and normalize params
        validated = validate_params(params)
        operation = validated['operation']
        
        # Route to handlers
        if operation == 'get_price':
            return get_price(validated)
        elif operation == 'get_coin_info':
            return get_coin_info(validated)
        elif operation == 'search_coins':
            return search_coins(validated)
        elif operation == 'get_market_chart':
            return get_market_chart(validated)
        elif operation == 'get_trending':
            return get_trending(validated)
        elif operation == 'get_global_data':
            return get_global_data(validated)
        elif operation == 'list_coins':
            return list_coins(validated)
        elif operation == 'get_exchanges':
            return get_exchanges(validated)
        elif operation == 'get_coin_history':
            return get_coin_history(validated)
        elif operation == 'compare_coins':
            return compare_coins(validated)
        else:
            raise ValueError(f"Unknown operation: {operation}")
            
    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'error_type': type(e).__name__
        }
