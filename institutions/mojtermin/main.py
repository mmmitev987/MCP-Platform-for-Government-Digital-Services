"""
institutions/mojtermin/main.py
────────────────────────────────────────────────────────────────────────────────
FastMCP server entry point for mojtermin.mk.

Exposes all mojtermin tools via the MCP stdio transport.  Designed to run as
a subprocess under gateway/main.py, but also works standalone for testing:

    python -m institutions.mojtermin.main

Tools exposed (the gateway will prefix them with "mojtermin__"):
  Public:   get_locations, get_location_by_name, get_specialties,
            get_doctors,
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
from institutions.mojtermin.tools.institutions import (
    get_institution_types as _get_institution_types,
    get_institutions_by_type as _get_institutions_by_type,
    get_institution_info as _get_institution_info,
)
from institutions.mojtermin.tools.equipment import (
    get_equipment_types as _get_equipment_types,
    get_equipment_in_city as _get_equipment_in_city,
    get_equipment_slots as _get_equipment_slots,
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
    Do NOT call this just to find doctors in a city — use get_doctors
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
    use get_doctors instead.

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
def get_specialties() -> list[str]: # dobro na Cvetan
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
def get_doctors(city: str | None = None, specialty: str | None = None) -> list[dict]: # moe
    """
    Return doctors, optionally filtered by city and/or specialty.

    All combinations are supported:
      get_doctors()                              → all doctors portal-wide (EXPENSIVE)
      get_doctors(city="СКОПЈЕ")                → all doctors in Skopje
      get_doctors(specialty="Кардиологија")     → all cardiologists countrywide
      get_doctors(city="СКОПЈЕ",
                  specialty="Кардиологија")     → cardiologists in Skopje

    Always pass at least one filter when the user has provided any context
    (city or specialty). Only call with no arguments if the user explicitly
    wants a full portal-wide list.

    No login required.

    Args:
        city:      City name, case-insensitive, Latin input supported
                   (e.g. "Skopje" or "СКОПЈЕ"). Optional.
        specialty: Medical specialty, case-insensitive, Latin input supported
                   (e.g. "Kardiologija" or "Кардиологија"). Optional.

    Returns:
        Sorted list of dicts with keys: "doctor", "specialty", "clinic", "city".
        On error: { "error": true, "code": str, "message": str }
    """
    return _get_doctors(city=city, specialty=specialty)


@mcp.tool()
def get_available_appointments_by_name(doctor_name: str) -> dict | str: # popraveno od mene
    """
    Return all available appointment slots for a specific doctor, grouped by date.

    Call this ONLY when the user explicitly wants to check or book an appointment
    — not just to find a doctor. You must know the doctor's name before calling
    this; use get_doctors first if you don't. Never call this speculatively.

    No login required.

    Args:
        doctor_name: Full or partial doctor name in UPPERCASE,
                     e.g. "ЛИЛЈАНА СПАСЕВСКА".

    Returns:
        Dict with keys "doctor" and "slots_by_date" (date → list of "HH:MM").
        On error: { "error": true, "code": str, "message": str }
    """
    return _get_available_appointments_by_name(doctor_name=doctor_name)


# @mcp.tool()
# def get_clinics() -> list[dict]:# pregolema e funkcijava na Cvetan pagja llmot
#     """
#     Return all clinics registered on mojtermin.mk with their city info.
#
#     No login required.
#
#     Returns:
#         Sorted list of dicts with keys: "clinic", "clinic_id", "city", "city_id".
#     """
#     return _get_clinics()


@mcp.tool()
def get_resources_by_city(city_name: str) -> list[dict]: # mu raboti na Cvetan
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


# @mcp.tool()
# def search_resources(query: str) -> list[dict]:
#     """
#     Search all resources (clinics, doctors, rooms, institutions) by name.
#
#     Uses case-insensitive matching with Latin-to-Cyrillic normalization, so
#     searching for "struga" will match "Струга" in the database.
#
#     No login required.
#
#     Args:
#         query: Partial name to search for, e.g. "Кардио" or "Kardio".
#
#     Returns:
#         List of matching resource nodes from the nav tree (each node has at
#         least "name" and "id" keys, plus optional "type", "subsections", etc.).
#     """
#     return _search_resources(query=query)


# @mcp.tool()
# def get_available_slots(name: str, date: str) -> dict:
#     """
#     Return available appointment slots for a named resource on a specific date.
#
#     Works with doctors, clinics, and any other resource on mojtermin.mk.
#
#     No login required.
#
#     Args:
#         name: Resource name, e.g. "Амбуланта по интерна медицина- ЗД Ресен"
#               or a doctor name like "ЛИЛЈАНА СПАСЕВСКА".
#         date: Date in YYYY-MM-DD format, e.g. "2026-04-11".
#
#     Returns:
#         Dict with keys "resource", "resource_id", "date", "available_slots"
#         (list of "HH:MM" strings). If resource not found, returns an error dict.
#     """
#     return _get_available_slots(name=name, date=date)


@mcp.tool()
def get_slots_range(name: str, start_date: str, end_date: str) -> dict: # mu raboti na Cvetan
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
def get_first_available(name: str, days_ahead: int = 30) -> dict: # mu raboti na Cvetan
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


