"""
shared/browser_auth.py
────────────────────────────────────────────────────────────────────────────────
Generic Playwright browser authenticator.

This is the parameterized version of the original server/auth/browser_auth.py.
All portal-specific values (login URL, success hostname, display name) are
injected via __init__() so the same class works for any institution.

Why browser-based auth?
  Modern government portals use SSO, eID, dynamic JS redirects, and sometimes
  CAPTCHAs or popup windows that cannot be replicated with raw HTTP requests.
  Opening a real browser lets the user handle all of that manually while this
  code just waits and harvests the resulting cookies.

Flow:
  1. Open Chromium (headed/visible) at the institution's login URL.
  2. Show clear on-screen instructions for the user.
  3. Wait up to `timeout_seconds` for the browser to land on a URL whose
     hostname contains `post_login_hostname` (signals successful login).
  4. Capture all cookies for the portal domain.
  5. Return them as a plain dict so the caller can pass them to SessionManager.
"""
import sys
import io
import asyncio
import concurrent.futures
from typing import Optional

from playwright.async_api import (
    BrowserContext,
    Page,
    async_playwright,
    TimeoutError as PlaywrightTimeout,
)

# Fix Windows console encoding — prevents 'charmap' codec errors
# when printing Unicode/Cyrillic characters to the terminal.
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

class BrowserAuthenticator:
    """
    Opens a visible Chromium browser and waits for the user to log in.

    After successful login the resulting session cookies are captured and
    returned to the caller — this class never persists them itself.

    Args:
        login_url:            URL to open initially (the portal homepage or
                              direct login page).
        post_login_hostname:  Substring of the hostname that appears in the
                              URL after a successful login.  Used to detect
                              when the SSO round-trip is complete.
                              e.g. "uslugi.gov.mk" or "mojtermin.mk"
        portal_base_url:      Base URL of the portal, used to scope the cookie
                              capture to the right domain.
        institution_name:     Human-readable name shown in terminal messages.
        timeout_seconds:      How long to wait for the user to finish logging
                              in before giving up.  Default: 180 s (3 min).
    """

    def __init__(
        self,
        login_url: str,
        post_login_hostname: str,
        portal_base_url: str,
        institution_name: str,
        timeout_seconds: int = 180,
    ):
        self._login_url = login_url
        self._post_login_hostname = post_login_hostname
        self._portal_base_url = portal_base_url
        self._institution_name = institution_name
        # Playwright timeouts are in milliseconds.
        self._timeout_ms = timeout_seconds * 1000

    # ── Async core ────────────────────────────────────────────────────────────

    async def authenticate(self) -> Optional[dict]:
        """
        Launch a browser, wait for login, and return the captured cookies.

        Returns:
            dict of { cookie_name: cookie_value } on success, or None on
            timeout / error.
        """
        async with async_playwright() as pw:
            # ── Open a visible Chromium window ─────────────────────────────
            # headless=False is intentional: the user MUST interact with the
            # browser to complete login.  We never send keystrokes ourselves.
            browser = await pw.chromium.launch(headless=False)

            # Fresh context means no cookies from previous sessions bleed in.
            context: BrowserContext = await browser.new_context()
            page: Page = await context.new_page()

            # Print instructions to the terminal so the user knows what to do.
            print(
                f"\n╔══════════════════════════════════════════════════════════╗\n"
                f"║  BROWSER LOGIN REQUIRED — {self._institution_name:<32}║\n"
                f"║                                                          ║\n"
                f"║  A browser window will open.  Please:                    ║\n"
                f"║    1. Log in with your credentials.                      ║\n"
                f"║    2. Complete any 2FA / eID / CAPTCHA prompts.          ║\n"
                f"║    3. The window closes automatically after login.        ║\n"
                f"╚══════════════════════════════════════════════════════════╝\n"
            )

            # Navigate to the institution's login page.
            await page.goto(self._login_url)

            # ── Wait for post-login redirect ───────────────────────────────
            # We wait for a JavaScript expression (evaluated inside the
            # browser) to become truthy.  The expression checks that:
            #   - The browser has returned to the portal's domain.
            #   - The path is not just "/" (i.e. we're on a post-login page,
            #     not the bare homepage before the user clicked "Login").
            #
            # Why wait_for_function instead of wait_for_url?
            #   SSO round-trips visit multiple domains (portal → identity
            #   provider → portal).  wait_for_url only fires once, so it can
            #   miss the final redirect if the URL matches an intermediate step.
            #   Polling via wait_for_function is more robust.
            hostname = self._post_login_hostname
            try:
                await page.wait_for_function(
                    # This JS runs inside the Chromium tab, not in Python.
                    # It returns True only when the browser is back on the
                    # portal domain AND past the landing page.
                    f"() => window.location.hostname.includes('{hostname}') "
                    f"    && window.location.pathname !== '/'",
                    timeout=self._timeout_ms,
                )
            except PlaywrightTimeout:
                print(
                    f"[BrowserAuth:{self._institution_name}] Timeout: "
                    f"user did not complete login within "
                    f"{self._timeout_ms // 1000} seconds."
                )
                await browser.close()
                return None

            print(f"[BrowserAuth:{self._institution_name}] Post-login URL detected: {page.url}")

            # ── Capture cookies ────────────────────────────────────────────
            # context.cookies(url) returns only cookies relevant to that URL,
            # which filters out anything set by the identity provider.
            all_cookies = await context.cookies(self._portal_base_url)

            # Convert Playwright's list of cookie objects to a simple dict.
            cookies: dict = {c["name"]: c["value"] for c in all_cookies}

            print(
                f"[BrowserAuth:{self._institution_name}] Login successful. "
                f"Captured {len(cookies)} cookie(s): {list(cookies.keys())}"
            )

            await browser.close()
            return cookies

    # ── Synchronous wrapper ───────────────────────────────────────────────────

    def run(self) -> Optional[dict]:
        """
        Blocking wrapper around the async authenticate() method.

        WHY a thread instead of asyncio.run()?
        ────────────────────────────────────────
        FastMCP runs its own asyncio event loop.  When an MCP tool handler
        calls this method, we are already *inside* that running loop.
        Calling asyncio.run() from a running loop raises RuntimeError.

        Fix: run the coroutine in a fresh worker thread that has no existing
        event loop.  asyncio.run() in that thread creates a new loop, runs
        Playwright, and returns the result safely back to the calling thread.
        """

        def _run_in_new_loop() -> Optional[dict]:
            # This executes in a worker thread — there is no pre-existing
            # event loop in this thread, so asyncio.run() is safe to call.
            return asyncio.run(self.authenticate())

        # Use a single-worker pool so we can get the return value via future.
        # Timeout is slightly beyond the Playwright timeout to ensure the
        # browser has time to close before the thread is abandoned.
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(_run_in_new_loop)
            return future.result(timeout=(self._timeout_ms / 1000) + 30)
