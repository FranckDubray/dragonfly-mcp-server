"""Utility functions for Ollama operations."""
import os


# Constants
OLLAMA_LOCAL_URL = "http://localhost:11434"
OLLAMA_WEB_SEARCH_URL = "https://ollama.com/api/web_search"

# Default timeouts (in seconds)
DEFAULT_LOCAL_TIMEOUT = 120  # 2 minutes for local operations
DEFAULT_WEB_SEARCH_TIMEOUT = 60  # 1 minute for web search


def get_web_search_token() -> str:
    """Get web search token from environment."""
    return os.getenv("OLLAMA_WEB_SEARCH_TOKEN")


def is_web_search_available() -> bool:
    """Check if web search is available (token present)."""
    token = get_web_search_token()
    return token is not None and token.strip() != ""


def format_model_size(size_bytes: int) -> str:
    """Format model size in human-readable format."""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 ** 2:
        return f"{size_bytes / 1024:.1f} KB"
    elif size_bytes < 1024 ** 3:
        return f"{size_bytes / (1024 ** 2):.1f} MB"
    else:
        return f"{size_bytes / (1024 ** 3):.1f} GB"


def format_duration(duration_ns: int) -> str:
    """Format duration from nanoseconds to human-readable format."""
    if duration_ns < 1_000_000:  # Less than 1ms
        return f"{duration_ns / 1_000:.1f} μs"
    elif duration_ns < 1_000_000_000:  # Less than 1s
        return f"{duration_ns / 1_000_000:.1f} ms"
    else:
        return f"{duration_ns / 1_000_000_000:.1f} s"


def truncate_text(text: str, max_length: int = 100) -> str:
    """Truncate text to max_length with ellipsis."""
    if len(text) <= max_length:
        return text
    return text[:max_length - 3] + "..."