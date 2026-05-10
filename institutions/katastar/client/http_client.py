"""
institutions/katastar/client/http_client.py
────────────────────────────────────────────────────────────────────────────────
Instantiates the shared AuthenticatedClient for e-uslugi.katastar.gov.mk.

The `authenticated_client` singleton is the single object that all katastar
tool functions must use when they need to make authenticated HTTP calls.
It automatically injects the current session cookies before every request.

Re-exporting SessionExpiredError here so tool code can do:
    from institutions.katastar.client.http_client import (
        authenticated_client, SessionExpiredError
    )
without knowing about the shared/ layer.
"""

from shared.http_client import AuthenticatedClient, SessionExpiredError  # re-export
from institutions.katastar.auth.session import session_manager
from institutions.katastar.config import PORTAL_BASE_URL, LOGIN_URL, COOKIE_DOMAIN

authenticated_client = AuthenticatedClient(
    session_manager=session_manager,
    portal_base_url=PORTAL_BASE_URL,
    login_url=LOGIN_URL,
    cookie_domain=COOKIE_DOMAIN,
)

__all__ = ["authenticated_client", "SessionExpiredError"]