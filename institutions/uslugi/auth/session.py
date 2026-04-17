"""
institutions/uslugi/auth/session.py
────────────────────────────────────────────────────────────────────────────────
Instantiates the shared SessionManager for uslugi.gov.mk.

This file is intentionally thin — all logic lives in shared/session.py.
We just wire it up with the right config values for this institution.

The singleton `session_manager` is imported by:
  • institutions/uslugi/auth/session_tools.py  (login / logout / check_session)
  • institutions/uslugi/client/http_client.py  (cookie injection on requests)
"""

from shared.session import SessionManager
from institutions.uslugi.config import SESSION_FILE

session_manager = SessionManager(
    session_file=SESSION_FILE,
    institution_id="uslugi",
)
