from __future__ import annotations

import json
import logging
import time
from typing import Any

import requests

from .config import Settings

LOGGER = logging.getLogger("legifrance_ingestion.http_writer")

RETRYABLE_STATUS_CODES = {429, 500, 502, 503, 504}


class DragonflyWriteError(RuntimeError):
    """Raised when a Dragonfly write operation fails permanently."""


class DragonflyRetryExhaustedError(RuntimeError):
    """Raised when all retry attempts have been exhausted."""


class DragonflyWriter:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.session = requests.Session()
        self.session.headers.update(
            {
                "X-API-KEY": settings.dragonfly_api_key,
                "Content-Type": "application/json",
            }
        )

    def _post_s3_object(self, path: str, payload: dict[str, Any]) -> requests.Response:
        url = f"{self.settings.dragonfly_api_base_url}/api/v1/s3/object"
        params = {
            "scope": "datasource",
            "datasource": self.settings.datasource_name,
            "path": path,
        }
        body = {
            "scope": "datasource",
            "path": path,
            "content": json.dumps(payload, ensure_ascii=False, separators=(",", ":")),
            "content_type": "application/json",
            "datasource": self.settings.datasource_name,
        }
        return self.session.post(url, params=params, json=body, timeout=self.settings.http_timeout)

    def write_json(self, path: str, payload: dict[str, Any]) -> dict[str, Any]:
        attempts = 0
        last_error: str | None = None

        while attempts < self.settings.http_max_retries:
            response = self._post_s3_object(path, payload)

            if response.ok:
                try:
                    return response.json()
                except Exception:
                    return {"success": True, "status_code": response.status_code}

            if response.status_code in RETRYABLE_STATUS_CODES:
                attempts += 1
                last_error = response.text
                delay = self.settings.http_retry_backoff ** attempts
                LOGGER.warning(
                    "Retryable Dragonfly error | path=%s status=%s attempt=%s delay=%ss",
                    path,
                    response.status_code,
                    attempts,
                    delay,
                )
                time.sleep(delay)
                continue

            raise DragonflyWriteError(
                f"Dragonfly write failed for path={path} status={response.status_code} body={response.text}"
            )

        raise DragonflyRetryExhaustedError(
            f"Dragonfly write retries exhausted for path={path}. last_error={last_error}"
        )

    def write_jsonl(self, path: str, rows: list[dict[str, Any]]) -> dict[str, Any]:
        payload = {
            "format": "jsonl",
            "rows": rows,
        }
        return self.write_json(path, payload)
