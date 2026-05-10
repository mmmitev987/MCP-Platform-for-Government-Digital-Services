"""
institutions/mojtermin/tools/resources.py
────────────────────────────────────────────────────────────────────────────────
MCP tool implementations for mojtermin.mk resource discovery (clinics, doctors,
search, city-based lookups).

All endpoints here are public — no authentication required.

Available tools:
  • get_clinics()              — all clinics with their city info
  • get_resources_by_city(city)— all resources (doctors + institutions) in a city
  • search_resources(query)    — fuzzy search across all resources
"""

from institutions.mojtermin.tools.appointments import (
    _flat,
    _pat,
    is_doctor,
    normalize,
    MojTerminError,
)
from institutions.shared.errors import tool_error


def get_clinics() -> list[dict] | dict:
    """
    Return all clinics registered on mojtermin.mk.

    Returns:
        Sorted list of dicts, each with keys:
            "clinic"    — clinic name,
            "clinic_id" — internal API id,
            "city"      — city name (may be empty),
            "city_id"   — parent location id (may be absent).
        On error: { "error": true, "code": str, "message": str }
    """
    try:
        return sorted(
            [
                {
                    "clinic": n["name"],
                    "clinic_id": n["id"],
                    "city": n.get("city", ""),
                    "city_id": n.get("locationId"),
                }
                for n in _flat()
                if n.get("type") == "clinic"
            ],
            key=lambda x: x["clinic"],
        )
    except MojTerminError as e:
        return tool_error("network_error", str(e))


def get_resources_by_city(city_name: str) -> list[dict] | dict:
    """
    Return all resources (doctors and institutions) under clinics in a given city.

    Args:
        city_name: City name to filter by, e.g. "Скопје" or "Skopje" (Latin supported).

    Returns:
        Sorted list of dicts, each with keys:
            "name"   — resource name,
            "id"     — internal API id,
            "kind"   — "doctor" or "institution",
            "clinic" — parent clinic name,
            "city"   — parent city name.
        On error: { "error": true, "code": str, "message": str }
    """
    try:
        flat = _flat()
    except MojTerminError as e:
        return tool_error("network_error", str(e))
    pattern = _pat(city_name)
    results = []
    for node in flat:
        if node.get("type") != "location" or not pattern.search(normalize(node["name"])):
            continue
        for clinic in node.get("subsections", []):
            for r in clinic.get("subsections", []):
                results.append({
                    "name": r["name"],
                    "id": r["id"],
                    "kind": "doctor" if is_doctor(r["name"]) else "institution",
                    "clinic": clinic["name"],
                    "city": node["name"],
                })
    return sorted(results, key=lambda x: x["name"])


def search_resources(query: str) -> list[dict] | dict:
    """
    Search all resources (clinics, doctors, rooms, institutions) by name.

    Uses case-insensitive matching with Latin-to-Cyrillic normalization, so
    searching for "struga" will match "Струга" in the database.

    Args:
        query: Partial name to search for, e.g. "Кардио" or "Kardio".

    Returns:
        List of matching resource nodes from the nav tree (each node has at
        least "name" and "id" keys, plus optional "type", "subsections", etc.).
        On error: { "error": true, "code": str, "message": str }
    """
    try:
        flat = _flat()
    except MojTerminError as e:
        return tool_error("network_error", str(e))
    pattern = _pat(query)
    return [
        n for n in flat
        if n.get("id") and pattern.search(normalize(n["name"]))
    ]
