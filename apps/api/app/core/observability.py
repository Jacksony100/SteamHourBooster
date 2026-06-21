"""Production observability: structured logging, request-id context, optional Sentry.

This module deliberately never logs secrets, passwords, tokens, Steam Guard codes,
or raw credentials. Log call sites pass only non-sensitive identifiers.
"""

from __future__ import annotations

import json
import logging
import sys
from contextvars import ContextVar

from app.core.config import Settings

# Correlation id for the in-flight request; set by RequestContextMiddleware.
request_id_ctx: ContextVar[str | None] = ContextVar("request_id", default=None)

_SENSITIVE_KEYS = {
    "password",
    "secret",
    "token",
    "api_key",
    "apikey",
    "authorization",
    "encryption_key",
    "steam_guard_code",
    "auth_code",
    "shared_secret",
}

_configured = False


class JsonLogFormatter(logging.Formatter):
    """Render log records as single-line JSON with the current request id."""

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, object] = {
            "ts": self.formatTime(record, "%Y-%m-%dT%H:%M:%S%z"),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        rid = request_id_ctx.get()
        if rid:
            payload["request_id"] = rid
        # Allow structured extras via logger.info(..., extra={"extra_fields": {...}})
        extra = getattr(record, "extra_fields", None)
        if isinstance(extra, dict):
            for key, value in extra.items():
                if key.lower() in _SENSITIVE_KEYS:
                    continue
                payload[key] = value
        if record.exc_info:
            payload["exc_info"] = self.formatException(record.exc_info)
        return json.dumps(payload, ensure_ascii=False, default=str)


def configure_logging(settings: Settings) -> None:
    """Install a stdout handler. JSON in production, plain text in dev/test."""

    global _configured
    if _configured:
        return

    root = logging.getLogger()
    root.setLevel(settings.log_level.upper())
    # Drop any pre-existing handlers so we don't double-log under uvicorn reload.
    for handler in list(root.handlers):
        root.removeHandler(handler)

    handler = logging.StreamHandler(sys.stdout)
    if settings.log_json or settings.environment == "production":
        handler.setFormatter(JsonLogFormatter())
    else:
        handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s %(message)s"))
    root.addHandler(handler)

    # Quiet noisy access logs from uvicorn; we emit our own access line.
    logging.getLogger("uvicorn.access").handlers = []
    _configured = True


def init_sentry(settings: Settings) -> bool:
    """Initialise Sentry if a DSN is configured and the SDK is installed.

    Returns True when active. Never fails hard: missing SDK / DSN is a no-op so
    the service runs identically without error reporting wired up.
    """

    if not settings.sentry_dsn:
        return False
    try:
        import sentry_sdk
    except ImportError:
        logging.getLogger(__name__).warning("SENTRY_DSN set but sentry-sdk is not installed; skipping")
        return False
    sentry_sdk.init(
        dsn=settings.sentry_dsn,
        environment=settings.environment,
        traces_sample_rate=settings.sentry_traces_sample_rate,
        send_default_pii=False,
    )
    return True


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)
