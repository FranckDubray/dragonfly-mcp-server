from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Dict, Optional, List, Tuple
import httpx
import time
import json

@dataclass
class HttpResult:
    status_code: int
    json: Optional[Dict[str, Any]]
    headers: Dict[str, str]


def http_request(method: str, url: str, json_body: Optional[Dict[str, Any]] = None, allow_429_retry: bool = True, max_retries: int = 3, timeout: float = 30.0) -> HttpResult:
    backoffs = [0.25, 0.5, 1.0]
    attempt = 0
    while True:
        try:
            with httpx.Client() as client:
                resp = client.request(method, url, json=json_body, timeout=timeout)
        except httpx.RequestError as e:
            if attempt >= max_retries - 1:
                raise RuntimeError(f"Discord network error: {e}")
            time.sleep(backoffs[min(attempt, len(backoffs) - 1)])
            attempt += 1
            continue

        if resp.status_code == 429 and allow_429_retry and attempt < max_retries:
            retry_after = 0.5
            try:
                data = resp.json()
                retry_after = float(data.get("retry_after") or data.get("Retry-After") or retry_after)
            except Exception:
                ra_hdr = resp.headers.get("Retry-After")
                if ra_hdr:
                    try:
                        retry_after = float(ra_hdr)
                    except Exception:
                        pass
            time.sleep(retry_after)
            attempt += 1
            continue

        if 500 <= resp.status_code < 600 and attempt < max_retries:
            time.sleep(backoffs[min(attempt, len(backoffs) - 1)])
            attempt += 1
            continue

        try:
            js = resp.json() if resp.headers.get("content-type", "").startswith("application/json") else None
        except Exception:
            js = None
        return HttpResult(status_code=resp.status_code, json=js, headers=dict(resp.headers))


def http_request_multipart(method: str, url: str, payload_json: Dict[str, Any], files_data: List[Tuple[str, str, bytes, str]] , allow_429_retry: bool = True, max_retries: int = 3, timeout: float = 30.0) -> HttpResult:
    """
    Send multipart/form-data to Discord webhook endpoints with attachments.
    files_data: list of tuples (field_name, filename, content_bytes, content_type)
      - Discord expects fields named like: files[0], files[1], ...
    payload_json: the JSON message payload (will be sent as 'payload_json')
    """
    backoffs = [0.25, 0.5, 1.0]
    attempt = 0
    while True:
        try:
            multipart_files = []
            # Add payload_json part
            multipart_files.append(("payload_json", (None, json.dumps(payload_json), "application/json")))
            # Add file parts
            for (field_name, filename, content, content_type) in files_data:
                multipart_files.append((field_name, (filename, content, content_type or "application/octet-stream")))
            with httpx.Client() as client:
                resp = client.request(method, url, files=multipart_files, timeout=timeout)
        except httpx.RequestError as e:
            if attempt >= max_retries - 1:
                raise RuntimeError(f"Discord network error (multipart): {e}")
            time.sleep(backoffs[min(attempt, len(backoffs) - 1)])
            attempt += 1
            continue

        if resp.status_code == 429 and allow_429_retry and attempt < max_retries:
            retry_after = 0.5
            try:
                data = resp.json()
                retry_after = float(data.get("retry_after") or data.get("Retry-After") or retry_after)
            except Exception:
                ra_hdr = resp.headers.get("Retry-After")
                if ra_hdr:
                    try:
                        retry_after = float(ra_hdr)
                    except Exception:
                        pass
            time.sleep(retry_after)
            attempt += 1
            continue

        if 500 <= resp.status_code < 600 and attempt < max_retries:
            time.sleep(backoffs[min(attempt, len(backoffs) - 1)])
            attempt += 1
            continue

        try:
            js = resp.json() if resp.headers.get("content-type", "").startswith("application/json") else None
        except Exception:
            js = None
        return HttpResult(status_code=resp.status_code, json=js, headers=dict(resp.headers))
