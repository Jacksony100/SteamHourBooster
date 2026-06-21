"""HTTP middleware: security headers and request-context/access logging."""

from __future__ import annotations

import time
from secrets import token_hex

from app.core.config import Settings
from app.core.metrics import record_request
from app.core.observability import get_logger, request_id_ctx
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from starlette.types import ASGIApp

logger = get_logger("app.access")

# Paths where a strict CSP would break the interactive Swagger/ReDoc UI.
_DOCS_PREFIXES = ("/docs", "/redoc", "/openapi.json")


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Attach defence-in-depth headers to every response.

    These complement (do not replace) edge/reverse-proxy headers. The API serves
    JSON, so a strict CSP is safe; docs paths get a relaxed CSP so Swagger renders.
    """

    def __init__(self, app: ASGIApp, settings: Settings) -> None:
        super().__init__(app)
        self.settings = settings

    async def dispatch(self, request: Request, call_next):
        response: Response = await call_next(request)
        headers = response.headers
        headers.setdefault("X-Content-Type-Options", "nosniff")
        headers.setdefault("X-Frame-Options", "DENY")
        headers.setdefault("Referrer-Policy", "no-referrer")
        headers.setdefault("Permissions-Policy", "geolocation=(), microphone=(), camera=(), payment=()")
        headers.setdefault("Cross-Origin-Opener-Policy", "same-origin")

        if request.url.path.startswith(_DOCS_PREFIXES):
            headers.setdefault(
                "Content-Security-Policy",
                "default-src 'self'; img-src 'self' data: https:; "
                "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
                "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
                "frame-ancestors 'none'",
            )
        else:
            headers.setdefault(
                "Content-Security-Policy",
                "default-src 'none'; frame-ancestors 'none'; base-uri 'none'; form-action 'none'",
            )

        if self.settings.environment == "production":
            headers.setdefault("Strict-Transport-Security", "max-age=63072000; includeSubDomains; preload")
        return response


class RequestContextMiddleware(BaseHTTPMiddleware):
    """Assign a request id, expose it as X-Request-ID, and emit one access log line."""

    async def dispatch(self, request: Request, call_next):
        incoming = request.headers.get("X-Request-ID")
        request_id = incoming if incoming and len(incoming) <= 64 else token_hex(8)
        token = request_id_ctx.set(request_id)
        started = time.perf_counter()
        status_code = 500
        try:
            response: Response = await call_next(request)
            status_code = response.status_code
            response.headers["X-Request-ID"] = request_id
            return response
        finally:
            duration_ms = round((time.perf_counter() - started) * 1000, 2)
            record_request(request.method, status_code, duration_ms)
            logger.info(
                "%s %s -> %s (%sms)",
                request.method,
                request.url.path,
                status_code,
                duration_ms,
                extra={
                    "extra_fields": {
                        "method": request.method,
                        "path": request.url.path,
                        "status": status_code,
                        "duration_ms": duration_ms,
                        "client": request.client.host if request.client else None,
                    }
                },
            )
            request_id_ctx.reset(token)
