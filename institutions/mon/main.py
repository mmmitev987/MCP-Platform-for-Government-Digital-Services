"""
institutions/mon/main.py
────────────────────────────────────────────────────────────────────────────────
FastMCP server entry point for the Ministry of Education and Science (MON).
Uses e-uslugi.mon.gov.mk (REST API, JWT auth).

Run standalone for testing:
    python -m institutions.mon.main

Tools exposed (gateway will prefix them with "mon__"):
  Session:    login_mon, logout_mon, check_session_mon
  Services:   list_mon_services, get_mon_service_requirements
  Documents:  list_mon_document_types, get_mon_document_requirements
"""

from mcp.server.fastmcp import FastMCP

from institutions.mon.tools.session_tools import (
    login as _login,
    logout as _logout,
    check_session as _check_session,
)
from institutions.mon.tools.apply_tools import (
    list_mon_services as _list_mon_services,
    get_mon_service_requirements as _get_mon_service_requirements,
)
from institutions.mon.tools.document_tools import (
    list_mon_document_types as _list_mon_document_types,
    get_mon_document_requirements as _get_mon_document_requirements,
)

mcp = FastMCP("mon-gov-mk")


# ═══════════════════════════════════════════════════════════════════════════════
# SESSION TOOLS
# ═══════════════════════════════════════════════════════════════════════════════

@mcp.tool()
def login_mon() -> dict:
    """
    Log in to e-uslugi.mon.gov.mk via browser and save the session.

    Opens a Chromium window for the user to complete login.
    Required before calling get_mon_service_requirements.

    Returns:
        { "success": bool, "message": str }
    """
    return _login()


@mcp.tool()
def logout_mon() -> dict:
    """
    Log out of e-uslugi.mon.gov.mk by deleting the stored session.

    Returns:
        { "success": bool, "message": str }
    """
    return _logout()


@mcp.tool()
def check_session_mon() -> dict:
    """
    Check whether an active MON session exists.

    Returns:
        { "active": bool, "saved_at": str | None, "message": str }
    """
    return _check_session()


# ═══════════════════════════════════════════════════════════════════════════════
# SERVICE TOOLS
# ═══════════════════════════════════════════════════════════════════════════════

@mcp.tool()
def list_mon_services(page: int = 0, size: int = 20) -> dict:
    """
    List all currently active MON services and contests from e-uslugi.mon.gov.mk.

    No login required.

    Args:
        page: Page number (0-based). Default 0.
        size: Results per page. Default 20.

    Returns:
        { "services": list of { id, name, reference_number, active_from, active_to, apply_url }, "count": int }
    """
    return _list_mon_services(page=page, size=size)


@mcp.tool()
def get_mon_service_requirements(service_id: int) -> dict:
    """
    Find out what you need in order to apply for a specific MON service or contest.

    Returns the service name, application period, whether you can currently
    apply, and the list of documents you need to upload.

    Requires an active MON session — call login_mon() first.

    Args:
        service_id: Numeric ID from list_mon_services().

    Returns:
        {
            "service_id":         int,
            "name":               str,
            "reference_number":   str,
            "active_from":        str,
            "active_to":          str,
            "can_apply":          bool,
            "documents_required": list[str],
            "apply_url":          str,
        }
    """
    return _get_mon_service_requirements(service_id=service_id)


# ═══════════════════════════════════════════════════════════════════════════════
# DOCUMENT TOOLS
# ═══════════════════════════════════════════════════════════════════════════════

@mcp.tool()
def list_mon_document_types() -> dict:
    """
    List official document types obtainable through MON or a higher-education
    institution, with a brief description of each.

    No login required.

    Returns:
        { "document_types": list of { type, name, description } }
    """
    return _list_mon_document_types()


@mcp.tool()
def get_mon_document_requirements(document_type: str) -> dict:
    """
    Find out what you need in order to obtain a specific official document
    from MON or a higher-education institution.

    No login required.

    Args:
        document_type: Type key from list_mon_document_types(). Examples:
            "потврда_за_запис"     — Certificate of enrollment
            "уверение_за_завршено" — Graduation certificate
            "нострификација"       — Diploma recognition
            "уверение_стипендија"  — Scholarship confirmation
            "уверение_оценки"      — Transcript of records

    Returns:
        { document_type, name, description, documents_required, conditions, fee, where_to_apply }
    """
    return _get_mon_document_requirements(document_type=document_type)


# ── Entry point ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    mcp.run()
