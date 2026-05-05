"""
institutions/mon/config.py
────────────────────────────────────────────────────────────────────────────────
Configuration for the Ministry of Education and Science (MON) institution.

All env vars are prefixed with MON_ to avoid conflicts with other institutions.

Env vars (set in .env or system environment):
  MON_EUSLUGI_BASE_URL   — e-services portal root (default: https://e-uslugi.mon.gov.mk)
  MON_SESSION_FILE       — path (relative to project root) for encrypted cookie file
  GEMINI_API_KEY         — shared Gemini key (no MON_ prefix)

Public info tools use uslugi.gov.mk (no auth needed).
Authenticated tools use e-uslugi.mon.gov.mk.
"""

import os
from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).parent.parent.parent.resolve()
load_dotenv(PROJECT_ROOT / ".env")

# ── e-uslugi.mon.gov.mk portal ────────────────────────────────────────────────

PORTAL_BASE_URL: str = os.getenv("MON_EUSLUGI_BASE_URL", "https://e-uslugi.mon.gov.mk")

# ── Session / cookie storage ──────────────────────────────────────────────────

_session_file_rel = os.getenv("MON_SESSION_FILE", "storage/mon_session.enc")
SESSION_FILE: Path = PROJECT_ROOT / _session_file_rel

# ── Auth flow ─────────────────────────────────────────────────────────────────

LOGIN_URL: str = PORTAL_BASE_URL
POST_LOGIN_HOSTNAME: str = "mon.gov.mk"
COOKIE_DOMAIN: str = "e-uslugi.mon.gov.mk"

# ── Central uslugi.gov.mk (public info) ───────────────────────────────────────

USLUGI_BASE_URL: str = "https://uslugi.gov.mk"

# Education subcategory IDs on uslugi.gov.mk
MON_SUBCATEGORY_IDS: dict[str, int] = {
    "pretshkolska": 324,       # Preschool
    "skolska": 325,             # School
    "visoko_obrazovanie": 326,  # Higher Education
    "stipendii": 327,           # Scholarships
    "obuki": 328,               # Training
    "nauka": 390,               # Science
}

# ── Gemini (shared) ───────────────────────────────────────────────────────────

GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL: str = "gemini-2.5-flash"
