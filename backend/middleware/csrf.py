"""
backend/middleware/csrf.py
──────────────────────────
Double Submit Cookie CSRF protection.

How it works:
  1. Client calls GET /api/auth/csrf-token → receives a random token
     in both a cookie (csrf_token) and a JSON response body.
  2. Frontend stores the token and attaches it as X-CSRF-Token header
     on every state-changing request (POST, PUT, PATCH, DELETE).
  3. This middleware reads the cookie value and the header value and
     compares them. If they don't match → 403 Forbidden.

Why this is safe:
  - A malicious cross-origin site can trigger a request that sends the
    cookie automatically, but it cannot READ the cookie (same-origin
    policy), so it cannot set the matching X-CSRF-Token header.
  - Safe methods (GET, HEAD, OPTIONS) are not checked.
  - The /api/auth/csrf-token endpoint itself is excluded (it issues tokens).
"""

import secrets
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

SAFE_METHODS = {"GET", "HEAD", "OPTIONS"}
EXEMPT_PATHS = {"/api/auth/csrf-token", "/api/auth/login", "/api/auth/register"}


class CSRFMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if request.method in SAFE_METHODS or request.url.path in EXEMPT_PATHS:
            return await call_next(request)

        cookie_token = request.cookies.get("csrf_token")
        header_token = request.headers.get("X-CSRF-Token")

        if not cookie_token or not header_token:
            return JSONResponse(
                status_code=403,
                content={"detail": "CSRF token missing."},
            )

        if not secrets.compare_digest(cookie_token, header_token):
            return JSONResponse(
                status_code=403,
                content={"detail": "CSRF token invalid."},
            )

        return await call_next(request)
