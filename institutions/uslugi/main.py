"""
institutions/uslugi/main.py
────────────────────────────────────────────────────────────────────────────────
FastMCP server entry point for uslugi.gov.mk.

This file wires together all tools for this institution and exposes them via
the MCP stdio transport.  It is designed to be run as a subprocess by the
gateway (gateway/main.py), but can also be run standalone for testing:

    python -m institutions.uslugi.main

Architecture in context:
  gateway/main.py
    └── spawns this as a subprocess
    └── connects via MCP stdio
    └── exposes tools to the agent under the "uslugi__" namespace

Adding new tools:
  1. Create the tool function in institutions/uslugi/tools/<file>.py.
  2. Import it here and decorate the wrapper with @mcp.tool().
  3. Write a clear docstring — it becomes the tool description shown to the LLM.
"""

from mcp.server.fastmcp import FastMCP

# ── Tool implementations ──────────────────────────────────────────────────────
from institutions.uslugi.tools.passport import info_passport_renewal as _info_passport_renewal
from institutions.uslugi.tools.session_tools import (
    login as _login,
    logout as _logout,
    check_session as _check_session,
)
# Import the new Discovery Logic
from institutions.uslugi.tools.discovery import (
    search_portal as _search,
    get_group_contents as _get_group,
    get_service_details as _get_details
)

# ── Create the FastMCP server instance ───────────────────────────────────────
# The name here is only used in MCP handshake metadata — it is NOT the
# tool prefix.  The gateway adds the "uslugi__" prefix when it registers
# these tools in its own namespace.
mcp = FastMCP("uslugi-gov-mk")


# ═══════════════════════════════════════════════════════════════════════════════
# SESSION TOOLS
# Control the authentication lifecycle.  The LLM can call these but never
# sees passwords or raw cookie values.
# ═══════════════════════════════════════════════════════════════════════════════

@mcp.tool()
def login() -> dict:
    """
    Authenticate the user on uslugi.gov.mk via browser and save the session.

    Opens a Chromium window for the user to complete the eid.mk SSO login.

    Returns:
        { "success": bool, "message": str, "strategy_used": str, "cookies_saved": int }
    """
    return _login()


@mcp.tool()
def logout() -> dict:
    """
    Log out of uslugi.gov.mk by deleting the stored session cookies.

    Returns:
        { "success": bool, "message": str }
    """
    return _logout()


@mcp.tool()
def check_session() -> dict:
    """
    Check whether an active session exists for uslugi.gov.mk.

    This is a local file check — it does NOT make a network request.
    Call this before authenticated requests to surface a friendly error
    instead of an unexpected HTTP failure.

    Returns:
        { "active": bool, "saved_at": str | None, "message": str }
    """
    return _check_session()


# ═══════════════════════════════════════════════════════════════════════════════
# PUBLIC INFORMATION TOOLS
# These do not require authentication.
# ═══════════════════════════════════════════════════════════════════════════════

@mcp.tool()
def info_passport_renewal() -> dict:
    """
    Fetch detailed information about the passport renewal service (ID 5200)
    from uslugi.gov.mk.

    No login required — this endpoint is publicly accessible.

    Returns a dict with:
        name, description, requirements, conditions, deadlines,
        delivery_in, delivery_out, contact, applyUrl.
    """
    return _info_passport_renewal()


@mcp.tool()
def search_services(query: str) -> list[dict]:
    """
    Search the portal for services (e.g., 'passport', 'driver license').
    Returns a list of results. If a result has 'is_group': true,
    you MUST call get_group_contents(id) to see the specific services inside.
    """
    return _search(query)

@mcp.tool()
def get_group_contents(group_id: int) -> list[dict]:
    """
    Lists all specific services within a service category/group.
    Call this when search_services indicates a result is a group.
    """
    return _get_group(group_id)

@mcp.tool()
def get_service_requirements(service_id: int) -> dict:
    """
    Fetches the documents, price, and application link for a specific service ID.
    Call this once you have identified the exact service the user wants.
    """
    return _get_details(service_id)

# ── Entry point ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    # mcp.run() starts the stdio transport loop.
    # This process will block, reading MCP JSON-RPC from stdin and writing
    # responses to stdout until the parent process (the gateway) closes the pipe.
    mcp.run()

# sakam da apliciram za izvod
# llm
#