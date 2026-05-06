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
            get_available_appointments_by_name,
            get_clinics, get_resources_by_city, search_resources,
            get_available_slots, get_slots_range, get_first_available,
            get_availability_summary, get_slots_for_city

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
from institutions.mojtermin.tools.resources import (
    get_clinics as _get_clinics,
    get_resources_by_city as _get_resources_by_city,
    search_resources as _search_resources,
)
from institutions.mojtermin.tools.slots import (
    get_available_slots as _get_available_slots,
    get_slots_range as _get_slots_range,
    get_first_available as _get_first_available,
    get_availability_summary as _get_availability_summary,
    get_slots_for_city as _get_slots_for_city,
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
        List of doctor name strings (2-3 fully uppercase words).
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


@mcp.tool()
def get_clinics() -> list[dict]:
    """
    Return all clinics registered on mojtermin.mk with their city info.

    No login required.

    Returns:
        Sorted list of dicts with keys: "clinic", "clinic_id", "city", "city_id".
    """
    return _get_clinics()


@mcp.tool()
def get_resources_by_city(city_name: str) -> list[dict]:
    """
    Return all resources (doctors and institutions) in a given city.

    No login required.

    Args:
        city_name: City to filter by, e.g. "Скопје" or "Skopje". Case-insensitive,
                   supports Latin input that matches Cyrillic names.

    Returns:
        Sorted list of dicts with keys: "name", "id", "kind" ("doctor" or
        "institution"), "clinic", "city".
    """
    return _get_resources_by_city(city_name=city_name)


@mcp.tool()
def search_resources(query: str) -> list[dict]:
    """
    Search all resources (clinics, doctors, rooms, institutions) by name.

    Uses case-insensitive matching with Latin-to-Cyrillic normalization, so
    searching for "struga" will match "Струга" in the database.

    No login required.

    Args:
        query: Partial name to search for, e.g. "Кардио" or "Kardio".

    Returns:
        List of matching resource nodes from the nav tree (each node has at
        least "name" and "id" keys, plus optional "type", "subsections", etc.).
    """
    return _search_resources(query=query)


@mcp.tool()
def get_available_slots(name: str, date: str) -> dict:
    """
    Return available appointment slots for a named resource on a specific date.

    Works with doctors, clinics, and any other resource on mojtermin.mk.

    No login required.

    Args:
        name: Resource name, e.g. "Амбуланта по интерна медицина- ЗД Ресен"
              or a doctor name like "ЛИЛЈАНА СПАСЕВСКА".
        date: Date in YYYY-MM-DD format, e.g. "2026-04-11".

    Returns:
        Dict with keys "resource", "resource_id", "date", "available_slots"
        (list of "HH:MM" strings). If resource not found, returns an error dict.
    """
    return _get_available_slots(name=name, date=date)


@mcp.tool()
def get_slots_range(name: str, start_date: str, end_date: str) -> dict:
    """
    Return available slots for a resource across a date range (inclusive).

    No login required.

    Args:
        name:       Resource name (doctor or institution).
        start_date: Start date in YYYY-MM-DD format.
        end_date:   End date in YYYY-MM-DD format.

    Returns:
        Dict with keys "resource", "resource_id", "slots_by_date" (dict mapping
        each date with slots to a list of "HH:MM" strings).
    """
    return _get_slots_range(name=name, start_date=start_date, end_date=end_date)


@mcp.tool()
def get_first_available(name: str, days_ahead: int = 30) -> dict:
    """
    Find the earliest available appointment slot for a resource.

    No login required.

    Args:
        name:       Resource name (doctor or institution).
        days_ahead: How many days into the future to search (default 30).

    Returns:
        Dict with keys "resource", "resource_id", "date", "time" for the first
        available slot, or a message dict if no slots found within the window.
    """
    return _get_first_available(name=name, days_ahead=days_ahead)


@mcp.tool()
def get_availability_summary(name: str, days_ahead: int = 14) -> dict:
    """
    Return a day-by-day count of available slots for a resource.

    Useful for a mini-calendar view of availability density.

    No login required.

    Args:
        name:       Resource name (doctor or institution).
        days_ahead: Number of days to include starting from today (default 14).

    Returns:
        Dict with keys "resource", "resource_id", "summary" (list of
        {"date": str, "count": int} for each day).
    """
    return _get_availability_summary(name=name, days_ahead=days_ahead)


@mcp.tool()
def get_slots_for_city(city_name: str, date: str) -> list[dict]:
    """
    Return available slots for all resources in a city on a given date.

    Queries every doctor and institution under the city and aggregates results.
    May be slow for large cities as each resource makes a separate API call.

    No login required.

    Args:
        city_name: City name, e.g. "Скопје" or "Skopje" (Latin supported).
        date:      Date in YYYY-MM-DD format.

    Returns:
        List of dicts with keys "resource", "resource_id", "clinic", "slots"
        (list of "HH:MM" strings). Only resources with at least one slot are included.
    """
    return _get_slots_for_city(city_name=city_name, date=date)


# ── Entry point ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    mcp.run()
