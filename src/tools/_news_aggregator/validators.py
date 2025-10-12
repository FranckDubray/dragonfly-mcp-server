"""Input validation for news aggregator."""


def validate_query_required(query):
    """Validate query parameter is present and non-empty."""
    if not query or not isinstance(query, str) or not query.strip():
        return {"valid": False, "error": "Parameter 'query' is required and must be a non-empty string"}
    return {"valid": True}


def validate_country_required(country):
    """Validate country parameter for top_headlines."""
    if not country or not isinstance(country, str) or not country.strip():
        return {"valid": False, "error": "Parameter 'country' is required for top_headlines operation"}
    return {"valid": True}


def validate_limit(limit):
    """Validate limit parameter respects anti-flood policy."""
    if limit is not None:
        if not isinstance(limit, int):
            return {"valid": False, "error": "Parameter 'limit' must be an integer"}
        if limit < 1:
            return {"valid": False, "error": "Parameter 'limit' must be at least 1"}
        if limit > 100:
            return {"valid": False, "error": "Parameter 'limit' cannot exceed 100 (anti-flood policy)"}
    return {"valid": True}


def validate_page(page):
    """Validate page parameter for pagination."""
    if page is not None:
        if not isinstance(page, int):
            return {"valid": False, "error": "Parameter 'page' must be an integer"}
        if page < 1:
            return {"valid": False, "error": "Parameter 'page' must be at least 1"}
    return {"valid": True}


def validate_date_format(date_str, param_name):
    """Validate date string format (YYYY-MM-DD)."""
    if not date_str:
        return {"valid": True}  # Optional
    
    if not isinstance(date_str, str):
        return {"valid": False, "error": f"Parameter '{param_name}' must be a string"}
    
    # Simple format check
    parts = date_str.split("-")
    if len(parts) != 3:
        return {"valid": False, "error": f"Parameter '{param_name}' must be in format YYYY-MM-DD"}
    
    try:
        year, month, day = int(parts[0]), int(parts[1]), int(parts[2])
        if year < 2000 or year > 2100:
            return {"valid": False, "error": f"Invalid year in '{param_name}'"}
        if month < 1 or month > 12:
            return {"valid": False, "error": f"Invalid month in '{param_name}'"}
        if day < 1 or day > 31:
            return {"valid": False, "error": f"Invalid day in '{param_name}'"}
    except ValueError:
        return {"valid": False, "error": f"Parameter '{param_name}' must contain valid numbers"}
    
    return {"valid": True}
