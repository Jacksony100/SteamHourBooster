from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from redis import Redis
from sqlalchemy import text

from app.admin.routes import router as admin_router
from app.auth.routes import router as auth_router
from app.billing.routes import router as billing_router
from app.core.config import get_settings
from app.core.database import SessionLocal
from app.dashboard.routes import router as dashboard_router
from app.games.routes import router as games_router
from app.sessions.manager import get_session_manager
from app.sessions.routes import router as sessions_router
from app.steam_accounts.routes import router as steam_accounts_router
from app.system.routes import router as system_router

settings = get_settings()


@asynccontextmanager
async def lifespan(_app: FastAPI):
    yield
    db = SessionLocal()
    try:
        get_session_manager().shutdown_active_sessions(db)
    finally:
        db.close()


app = FastAPI(
    title="DeckPilot API",
    version="2.0.0",
    description="Transparent account/session manager for user-owned Steam accounts. No stealth or evasion behavior.",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(ValueError)
async def value_error_handler(_request: Request, exc: ValueError):
    return JSONResponse(status_code=400, content={"detail": str(exc)})


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
    db = SessionLocal()
    try:
        db.execute(text("SELECT 1"))
        checks["database"] = True
    except Exception as exc:
        return JSONResponse(status_code=503, content={"ok": False, "status": "not_ready", "checks": checks, "detail": str(exc)})
    finally:
        db.close()

    if settings.environment == "production":
        try:
            Redis.from_url(settings.redis_url, socket_connect_timeout=1, socket_timeout=1).ping()
            checks["redis"] = True
        except Exception as exc:
            checks["redis"] = False
            return JSONResponse(status_code=503, content={"ok": False, "status": "not_ready", "checks": checks, "detail": str(exc)})

    return {"ok": True, "service": "api", "status": "ready", "checks": checks}


api_prefix = "/api/v1"
app.include_router(auth_router, prefix=api_prefix)
app.include_router(dashboard_router, prefix=api_prefix)
app.include_router(steam_accounts_router, prefix=api_prefix)
app.include_router(games_router, prefix=api_prefix)
app.include_router(sessions_router, prefix=api_prefix)
app.include_router(billing_router, prefix=api_prefix)
app.include_router(admin_router, prefix=api_prefix)
app.include_router(system_router, prefix=api_prefix)
