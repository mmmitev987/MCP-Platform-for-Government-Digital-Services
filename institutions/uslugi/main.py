"""
institutions/uslugi/main.py
────────────────────────────────────────────────────────────────────────────────
FastMCP server entry point for uslugi.gov.mk.
"""

from mcp.server.fastmcp import FastMCP

from institutions.uslugi.tools.passport import info_passport_renewal as _info_passport_renewal
from institutions.uslugi.tools.session_tools import (
    login as _login,
    logout as _logout,
    check_session as _check_session,
)
from institutions.uslugi.tools.discovery import (
    search_portal as _search,
    get_group_contents as _get_group,
    get_service_details as _get_details,
    list_all_services as _list_all_services,
)

mcp = FastMCP("uslugi-gov-mk")


# ═══════════════════════════════════════════════════════════════════════════════
# SESSION TOOLS
# ═══════════════════════════════════════════════════════════════════════════════

@mcp.tool()
def login() -> dict:
    """
    Open a browser window so the user can log in to uslugi.gov.mk via eid.mk SSO.

    Call this only when the user explicitly asks to log in, or when
    check_session() reports no active session and an authenticated action
    is needed. Do NOT call without user consent — it opens a visible browser.

    Returns:
        { "success": bool, "message": str, "strategy_used": str, "cookies_saved": int }
        On error: { "error": true, "code": str, "message": str }
    """
    return _login()


@mcp.tool()
def logout() -> dict:
    """
    Log out of uslugi.gov.mk by deleting the saved session cookies.

    Call this only when the user explicitly asks to log out.
    No network request is made — this only deletes local cookie files.

    Returns:
        { "success": bool, "message": str }
        On error: { "error": true, "code": str, "message": str }
    """
    return _logout()


@mcp.tool()
def check_session() -> dict:
    """
    Check whether the user is currently logged in to uslugi.gov.mk (local check, no network).

    Call this before login() to avoid opening the browser unnecessarily.
    Also useful before any tool that requires authentication.

    Returns:
        { "active": bool, "saved_at": str | None, "message": str }
        On error: { "error": true, "code": str, "message": str }
    """
    return _check_session()


# ═══════════════════════════════════════════════════════════════════════════════
# PUBLIC INFORMATION TOOLS  (no login required)
# ═══════════════════════════════════════════════════════════════════════════════

@mcp.tool()
def search_services(query: str) -> list[dict]:
    """
    Search uslugi.gov.mk for a government service by keyword. Always call this FIRST.

    IMPORTANT — query MUST be in Macedonian Cyrillic, never Latin or English:
      "пасош"           (passport)
      "лична карта"     (ID card)
      "возачка дозвола" (driver licence)
      "регистрација возило" (vehicle registration)

    If a result has is_group: true, you MUST call get_group_contents(id) next
    to see the individual services inside that category.

    If results are empty or irrelevant, fall back to list_all_services().
    Never call both search_services AND list_all_services for the same query.

    Returns:
        List of { id, name, is_group, intro }.
        On error: [{ "error": true, "code": str, "message": str }]
    """
    return _search(query)


@mcp.tool()
def get_group_contents(group_id: int) -> list[dict]:
    """
    Expand a service category to reveal its individual services.

    Call this ONLY when search_services returns a result where is_group is true.
    Pass the id from that search result. Do NOT call speculatively.

    Returns:
        List of { id, name, is_electronic, intro }.
        On error: [{ "error": true, "code": str, "message": str }]
    """
    return _get_group(group_id)


@mcp.tool()
def list_all_services() -> str | dict:
    """
    Fallback: return the complete list of all ~1000 services on uslugi.gov.mk as plain text.

    Each line is: ID — service name (Macedonian Cyrillic).

    Use ONLY when search_services returned 0 relevant results. This response is
    large — after calling it, identify the correct service ID and call
    get_service_requirements(id) directly. Never call this if search_services
    already found relevant results.

    Returns:
        Plain-text string with one service per line.
        On error: { "error": true, "code": str, "message": str }
    """
    return _list_all_services()


@mcp.tool()
def get_service_requirements(service_id: int) -> dict:
    """
    Get the required documents, fees, deadline, and application link for a specific service.

    Call this ONLY once you have a confirmed numeric service ID from either
    search_services or list_all_services. Do NOT call just to verify a service
    exists — use search_services for that.

    No login required — all service details are publicly accessible.

    Returns:
        {
            id, name, description, is_electronic,
            requirements: list[str],   # documents to bring
            conditions:   list[str],   # eligibility conditions
            prices:       list[{ label, amount, currency }],
            deadline_days: int | null,
            institution:  str,         # responsible government body
            applyUrl:     str | null,  # link to apply online (null = in-person only)
        }
        On error: { "error": true, "code": str, "message": str }
    """
    return _get_details(service_id)


# ── Entry point ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    mcp.run()
