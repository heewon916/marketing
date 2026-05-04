from __future__ import annotations

from collections.abc import Mapping
import contextvars
import json
import logging
import uuid
from typing import Any

REQUEST_ID_CONTEXT: contextvars.ContextVar[str] = contextvars.ContextVar(
    "request_id",
    default="-",
)

_RESERVED_LOG_RECORD_FIELDS = set(logging.makeLogRecord({}).__dict__.keys()) | {
    "message",
    "asctime",
}
_CORE_CONTEXT_FIELDS = (
    "event",
    "request_id",
    "session_id",
    "route",
    "method",
    "status_code",
    "elapsed_ms",
    "stage",
    "component",
    "outcome",
    "error_type",
)
_REDACTED_KEYS = {
    "authorization",
    "cookie",
    "openai_api_key",
    "password",
    "redis_password",
    "s3_access_key",
    "s3_secret_key",
    "secret",
    "set-cookie",
    "x-api-key",
}


def new_request_id() -> str:
    return uuid.uuid4().hex


def set_request_id(request_id: str) -> contextvars.Token[str]:
    return REQUEST_ID_CONTEXT.set(request_id)


def reset_request_id(token: contextvars.Token[str]) -> None:
    REQUEST_ID_CONTEXT.reset(token)


def get_request_id() -> str:
    return REQUEST_ID_CONTEXT.get()


def preview_text(value: str, max_length: int) -> str:
    if len(value) <= max_length:
        return value
    return f"{value[:max_length]}..."


def build_log_extra(event: str, **fields: Any) -> dict[str, Any]:
    extra: dict[str, Any] = {"event": event}
    for key, value in fields.items():
        if value is None:
            continue
        extra[key] = value
    return extra


def _is_sensitive_key(key: str) -> bool:
    normalized = key.lower()
    if normalized in _REDACTED_KEYS:
        return True
    return normalized.endswith("_password") or normalized.endswith("_secret")


def _format_value(value: Any) -> str:
    if isinstance(value, str):
        return json.dumps(value, ensure_ascii=False)
    if isinstance(value, bool):
        return "true" if value else "false"
    if value is None:
        return "null"
    if isinstance(value, (int, float)):
        return str(value)
    if isinstance(value, Mapping):
        return json.dumps(dict(value), ensure_ascii=False, sort_keys=True)
    if isinstance(value, (list, tuple, set)):
        return json.dumps(list(value), ensure_ascii=False)
    return json.dumps(str(value), ensure_ascii=False)


class AppContextFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        if not getattr(record, "request_id", None):
            record.request_id = get_request_id()
        for field in _CORE_CONTEXT_FIELDS:
            if not hasattr(record, field):
                setattr(record, field, "-")
        return True


class KeyValueFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        record.message = record.getMessage()
        if self.usesTime():
            record.asctime = self.formatTime(record, self.datefmt)

        base_message = f"{record.levelname}:{record.name}:{record.message}"
        extras: list[str] = []
        for key in sorted(record.__dict__):
            if key.startswith("_") or key in _RESERVED_LOG_RECORD_FIELDS:
                continue

            value = record.__dict__[key]
            if value in ("-", None):
                continue
            if _is_sensitive_key(key):
                value = "<redacted>"
            extras.append(f"{key}={_format_value(value)}")

        if extras:
            base_message = f"{base_message} | {' '.join(extras)}"

        if record.exc_info:
            if not record.exc_text:
                record.exc_text = self.formatException(record.exc_info)
            base_message = f"{base_message}\n{record.exc_text}"
        if record.stack_info:
            base_message = f"{base_message}\n{self.formatStack(record.stack_info)}"
        return base_message


def configure_app_logging(level_name: str) -> None:
    app_logger = logging.getLogger("app")
    level = getattr(logging, level_name.upper(), logging.INFO)
    app_logger.setLevel(level)

    handler = app_logger.handlers[0] if app_logger.handlers else logging.StreamHandler()
    handler.setLevel(level)
    handler.setFormatter(KeyValueFormatter())

    has_filter = any(isinstance(existing, AppContextFilter) for existing in handler.filters)
    if not has_filter:
        handler.addFilter(AppContextFilter())

    if not app_logger.handlers:
        app_logger.addHandler(handler)

    app_logger.propagate = False
