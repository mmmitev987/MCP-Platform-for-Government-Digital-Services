"""
shared/http_client.py
────────────────────────────────────────────────────────────────────────────────
Generic authenticated HTTP client.

This is the parameterized version of the original server/client/http_client.py.

Responsibilities:
  1. Load the institution's saved session cookies via the injected
     SessionManager instance.
  2. Inject those cookies on every request via a requests.Session.
  3. Detect expired sessions (HTTP 401/403 or redirect to login page) and
     raise SessionExpiredError so the MCP tool layer can return a helpful
     error message to the LLM instead of an ugly stack trace.
  4. Provide clean get() / post() wrappers so tool code never touches cookies.

Session freshness:
  Each call to get() / post() rebuilds the requests.Session from the *latest*
  cookies on disk.  This means if a re-login happened between two tool calls,
  the next call automatically picks up the new cookies without any extra work.
"""

import requests

from shared.session import SessionManager


class SessionExpiredError(Exception):
    """
    Raised when the server indicates the session is no longer valid.

    Possible triggers:
      • HTTP 401 Unauthorized — token missing or invalid.
      • HTTP 403 Forbidden   — authenticated but the resource is not accessible
                               (sometimes also used for expired sessions).
      • Redirect to the login page — the portal silently bounced the request.
    """


class AuthenticatedClient:
    """
    Thin wrapper around requests.Session that auto-injects session cookies.

    All tool functions should use this client rather than calling requests
    directly.  Doing so ensures cookies are always fresh and session expiry
    is detected and surfaced cleanly.

    Args:
        session_manager:  The institution's SessionManager — used to load
                          the current cookies before each request.
        portal_base_url:  Root URL of the portal (e.g. "https://uslugi.gov.mk").
                          Used in request headers (Origin, Referer) and for
                          setting the correct cookie domain.
        login_url:        The portal's login page URL.  Used to detect
                          silent redirects to the login page.
        cookie_domain:    The domain string to use when injecting cookies into
                          the requests.Session (e.g. "uslugi.gov.mk").
    """

    def __init__(
        self,
        session_manager: SessionManager,
        portal_base_url: str,
        login_url: str,
        cookie_domain: str,
    ):
        self._session_manager = session_manager
        self._portal_base_url = portal_base_url
        self._login_url = login_url
        self._cookie_domain = cookie_domain

        # Standard browser-like headers prevent most bot-detection blocks.
        # We set Origin and Referer to the portal so the server sees a
        # plausible browser navigation context.
        self._base_headers = {
            "User-Agent": (
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            ),
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "mk-MK,mk;q=0.9,en;q=0.8",
            "Origin": portal_base_url,
            "Referer": portal_base_url + "/",
        }

    # ── Private helpers ───────────────────────────────────────────────────────

    def _build_session(self) -> requests.Session:
        """
        Build a requests.Session pre-loaded with the latest saved cookies.

        Called before every HTTP request so cookies are always current.

        Raises:
            SessionExpiredError: If no cookies are found on disk (user has not
                                  logged in, or has logged out).
        """
        cookies = self._session_manager.load()

        if not cookies:
            raise SessionExpiredError(
                f"No active session for {self._cookie_domain}. "
                "Please call the 'login' tool first."
            )

        session = requests.Session()
        session.headers.update(self._base_headers)

        # Inject each saved cookie.  We bind them to the specific domain so
        # requests sends them only to that domain (not to any other host that
        # might redirect through the portal).
        for name, value in cookies.items():
            session.cookies.set(name, value, domain=self._cookie_domain)

        return session

    def _check_response(self, response: requests.Response) -> None:
        """
        Inspect a response for signs that the session has expired.

        Raises SessionExpiredError for:
          • HTTP 401 / 403
          • The final URL (after redirects) contains the login path
        """
        if response.status_code in (401, 403):
            raise SessionExpiredError(
                f"Session expired (HTTP {response.status_code}) on "
                f"{self._cookie_domain}. Please call the 'login' tool."
            )

        # Some portals silently redirect expired-session requests to the login
        # page with HTTP 200.  Detect that by checking the final URL.
        if self._login_url.rstrip("/") in response.url:
            raise SessionExpiredError(
                f"Session expired (redirected to login page) on "
                f"{self._cookie_domain}. Please call the 'login' tool."
            )

    # ── Public API ────────────────────────────────────────────────────────────

    def get(self, url: str, **kwargs) -> requests.Response:
        """
        Perform an authenticated GET request.

        Args:
            url:      Absolute URL to request.
            **kwargs: Forwarded to requests.Session.get() — e.g. params=,
                      headers=, timeout=.

        Returns:
            requests.Response

        Raises:
            SessionExpiredError: If no session or the server rejects the cookies.
        """
        session = self._build_session()
        response = session.get(url, allow_redirects=True, timeout=20, **kwargs)
        self._check_response(response)
        return response

    def post(self, url: str, **kwargs) -> requests.Response:
        """
        Perform an authenticated POST request.

        Args:
            url:      Absolute URL to POST to.
            **kwargs: Forwarded to requests.Session.post() — e.g. json=,
                      data=, headers=, timeout=.

        Returns:
            requests.Response

        Raises:
            SessionExpiredError: If no session or the server rejects the cookies.
        """
        session = self._build_session()
        response = session.post(url, allow_redirects=True, timeout=20, **kwargs)
        self._check_response(response)
        return response
