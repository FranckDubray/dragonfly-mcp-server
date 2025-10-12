"""
Trivia API core business logic
Pure business logic, coordinates validators and API client
"""
from typing import Dict, Any
import logging
from .services.api_client import TriviaAPIClient
from .utils import (
    build_query_params,
    decode_question,
    format_question_with_all_answers,
    parse_response_code
)

logger = logging.getLogger(__name__)


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
    
    logger.info(f"Fetching {query_params.get('amount', 10)} questions (category: {query_params.get('category', 'any')})")
    
    # Make API request
    response = client.get_questions(query_params)
    
    # Parse response code
    response_info = parse_response_code(response.get("response_code", 0))
    
    if not response_info["success"]:
        logger.warning(f"API response code {response_info['code']}: {response_info['message']}")
    
    # Decode questions
    decoded_questions = []
    for question_dict in response.get("results", []):
        decoded = decode_question(question_dict, encoding)
        # Add shuffled answers with correct answer index
        formatted = format_question_with_all_answers(decoded)
        decoded_questions.append(formatted)
    
    logger.info(f"Retrieved {len(decoded_questions)} questions")
    
    return {
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
    logger.info("Fetching trivia categories")
    response = client.list_categories()
    categories = response.get("trivia_categories", [])
    
    logger.info(f"Retrieved {len(categories)} categories")
    
    return {
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
    logger.info(f"Fetching question count for category {category_id}")
    
    response = client.get_category_count(category_id)
    
    return {
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
    logger.info("Fetching global question counts")
    response = client.get_global_count()
    
    # Global count endpoint returns different structure
    # It includes overall stats and categories breakdown
    return {
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
    logger.info("Creating session token")
    response = client.create_session_token()
    
    # Parse response code
    response_info = parse_response_code(response.get("response_code", 0))
    
    if not response_info["success"]:
        logger.warning(f"Token creation failed: {response_info['message']}")
    
    token = response.get("token")
    logger.info(f"Session token created: {token[:16]}...")
    
    return {
        "token": token
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
    logger.info(f"Resetting session token: {token[:16]}...")
    
    response = client.reset_session_token(token)
    
    # Parse response code
    response_info = parse_response_code(response.get("response_code", 0))
    
    if not response_info["success"]:
        logger.warning(f"Token reset failed: {response_info['message']}")
    
    reset_token = response.get("token")
    logger.info(f"Token reset successful")
    
    return {
        "token": reset_token,
        "message": "Token has been reset - all questions are available again"
    }
