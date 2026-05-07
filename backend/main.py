from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.httpsredirect import HTTPSRedirectMiddleware

from sqlalchemy import text
from backend.middleware.csrf import CSRFMiddleware
from backend.config import settings
from backend.database import engine, Base
from backend.models import password_reset  # noqa: F401 — registers model with Base
from backend.services.chat_service import chat_service
from backend.routers import auth, chat, services, activity, settings as settings_router

Base.metadata.create_all(bind=engine)

# Add disabled_institutions column if it doesn't exist yet (safe migration)
with engine.connect() as _conn:
    try:
        _conn.execute(text("ALTER TABLE users ADD COLUMN disabled_institutions TEXT DEFAULT ''"))
        _conn.commit()
    except Exception:
        pass
    # Add indexes for fast session loading (safe — IF NOT EXISTS)
    try:
        _conn.execute(text("CREATE INDEX IF NOT EXISTS ix_messages_session_created ON messages (session_id, created_at)"))
        _conn.execute(text("CREATE INDEX IF NOT EXISTS ix_chat_sessions_user_id ON chat_sessions (user_id)"))
        _conn.commit()
    except Exception:
        pass
    # Add indexes for fast activity loading
    try:
        _conn.execute(text("CREATE INDEX IF NOT EXISTS ix_activity_user_created ON activity_logs (user_id, created_at)"))
        _conn.execute(text("CREATE INDEX IF NOT EXISTS ix_activity_user_status_created ON activity_logs (user_id, status, created_at)"))
        _conn.commit()
    except Exception:
        pass


@asynccontextmanager
async def lifespan(app: FastAPI):
    await chat_service.start()
    yield
    await chat_service.stop()


app = FastAPI(title="MCP Government Platform", lifespan=lifespan)

# ── HTTPS enforcement (production only) ──────────────────────────────────────
if settings.PRODUCTION:
    app.add_middleware(HTTPSRedirectMiddleware)

# ── CSRF protection (Double Submit Cookie) ────────────────────────────────────
app.add_middleware(CSRFMiddleware)

# ── Security headers middleware ───────────────────────────────────────────────
@app.middleware("http")
async def add_security_headers(request: Request, call_next) -> Response:
    response = await call_next(request)
    if settings.PRODUCTION:
        # Force HTTPS for 1 year, include subdomains
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    # Prevent clickjacking
    response.headers["X-Frame-Options"] = "DENY"
    # Prevent MIME sniffing
    response.headers["X-Content-Type-Options"] = "nosniff"
    # Basic XSS protection
    response.headers["X-XSS-Protection"] = "1; mode=block"
    # Referrer policy
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    return response

# ── CORS ──────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_URL] if settings.PRODUCTION else ["http://localhost:3000"],
    allow_credentials=True,  # Required for CSRF cookie to be sent cross-origin in dev
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization", "Accept", "X-CSRF-Token"],
    expose_headers=["X-Captcha-Token"],
)

app.include_router(auth.router,             prefix="/api/auth",     tags=["auth"])
app.include_router(chat.router,             prefix="/api/chat",     tags=["chat"])
app.include_router(services.router,         prefix="/api/services", tags=["services"])
app.include_router(activity.router,         prefix="/api/activity", tags=["activity"])
app.include_router(settings_router.router,  prefix="/api/settings", tags=["settings"])
