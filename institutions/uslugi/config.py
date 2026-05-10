"""
institutions/uslugi/config.py
────────────────────────────────────────────────────────────────────────────────
All configuration for the uslugi.gov.mk institution.

Every env var here is prefixed with USLUGI_ to avoid conflicts with other
institutions.

Env vars (set in .env or the system environment):
  USLUGI_BASE_URL                  — portal root URL
  USLUGI_SESSION_FILE              — path (relative to project root) for the
                                     encrypted cookie file
  USLUGI_COOKIE_ENCRYPTION_KEY     — Fernet key; auto-generated if empty
  GEMINI_API_KEY                   — shared Gemini key (no institution prefix)
"""

import os
from pathlib import Path

from dotenv import load_dotenv

# ── Resolve project root ──────────────────────────────────────────────────────
# This file lives at  institutions/uslugi/config.py
# Project root is     ../../   (two levels up)
PROJECT_ROOT = Path(__file__).parent.parent.parent.resolve()

# Load .env from project root.  python-dotenv is silent if the file is absent.
load_dotenv(PROJECT_ROOT / ".env")


# ── Portal settings ───────────────────────────────────────────────────────────

PORTAL_BASE_URL: str = os.getenv("USLUGI_BASE_URL", "https://uslugi.gov.mk")


# ── Session / cookie storage ──────────────────────────────────────────────────

# Path to the Fernet-encrypted cookie file, relative to project root.
# Using a USLUGI-specific name keeps it separate from the mojtermin session.
_session_file_rel = os.getenv("USLUGI_SESSION_FILE", "storage/uslugi_session.enc")
SESSION_FILE: Path = PROJECT_ROOT / _session_file_rel


# ── Auth flow URLs ────────────────────────────────────────────────────────────

# URL to navigate to when starting a browser login.
# The portal homepage is preferred over the direct eid.mk URL because the
# portal generates a fresh short-lived wctx token in the SSO redirect URL.
LOGIN_URL: str = PORTAL_BASE_URL

# URL path that indicates a redirect to the login page (session expired).
# Used by AuthenticatedClient._check_response() to detect silent redirects.
# Must be specific enough to NOT match normal API response URLs.
LOGIN_REDIRECT_URL: str = PORTAL_BASE_URL + "/login.nspx"

# Substring of the hostname we wait for after a successful SSO round-trip.
# Once the browser's URL hostname contains this string, we know login worked.
POST_LOGIN_HOSTNAME: str = "uslugi.gov.mk"

# The cookie domain that the portal's session cookie is scoped to.
COOKIE_DOMAIN: str = "uslugi.gov.mk"


# ── Gemini (shared between institutions — no USLUGI_ prefix) ─────────────────

GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL: str = "gemini-2.5-flash"
