from typing import Any, Dict
import requests


def build_headers(token: str) -> Dict[str, str]:
    return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}


def post_stream(endpoint: str, headers: Dict[str, str], json_payload: Dict[str, Any], timeout_sec: int):
    return requests.post(endpoint, headers=headers, json=json_payload, stream=True, timeout=timeout_sec, verify=False)
