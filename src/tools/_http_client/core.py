"""Core business logic for HTTP Client."""
from __future__ import annotations
from typing import Dict, Any
import logging
import requests

from .validators import (
    validate_url,
    validate_timeout,
    validate_proxy,
    validate_max_retries,
    validate_retry_delay
)
from .auth import build_auth_headers, validate_auth_params
from .utils import parse_response, save_response_to_file, build_request_summary
from .retry import retry_with_backoff

LOG = logging.getLogger(__name__)


def execute_request(method: str, url: str, **params) -> Dict[str, Any]:
    """Execute HTTP request with all options.
    
    Args:
        method: HTTP method
        url: Target URL
        **params: Request parameters
        
    Returns:
        Response data or error
    """
    # Validate URL
    url_validation = validate_url(url)
    if not url_validation["valid"]:
        LOG.warning(f"❌ Invalid URL: {url_validation['error']}")
        return {"error": url_validation["error"]}
    
    url = url_validation["url"]
    
    # Validate timeout
    timeout_validation = validate_timeout(params.get("timeout"))
    if not timeout_validation["valid"]:
        LOG.warning(f"❌ Invalid timeout: {timeout_validation['error']}")
        return {"error": timeout_validation["error"]}
    
    timeout = timeout_validation["timeout"]
    
    # Validate proxy
    proxy_validation = validate_proxy(params.get("proxy"))
    if not proxy_validation["valid"]:
        LOG.warning(f"❌ Invalid proxy: {proxy_validation['error']}")
        return {"error": proxy_validation["error"]}
    
    proxy = proxy_validation["proxy"]
    
    # Validate retries
    retries_validation = validate_max_retries(params.get("max_retries"))
    if not retries_validation["valid"]:
        LOG.warning(f"❌ Invalid max_retries: {retries_validation['error']}")
        return {"error": retries_validation["error"]}
    
    max_retries = retries_validation["max_retries"]
    
    # Validate retry delay
    delay_validation = validate_retry_delay(params.get("retry_delay"))
    if not delay_validation["valid"]:
        LOG.warning(f"❌ Invalid retry_delay: {delay_validation['error']}")
        return {"error": delay_validation["error"]}
    
    retry_delay = delay_validation["retry_delay"]
    
    # Validate auth
    auth_valid, auth_error = validate_auth_params(
        auth_type=params.get("auth_type"),
        auth_user=params.get("auth_user"),
        auth_password=params.get("auth_password"),
        auth_token=params.get("auth_token"),
        auth_api_key_name=params.get("auth_api_key_name"),
        auth_api_key_value=params.get("auth_api_key_value")
    )
    
    if not auth_valid:
        LOG.warning(f"❌ Invalid auth: {auth_error}")
        return {"error": auth_error}
    
    # Build headers
    headers = params.get("headers", {}).copy()
    
    # Add auth headers
    auth_headers = build_auth_headers(
        auth_type=params.get("auth_type"),
        auth_user=params.get("auth_user"),
        auth_password=params.get("auth_password"),
        auth_token=params.get("auth_token"),
        auth_api_key_name=params.get("auth_api_key_name"),
        auth_api_key_value=params.get("auth_api_key_value")
    )
    headers.update(auth_headers)
    
    # Build request kwargs
    request_kwargs = {
        "method": method,
        "url": url,
        "headers": headers,
        "timeout": timeout,
        "allow_redirects": params.get("follow_redirects", True),
        "verify": params.get("verify_ssl", True)
    }
    
    # Add query params
    if params.get("params"):
        request_kwargs["params"] = params["params"]
    
    # Add body
    if params.get("json"):
        request_kwargs["json"] = params["json"]
    elif params.get("form_data"):
        request_kwargs["data"] = params["form_data"]
    elif params.get("body"):
        request_kwargs["data"] = params["body"]
    
    # Add proxy
    if proxy:
        request_kwargs["proxies"] = {"http": proxy, "https": proxy}
    
    # Log request start
    LOG.info(f"🌐 {method} {url} (timeout: {timeout}s, retries: {max_retries})")
    
    # Execute with retry
    def make_request():
        return requests.request(**request_kwargs)
    
    try:
        if max_retries > 0:
            response = retry_with_backoff(
                make_request,
                max_retries=max_retries,
                retry_delay=retry_delay
            )
        else:
            response = make_request()
        
        # Parse response
        response_format = params.get("response_format", "auto")
        response_data = parse_response(response, response_format)
        
        # Add request summary
        response_data["request"] = build_request_summary(method, url, **params)
        
        # Save if requested
        if params.get("save_response"):
            save_result = save_response_to_file(response_data)
            response_data["saved"] = save_result
        
        # Log success
        status = response_data.get("status_code")
        body_len = response_data.get("body_length", 0)
        if response_data.get("ok"):
            LOG.info(f"✅ {method} {url} → {status} ({body_len} bytes)")
        else:
            LOG.warning(f"⚠️ {method} {url} → {status} (HTTP error)")
        
        # Check for truncation warning (body > 100 KB)
        if body_len > 100_000:
            LOG.warning(f"⚠️ Large response body: {body_len} bytes ({body_len / 1024:.1f} KB)")
            response_data["truncation_warning"] = f"Response body is large: {body_len / 1024:.1f} KB"
        
        return response_data
        
    except requests.exceptions.Timeout:
        LOG.warning(f"⏱️ Timeout: {method} {url} after {timeout}s")
        return {
            "error": f"Request timed out after {timeout} seconds",
            "error_type": "timeout"
        }
    
    except requests.exceptions.ConnectionError as e:
        LOG.warning(f"❌ Connection error: {method} {url}")
        return {
            "error": f"Connection error: {str(e)}",
            "error_type": "connection"
        }
    
    except requests.exceptions.SSLError as e:
        LOG.warning(f"🔒 SSL error: {method} {url}")
        return {
            "error": f"SSL error: {str(e)}",
            "error_type": "ssl",
            "hint": "Try setting verify_ssl=false if you trust this endpoint"
        }
    
    except requests.exceptions.RequestException as e:
        LOG.warning(f"❌ Request failed: {method} {url} - {e}")
        return {
            "error": f"Request failed: {str(e)}",
            "error_type": "request"
        }
    
    except Exception as e:
        LOG.error(f"💥 Unexpected error: {method} {url} - {e}")
        return {
            "error": f"Unexpected error: {str(e)}",
            "error_type": "unknown"
        }
