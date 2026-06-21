import logging
from collections.abc import Mapping


SENSITIVE_KEYS = {
    "password",
    "passwd",
    "secret",
    "shared_secret",
    "token",
    "api_key",
    "apikey",
    "authorization",
    "steam_guard_code",
    "encryption_key",
    "coinbase_api_key",
    "coinbase_webhook_secret",
}

REDACTED = "[REDACTED]"


def _is_sensitive_key(key: object) -> bool:
    normalized = str(key).lower().replace("-", "_")
    return any(part in normalized for part in SENSITIVE_KEYS)


def redact_value(value):
    if isinstance(value, Mapping):
        return redact_mapping(value)
    if isinstance(value, list):
        return [redact_value(item) for item in value]
    if isinstance(value, tuple):
        return tuple(redact_value(item) for item in value)
    return value


def redact_mapping(values: Mapping) -> dict:
    redacted = {}
    for key, value in values.items():
        redacted[key] = REDACTED if _is_sensitive_key(key) else redact_value(value)
    return redacted


class RedactingFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        if isinstance(record.args, Mapping):
            record.args = redact_mapping(record.args)
        elif isinstance(record.args, tuple):
            record.args = tuple(redact_value(arg) for arg in record.args)
        return True
