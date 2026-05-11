from shared.http_client import AuthenticatedClient, SessionExpiredError
from institutions.agencijaZaVrabotuvanje.auth.session import session_manager
from institutions.agencijaZaVrabotuvanje.config import (
    PORTAL_BASE_URL,
    LOGIN_URL,
    COOKIE_DOMAIN,
)

authenticated_client = AuthenticatedClient(
    session_manager=session_manager,
    portal_base_url=PORTAL_BASE_URL,
    login_url=LOGIN_URL,
    cookie_domain=COOKIE_DOMAIN,
)

__all__ = ["authenticated_client", "SessionExpiredError"]