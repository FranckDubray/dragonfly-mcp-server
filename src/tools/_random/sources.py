"""Physical random sources: RANDOM.ORG and Cisco QRNG."""

import os
import logging
from typing import Optional, List
from enum import Enum

logger = logging.getLogger(__name__)


class RandomSource(str, Enum):
    """Random number source types."""
    ATMOSPHERIC = "atmospheric"
    QUANTUM = "quantum"
    FALLBACK = "fallback"


class RandomList(list):
    """List with source tracking."""
    def __init__(self, items, source: RandomSource):
        super().__init__(items)
        self.source = source


class RandomBytes(bytes):
    """Bytes with source tracking."""
    def __new__(cls, data, source: RandomSource):
        instance = super().__new__(cls, data)
        instance.source = source
        return instance


def get_random_integers(
    min_val: int,
    max_val: int,
    count: int,
    unique: bool = False,
    source: str = "auto"
) -> Optional[RandomList]:
    """Get random integers from physical sources.
    
    Args:
        min_val: Minimum value (inclusive)
        max_val: Maximum value (inclusive)
        count: Number of integers
        unique: Ensure uniqueness
        source: Source preference (auto, atmospheric, quantum)
        
    Returns:
        List of random integers with source tracking
    """
    # Try sources in order based on preference
    if source == "quantum":
        result = _try_cisco_qrng_integers(min_val, max_val, count, unique)
        if result:
            return result
    elif source == "atmospheric":
        result = _try_random_org_integers(min_val, max_val, count, unique)
        if result:
            return result
    else:  # auto
        # Try quantum first (faster, more secure)
        result = _try_cisco_qrng_integers(min_val, max_val, count, unique)
        if result:
            return result
        
        # Fallback to atmospheric
        result = _try_random_org_integers(min_val, max_val, count, unique)
        if result:
            return result
    
    # Final fallback: Python's secrets module (CSPRNG, not true random)
    logger.warning("All physical sources failed, using fallback CSPRNG")
    return _fallback_integers(min_val, max_val, count, unique)


def get_random_bytes(
    length: int,
    source: str = "auto"
) -> Optional[RandomBytes]:
    """Get random bytes from physical sources.
    
    Args:
        length: Number of bytes
        source: Source preference (auto, atmospheric, quantum)
        
    Returns:
        Random bytes with source tracking
    """
    # Try sources in order
    if source == "quantum":
        result = _try_cisco_qrng_bytes(length)
        if result:
            return result
    elif source == "atmospheric":
        result = _try_random_org_bytes(length)
        if result:
            return result
    else:  # auto
        result = _try_cisco_qrng_bytes(length)
        if result:
            return result
        
        result = _try_random_org_bytes(length)
        if result:
            return result
    
    # Final fallback
    logger.warning("All physical sources failed, using fallback CSPRNG")
    return _fallback_bytes(length)


