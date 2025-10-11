"""
Trivia API utilities
Pure helper functions, no I/O
"""
import html
import base64
import urllib.parse


def decode_text(text: str, encoding: str) -> str:
    """
    Decode text based on encoding type
    
    Args:
        text: Encoded text
        encoding: One of 'url3986', 'urlLegacy', 'base64'
    
    Returns:
        Decoded plain text
    """
    if encoding == "base64":
        # Base64 decode
        try:
            decoded_bytes = base64.b64decode(text)
            return decoded_bytes.decode('utf-8')
        except Exception as e:
            # Fallback to original text if decode fails
            return text
    
    elif encoding in ["url3986", "urlLegacy"]:
        # URL decode
        decoded = urllib.parse.unquote(text)
        # Also decode HTML entities
        return html.unescape(decoded)
    
    else:
        # Unknown encoding, return as-is
        return text


def decode_question(question_dict: dict, encoding: str) -> dict:
    """
    Decode all text fields in a question object
    
    Args:
        question_dict: Raw question dict from API
        encoding: Encoding type used
    
    Returns:
        Question dict with decoded text fields
    """
    decoded = question_dict.copy()
    
    # Decode ALL text fields (including metadata)
    if "type" in decoded:
        decoded["type"] = decode_text(decoded["type"], encoding)
    
    if "difficulty" in decoded:
        decoded["difficulty"] = decode_text(decoded["difficulty"], encoding)
    
    if "category" in decoded:
        decoded["category"] = decode_text(decoded["category"], encoding)
    
    if "question" in decoded:
        decoded["question"] = decode_text(decoded["question"], encoding)
    
    if "correct_answer" in decoded:
        decoded["correct_answer"] = decode_text(decoded["correct_answer"], encoding)
    
    if "incorrect_answers" in decoded:
        decoded["incorrect_answers"] = [
            decode_text(ans, encoding) for ans in decoded["incorrect_answers"]
        ]
    
    return decoded


def format_question_with_all_answers(question_dict: dict) -> dict:
    """
    Format question by combining correct and incorrect answers into a single shuffled list
    
    Args:
        question_dict: Decoded question dict
    
    Returns:
        Question dict with 'all_answers' field and 'correct_answer_index'
    """
    import random
    
    formatted = question_dict.copy()
    
    # Combine all answers
    all_answers = [formatted["correct_answer"]] + formatted["incorrect_answers"]
    
    # Shuffle answers
    shuffled_answers = all_answers.copy()
    random.shuffle(shuffled_answers)
    
    # Find correct answer index in shuffled list
    correct_index = shuffled_answers.index(formatted["correct_answer"])
    
    # Add to formatted output
    formatted["all_answers"] = shuffled_answers
    formatted["correct_answer_index"] = correct_index
    
    return formatted


def parse_response_code(code: int) -> dict:
    """
    Parse API response code into human-readable message
    
    Args:
        code: Response code from API
    
    Returns:
        Dict with code, success flag, and message
    """
    codes = {
        0: {"success": True, "message": "Success"},
        1: {"success": False, "message": "No results - invalid question amount"},
        2: {"success": False, "message": "No results - not enough questions for given parameters"},
        3: {"success": False, "message": "Token not found - invalid session token"},
        4: {"success": False, "message": "Token empty - all questions have been used, reset token"},
        5: {"success": False, "message": "Rate limit exceeded - wait ~5 seconds before retry"}
    }
    
    return {
        "code": code,
        **codes.get(code, {"success": False, "message": f"Unknown response code: {code}"})
    }


def build_query_params(params: dict) -> dict:
    """
    Build query parameters for API request
    
    Args:
        params: Tool parameters
    
    Returns:
        Dict of query parameters for API
    """
    query = {}
    
    # Amount (required for get_questions)
    if "amount" in params:
        query["amount"] = params["amount"]
    
    # Category (optional)
    if "category" in params:
        query["category"] = params["category"]
    
    # Difficulty (optional)
    if "difficulty" in params:
        query["difficulty"] = params["difficulty"]
    
    # Type (optional)
    if "type" in params:
        query["type"] = params["type"]
    
    # Encode (default to base64)
    encode = params.get("encode", "base64")
    query["encode"] = encode
    
    # Token (optional)
    if "token" in params:
        query["token"] = params["token"]
    
    return query
