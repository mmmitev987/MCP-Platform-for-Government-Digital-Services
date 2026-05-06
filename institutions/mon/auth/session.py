"""
institutions/mon/auth/session.py
────────────────────────────────────────────────────────────────────────────────
Instantiates the shared SessionManager for e-uslugi.mon.gov.mk.
"""

from shared.session import SessionManager
from institutions.mon.config import SESSION_FILE

session_manager = SessionManager(
    session_file=SESSION_FILE,
    institution_id="mon",
)
