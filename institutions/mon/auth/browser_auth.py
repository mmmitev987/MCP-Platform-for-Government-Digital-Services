"""
institutions/mon/auth/browser_auth.py
────────────────────────────────────────────────────────────────────────────────
MON-specific browser authenticator.

e-uslugi.mon.gov.mk stores the JWT access token in localStorage, not in
cookies, so we cannot use the shared BrowserAuthenticator directly.
After the user logs in we extract the token via page.evaluate() and return
it as {"access_token": "..."} so the SessionManager can store it.
"""

import asyncio
import concurrent.futures
from typing import Optional

from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeout

from institutions.mon.config import LOGIN_URL, POST_LOGIN_HOSTNAME


class MonBrowserAuthenticator:
    _TIMEOUT_S = 180

    async def _authenticate(self) -> Optional[dict]:
        async with async_playwright() as pw:
            browser = await pw.chromium.launch(headless=False)
            context = await browser.new_context()
            page = await context.new_page()

            print(
                "\n╔══════════════════════════════════════════════════════════╗\n"
                "║  BROWSER LOGIN REQUIRED — e-uslugi.mon.gov.mk            ║\n"
                "║                                                          ║\n"
                "║  A browser window will open.  Please:                    ║\n"
                "║    1. Log in with your credentials.                      ║\n"
                "║    2. Complete any 2FA / eID prompts.                    ║\n"
                "║    3. The window closes automatically after login.        ║\n"
                "╚══════════════════════════════════════════════════════════╝\n"
            )

            await page.goto(LOGIN_URL)

            try:
                await page.wait_for_function(
                    "() => !!localStorage.getItem('access_token')",
                    timeout=self._TIMEOUT_S * 1000,
                )
            except PlaywrightTimeout:
                print("[MON Auth] Timeout — user did not complete login in time.")
                await browser.close()
                return None

            # MON portal stores the JWT in localStorage, not cookies.
            token = await page.evaluate("localStorage.getItem('access_token')")
            await browser.close()

            if not token:
                print("[MON Auth] Login detected but no access_token found in localStorage.")
                return None

            print("[MON Auth] Login successful. JWT token captured.")
            return {"access_token": token}

    def run(self) -> Optional[dict]:
        def _run_in_new_loop():
            return asyncio.run(self._authenticate())

        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(_run_in_new_loop)
            return future.result(timeout=self._TIMEOUT_S + 30)


browser_authenticator = MonBrowserAuthenticator()
