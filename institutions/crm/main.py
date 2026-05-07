"""
institutions/crm/main.py
────────────────────────────────────────────────────────────────────────────────
FastMCP server entry point for crm.com.mk (Central Registry of North Macedonia).

Architecture in context:
  gateway/main.py
    └── spawns this as a subprocess
    └── connects via MCP stdio
    └── exposes tools to the agent under the "crm__" namespace

Key difference from uslugi:
  uslugi uses Playwright once for a manual SSO login and saves cookies to disk.
  CRM requires a live browser for every request because reCAPTCHA fires on each
  API call. We start ONE persistent Chromium instance on server startup (via the
  FastMCP lifespan hook) and reuse it for the entire lifetime of this process.
  No cookies are saved to disk — no login flow is needed.

Standalone test:
    python -m institutions.crm.main
"""

from contextlib import asynccontextmanager

from mcp.server.fastmcp import FastMCP

from institutions.crm.client.browser import crm_browser


# ── Lifespan: start and stop the persistent browser ───────────────────────────

@asynccontextmanager
async def lifespan(server: FastMCP):
    """
    Start the Playwright browser when the MCP server starts,
    and close it cleanly when the server shuts down.

    This runs once per process — the browser is shared across all tool calls.
    """
    await crm_browser.start()
    try:
        yield
    finally:
        await crm_browser.stop()


# ── Create the FastMCP server instance ───────────────────────────────────────

mcp = FastMCP("crm-com-mk", lifespan=lifespan)


# ═══════════════════════════════════════════════════════════════════════════════
# COMPANY TOOLS
# All public — no login required.
# reCAPTCHA is handled transparently by the Playwright browser.
# ═══════════════════════════════════════════════════════════════════════════════

@mcp.tool()
async def search_companies(name: str) -> list[dict]:
    """
    Search for registered companies in the Central Registry by name. Always call
    this FIRST — every other CRM tool requires the leid returned here.

    Supports partial name matching in both Cyrillic and Latin script.
    reCAPTCHA is handled automatically by the internal Playwright browser.
    No login required.

    Args:
        name: Full or partial company name. Examples:
            "Бисера"   — Cyrillic partial name
            "Bisera"   — Latin transliteration also works
            "МКД"      — abbreviation search

    Returns:
        List of matching companies, each with:
            - fullName      Full legal name (Cyrillic)
            - fullNameLat   Full legal name (Latin)
            - leid          Unique company ID — required by all follow-up tools
            - municipality  Municipality of registration
        On error: [{ "error": true, "code": str, "message": str }]
    """
    return await crm_browser.search_companies(name)


@mcp.tool()
async def get_company_details(leid: int) -> dict:
    """
    Get the full registration profile for a company (address, status, legal form,
    registration number, business activity).

    Prerequisite: call search_companies() first to obtain the leid.
    Call this when the user asks for general company information.
    Do NOT call this if the user asked specifically about people/ownership
    (use get_founders_and_directors) or finances (use get_annual_reports).
    Never call more than one detail tool unless the user explicitly asked for both.

    No login required.

    Args:
        leid: Unique company ID from search_companies().

    Returns:
        Dict with full registration details: address, status, registration
        number, legal form, and business activity.
        On error: { "error": true, "code": str, "message": str }
    """
    return await crm_browser.get_company_details(leid)


@mcp.tool()
async def get_founders_and_directors(leid: int) -> list[dict]:
    """
    Get founders, directors, and other associated persons for a company.

    Prerequisite: call search_companies() first to obtain the leid.
    Call this ONLY when the user asks about people — ownership, founders,
    directors, or management. Do NOT call this for general company info
    (use get_company_details) or financial data (use get_annual_reports).

    IMPORTANT: This data is NOT available on the free public tier of crm.com.mk.
    If the registry does not expose it, the tool returns an error explaining
    that the data requires a paid subscription. Do NOT retry or call another
    tool — inform the user directly.

    No login required.

    Args:
        leid: Unique company ID from search_companies().

    Returns:
        List of associated persons with their role and identification details.
        On error: { "error": true, "code": str, "message": str }
    """
    return await crm_browser.get_founders_and_directors(leid)


@mcp.tool()
async def get_annual_reports(leid: int) -> list[dict]:
    """
    Get available annual reports and financial filing data for a company.

    Prerequisite: call search_companies() first to obtain the leid.
    Call this ONLY when the user asks about finances, annual reports, or
    financial statements. Do NOT call this for general info (get_company_details)
    or people/ownership (get_founders_and_directors).

    IMPORTANT: This data is NOT available on the free public tier of crm.com.mk.
    If the registry does not expose it, the tool returns an error explaining
    that the data requires a paid subscription. Do NOT retry or call another
    tool — inform the user directly.

    No login required.

    Args:
        leid: Unique company ID from search_companies().

    Returns:
        List of annual reports with year, filing status, dates, and links.
        On error: { "error": true, "code": str, "message": str }
    """
    return await crm_browser.get_annual_reports(leid)


# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    mcp.run()
