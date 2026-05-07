"""
institutions/crm/client/browser.py
────────────────────────────────────────────────────────────────────────────────
Persistent Playwright browser session for crm.com.mk.

Why a persistent session?
  reCAPTCHA scores requests based on long-lived browser behaviour (mouse moves,
  page history, cookie age). A fresh browser per request looks bot-like and
  will likely start failing. One browser kept open for the lifetime of the MCP
  server process scores as a normal returning user.

Lifecycle (managed by CRMBrowserClient):
  startup  → start()        — launches Chromium, navigates to search page once
  per-call → search / get_* — reuse the same page, intercept XHR responses
  shutdown → stop()         — closes browser when MCP server exits

Response interception strategy:
  Instead of parsing HTML, we listen for the JSON responses that the Angular
  app receives from /CRMPublicPortalApi/api/freeservice/*.  The reCAPTCHA
  token is injected by the browser's JS automatically — we never touch it.
"""

import asyncio
import base64
import json
import os
from typing import Any

from google import genai
from google.genai import types as genai_types
from playwright.async_api import (
    async_playwright,
    Browser,
    BrowserContext,
    Page,
    Playwright,
    Response,
)

from institutions.crm.config import (
    HEADLESS,
    RESPONSE_TIMEOUT_MS,
    SEARCH_PAGE_URL,
    TYPING_DELAY_MS,
)
from institutions.shared.errors import tool_error


