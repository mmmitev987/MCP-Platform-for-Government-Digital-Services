"""
institutions/uslugi/auth/browser_auth.py
────────────────────────────────────────────────────────────────────────────────
Instantiates the shared BrowserAuthenticator for uslugi.gov.mk.

uslugi.gov.mk uses the eid.mk federated identity provider (SSO).
The login flow involves multiple domain hops:
  1. User lands on uslugi.gov.mk.
  2. Clicks "Најави се" → browser is redirected to eid.mk.
  3. User authenticates on eid.mk (with credentials, eID chip, or 2FA).
  4. eid.mk redirects the browser back to uslugi.gov.mk/home.nspx.

We detect step 4 by waiting until the browser's hostname contains
"uslugi.gov.mk" AND the path is not just "/".
"""

from shared.browser_auth import BrowserAuthenticator
from institutions.uslugi.config import LOGIN_URL, POST_LOGIN_HOSTNAME, PORTAL_BASE_URL

# Singleton — created once when this module is first imported.
# Callers just invoke  browser_authenticator.run()  which blocks until the
# user finishes logging in in the Chromium window.
browser_authenticator = BrowserAuthenticator(
    login_url=LOGIN_URL,
    post_login_hostname=POST_LOGIN_HOSTNAME,
    portal_base_url=PORTAL_BASE_URL,
    institution_name="uslugi.gov.mk",
    timeout_seconds=180,  # 3 minutes — generous for the eid.mk SSO flow
)