# @mcp.tool()
# def get_availability_summary(name: str, days_ahead: int = 14) -> dict:# ne raboti
#     """
#     Return a day-by-day count of available slots for a resource.
#
#     Useful for a mini-calendar view of availability density.
#
#     No login required.
#
#     Args:
#         name:       Resource name (doctor or institution).
#         days_ahead: Number of days to include starting from today (default 14).
#
#     Returns:
#         Dict with keys "resource", "resource_id", "summary" (list of
#         {"date": str, "count": int} for each day).
#     """
#     return _get_availability_summary(name=name, days_ahead=days_ahead)


@mcp.tool()
def get_slots_for_doctors_for_specific_city(city_name: str, date: str) -> list[dict]:# mu go promeniv imeto, a mu raboti
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


# ═══════════════════════════════════════════════════════════════════════════════
# INSTITUTION TOOLS
# ═══════════════════════════════════════════════════════════════════════════════

@mcp.tool()
def get_institution_types() -> list[str]:# od mene
    """
    Return all institution department type names available on mojtermin.mk.

    Call this when the user asks what types of institutions exist, or when
    they mention an institution type you are not sure about.

    No login required.

    Returns:
        List of department type name strings, e.g.:
        ["Универзитетски клиники", "Клинички болници", "Заводи", ...]
        On error: { "error": true, "code": str, "message": str }
    """
    return _get_institution_types()


@mcp.tool()
def get_institutions_by_type(type_name: str) -> list[dict]:# od mene
    """
    Return all institutions of a given department type.

    Call this when the user asks to list institutions of a specific type,
    e.g. "give me all university clinics" or "list all institutes".
    Use get_institution_types() first if you are unsure of the exact type name.

    No login required.

    Args:
        type_name: Department type name, e.g. "Универзитетски клиники" or
                   "Zavodi". Case-insensitive, Latin input supported.

    Returns:
        Sorted list of dicts with keys: "name", "id".
        On error: { "error": true, "code": str, "message": str }
    """
    return _get_institutions_by_type(type_name=type_name)


@mcp.tool()
def get_institution_info(name: str) -> dict:# od mene
    """
    Return contact information and sections for a specific institution.

    Call this when the user asks for the phone number, address, email, or
    working hours of a specific institution, or wants to see what doctors
    and ambulances are registered under it.
    Use get_institutions_by_type() first to find the exact name if needed.

    No login required.

    Args:
        name: Full or partial institution name, e.g. "УК за Нефрологија".
              Case-insensitive, Latin input supported.

    Returns:
        Dict with keys: "name", "phone", "street", "email", "workTime",
        "sections" (grouped lists of doctors, ambulances, equipment, etc.).
        On error: { "error": true, "code": str, "message": str }
    """
    return _get_institution_info(name=name)


# ═══════════════════════════════════════════════════════════════════════════════
# EQUIPMENT / APPARATUS TOOLS
# ═══════════════════════════════════════════════════════════════════════════════

@mcp.tool()
def get_equipment_types() -> list[str]:
    """
    Return all equipment/apparatus type names available on mojtermin.mk.

    Call this when the user asks what kinds of medical equipment or procedures
    exist on the portal (e.g. "what scans can I book?", "do they have MRI?").

    No login required.

    Returns:
        List of equipment type name strings, e.g.:
        ["ЕХО", "РТГ", "ЕЕГ", "Магнетна резонанца (МР)", "Гастроскопија", ...]
        On error: { "error": true, "code": str, "message": str }
    """
    return _get_equipment_types()


@mcp.tool()
def get_equipment_in_city(equipment_type: str, city: str | None = None) -> list[dict]:
    """
    Return all specific tools of a given equipment type, optionally filtered by city.

    Call this when the user wants to know where a certain type of equipment is
    available (e.g. "where can I get an ЕХО in Скопје?", "which hospitals in
    Битола have МР?"). If no city is given, returns results from all cities.

    Use get_equipment_types() first if unsure of the exact type name.

    No login required.

    Args:
        equipment_type: Equipment category, e.g. "ЕХО" or "RTG".
                        Case-insensitive, Latin input supported.
        city:           Optional city to narrow results, e.g. "Скопје".

    Returns:
        Sorted list of dicts with keys: "resource", "resource_id", "clinic", "city".
        On error: { "error": true, "code": str, "message": str }
    """
    return _get_equipment_in_city(equipment_type=equipment_type, city=city)


@mcp.tool()
def get_equipment_slots(resource_name: str, city: str | None = None) -> list[dict]:
    """
    Return available appointment slots for a specific equipment resource.

    Call this when the user wants to book or check availability for a specific
    procedure or device (e.g. "when can I get Ехо на абдомен in Скопје?").
    Use get_equipment_in_city() first to find exact resource names.

    Because the same resource name can exist in multiple clinics and cities,
    results are a list — one entry per matching location. Pass city to narrow
    down to a specific location.

    No login required.

    Args:
        resource_name: Specific tool/procedure name, e.g. "Ехо на абдомен".
                       Case-insensitive, Latin input supported.
        city:          Optional city filter, e.g. "Скопје".

    Returns:
        List of dicts with keys: "resource", "resource_id", "clinic", "city",
        "slots_by_date" (date → list of "HH:MM" strings).
        Only locations with at least one available slot are included.
        On error: { "error": true, "code": str, "message": str }
    """
    return _get_equipment_slots(resource_name=resource_name, city=city)


# ── Entry point ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    mcp.run()