class CRMBrowserClient:
    """
    Persistent Playwright browser that handles all crm.com.mk API calls.

    Instantiate once at MCP server startup and call await client.start().
    All tool functions call methods on this single instance.
    Call await client.stop() on server shutdown.

    Example (standalone test):
        import asyncio
        from institutions.crm.client.browser import CRMBrowserClient

        async def main():
            client = CRMBrowserClient()
            await client.start()
            results = await client.search_companies("Алфа")
            print(results)
            await client.stop()

        asyncio.run(main())
    """

    def __init__(self):
        self._playwright:      Playwright | None     = None
        self._browser:         Browser | None        = None
        self._context:         BrowserContext | None = None
        self._page:            Page | None           = None
        self._ready:           bool                  = False
        self._leid_to_name:    dict[int, str]        = {}  # leid → fullName (Cyrillic)

    # ── Lifecycle ─────────────────────────────────────────────────────────────

    async def start(self):
        """
        Launch Chromium and warm up the search page so reCAPTCHA initialises.
        Call this once before any tool functions are used.
        """
        self._playwright = await async_playwright().start()

        self._browser = await self._playwright.chromium.launch(
            headless=HEADLESS,
            args=[
                "--no-sandbox",
                # Prevents navigator.webdriver=true which reCAPTCHA checks.
                "--disable-blink-features=AutomationControlled",
            ],
        )

        self._context = await self._browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            ),
            locale="mk-MK",
            viewport={"width": 1280, "height": 800},
        )

        self._page = await self._context.new_page()

        # Navigate once — this initialises reCAPTCHA and loads the Angular app.
        await self._page.goto(SEARCH_PAGE_URL, wait_until="networkidle")
        self._ready = True

    async def stop(self):
        """Cleanly close the browser. Call on MCP server shutdown."""
        if self._browser:
            await self._browser.close()
        if self._playwright:
            await self._playwright.stop()
        self._ready = False

    def _assert_ready(self):
        if not self._ready:
            raise RuntimeError(
                "CRMBrowserClient not started. Call await client.start() first."
            )

    def _not_ready_error(self):
        return tool_error(
            "browser_error",
            "The CRM browser session is not active. The server may still be starting up — please try again in a moment."
        )

    # ── Response interception ─────────────────────────────────────────────────

    async def _wait_for_api_response(self, url_fragment: str) -> Any:
        """
        Attach a one-shot response listener and return the JSON body of the
        first response whose URL contains `url_fragment`.

        Args:
            url_fragment: Substring to match in the response URL,
                          e.g. "basicProfile" or "annualReport".

        Returns:
            Parsed JSON (dict or list).

        Raises:
            asyncio.TimeoutError: if no matching response arrives in time.
        """
        loop = asyncio.get_event_loop()
        future: asyncio.Future[Any] = loop.create_future()

        async def handler(response: Response):
            if url_fragment in response.url and not future.done():
                try:
                    body = await response.json()
                    future.set_result(body)
                except Exception as exc:
                    if not future.done():
                        future.set_exception(exc)

        self._page.on("response", handler)
        try:
            return await asyncio.wait_for(
                asyncio.shield(future),
                timeout=RESPONSE_TIMEOUT_MS / 1000,
            )
        finally:
            self._page.remove_listener("response", handler)

    # ── DOM helpers ───────────────────────────────────────────────────────────

    async def _fill_search_box(self, query: str):
        """
        Locate the search <input> on the basic-profile page, clear it,
        and type the query with human-like delays so reCAPTCHA sees activity.

        Selector priority:
          1. input with Cyrillic placeholder "Внесете" (most specific)
          2. First visible text input on the page (fallback)

        If CRM updates their markup, run test_crm.py with HEADLESS=False,
        right-click the search box → Inspect, and update the selector here.
        """
        try:
            box = self._page.locator("input[placeholder*='Внесете']").first
            await box.wait_for(state="visible", timeout=5_000)
        except Exception:
            box = self._page.locator("input[type='text']:visible").first

        await box.click()
        await box.press("Control+a")
        await box.type(query, delay=TYPING_DELAY_MS)

    async def _click_company_row(self, leid: int):
        """
        Click the table row for a company identified by `leid`.

        Rows are plain <tr tabindex="0"> elements whose only text content is
        the Cyrillic fullName. We look up the name from the cache populated
        by search_companies(), then match on the first ~40 characters.
        """
        full_name = self._leid_to_name.get(leid, "")
        if not full_name:
            raise asyncio.TimeoutError(f"leid {leid} not in search cache — run search_companies first")

        snippet = full_name[:40].replace("'", "\\'")
        row = self._page.locator(f"tr[tabindex='0']:has-text('{snippet}')").first
        await row.wait_for(state="visible", timeout=5_000)
        await row.click()

    # ── Public tool methods ───────────────────────────────────────────────────

    async def search_companies(self, name: str) -> list[dict]:
        """
        Search for companies by partial name.

        Navigates to the search page if not already there, types the query,
        and returns the list of matching companies from the intercepted XHR.

        Args:
            name: Partial or full company name (Cyrillic or Latin).

        Returns:
            List of dicts — each has: fullName, fullNameLat, leid, municipality.
            Empty list if no matches found.
            On error, returns a list with a single error dict.
        """
        if not self._ready:
            return [self._not_ready_error()]

        try:
            if SEARCH_PAGE_URL not in self._page.url:
                await self._page.goto(SEARCH_PAGE_URL, wait_until="networkidle")

            # Register the listener BEFORE typing so we don't race the response.
            response_task = asyncio.create_task(
                self._wait_for_api_response("basicProfile")
            )

            await self._fill_search_box(name)

            data = await response_task
            companies = data.get("companies", [])
            # Cache leid → fullName so _click_company_row() can find rows by text.
            for c in companies:
                self._leid_to_name[c["leid"]] = c["fullName"]
            return companies
        except asyncio.TimeoutError:
            return [tool_error("network_error", "crm.com.mk did not respond in time. Please try again.")]
        except Exception as exc:
            return [tool_error("unexpected_error", f"An unexpected error occurred while searching companies: {exc}")]

    async def get_company_details(self, leid: int) -> dict | str:
        """
        Get the full registration profile for a specific company.

        Navigates to ?embs={leid}, intercepts the basicProfile/{leid} response
        (a base64-encoded PNG), then uses Claude Vision to extract structured
        registration data from the image.

        Args:
            leid: Unique company ID from search_companies().

        Returns:
            Dict with: full_name, short_name, embс, edb, founded_date,
            legal_form, legal_status, address, primary_activity, company_size.
            Returns "Company not found" if the leid is invalid or times out.
        """
        if not self._ready:
            return self._not_ready_error()

        # The Angular app fires basicProfile/{leid}?sci={...} after navigation.
        # Response content-type is text/plain; body is a base64-encoded PNG —
        # not JSON — so we capture raw bytes instead of calling .json().
        loop = asyncio.get_event_loop()
        raw_future: asyncio.Future[bytes] = loop.create_future()

        async def handler(response: Response):
            if f"basicProfile/{leid}" in response.url and not raw_future.done():
                try:
                    raw_future.set_result(await response.body())
                except Exception as exc:
                    if not raw_future.done():
                        raw_future.set_exception(exc)

        self._page.on("response", handler)
        try:
            await self._page.goto(
                f"{SEARCH_PAGE_URL}?embs={leid}",
                wait_until="domcontentloaded",
            )
            raw_body = await asyncio.wait_for(
                asyncio.shield(raw_future),
                timeout=RESPONSE_TIMEOUT_MS / 1000,
            )
        except asyncio.TimeoutError:
            return tool_error("not_found", f"Company with ID {leid} was not found on crm.com.mk, or the page timed out.")
        except Exception as exc:
            return tool_error("unexpected_error", f"An unexpected error occurred while fetching company details: {exc}")
        finally:
            self._page.remove_listener("response", handler)

        # Decode: the body is usually base64 text, but guard against raw PNG too.
        if raw_body[:4] == b"\x89PNG":
            png_bytes = raw_body
        else:
            try:
                png_bytes = base64.b64decode(raw_body)
            except Exception:
                return tool_error("parse_error", "Received the company profile but could not decode the image data.")

        # Send the PNG to Gemini Vision and ask it to extract the table fields.
        try:
            ai = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
            response = await asyncio.to_thread(
                ai.models.generate_content,
                model="gemini-2.0-flash",
                contents=[
                    genai_types.Part.from_bytes(data=png_bytes, mime_type="image/png"),
                    (
                        "This is a company registration record from the Central Registry "
                        "of North Macedonia (ЦРРСМ). Extract every visible field and "
                        "return them as a JSON object with English keys. "
                        "Return only valid JSON — no markdown fences, no other text.\n\n"
                        "Use these English key names:\n"
                        "  full_name, short_name, embs, edb, founded_date,\n"
                        "  legal_form, legal_status, address, primary_activity, company_size"
                    ),
                ],
            )
        except Exception as exc:
            return tool_error("unexpected_error", f"Failed to extract company data from the profile image: {exc}")

        text = response.text.strip()
        # Strip markdown code fences if the model adds them despite the instruction.
        if text.startswith("```"):
            lines = text.splitlines()
            text = "\n".join(ln for ln in lines if not ln.startswith("```")).strip()

        try:
            return json.loads(text)
        except json.JSONDecodeError:
            return {"raw_extraction": text}

    async def get_founders_and_directors(self, leid: int) -> list[dict] | str:
        """
        Get founders, directors, and other associated persons for a company.

        Args:
            leid: Unique company ID from search_companies().

        Returns:
            Not available on the public free tier of crm.com.mk.
            Professional (paid) access is required for persons data.
        """
        return (
            "Founders and directors data is not available on the free public tier "
            "of crm.com.mk. Professional access is required."
        )

    async def get_annual_reports(self, leid: int) -> list[dict] | str:
        """
        Get available annual reports and financial data for a company.

        Args:
            leid: Unique company ID from search_companies().

        Returns:
            Not available on the public free tier of crm.com.mk.
            Professional (paid) access is required for annual reports.
        """
        return (
            "Annual reports are not available on the free public tier "
            "of crm.com.mk. Professional access is required."
        )


# ── Module-level singleton ────────────────────────────────────────────────────
# main.py imports this and calls await crm_browser.start() / .stop()
# on server startup / shutdown via FastMCP lifespan hooks.

crm_browser = CRMBrowserClient()
