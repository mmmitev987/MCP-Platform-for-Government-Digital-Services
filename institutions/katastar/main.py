"""
institutions/katastar/main.py
────────────────────────────────────────────────────────────────────────────────
FastMCP server entry point for e-uslugi.katastar.gov.mk.

This file wires together all tools for this institution and exposes them via
the MCP stdio transport.  It is designed to be run as a subprocess by the
gateway (gateway/main.py), but can also be run standalone for testing:

    python -m institutions.katastar.main

Architecture in context:
  gateway/main.py
    └── spawns this as a subprocess
    └── connects via MCP stdio
    └── exposes tools to the agent under the "katastar__" namespace

Adding new tools:
  1. Create the tool function in institutions/katastar/tools/<file>.py.
  2. Import it here and decorate the wrapper with @mcp.tool().
  3. Write a clear docstring — it becomes the tool description shown to the LLM.
"""

from mcp.server.fastmcp import FastMCP

# ── Tool implementations ──────────────────────────────────────────────────────
from institutions.katastar.tools.session_tools import (
    login          as _login,
    logout         as _logout,
    check_session  as _check_session,
)
from institutions.katastar.tools.imoten_list import (
    search_municipality       as _search_municipality,
    get_cadastre_department   as _get_cadastre_department,
    get_cadastre_municipality as _get_cadastre_municipality,
    find_parcels              as _find_parcels,
    check_property_favorited  as _check_property_favorited,
    find_buildings             as _find_buildings,
    get_total_parcel_area  as _get_total_parcel_area,

)

# ── Create the FastMCP server instance ────────────────────────────────────────
# The name here is only used in MCP handshake metadata — it is NOT the
# tool prefix.  The gateway adds the "katastar__" prefix when it registers
# these tools in its own namespace.
mcp = FastMCP("katastar-gov-mk")


# ═══════════════════════════════════════════════════════════════════════════════
# SESSION TOOLS
# ═══════════════════════════════════════════════════════════════════════════════

@mcp.tool()
def login() -> dict:
    """
    Authenticate the user on e-uslugi.katastar.gov.mk via browser and save the session.

    Opens a Chromium window for the user to enter their cadastre portal credentials.

    Returns:
        { "success": bool, "message": str, "strategy_used": str, "cookies_saved": int }
    """
    return _login()


@mcp.tool()
def logout() -> dict:
    """
    Log out of e-uslugi.katastar.gov.mk by deleting the stored session cookies.

    Returns:
        { "success": bool, "message": str }
    """
    return _logout()


@mcp.tool()
def check_session() -> dict:
    """
    Check whether an active session exists for e-uslugi.katastar.gov.mk.

    This is a local file check — it does NOT make a network request.
    Call this before authenticated requests to surface a friendly error
    instead of an unexpected HTTP failure.

    Returns:
        { "active": bool, "saved_at": str | None, "message": str }
    """
    return _check_session()


# ═══════════════════════════════════════════════════════════════════════════════
# ИМОТЕН ЛИСТ TOOLS
# These require authentication — call login() first.
# ═══════════════════════════════════════════════════════════════════════════════

@mcp.tool()
def search_municipality(search_string: str) -> dict:
    """
    Search for a cadastre municipality by name.

    Returns departmentID and municipalityID — required for all
    property certificate queries.

    Args:
        search_string: Municipality name, e.g. "КУМАНОВО", "SKOPJE", "БИТОЛА"
    """
    return _search_municipality(search_string)


@mcp.tool()
def get_cadastre_department(department_id: int) -> dict:
    """
    Return details for a cadastre department by its numeric ID.

    Args:
        department_id: e.g. 17 for Куманово.
    """
    return _get_cadastre_department(department_id)


@mcp.tool()
def get_cadastre_municipality(department_id: int, municipality_id: int) -> dict:
    """
    Return details for a specific cadastre municipality.

    Args:
        department_id:   e.g. 17
        municipality_id: e.g. 52
    """
    return _get_cadastre_municipality(department_id, municipality_id)


@mcp.tool()
def find_parcels(
    department_id: int,
    municipality_id: int,
    property_certificate: str,
    page: int = 0,
    size: int = 10,
) -> dict:
    """
    Return paginated parcels for a property certificate (имотен лист).

    Each parcel: parcelID, cadastre number, usage type, area (m²),
    location, propertyRight.

    Args:
        department_id:        e.g. 17
        municipality_id:      e.g. 52
        property_certificate: Imoten list number, e.g. "14"
        page:                 Zero-based page index (default 0)
        size:                 Results per page (default 10)
    """
    return _find_parcels(
        department_id, municipality_id, property_certificate, page, size
    )



@mcp.tool()
def check_property_favorited(property_certificate_id: int) -> dict:
    """
    Check if a property certificate is saved in the user's favorites.

    Args:
        property_certificate_id: Internal certificate ID, e.g. 591908.
    """
    return _check_property_favorited(property_certificate_id)


@mcp.tool()
def find_buildings(
    department_id: int,
    municipality_id: int,
    property_certificate: str,
    page: int = 0,
    size: int = 10,
) -> dict:
    """
    Return paginated buildings for a property certificate (имотен лист).

    Args:
        department_id:        e.g. 17
        municipality_id:      e.g. 52
        property_certificate: Imoten list number, e.g. "14"
        page:                 Zero-based page index (default 0)
        size:                 Results per page (default 10)
    """
    return _find_buildings(
        department_id, municipality_id, property_certificate, page, size
    )



@mcp.tool()
def get_total_parcel_area(
    department_id: int,
    municipality_id: int,
    property_certificate: str,
) -> dict:
    """
    Return document type and total parcel area for a property certificate.

    Args:
        department_id:        e.g. 17
        municipality_id:      e.g. 52
        property_certificate: Imoten list number, e.g. "14"
    """
    return _get_total_parcel_area(
        department_id, municipality_id, property_certificate
    )

# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    mcp.run()