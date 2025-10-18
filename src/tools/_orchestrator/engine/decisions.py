# Decision evaluation (truthy, enum_from_field, compare, regex_match, in_list, has_key)

import re
from typing import Any, Dict, List

class DecisionError(Exception):
    """Raised when decision evaluation fails"""
    pass

def evaluate_decision(kind: str, input_value: Any, decision_spec: Dict, available_routes: List[str]) -> str:
    """
    Evaluate decision and return route label.
    
    Args:
        kind: Decision kind
        input_value: Resolved input value
        decision_spec: Full decision spec (from node)
        available_routes: Available route labels (from edges)
    
    Returns:
        Route label (e.g., "true", "false", "SPAM", "match")
    
    Raises:
        DecisionError: If evaluation fails or no matching route
    """
    if kind == 'truthy':
        return evaluate_truthy(input_value)
    elif kind == 'enum_from_field':
        return evaluate_enum_from_field(input_value, decision_spec, available_routes)
    elif kind == 'compare':
        return evaluate_compare(input_value, decision_spec)
    elif kind == 'regex_match':
        return evaluate_regex_match(input_value, decision_spec)
    elif kind == 'in_list':
        return evaluate_in_list(input_value, decision_spec)
    elif kind == 'has_key':
        return evaluate_has_key(input_value, decision_spec)
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
    
    Example:
        value = "spam", normalize = "upper", available_routes = ["SPAM", "HAM"]
        → returns "SPAM"
    """
    if not isinstance(value, str):
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
    
    raise DecisionError(
        f"No matching route for value '{value}' (available: {available_routes}, no fallback)"
    )

def evaluate_compare(value: Any, decision_spec: Dict) -> str:
    """
    Evaluate compare decision (numeric/string comparison).
    
    Example:
        value = 8.5, operator = ">=", value = 7 → returns "true"
    """
    operator = decision_spec.get('operator')
    right_value = decision_spec.get('value')
    
    if not operator:
        raise DecisionError("compare decision missing 'operator' field")
    if right_value is None:
        raise DecisionError("compare decision missing 'value' field")
    
    # Try numeric comparison first
    try:
        left = float(value)
        right = float(right_value)
        
        if operator == '==':
            result = left == right
        elif operator == '!=':
            result = left != right
        elif operator == '>':
            result = left > right
        elif operator == '>=':
            result = left >= right
        elif operator == '<':
            result = left < right
        elif operator == '<=':
            result = left <= right
        else:
            raise DecisionError(f"Unknown operator: {operator} (valid: ==, !=, >, >=, <, <=)")
        
        return "true" if result else "false"
    
    except (ValueError, TypeError):
        # Fallback to string comparison
        left_str = str(value)
        right_str = str(right_value)
        
        if operator == '==':
            result = left_str == right_str
        elif operator == '!=':
            result = left_str != right_str
        else:
            raise DecisionError(f"Operator {operator} requires numeric values")
        
        return "true" if result else "false"

def evaluate_regex_match(value: Any, decision_spec: Dict) -> str:
    """
    Evaluate regex_match decision (pattern matching).
    
    Args:
        value: Input string
        decision_spec: Must contain 'pattern', optional 'flags'
    
    Returns:
        "match" if pattern matches, "no_match" otherwise
    
    Example:
        value = "RE: Important", pattern = "^RE:", flags = "i" → returns "match"
    """
    pattern = decision_spec.get('pattern')
    if not pattern:
        raise DecisionError("regex_match decision missing 'pattern' field")
    
    # Parse flags (e.g., "i" for case-insensitive)
    flags_str = decision_spec.get('flags', '')
    flags = 0
    if 'i' in flags_str:
        flags |= re.IGNORECASE
    if 'm' in flags_str:
        flags |= re.MULTILINE
    if 's' in flags_str:
        flags |= re.DOTALL
    
    # Convert value to string
    text = str(value)
    
    try:
        if re.search(pattern, text, flags):
            return "match"
        else:
            return "no_match"
    except re.error as e:
        raise DecisionError(f"Invalid regex pattern '{pattern}': {e}")

def evaluate_in_list(value: Any, decision_spec: Dict) -> str:
    """
    Evaluate in_list decision (membership test).
    
    Args:
        value: Value to check
        decision_spec: Must contain 'list' (array)
    
    Returns:
        "true" if value in list, "false" otherwise
    
    Example:
        value = "apple", list = ["apple", "banana"] → returns "true"
    """
    target_list = decision_spec.get('list')
    if not isinstance(target_list, list):
        raise DecisionError("in_list decision missing 'list' field (must be array)")
    
    # Check membership
    if value in target_list:
        return "true"
    else:
        return "false"

def evaluate_has_key(value: Any, decision_spec: Dict) -> str:
    """
    Evaluate has_key decision (check if object has key).
    
    Args:
        value: Object/dict to check
        decision_spec: Must contain 'key' (string)
    
    Returns:
        "true" if key exists, "false" otherwise
    
    Example:
        value = {"name": "Alice"}, key = "name" → returns "true"
    """
    key = decision_spec.get('key')
    if not key:
        raise DecisionError("has_key decision missing 'key' field")
    
    if not isinstance(value, dict):
        return "false"
    
    if key in value:
        return "true"
    else:
        return "false"
