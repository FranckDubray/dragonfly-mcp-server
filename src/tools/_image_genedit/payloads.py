from typing import Any, Dict, List, Optional, Tuple

DEFAULT_RATIO = "1:1"
DEFAULT_SIZE = 1024
DEFAULT_N = 4
DEFAULT_FORMAT = "png"  # png by default


def parse_ratio(ratio: str) -> Tuple[int, int]:
    try:
        w, h = ratio.split(":", 1)
        return max(1, int(w)), max(1, int(h))
    except Exception:
        return 1, 1


def infer_dimensions(ratio: Optional[str], width: Optional[int], height: Optional[int]) -> Tuple[int, int]:
    # Backend is fixed to square 1024x1024; ignore custom dims/ratio and return defaults
    return DEFAULT_SIZE, DEFAULT_SIZE


def build_messages_for_generate(prompt: str) -> List[Dict[str, Any]]:
    return [
        {
            "role": "user",
            "content": [
                {"type": "text", "text": prompt}
            ]
        }
    ]


def build_messages_for_edit(prompt: str, images_data_urls: List[str]) -> List[Dict[str, Any]]:
    content: List[Dict[str, Any]] = [{"type": "text", "text": prompt}]
    for url in images_data_urls:
        content.append({
            "type": "image_url",
            "image_url": {"url": url}
        })
    return [{"role": "user", "content": content}]


def build_initial_payload(messages: List[Dict[str, Any]], n: int, model: str, width: int, height: int, fmt: str) -> Dict[str, Any]:
    # Minimal schema known to be accepted by backend (aligned with call_llm)
    payload: Dict[str, Any] = {
        "model": model,
        "messages": messages,
        "temperature": 1,
        "stream": True,
        "n": n,
    }
    # NOTE: width/height/format intentionally NOT sent (backend fixed 1024x1024 PNG).
    return payload
