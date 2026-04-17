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
    Return all clinic/office locations registered on mojtermin.mk.

    No login required.

    Returns:
        Dict keyed by location ID, each value containing location metadata
        (name, address, etc.) as returned by the API.
    """
    return _get_locations()


@mcp.tool()
def get_location_by_name(name: str) -> dict | None:
    """
    Find a single location whose name contains the given string (case-insensitive).

    No login required.

    Args:
        name: Partial or full location name to search for, e.g. "СТРУГА".

    Returns:
        The location dict if found, or None if no match.
    """
    return _get_location_by_name(name=name)


@mcp.tool()
def get_specialties() -> list[str]:
    """
    Return a list of all medical specialties available on mojtermin.mk.

    No login required.

    Returns:
        List of specialty name strings.
    """
    return _get_specialties()


@mcp.tool()
def get_doctors() -> list[str]:
    """
    Return a sorted, deduplicated list of all doctor names across the entire portal.

    No login required.

    Returns:
        List of doctor name strings (2–3 fully uppercase words).
    """
    return _get_doctors()


@mcp.tool()
def get_doctors_by_city(city_name: str) -> list[dict]:
    """
    Return all doctors in a given city, along with their clinic name.

    No login required.

    Args:
        city_name: City to filter by, e.g. "СТРУГА". Case-insensitive.

    Returns:
        List of dicts, each with keys: "doctor", "clinic", "city".
        Sorted alphabetically by doctor name.
    """
    return _get_doctors_by_city(city_name=city_name)


@mcp.tool()
def get_available_appointments_by_name(city: str, doctor_name: str, date: str) -> dict | str:
    """
    Return available appointment slots for a specific doctor on a given date.

    No login required.

    Args:
        city:        City name to narrow the search, e.g. "СТРУГА".
        doctor_name: Full or partial doctor name, e.g. "ЛИЛЈАНА СПАСЕВСКА".
        date:        Date in YYYY-MM-DD format, e.g. "2026-04-11".

    Returns:
        Dict with keys "doctor", "date", "available_slots" (list of "HH:MM" strings),
        or the string "Doctor not found" if no match.
    """
    return _get_available_appointments_by_name(city=city, doctor_name=doctor_name, date=date)


# ── Entry point ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    mcp.run()
