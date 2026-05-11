from shared.browser_auth import BrowserAuthenticator
from institutions.agencijaZaVrabotuvanje.config import (
    LOGIN_URL,
    POST_LOGIN_HOSTNAME,
    PORTAL_BASE_URL,
)

browser_authenticator = BrowserAuthenticator(
    login_url=LOGIN_URL,
    post_login_hostname=POST_LOGIN_HOSTNAME,
    portal_base_url=PORTAL_BASE_URL,
    institution_name="agencijaZaVrabotuvanje",
    timeout_seconds=180,
)