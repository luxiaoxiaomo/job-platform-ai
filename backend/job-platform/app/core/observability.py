"""Structured logging and request correlation utilities."""

from __future__ import annotations

from contextvars import ContextVar
from datetime import datetime, timezone
import json
import logging
from time import perf_counter
from typing import Any
from uuid import uuid4

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request


request_id_context: ContextVar[str] = ContextVar("request_id", default="-")
_SENSITIVE_KEY_PARTS = ("authorization", "cookie", "password", "secret", "token", "api_key", "apikey")


def _is_sensitive_key(key: object) -> bool:
    normalized = str(key).lower().replace("-", "_")
    return any(part in normalized for part in _SENSITIVE_KEY_PARTS)


def sanitize_log_value(value: Any) -> Any:
    """Recursively redact values stored under sensitive keys."""
    if isinstance(value, dict):
        return {
            str(key): "[REDACTED]" if _is_sensitive_key(key) else sanitize_log_value(item)
            for key, item in value.items()
        }
    if isinstance(value, (list, tuple)):
        return [sanitize_log_value(item) for item in value]
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    return str(value)


class JsonFormatter(logging.Formatter):
    """Render one JSON object per log record."""

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "request_id": getattr(record, "request_id", request_id_context.get()),
        }
        context = getattr(record, "context", None)
        if context:
            payload["context"] = sanitize_log_value(context)
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        return json.dumps(payload, ensure_ascii=False, separators=(",", ":"))


def configure_logging(level: str = "INFO", log_format: str = "json") -> None:
    """Configure application logging without exposing sensitive configuration."""
    handler = logging.StreamHandler()
    if log_format.lower() == "json":
        handler.setFormatter(JsonFormatter())
    else:
        handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s %(message)s"))

    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(getattr(logging, level.upper(), logging.INFO))


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Attach a request ID and emit one structured completion log per request."""

    async def dispatch(self, request: Request, call_next):
        incoming = request.headers.get("X-Request-ID", "").strip()
        request_id = incoming[:128] if incoming else str(uuid4())
        token = request_id_context.set(request_id)
        started_at = perf_counter()
        logger = logging.getLogger("app.http")
        try:
            response = await call_next(request)
        except Exception:
            logger.exception(
                "request failed",
                extra={"request_id": request_id, "context": {"method": request.method, "path": request.url.path}},
            )
            raise
        finally:
            request_id_context.reset(token)

        duration_ms = round((perf_counter() - started_at) * 1000, 2)
        response.headers["X-Request-ID"] = request_id
        logger.info(
            "request completed",
            extra={
                "request_id": request_id,
                "context": {
                    "method": request.method,
                    "path": request.url.path,
                    "status_code": response.status_code,
                    "duration_ms": duration_ms,
                },
            },
        )
        return response
