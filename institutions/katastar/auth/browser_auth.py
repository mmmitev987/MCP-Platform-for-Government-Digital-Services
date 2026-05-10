"""
institutions/katastar/auth/browser_auth.py
────────────────────────────────────────────────────────────────────────────────
Instantiates the shared BrowserAuthenticator for e-uslugi.katastar.gov.mk.

The portal uses a standard username/password login form.
The user must enter credentials in the opened Chromium window.
After login the session cookie is captured automatically.
"""

from shared.browser_auth import BrowserAuthenticator
from institutions.katastar.config import LOGIN_URL, POST_LOGIN_HOSTNAME, PORTAL_BASE_URL

# Singleton — created once when this module is first imported.
# Callers just invoke  browser_authenticator.run()  which blocks until the
# user finishes logging in in the Chromium window.
browser_authenticator = BrowserAuthenticator(
    login_url=LOGIN_URL,
    post_login_hostname=POST_LOGIN_HOSTNAME,
    portal_base_url=PORTAL_BASE_URL,
    institution_name="e-uslugi.katastar.gov.mk",
    timeout_seconds=180,
)