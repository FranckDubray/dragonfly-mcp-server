"""Physical random sources: RANDOM.ORG (atmospheric noise)."""

import logging
from typing import Optional, List

logger = logging.getLogger(__name__)


def get_random_integers(
    min_val: int,
    max_val: int,
    count: int,
    unique: bool = False
) -> Optional[List[int]]:
    """Get random integers from physical sources.
    
    Args:
        min_val: Minimum value (inclusive)
        max_val: Maximum value (inclusive)
        count: Number of integers
        unique: Ensure uniqueness
        
    Returns:
        List of random integers
    """
    # Try RANDOM.ORG (atmospheric)
    result = _try_random_org_integers(min_val, max_val, count, unique)
    if result:
        return result
    
    # Fallback: Python secrets (CSPRNG)
    logger.warning("RANDOM.ORG failed, using fallback CSPRNG")
    return _fallback_integers(min_val, max_val, count, unique)


def get_random_bytes(length: int) -> Optional[bytes]:
    """Get random bytes from physical sources.
    
    Args:
        length: Number of bytes
        
    Returns:
        Random bytes
    """
    # Try RANDOM.ORG
    result = _try_random_org_bytes(length)
    if result:
        return result
    
    # Fallback
    logger.warning("RANDOM.ORG failed, using fallback CSPRNG")
    return _fallback_bytes(length)


def _try_random_org_integers(min_val: int, max_val: int, count: int, unique: bool) -> Optional[List[int]]:
    """Try to get integers from RANDOM.ORG."""
    try:
        import requests
        
        url = "https://www.random.org/integers/"
        params = {
            "num": count,
            "min": min_val,
            "max": max_val,
            "col": 1,
            "base": 10,
            "format": "plain",
            "rnd": "new"
        }
        
        response = requests.get(url, params=params, timeout=5)
        
        if response.status_code == 200:
            numbers = [int(line.strip()) for line in response.text.strip().split('\n') if line.strip()]
            
            if unique and len(set(numbers)) != len(numbers):
                numbers = list(dict.fromkeys(numbers))
                if len(numbers) < count:
                    return None
            
            return numbers
        
        return None
        
    except Exception as e:
        logger.debug(f"RANDOM.ORG error: {e}")
        return None


def _try_random_org_bytes(length: int) -> Optional[bytes]:
    """Try to get bytes from RANDOM.ORG."""
    try:
        import requests
        
        url = "https://www.random.org/integers/"
        params = {
            "num": length,
            "min": 0,
            "max": 255,
            "col": 1,
            "base": 10,
            "format": "plain",
            "rnd": "new"
        }
        
        response = requests.get(url, params=params, timeout=5)
        
        if response.status_code == 200:
            numbers = [int(line.strip()) for line in response.text.strip().split('\n') if line.strip()]
            return bytes(numbers[:length])
        
        return None
        
    except Exception as e:
        logger.debug(f"RANDOM.ORG bytes error: {e}")
        return None


def _fallback_integers(min_val: int, max_val: int, count: int, unique: bool) -> List[int]:
    """Fallback to Python's secrets module (CSPRNG)."""
    import secrets
    
    if unique:
        if count > (max_val - min_val + 1):
            raise ValueError("Cannot generate unique numbers: count exceeds range")
        
        numbers = []
        seen = set()
        while len(numbers) < count:
            num = secrets.randbelow(max_val - min_val + 1) + min_val
            if num not in seen:
                numbers.append(num)
                seen.add(num)
    else:
        numbers = [secrets.randbelow(max_val - min_val + 1) + min_val for _ in range(count)]
    
    return numbers


def _fallback_bytes(length: int) -> bytes:
    """Fallback to Python's secrets module (CSPRNG)."""
    import secrets
    return secrets.token_bytes(length)