def _try_cisco_qrng_integers(min_val: int, max_val: int, count: int, unique: bool) -> Optional[RandomList]:
    """Try to get integers from Cisco QRNG."""
    try:
        import requests
        
        api_key = os.getenv("CISCO_QRNG_API_KEY", "").strip()
        if not api_key:
            logger.debug("CISCO_QRNG_API_KEY not found, skipping quantum source")
            return None
        
        # Cisco QRNG API endpoint (check latest docs)
        url = "https://qrng.cisco.com/api/v1/randint"
        
        headers = {
            "x-api-key": api_key,
            "Content-Type": "application/json"
        }
        
        payload = {
            "min": min_val,
            "max": max_val,
            "count": count
        }
        
        response = requests.post(url, json=payload, headers=headers, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            numbers = data.get("data", [])
            
            if unique and len(set(numbers)) != len(numbers):
                # Retry with more numbers and deduplicate
                payload["count"] = count * 2
                response = requests.post(url, json=payload, headers=headers, timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    numbers = list(dict.fromkeys(data.get("data", [])))[:count]
            
            logger.info(f"Generated {len(numbers)} integers from Cisco QRNG")
            return RandomList(numbers, RandomSource.QUANTUM)
        
        logger.warning(f"Cisco QRNG failed: {response.status_code}")
        return None
        
    except Exception as e:
        logger.debug(f"Cisco QRNG error: {e}")
        return None


def _try_random_org_integers(min_val: int, max_val: int, count: int, unique: bool) -> Optional[RandomList]:
    """Try to get integers from RANDOM.ORG."""
    try:
        import requests
        
        # RANDOM.ORG simple HTTP API (no key required for basic usage)
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
        
        response = requests.get(url, params=params, timeout=10)
        
        if response.status_code == 200:
            numbers = [int(line.strip()) for line in response.text.strip().split('\n') if line.strip()]
            
            if unique and len(set(numbers)) != len(numbers):
                # RANDOM.ORG doesn't guarantee uniqueness without API key
                # Deduplicate and request more if needed
                numbers = list(dict.fromkeys(numbers))
                if len(numbers) < count:
                    logger.warning(f"Could not get {count} unique numbers from RANDOM.ORG")
                    return None
            
            logger.info(f"Generated {len(numbers)} integers from RANDOM.ORG (atmospheric)")
            return RandomList(numbers, RandomSource.ATMOSPHERIC)
        
        logger.warning(f"RANDOM.ORG failed: {response.status_code}")
        return None
        
    except Exception as e:
        logger.debug(f"RANDOM.ORG error: {e}")
        return None


def _try_cisco_qrng_bytes(length: int) -> Optional[RandomBytes]:
    """Try to get bytes from Cisco QRNG."""
    try:
        import requests
        
        api_key = os.getenv("CISCO_QRNG_API_KEY", "").strip()
        if not api_key:
            logger.debug("CISCO_QRNG_API_KEY not found, skipping quantum source")
            return None
        
        url = "https://qrng.cisco.com/api/v1/randbytes"
        
        headers = {
            "x-api-key": api_key,
            "Content-Type": "application/json"
        }
        
        payload = {
            "length": length
        }
        
        response = requests.post(url, json=payload, headers=headers, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            # Assuming API returns base64 or hex
            import base64
            bytes_data = base64.b64decode(data.get("data", ""))
            
            logger.info(f"Generated {len(bytes_data)} bytes from Cisco QRNG")
            return RandomBytes(bytes_data, RandomSource.QUANTUM)
        
        logger.warning(f"Cisco QRNG bytes failed: {response.status_code}")
        return None
        
    except Exception as e:
        logger.debug(f"Cisco QRNG bytes error: {e}")
        return None


def _try_random_org_bytes(length: int) -> Optional[RandomBytes]:
    """Try to get bytes from RANDOM.ORG."""
    try:
        import requests
        
        # Get integers and convert to bytes
        count = length
        url = "https://www.random.org/integers/"
        
        params = {
            "num": count,
            "min": 0,
            "max": 255,
            "col": 1,
            "base": 10,
            "format": "plain",
            "rnd": "new"
        }
        
        response = requests.get(url, params=params, timeout=10)
        
        if response.status_code == 200:
            numbers = [int(line.strip()) for line in response.text.strip().split('\n') if line.strip()]
            bytes_data = bytes(numbers[:length])
            
            logger.info(f"Generated {len(bytes_data)} bytes from RANDOM.ORG (atmospheric)")
            return RandomBytes(bytes_data, RandomSource.ATMOSPHERIC)
        
        logger.warning(f"RANDOM.ORG bytes failed: {response.status_code}")
        return None
        
    except Exception as e:
        logger.debug(f"RANDOM.ORG bytes error: {e}")
        return None


def _fallback_integers(min_val: int, max_val: int, count: int, unique: bool) -> RandomList:
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
    
    return RandomList(numbers, RandomSource.FALLBACK)


def _fallback_bytes(length: int) -> RandomBytes:
    """Fallback to Python's secrets module (CSPRNG)."""
    import secrets
    return RandomBytes(secrets.token_bytes(length), RandomSource.FALLBACK)
