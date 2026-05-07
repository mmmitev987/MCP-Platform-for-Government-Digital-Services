"""
institutions/mojtermin/main.py
────────────────────────────────────────────────────────────────────────────────
FastMCP server entry point for mojtermin.mk.

Exposes all mojtermin tools via the MCP stdio transport.  Designed to run as
a subprocess under gateway/main.py, but also works standalone for testing:

    python -m institutions.mojtermin.main

Tools exposed (the gateway will prefix them with "mojtermin__"):
  Public:   get_locations, get_location_by_name, get_specialties,
            get_doctors, get_doctors_by_city,
            get_available_appointments_by_name

Adding new tools:
  1. Implement the function in institutions/mojtermin/tools/<file>.py.
  2. Import it here and wrap it with @mcp.tool().
  3. Write a clear docstring — the LLM reads it to decide when to call the tool.
"""

from mcp.server.fastmcp import FastMCP

# ── Tool implementations ──────────────────────────────────────────────────────
from institutions.mojtermin.tools.appointments import (
    get_locations as _get_locations,
    get_location_by_name as _get_location_by_name,
    get_specialties as _get_specialties,
    get_doctors as _get_doctors,
    get_doctors_by_city as _get_doctors_by_city,
    get_available_appointments_by_name as _get_available_appointments_by_name,
)

# ── FastMCP server ────────────────────────────────────────────────────────────
mcp = FastMCP("mojtermin-mk")


# ═══════════════════════════════════════════════════════════════════════════════
# PUBLIC TOOLS (no auth required)
# ═══════════════════════════════════════════════════════════════════════════════

@mcp.tool()
def get_locations() -> dict:
    """
    Return ALL clinic/office locations registered on mojtermin.mk as a raw dict.

    Call this ONLY when the user explicitly asks for a list of all clinic
    locations or wants to browse every location on the portal.
    Do NOT call this just to find doctors in a city — use get_doctors_by_city
    for that. Do NOT call this before get_available_appointments_by_name —
    city name is passed directly there.

    No login required. Results are large (entire location catalogue).

    Returns:
        Dict keyed by location ID, each value containing location metadata
        (name, address, city, etc.) as returned by the API.
        On error: { "error": true, "code": str, "message": str }
    """
    return _get_locations()


@mcp.tool()
def get_location_by_name(name: str) -> dict | None:
    """
    Find a single clinic/location whose name contains the given string.

    Call this ONLY when the user names a specific clinic and wants its
    address, ID, or other metadata. Do NOT call this to find doctors —
    use get_doctors_by_city instead.

    No login required.

    Args:
        name: Partial or full clinic name, case-insensitive. Examples:
            "СТРУГА"      — finds any location whose name contains "Струга"
            "СКОПЈЕ"      — finds any location in Skopje
            "Здравствен"  — finds health centres

    Returns:
        The location dict if found, or None if no match.
        On error: { "error": true, "code": str, "message": str }
    """
    return _get_location_by_name(name=name)


@mcp.tool()
def get_specialties() -> list[str]:
    """
    Return a list of all medical specialties available on mojtermin.mk.

    Call this ONLY when the user asks what medical specialties or disciplines
    are offered on the portal. Do NOT call this when the user already knows
    their specialty and just wants to find a doctor or book an appointment.

    No login required.

    Returns:
        List of specialty name strings (e.g. "Општа медицина", "Педијатрија").
        On error: [{ "error": true, "code": str, "message": str }]
    """
    return _get_specialties()


@mcp.tool()
def get_doctors() -> list[str]:
    """
    Return a sorted list of ALL doctor names across the entire portal.

    EXPENSIVE — fetches every location and doctor. Call this ONLY when the
    user has not mentioned any city. If the user mentions a city, always
    prefer get_doctors_by_city(city_name) instead — it is much faster and
    returns clinic information as well.

    Never call both get_doctors and get_doctors_by_city for the same request.

    No login required.

    Returns:
        List of doctor name strings in UPPERCASE (e.g. "ЛИЛЈАНА СПАСЕВСКА").
        On error: [{ "error": true, "code": str, "message": str }]
    """
    return _get_doctors()


@mcp.tool()
def get_doctors_by_city(city_name: str) -> list[dict]:
    """
    Return all doctors in a specific city, together with their clinic name.

    Call this whenever the user mentions a city — it is faster and more
    informative than get_doctors(). Always prefer this over get_doctors()
    when a city is known. Never call both tools for the same request.

    No login required.

    Args:
        city_name: City name in UPPERCASE Macedonian. Examples:
            "СКОПЈЕ"   — Skopje
            "СТРУГА"   — Struga
            "БИТОЛА"   — Bitola
            "ТЕТОВО"   — Tetovo

    Returns:
        List of dicts, each with keys: "doctor", "clinic", "city".
        Sorted alphabetically by doctor name.
        On error: [{ "error": true, "code": str, "message": str }]
    """
    return _get_doctors_by_city(city_name=city_name)


@mcp.tool()
def get_available_appointments_by_name(city: str, doctor_name: str, date: str) -> dict | str:
    """
    Return available appointment time slots for a specific doctor on a given date.

    Call this ONLY when the user explicitly wants to book an appointment or
    check available slots — not just to find a doctor. You must know the
    doctor's name and city before calling this; use get_doctors_by_city first
    if you don't. Never call this speculatively.

    No login required.

    Args:
        city:        City name in UPPERCASE, e.g. "СТРУГА", "СКОПЈЕ".
        doctor_name: Full or partial doctor name in UPPERCASE,
                     e.g. "ЛИЛЈАНА СПАСЕВСКА".
        date:        Date in YYYY-MM-DD format, e.g. "2026-05-15".

    Returns:
        Dict with keys "doctor", "date", "available_slots" (list of "HH:MM").
        On error: { "error": true, "code": str, "message": str }
    """
    return _get_available_appointments_by_name(city=city, doctor_name=doctor_name, date=date)


# ── Entry point ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    mcp.run()
