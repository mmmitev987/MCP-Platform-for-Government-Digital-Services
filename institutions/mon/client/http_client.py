"""
institutions/mon/client/http_client.py
────────────────────────────────────────────────────────────────────────────────
Instantiates the shared AuthenticatedClient for e-uslugi.mon.gov.mk.

Usage in tool files:
    from institutions.mon.client.http_client import authenticated_client, SessionExpiredError

    def some_authenticated_tool(...) -> dict:
        try:
            resp = authenticated_client.get("https://e-uslugi.mon.gov.mk/api/...")
            return resp.json()
        except SessionExpiredError:
            return {"error": "Session expired. Please call the login tool first."}
"""

from shared.http_client import AuthenticatedClient, SessionExpiredError  # re-export
from institutions.mon.auth.session import session_manager
from institutions.mon.config import PORTAL_BASE_URL, LOGIN_URL, COOKIE_DOMAIN

authenticated_client = AuthenticatedClient(
    session_manager=session_manager,
    portal_base_url=PORTAL_BASE_URL,
    login_url=LOGIN_URL,
    cookie_domain=COOKIE_DOMAIN,
)

__all__ = ["authenticated_client", "SessionExpiredError"]
