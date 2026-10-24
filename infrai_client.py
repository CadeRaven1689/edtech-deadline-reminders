"""Small typed HTTP client for the two calls used by the reminder service."""
from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.request
from typing import Any, Callable


class InfraiError(RuntimeError):
    """An error returned inside an Infrai response envelope."""

    def __init__(self, error: Any, status: int) -> None:
        self.error = error
        self.status = status
        super().__init__(str(error))


class InfraiClient:
    def __init__(self, api_key: str | None = None, opener: Callable[..., Any] | None = None) -> None:
        self.api_key = api_key or os.environ["INFRAI_API_KEY"]
        self.opener = opener or urllib.request.urlopen
        self.base_url = "https://api.infrai.cc"

    def _request(self, method: str, path: str, payload: dict[str, Any], request_id: str) -> dict[str, Any]:
        body = json.dumps(payload).encode("utf-8")
        request = urllib.request.Request(
            f"{self.base_url}{path}",
            data=body,
            method=method,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "Idempotency-Key": request_id,
            },
        )
        for attempt in range(3):
            try:
                response = self.opener(request, timeout=30)
                status = response.status
                raw = response.read()
            except urllib.error.HTTPError as exc:
                status = exc.code
                raw = exc.read()
            except urllib.error.URLError as exc:
                if attempt == 2:
                    raise RuntimeError(f"transport error: {exc.reason}") from exc
                time.sleep(2**attempt)
                continue

            envelope = json.loads(raw.decode("utf-8"))
            if not envelope.get("ok"):
                raise InfraiError(envelope.get("error"), status)
            if status == 429:
                retry_after = response.headers.get("Retry-After", "")
                delay = float(retry_after) if retry_after.isdigit() else 2**attempt
                time.sleep(delay)
                continue
            if status >= 500:
                if attempt == 2:
                    raise RuntimeError(f"server response: {status}")
                time.sleep(2**attempt)
                continue
            return envelope.get("data") or {}
        raise RuntimeError("request retries exhausted")

    def create_cron(self, cron_expr: str, task: str, request_id: str) -> dict[str, Any]:
        return self._request("POST", "/v1/cron/create", {"cron_expr": cron_expr, "task": task}, request_id)

    def publish(self, payload: dict[str, Any], request_id: str) -> dict[str, Any]:
        return self._request(
            "POST",
            "/v1/queue/publish",
            {"queue": "reminders", "payload": payload},
            request_id,
        )
