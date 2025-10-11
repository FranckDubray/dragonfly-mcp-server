"""
Input validation for CoinGecko operations
"""


def validate_params(params):
    """Validate and normalize parameters"""
    operation = params.get('operation')
    if not operation:
        raise ValueError("Missing required parameter: operation")
    
    # Validate operation-specific requirements
    if operation in ['get_price', 'get_coin_info', 'get_market_chart']:
        if not params.get('coin_id'):
            raise ValueError(f"{operation} requires 'coin_id'")
    
    elif operation == 'get_coin_history':
        if not params.get('coin_id'):
            raise ValueError("get_coin_history requires 'coin_id'")
        if not params.get('date'):
            raise ValueError("get_coin_history requires 'date' (format: DD-MM-YYYY)")
        # Validate date format
        date = params['date']
        if not _validate_date_format(date):
            raise ValueError("Invalid date format. Use DD-MM-YYYY (e.g., '30-12-2023')")
    
    elif operation == 'search_coins':
        if not params.get('query'):
            raise ValueError("search_coins requires 'query'")
        if len(params['query']) < 3:
            raise ValueError("Search query must be at least 3 characters")
    
    elif operation == 'compare_coins':
        if not params.get('coin_ids'):
            raise ValueError("compare_coins requires 'coin_ids' array")
        if not isinstance(params['coin_ids'], list):
            raise ValueError("coin_ids must be an array")
        if len(params['coin_ids']) < 2:
            raise ValueError("compare_coins requires at least 2 coin IDs")
        if len(params['coin_ids']) > 10:
            raise ValueError("compare_coins supports max 10 coins")
    
    # Set defaults
    validated = params.copy()
    validated.setdefault('vs_currency', 'usd')
    validated.setdefault('days', '7')
    validated.setdefault('include_market_cap', True)
    validated.setdefault('include_24hr_vol', True)
    validated.setdefault('include_24hr_change', True)
    validated.setdefault('limit', 50)
    
    return validated


def _validate_date_format(date_str):
    """Validate DD-MM-YYYY format"""
    import re
    pattern = r'^\d{2}-\d{2}-\d{4}$'
    if not re.match(pattern, date_str):
        return False
    
    # Additional check: parse date
    try:
        parts = date_str.split('-')
        day, month, year = int(parts[0]), int(parts[1]), int(parts[2])
        if day < 1 or day > 31 or month < 1 or month > 12 or year < 2000:
            return False
    except (ValueError, IndexError):
        return False
    
    return True
