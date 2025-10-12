

from __future__ import annotations
from typing import Any, Dict, List, Tuple, Callable, Optional
from .util import API_BASE
from .http_client import http_request, http_request_multipart

# files_data: list of tuples (field_name, filename, content_bytes, content_type)
MultipartFile = Tuple[str, str, bytes, str]


def send_create_batches(
    url: str,
    batches: List[List[Dict[str, Any]]],
    wait: bool,
    build_payload_for_batch: Callable[[int], Dict[str, Any]],
    files_data: Optional[List[MultipartFile]] = None,
) -> Tuple[int, List[str]]:
    posted = 0
    new_message_ids: List[str] = []
    for i in range(len(batches)):
        payload = build_payload_for_batch(i)
        if i == 0 and files_data:
            payload["attachments"] = [{"id": idx, "filename": fd[1]} for idx, fd in enumerate(files_data)]
            res = http_request_multipart("POST", f"{url}?wait={'true' if wait else 'false'}", payload_json=payload, files_data=files_data)
        else:
            res = http_request("POST", f"{url}?wait={'true' if wait else 'false'}", json_body=payload)
        posted += 1
        if wait:
            if res.status_code >= 300 or not res.json:
                raise RuntimeError(f"Discord POST failed (status {res.status_code})")
            msg_id = str(res.json.get("id")) if res.json else None
            if not msg_id:
                raise RuntimeError("Discord did not return a message id")
            new_message_ids.append(msg_id)
    return posted, new_message_ids


def send_update_batches(
    wh_id: str,
    token: str,
    url: str,
    messages_ids_existing: List[str],
    batches: List[List[Dict[str, Any]]],
    wait: bool,
    build_payload_for_batch: Callable[[int], Dict[str, Any]],
    files_data: Optional[List[MultipartFile]] = None,
) -> Tuple[int, List[str]]:
    posted = 0
    new_message_ids: List[str] = []

    min_len = min(len(messages_ids_existing), len(batches))
    for i in range(min_len):
        msg_id = messages_ids_existing[i]
        payload = build_payload_for_batch(i)
        if i == 0 and files_data:
            payload["attachments"] = [{"id": idx, "filename": fd[1]} for idx, fd in enumerate(files_data)]
            res = http_request_multipart("PATCH", f"{API_BASE}/webhooks/{wh_id}/{token}/messages/{msg_id}", payload_json=payload, files_data=files_data)
        else:
            res = http_request("PATCH", f"{API_BASE}/webhooks/{wh_id}/{token}/messages/{msg_id}", json_body=payload)
        posted += 1
        if res.status_code >= 300:
            raise RuntimeError(f"Discord PATCH failed (status {res.status_code})")
        new_message_ids.append(msg_id)

    if len(batches) > len(messages_ids_existing):
        for i in range(len(messages_ids_existing), len(batches)):
            payload = build_payload_for_batch(i)
            res = http_request("POST", f"{url}?wait={'true' if wait else 'false'}", json_body=payload)
            posted += 1
            if wait:
                if res.status_code >= 300 or not res.json:
                    raise RuntimeError(f"Discord POST failed (status {res.status_code})")
                msg_id = str(res.json.get("id")) if res.json else None
                if not msg_id:
                    raise RuntimeError("Discord did not return a message id")
                new_message_ids.append(msg_id)

    elif len(batches) < len(messages_ids_existing):
        # Delete extra messages
        for i in range(len(messages_ids_existing) - 1, len(batches) - 1, -1):
            msg_id = messages_ids_existing[i]
            res = http_request("DELETE", f"{API_BASE}/webhooks/{wh_id}/{token}/messages/{msg_id}")
            posted += 1
            if not (200 <= res.status_code < 300 or res.status_code == 404):
                raise RuntimeError(f"Discord DELETE failed (status {res.status_code})")

    return posted, new_message_ids

 
 
 
