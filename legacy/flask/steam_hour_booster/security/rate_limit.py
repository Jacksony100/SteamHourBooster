import time
from collections import defaultdict, deque
from functools import wraps

from flask import current_app, request

from steam_hour_booster.app import json_error


_BUCKETS: dict[tuple[str, str], deque[float]] = defaultdict(deque)


def rate_limit(name: str, limit: int, seconds: int):
    def decorator(fn):
        @wraps(fn)
        def wrapped(*args, **kwargs):
            if not current_app.config.get("RATE_LIMIT_ENABLED", True):
                return fn(*args, **kwargs)
            if request.method in {"GET", "HEAD", "OPTIONS"}:
                return fn(*args, **kwargs)

            identifier = request.remote_addr or "unknown"
            key = (name, identifier)
            now = time.time()
            bucket = _BUCKETS[key]
            while bucket and bucket[0] <= now - seconds:
                bucket.popleft()
            if len(bucket) >= limit:
                return json_error("Too many requests", 429, "rate_limited")
            bucket.append(now)
            return fn(*args, **kwargs)

        return wrapped

    return decorator
