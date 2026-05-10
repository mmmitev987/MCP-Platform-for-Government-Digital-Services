"""
institutions/uslugi/client/http_client.py
────────────────────────────────────────────────────────────────────────────────
Instantiates the shared AuthenticatedClient for uslugi.gov.mk.

The `authenticated_client` singleton is the single object that all uslugi
tool functions must use when they need to make authenticated HTTP calls.
It automatically injects the current session cookies before every request.

Re-exporting SessionExpiredError here so tool code can do:
    from institutions.uslugi.client.http_client import (
        authenticated_client, SessionExpiredError
    )
without knowing about the shared/ layer.
"""

from shared.http_client import AuthenticatedClient, SessionExpiredError  # re-export
from institutions.uslugi.auth.session import session_manager
from institutions.uslugi.config import PORTAL_BASE_URL, LOGIN_REDIRECT_URL, COOKIE_DOMAIN

authenticated_client = AuthenticatedClient(
    session_manager=session_manager,
    portal_base_url=PORTAL_BASE_URL,
    login_url=LOGIN_REDIRECT_URL,
    cookie_domain=COOKIE_DOMAIN,
)

# Make SessionExpiredError importable from this module so tool files don't
# need a separate import from shared/.
__all__ = ["authenticated_client", "SessionExpiredError"]


# ── How to use authenticated_client in a tool ─────────────────────────────────
#
# Imagine uslugi.gov.mk has an endpoint that returns the logged-in user's
# submitted requests.  It requires the user to be authenticated (cookies).
#
# WITHOUT authenticated_client you would have to:
#   1. Load the cookies from disk manually
#   2. Inject them into a requests.Session yourself
#   3. Make the request
#   4. Check if the response is a 401/403 or a redirect to the login page
#   5. Raise a meaningful error if the session expired
#
# WITH authenticated_client all of that is handled for you:
#
#   from institutions.uslugi.client.http_client import authenticated_client, SessionExpiredError
#
#   def get_my_submissions() -> dict:
#       try:
#           response = authenticated_client.get(
#               "https://uslugi.gov.mk/api/MyRequests/GetMyRequests"
#           )
#           return response.json()
#
#       except SessionExpiredError:
#           return {"error": "Session expired. Please call the login tool first."}
#
# What authenticated_client.get() does internally:
#   1. Loads the latest cookies from the encrypted file on disk
#   2. Creates a requests.Session and injects those cookies into it
#   3. Sends the GET request with browser-like headers (User-Agent, Origin, Referer)
#   4. Checks the response — if it's 401/403 or redirected to the login page,
#      raises SessionExpiredError instead of returning a confusing raw response
#   5. Returns the requests.Response so the tool can call .json() or .text on it
#
# authenticated_client.post() works the same way but for POST requests:
#
#   def submit_request(service_id: str) -> dict:
#       try:
#           response = authenticated_client.post(
#               "https://uslugi.gov.mk/api/MyRequests/Submit",
#               json={"serviceId": service_id},
#               headers={"from-angular": "true"},
#           )
#           return response.json()
#
#       except SessionExpiredError:
#           return {"error": "Session expired. Please call the login tool first."}
