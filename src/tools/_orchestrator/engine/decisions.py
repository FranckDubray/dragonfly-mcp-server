# Decision evaluation (truthy, enum_from_field, ...)

from typing import Any, Dict, List

class DecisionError(Exception):
    """Raised when decision evaluation fails"""
    pass

def evaluate_decision(kind: str, input_value: Any, decision_spec: Dict, available_routes: List[str]) -> str:
    """
    Evaluate decision and return route label.
    
    Args:
        kind: Decision kind (e.g., "truthy", "enum_from_field")
        input_value: Resolved input value
        decision_spec: Full decision spec (from node)
        available_routes: Available route labels (from edges)
    
    Returns:
        Route label (e.g., "true", "false", "SPAM", "HAM")
    
    Raises:
        DecisionError: If evaluation fails or no matching route
    """
    if kind == 'truthy':
        return evaluate_truthy(input_value)
    elif kind == 'enum_from_field':
        return evaluate_enum_from_field(input_value, decision_spec, available_routes)
    else:
        raise DecisionError(f"Unknown decision kind: {kind}")

def evaluate_truthy(value: Any) -> str:
    """
    Evaluate truthy (returns 'true' or 'false').
    
    Falsy values: None, False, 0, "", [], {}
    """
    if value is None or value is False:
        return "false"
    if isinstance(value, (int, float)) and value == 0:
        return "false"
    if isinstance(value, str) and value == "":
        return "false"
    if isinstance(value, (list, dict)) and len(value) == 0:
        return "false"
    return "true"

def evaluate_enum_from_field(value: Any, decision_spec: Dict, available_routes: List[str]) -> str:
    """
    Evaluate enum_from_field (route based on string value).
    
    Args:
        value: Input value (should be string)
        decision_spec: Decision spec (with optional normalize, fallback)
        available_routes: Available route labels
    
    Returns:
        Matching route label
    
    Raises:
        DecisionError: If no match and no fallback
    
    Example:
        value = "spam", normalize = "upper", available_routes = ["SPAM", "HAM"]
        → returns "SPAM"
    """
    if not isinstance(value, str):
        # Try to convert to string
        value = str(value)
    
    # Apply normalization
    normalize = decision_spec.get('normalize')
    if normalize == 'upper':
        value = value.upper()
    elif normalize == 'lower':
        value = value.lower()
    elif normalize == 'trim':
        value = value.strip()
    
    # Match against available routes
    if value in available_routes:
        return value
    
    # No match: use fallback if specified
    fallback = decision_spec.get('fallback')
    if fallback:
        return fallback
    
    # No match and no fallback → error
    raise DecisionError(
        f"No matching route for value '{value}' (available: {available_routes}, no fallback)"
    )
