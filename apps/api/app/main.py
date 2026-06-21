from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, PlainTextResponse
from redis import Redis
from sqlalchemy import text

from app.admin.routes import router as admin_router
from app.auth.routes import router as auth_router
from app.billing.routes import router as billing_router
from app.core.config import get_settings
from app.core.database import SessionLocal
from app.core.middleware import RequestContextMiddleware, SecurityHeadersMiddleware
from app.core.observability import configure_logging, get_logger, init_sentry
from app.dashboard.routes import router as dashboard_router
from app.faceit.routes import router as faceit_router
from app.games.routes import router as games_router
from app.sessions.manager import get_session_manager
from app.sessions.routes import router as sessions_router
from app.steam_accounts.routes import router as steam_accounts_router
from app.steam_data.routes import router as steam_data_router
from app.system.routes import router as system_router

settings = get_settings()
configure_logging(settings)
init_sentry(settings)
logger = get_logger("app.main")


@asynccontextmanager
async def lifespan(_app: FastAPI):
    logger.info("API starting (env=%s, steam_mode=%s)", settings.environment, settings.steam_integration_mode)
    yield
    db = SessionLocal()
    try:
        get_session_manager().shutdown_active_sessions(db)
    finally:
        db.close()
    logger.info("API shutdown complete")


_is_prod = settings.environment == "production"
app = FastAPI(
    title="DeckPilot API",
    version="2.0.0",
    description="Transparent account/session manager for user-owned Steam accounts. No stealth or evasion behavior.",
    lifespan=lifespan,
    docs_url=None if _is_prod else "/docs",
    redoc_url=None if _is_prod else "/redoc",
    openapi_url=None if _is_prod else "/openapi.json",
)

# Middleware order (outermost first): request-context -> security-headers -> CORS -> app.
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(SecurityHeadersMiddleware, settings=settings)
app.add_middleware(RequestContextMiddleware)


@app.exception_handler(ValueError)
async def value_error_handler(_request: Request, exc: ValueError):
    # ValueError is used intentionally for client-facing validation messages.
    return JSONResponse(status_code=400, content={"detail": str(exc)})


@app.exception_handler(Exception)
async def unhandled_exception_handler(_request: Request, exc: Exception):
    # Log full detail server-side; never leak internals to the client.
    logger.exception("Unhandled error: %s", type(exc).__name__)
    detail = "Internal server error" if _is_prod else f"{type(exc).__name__}: {exc}"
    return JSONResponse(status_code=500, content={"detail": detail})


@app.get("/metrics")
def metrics():
    from app.core.metrics import render_prometheus

    return PlainTextResponse(render_prometheus(), media_type="text/plain; version=0.0.4")


@app.get("/health")
def health():
    return {"ok": True, "service": "api"}


@app.get("/healthz")
@app.get("/health/live")
def healthz():
    return {"ok": True, "service": "api", "status": "live"}


@app.get("/readyz")
@app.get("/health/ready")
def readyz():
    checks = {"database": False, "redis": "skipped"}

    def _fail(exc: Exception) -> JSONResponse:
        # Do not leak raw driver errors (hostnames / DSNs) in production.
        body = {"ok": False, "status": "not_ready", "checks": checks}
        if not _is_prod:
            body["detail"] = str(exc)
        logger.warning("Readiness check failed: %s", type(exc).__name__)
        return JSONResponse(status_code=503, content=body)

    db = SessionLocal()
    try:
        db.execute(text("SELECT 1"))
        checks["database"] = True
    except Exception as exc:
        return _fail(exc)
    finally:
        db.close()

    if _is_prod:
        try:
            Redis.from_url(settings.redis_url, socket_connect_timeout=1, socket_timeout=1).ping()
            checks["redis"] = True
        except Exception as exc:
            checks["redis"] = False
            return _fail(exc)

    return {"ok": True, "service": "api", "status": "ready", "checks": checks}


api_prefix = "/api/v1"
app.include_router(auth_router, prefix=api_prefix)
app.include_router(dashboard_router, prefix=api_prefix)
app.include_router(steam_accounts_router, prefix=api_prefix)
app.include_router(steam_data_router, prefix=api_prefix)
app.include_router(games_router, prefix=api_prefix)
app.include_router(sessions_router, prefix=api_prefix)
app.include_router(billing_router, prefix=api_prefix)
app.include_router(admin_router, prefix=api_prefix)
app.include_router(system_router, prefix=api_prefix)
app.include_router(faceit_router, prefix=api_prefix)
