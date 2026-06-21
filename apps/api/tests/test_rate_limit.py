import asyncio
from types import SimpleNamespace

import app.core.rate_limit as rate_limit_module
import pytest
from fastapi import HTTPException, Response
from redis.exceptions import RedisError


class FailingRedis:
    def incr(self, key: str):
        raise RedisError("redis down")


def request_for(ip: str = "203.0.113.10"):
    return SimpleNamespace(client=SimpleNamespace(host=ip), state=SimpleNamespace())


def test_memory_rate_limit_blocks_after_limit():
    dependency = rate_limit_module.rate_limit("unit", 2, 60)
    request = request_for()

    asyncio.run(dependency(request, Response()))
    asyncio.run(dependency(request, Response()))

    with pytest.raises(HTTPException) as exc:
        asyncio.run(dependency(request, Response()))

    assert exc.value.status_code == 429


def test_production_rate_limit_fails_closed_when_redis_unavailable(monkeypatch):
    monkeypatch.setattr(rate_limit_module, "get_settings", lambda: SimpleNamespace(environment="production", redis_url="redis://unavailable:6379/0"))
    monkeypatch.setattr(rate_limit_module, "redis_client", lambda: FailingRedis())
    dependency = rate_limit_module.rate_limit("prod", 2, 60)

    with pytest.raises(HTTPException) as exc:
        asyncio.run(dependency(request_for(), Response()))

    assert exc.value.status_code == 503
    assert exc.value.detail == "Rate limit store unavailable"
