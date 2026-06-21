import time
from collections import defaultdict, deque
from collections.abc import Callable

from app.core.config import get_settings
from fastapi import HTTPException, Request, Response, status
from redis import Redis
from redis.exceptions import RedisError

_buckets: dict[str, deque[float]] = defaultdict(deque)
_redis_client: Redis | None = None


def reset_rate_limits() -> None:
    _buckets.clear()
    global _redis_client
    _redis_client = None


def redis_client() -> Redis:
    global _redis_client
    if _redis_client is None:
        _redis_client = Redis.from_url(get_settings().redis_url, socket_connect_timeout=1, socket_timeout=1, decode_responses=True)
    return _redis_client


def _bucket_identity(request: Request) -> str:
    user = getattr(request.state, "user", None)
    if user and getattr(user, "id", None):
        return f"user:{user.id}"
    return f"ip:{request.client.host if request.client else 'unknown'}"


def _memory_check(key: str, limit: int, seconds: int, now: float) -> tuple[int, int]:
    bucket = _buckets[key]
    while bucket and bucket[0] <= now - seconds:
        bucket.popleft()
    if len(bucket) >= limit:
        return 0, int(max(1, seconds - (now - bucket[0])))
    bucket.append(now)
    return max(0, limit - len(bucket)), 0


def _redis_check(key: str, limit: int, seconds: int) -> tuple[int, int]:
    client = redis_client()
    count = client.incr(key)
    if count == 1:
        client.expire(key, seconds)
    ttl = client.ttl(key)
    remaining = max(0, limit - int(count))
    retry_after = int(ttl if ttl and ttl > 0 else seconds)
    if int(count) > limit:
        return 0, retry_after
    return remaining, 0


def rate_limit(name: str, limit: int, seconds: int) -> Callable:
    async def dependency(request: Request, response: Response) -> None:
        settings = get_settings()
        key = f"rate:{name}:{_bucket_identity(request)}"
        now = time.time()

        if settings.environment == "production":
            try:
                remaining, retry_after = _redis_check(key, limit, seconds)
            except RedisError as exc:
                raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Rate limit store unavailable") from exc
        else:
            remaining, retry_after = _memory_check(key, limit, seconds, now)

        response.headers["X-RateLimit-Limit"] = str(limit)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        if retry_after:
            response.headers["Retry-After"] = str(retry_after)
            raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="Too many requests")

    return dependency
