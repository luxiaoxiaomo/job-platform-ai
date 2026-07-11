"""Structured logging and request-correlation tests."""

import json
import logging

from app.core.observability import JsonFormatter, sanitize_log_value


def test_sanitize_log_value_redacts_nested_secrets():
    value = {
        "authorization": "Bearer top-secret",
        "nested": {"password": "secret", "safe": "visible"},
        "access_token": "token-value",
    }

    assert sanitize_log_value(value) == {
        "authorization": "[REDACTED]",
        "nested": {"password": "[REDACTED]", "safe": "visible"},
        "access_token": "[REDACTED]",
    }


def test_json_formatter_emits_request_context_without_secrets():
    formatter = JsonFormatter()
    record = logging.LogRecord("app.http", logging.INFO, __file__, 10, "request completed", (), None)
    record.request_id = "req-123"
    record.context = {"method": "GET", "path": "/health", "authorization": "Bearer secret"}

    payload = json.loads(formatter.format(record))

    assert payload["level"] == "INFO"
    assert payload["logger"] == "app.http"
    assert payload["message"] == "request completed"
    assert payload["request_id"] == "req-123"
    assert payload["context"] == {
        "method": "GET",
        "path": "/health",
        "authorization": "[REDACTED]",
    }
