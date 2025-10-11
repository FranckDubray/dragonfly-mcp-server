"""
Trivia API core business logic
Pure business logic, coordinates validators and API client
"""
from typing import Dict, Any, List
from .services.api_client import TriviaAPIClient
from .utils import (
    build_query_params,
    decode_question,
    format_question_with_all_answers,
    parse_response_code
)


def get_questions(params: Dict[str, Any], client: TriviaAPIClient) -> Dict[str, Any]:
    """
    Get trivia questions with specified filters
    
    Args:
        params: Operation parameters
        client: API client instance
    
    Returns:
        Formatted questions data
    """
    # Build query parameters
    query_params = build_query_params(params)
    
    # Get encoding for decoding
    encoding = params.get("encode", "base64")
    
    # Make API request
    response = client.get_questions(query_params)
    
    # Parse response code
    response_info = parse_response_code(response.get("response_code", 0))
    
    # Decode questions
    decoded_questions = []
    for question_dict in response.get("results", []):
        decoded = decode_question(question_dict, encoding)
        # Add shuffled answers with correct answer index
        formatted = format_question_with_all_answers(decoded)
        decoded_questions.append(formatted)
    
    return {
        "success": response_info["success"],
        "response_code": response_info["code"],
        "message": response_info["message"],
        "count": len(decoded_questions),
        "questions": decoded_questions
    }


def list_categories(client: TriviaAPIClient) -> Dict[str, Any]:
    """
    Get list of all trivia categories
    
    Args:
        client: API client instance
    
    Returns:
        Categories data
    """
    response = client.list_categories()
    categories = response.get("trivia_categories", [])
    
    return {
        "success": True,
        "count": len(categories),
        "categories": categories
    }


def get_category_count(params: Dict[str, Any], client: TriviaAPIClient) -> Dict[str, Any]:
    """
    Get question count for a specific category
    
    Args:
        params: Operation parameters with category_id
        client: API client instance
    
    Returns:
        Category count data
    """
    category_id = params["category"]
    response = client.get_category_count(category_id)
    
    return {
        "success": True,
        "category_id": response.get("category_id"),
        "counts": response.get("category_question_count", {})
    }


def get_global_count(client: TriviaAPIClient) -> Dict[str, Any]:
    """
    Get global question count across all categories
    
    Args:
        client: API client instance
    
    Returns:
        Global count data
    """
    response = client.get_global_count()
    
    # Global count endpoint returns different structure
    # It includes overall stats and categories breakdown
    return {
        "success": True,
        "overall": response.get("overall", {}),
        "categories": response.get("categories", {})
    }


def create_session_token(client: TriviaAPIClient) -> Dict[str, Any]:
    """
    Create a new session token to avoid duplicate questions
    
    Args:
        client: API client instance
    
    Returns:
        Token data
    """
    response = client.create_session_token()
    
    # Parse response code
    response_info = parse_response_code(response.get("response_code", 0))
    
    return {
        "success": response_info["success"],
        "response_code": response_info["code"],
        "message": response_info["message"],
        "token": response.get("token"),
        "usage": "Include this token in get_questions requests to avoid duplicate questions in the same session"
    }


def reset_session_token(params: Dict[str, Any], client: TriviaAPIClient) -> Dict[str, Any]:
    """
    Reset a session token to replay all questions
    
    Args:
        params: Operation parameters with token
        client: API client instance
    
    Returns:
        Reset confirmation
    """
    token = params["token"]
    response = client.reset_session_token(token)
    
    # Parse response code
    response_info = parse_response_code(response.get("response_code", 0))
    
    return {
        "success": response_info["success"],
        "response_code": response_info["code"],
        "message": response_info["message"],
        "token": response.get("token"),
        "usage": "Token has been reset - all questions are available again"
    }
