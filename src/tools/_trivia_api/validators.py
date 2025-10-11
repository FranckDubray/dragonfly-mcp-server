"""
Trivia API validators
Pure validation logic, no I/O
"""


def validate_operation(operation: str) -> None:
    """Validate operation parameter"""
    valid_ops = [
        "get_questions",
        "list_categories",
        "get_category_count",
        "get_global_count",
        "create_session_token",
        "reset_session_token"
    ]
    if operation not in valid_ops:
        raise ValueError(f"Invalid operation: {operation}. Must be one of {valid_ops}")


def validate_amount(amount: int) -> None:
    """Validate amount parameter"""
    if not isinstance(amount, int):
        raise TypeError(f"amount must be an integer, got {type(amount).__name__}")
    if amount < 1 or amount > 50:
        raise ValueError(f"amount must be between 1 and 50, got {amount}")


def validate_category(category: int) -> None:
    """Validate category ID"""
    if not isinstance(category, int):
        raise TypeError(f"category must be an integer, got {type(category).__name__}")
    if category < 9 or category > 32:
        raise ValueError(f"category must be between 9 and 32, got {category}")


def validate_difficulty(difficulty: str) -> None:
    """Validate difficulty parameter"""
    valid_difficulties = ["easy", "medium", "hard"]
    if difficulty not in valid_difficulties:
        raise ValueError(f"Invalid difficulty: {difficulty}. Must be one of {valid_difficulties}")


def validate_type(question_type: str) -> None:
    """Validate question type parameter"""
    valid_types = ["multiple", "boolean"]
    if question_type not in valid_types:
        raise ValueError(f"Invalid type: {question_type}. Must be one of {valid_types}")


def validate_encode(encode: str) -> None:
    """Validate encoding parameter"""
    valid_encodings = ["url3986", "urlLegacy", "base64"]
    if encode not in valid_encodings:
        raise ValueError(f"Invalid encode: {encode}. Must be one of {valid_encodings}")


def validate_token(token: str) -> None:
    """Validate session token format"""
    if not isinstance(token, str):
        raise TypeError(f"token must be a string, got {type(token).__name__}")
    if not token.strip():
        raise ValueError("token cannot be empty")


def validate_get_questions_params(params: dict) -> None:
    """Validate parameters for get_questions operation"""
    # Amount validation
    amount = params.get("amount", 10)
    validate_amount(amount)
    
    # Optional category
    if "category" in params:
        validate_category(params["category"])
    
    # Optional difficulty
    if "difficulty" in params:
        validate_difficulty(params["difficulty"])
    
    # Optional type
    if "type" in params:
        validate_type(params["type"])
    
    # Optional encode
    if "encode" in params:
        validate_encode(params["encode"])
    
    # Optional token
    if "token" in params:
        validate_token(params["token"])


def validate_category_count_params(params: dict) -> None:
    """Validate parameters for get_category_count operation"""
    if "category" not in params:
        raise ValueError("category parameter is required for get_category_count operation")
    validate_category(params["category"])


def validate_reset_token_params(params: dict) -> None:
    """Validate parameters for reset_session_token operation"""
    if "token" not in params:
        raise ValueError("token parameter is required for reset_session_token operation")
    validate_token(params["token"])
