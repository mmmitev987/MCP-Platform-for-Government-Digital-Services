"""
institutions/katastar/config.py
────────────────────────────────────────────────────────────────────────────────
All configuration for the e-uslugi.katastar.gov.mk institution.

Every env var here is prefixed with KATASTAR_ to avoid conflicts with other
institutions.

Env vars (set in .env or the system environment):
  KATASTAR_BASE_URL             — portal root URL
  KATASTAR_SESSION_FILE         — path (relative to project root) for the
                                   encrypted cookie file
  KATASTAR_COOKIE_ENCRYPTION_KEY — Fernet key; auto-generated if empty
  GEMINI_API_KEY                — shared Gemini key (no institution prefix)
"""

"""
import os
from pathlib import Path

from dotenv import load_dotenv

# ── Resolve project root ──────────────────────────────────────────────────────
# This file lives at  institutions/katastar/config.py
# Project root is     ../../   (two levels up)
PROJECT_ROOT = Path(__file__).parent.parent.parent.resolve()

load_dotenv(PROJECT_ROOT / ".env")


# ── Portal settings ───────────────────────────────────────────────────────────

PORTAL_BASE_URL: str = os.getenv("KATASTAR_BASE_URL", "https://e-uslugi.katastar.gov.mk")


# ── Session / cookie storage ──────────────────────────────────────────────────

_session_file_rel = os.getenv("KATASTAR_SESSION_FILE", "storage/katastar_session.enc")
SESSION_FILE: Path = PROJECT_ROOT / _session_file_rel


# ── Auth flow URLs ────────────────────────────────────────────────────────────

LOGIN_URL: str = PORTAL_BASE_URL

# Substring of the hostname we wait for after a successful login.
POST_LOGIN_HOSTNAME: str = "e-uslugi.katastar.gov.mk"

# The cookie domain that the portal's session cookie is scoped to.
COOKIE_DOMAIN: str = "e-uslugi.katastar.gov.mk"


# ── Gemini (shared between institutions — no KATASTAR_ prefix) ───────────────

GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL: str = "gemini-2.5-flash" 
"""
"""
institutions/katastar/config.py
"""

import os
from pathlib import Path
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).parent.parent.parent.resolve()
load_dotenv(PROJECT_ROOT / ".env")

# ── Portal settings ───────────────────────────────────────────────────────────
PORTAL_BASE_URL: str = os.getenv("KATASTAR_BASE_URL", "https://e-uslugi.katastar.gov.mk")

# ── Session / cookie storage ──────────────────────────────────────────────────
_session_file_rel = os.getenv("KATASTAR_SESSION_FILE", "storage/katastar_session.enc")
SESSION_FILE: Path = PROJECT_ROOT / _session_file_rel

# ── Auth flow URLs ────────────────────────────────────────────────────────────
#LOGIN_URL: str = PORTAL_BASE_URL
# ── Auth flow URLs ────────────────────────────────────────────────────────────
LOGIN_URL: str = f"{PORTAL_BASE_URL}/Account/Login"

# Чека на КОЈ БИЛО URL на кatastar доменот (вклучувајки и "/")
POST_LOGIN_HOSTNAME: str = "e-uslugi.katastar.gov.mk"
POST_LOGIN_PATH: str = ""   # празно = прифати КОЈ БИЛО пат вклучувајки "/"

COOKIE_DOMAIN: str = "e-uslugi.katastar.gov.mk"

# ── Gemini ────────────────────────────────────────────────────────────────────
GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")