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
def check_session_mon() -> dict:
    """
    Check whether an active MON session exists (local check, no network).

    Call this FIRST before login_mon() — if a session is already active,
    there is no need to open a browser. Also call before any tool that
    requires authentication (get_mon_service_requirements).

    Returns:
        { "active": bool, "saved_at": str | None, "message": str }
        On error: { "error": true, "code": str, "message": str }
    """
    return _check_session()


@mcp.tool()
def login_mon() -> dict:
    """
    Log in to e-uslugi.mon.gov.mk via browser and save the session.

    Call this ONLY when check_session_mon() reports no active session AND
    the user needs an authenticated action (e.g. get_mon_service_requirements).
    Do NOT call without user consent — it opens a visible Chromium window.

    Returns:
        { "success": bool, "message": str }
        On error: { "error": true, "code": str, "message": str }
    """
    return _login()


@mcp.tool()
def logout_mon() -> dict:
    """
    Log out of e-uslugi.mon.gov.mk by deleting the stored session.

    Call this ONLY when the user explicitly asks to log out.
    No network request is made — this only deletes local session files.

    Returns:
        { "success": bool, "message": str }
        On error: { "error": true, "code": str, "message": str }
    """
    return _logout()


# ═══════════════════════════════════════════════════════════════════════════════
# SERVICE TOOLS
# ═══════════════════════════════════════════════════════════════════════════════

@mcp.tool()
def list_mon_services(page: int = 0, size: int = 20) -> dict:
    """
    List active MON services and contests from e-uslugi.mon.gov.mk.

    Call this when the user asks what services or competitions are currently
    open at the Ministry of Education. No login required.
    Do NOT confuse with list_mon_document_types — that tool is for official
    education documents (diplomas, transcripts, certificates), not services.
    Never call both in the same turn unless the user explicitly asked for both.

    Args:
        page: Page number (0-based). Default 0.
        size: Results per page. Default 20.

    Returns:
        {
            "services": list of { id, name, reference_number, active_from,
                                   active_to, apply_url },
            "count": int
        }
        On error: { "error": true, "code": str, "message": str }
    """
    return _list_mon_services(page=page, size=size)


@mcp.tool()
def get_mon_service_requirements(service_id: int) -> dict:
    """
    Get what documents are required to apply for a specific MON service or contest.

    Prerequisite: call list_mon_services() to get the service_id, then call
    check_session_mon() and login_mon() if the session is inactive.
    Requires an active MON session — do NOT call without authentication.
    Do NOT call this just to confirm a service exists; use list_mon_services for that.

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
        On error: { "error": true, "code": str, "message": str }
    """
    return _get_mon_service_requirements(service_id=service_id)


# ═══════════════════════════════════════════════════════════════════════════════
# DOCUMENT TOOLS
# ═══════════════════════════════════════════════════════════════════════════════

@mcp.tool()
def list_mon_document_types() -> dict:
    """
    List the types of official education documents obtainable through MON or a
    higher-education institution (e.g. enrollment certificate, diploma, transcript).

    Call this when the user asks about education documents — certificates,
    diplomas, transcript of records, scholarship confirmations, or diploma
    recognition. Do NOT confuse with list_mon_services — that tool lists
    active MON services and competitions, not document types.

    No login required.

    Returns:
        { "document_types": list of { type, name, description } }
        On error: { "error": true, "code": str, "message": str }
    """
    return _list_mon_document_types()


@mcp.tool()
def get_mon_document_requirements(document_type: str) -> dict:
    """
    Get the requirements (documents, conditions, fees, where to apply) for
    obtaining a specific official education document.

    Prerequisite: call list_mon_document_types() to get the valid type key,
    then pass it here. Do NOT guess type keys — only use values returned by
    list_mon_document_types(). No login required.

    Args:
        document_type: Type key from list_mon_document_types(). Examples:
            "потврда_за_запис"     — Certificate of enrollment
            "уверение_за_завршено" — Graduation certificate
            "нострификација"       — Diploma recognition (nostrification)
            "уверение_стипендија"  — Scholarship confirmation
            "уверение_оценки"      — Transcript of records

    Returns:
        { document_type, name, description, documents_required, conditions,
          fee, where_to_apply }
        On error: { "error": true, "code": str, "message": str }
    """
    return _get_mon_document_requirements(document_type=document_type)


# ── Entry point ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    mcp.run()
