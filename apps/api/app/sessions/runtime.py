"""Session runtime-state store.

Tracks which accounts currently have an active transparent session at runtime.
Previously this lived in a per-process in-memory set on the adapter, which broke
heartbeat/stop semantics across multiple API workers or a separate worker process.
This store centralizes it: Redis-backed in production (shared across processes),
in-memory in dev/test. The DB remains the source of truth for session records;
this only tracks live "is the runtime engaged" membership.
"""

from __future__ import annotations

from typing import Protocol

from app.core.config import get_settings
from app.core.observability import get_logger

logger = get_logger("app.sessions.runtime")

_RUNTIME_KEY = "deckpilot:sessions:started"
_STOP_KEY = "deckpilot:sessions:stop"


class RuntimeStore(Protocol):
    def mark_started(self, account_id: int) -> None: ...
    def mark_stopped(self, account_id: int) -> None: ...
    def is_started(self, account_id: int) -> bool: ...
    def clear(self) -> None: ...
    # Cooperative stop signalling for worker-driven real sessions.
    def request_stop(self, session_id: int) -> None: ...
    def is_stop_requested(self, session_id: int) -> bool: ...
    def clear_stop(self, session_id: int) -> None: ...


class MemoryRuntimeStore:
    def __init__(self) -> None:
        self._started: set[int] = set()
        self._stop: set[int] = set()

    def mark_started(self, account_id: int) -> None:
        self._started.add(account_id)

    def mark_stopped(self, account_id: int) -> None:
        self._started.discard(account_id)

    def is_started(self, account_id: int) -> bool:
        return account_id in self._started

    def clear(self) -> None:
        self._started.clear()
        self._stop.clear()

    def request_stop(self, session_id: int) -> None:
        self._stop.add(session_id)

    def is_stop_requested(self, session_id: int) -> bool:
        return session_id in self._stop

    def clear_stop(self, session_id: int) -> None:
        self._stop.discard(session_id)


class RedisRuntimeStore:
    def __init__(self) -> None:
        from redis import Redis

        self._redis = Redis.from_url(get_settings().redis_url, socket_connect_timeout=2, socket_timeout=2, decode_responses=True)

    def mark_started(self, account_id: int) -> None:
        self._redis.sadd(_RUNTIME_KEY, account_id)

    def mark_stopped(self, account_id: int) -> None:
        self._redis.srem(_RUNTIME_KEY, account_id)

    def is_started(self, account_id: int) -> bool:
        return bool(self._redis.sismember(_RUNTIME_KEY, account_id))

    def clear(self) -> None:
        self._redis.delete(_RUNTIME_KEY)

    def request_stop(self, session_id: int) -> None:
        self._redis.sadd(_STOP_KEY, session_id)

    def is_stop_requested(self, session_id: int) -> bool:
        return bool(self._redis.sismember(_STOP_KEY, session_id))

    def clear_stop(self, session_id: int) -> None:
        self._redis.srem(_STOP_KEY, session_id)


_store: RuntimeStore | None = None


def set_runtime_store(store: RuntimeStore | None) -> None:
    global _store
    _store = store


def get_runtime_store() -> RuntimeStore:
    global _store
    if _store is None:
        # Shared store in production so multiple workers agree on session liveness.
        if get_settings().environment == "production":
            _store = RedisRuntimeStore()
        else:
            _store = MemoryRuntimeStore()
    return _store
