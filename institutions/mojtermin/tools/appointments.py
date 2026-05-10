"""
institutions/mojtermin/tools/appointments.py
────────────────────────────────────────────────────────────────────────────────
MCP tool implementations for mojtermin.mk appointment browsing.

All endpoints here are public — no authentication required.

Available tools:
  • get_locations()                                  — all clinic locations
  • get_location_by_name(name)                       — find a location by name
  • get_specialties()                                — list medical specialties
  • get_doctors()                                    — all doctors across all locations
  • get_doctors_by_city(city_name)                   — doctors filtered by city
  • get_available_appointments_by_name(city,         — free slots for a specific
      doctor_name, date)                               doctor on a given date
"""

import re
import requests

from institutions.shared.errors import tool_error


# ── Shared helpers (used by all tool modules) ─────────────────────────────────

# Digraphs first so 'sh' beats 's'+'h', etc.
_LATIN = sorted({
    'sh': 'ш', 'zh': 'ж', 'ch': 'ч', 'dj': 'џ', 'gj': 'ѓ', 'kj': 'ќ',
    'lj': 'љ', 'nj': 'њ', 'dz': 'ѕ',
    'a': 'а', 'b': 'б', 'c': 'ц', 'd': 'д', 'e': 'е', 'f': 'ф', 'g': 'г',
    'h': 'х', 'i': 'и', 'j': 'ј', 'k': 'к', 'l': 'л', 'm': 'м', 'n': 'н',
    'o': 'о', 'p': 'п', 'q': 'ќ', 'r': 'р', 's': 'с', 't': 'т', 'u': 'у',
    'v': 'в', 'w': 'в', 'x': 'кс', 'y': 'и', 'z': 'з',
}.items(), key=lambda x: -len(x[0]))

_cache: dict = {}


class MojTerminError(Exception):
    """Custom exception for mojtermin.mk API errors."""
    pass


def normalize(text: str) -> str:
    """Convert Latin text to Cyrillic and lowercase for case-insensitive matching."""
    text = text.lower()
    for lat, cyr in _LATIN:
        text = text.replace(lat, cyr)
    return text


def _pat(text: str) -> re.Pattern:
    """Build a regex pattern from text after normalization."""
    return re.compile(re.escape(normalize(text)), re.IGNORECASE)


def _get(path: str):
    """
    Perform a GET to mojtermin.mk with error handling and JSON parsing.

    Args:
        path: URL path starting with "/", e.g. "/api/pp/side_navigation".

    Returns:
        Parsed JSON response.

    Raises:
        MojTerminError: On timeout, HTTP error, network error, or invalid JSON.
    """
    url = "https://mojtermin.mk" + path
    try:
        r = requests.get(
            url,
            headers={"Accept": "application/json", "User-Agent": "Mozilla/5.0"},
            timeout=15,
        )
        r.raise_for_status()
        return r.json()
    except requests.exceptions.Timeout:
        raise MojTerminError(f"Timeout: {url}")
    except requests.exceptions.HTTPError:
        raise MojTerminError(f"HTTP {r.status_code}: {url}")
    except requests.exceptions.RequestException as e:
        raise MojTerminError(f"Network error: {e}")
    except ValueError:
        raise MojTerminError(f"Invalid JSON: {url}")


def _cached(key: str, path: str):
    """Fetch from cache or API."""
    if key not in _cache:
        _cache[key] = _get(path)
    return _cache[key]


def _nav() -> list:
    """Return the full side-navigation tree (cached)."""
    return _cached("nav", "/api/pp/side_navigation")


def _flat() -> list:
    """Flatten the nav tree into a single list of all nodes (cached)."""
    if "flat" not in _cache:
        stack, result = list(_nav()), []
        while stack:
            node = stack.pop()
            result.append(node)
            stack.extend(node.get("subsections", []))
        _cache["flat"] = result
    return _cache["flat"]


def is_doctor(name: str) -> bool:
    """
    Heuristic: a resource is a doctor if its name is 2-3 all-uppercase words.
    Filters out rooms, equipment, and other non-person resources in the nav tree.

    Examples:
        "ЛИЛЈАНА СПАСЕВСКА"  → True   (2 uppercase words)
        "ИВАН ПЕТРОВ ПОПОВ"  → True   (3 uppercase words)
        "Ординација 1"       → False  (mixed case)
        "МРИ"                → False  (1 word)
    """
    words = name.strip().split()
    return 2 <= len(words) <= 3 and all(word.isupper() for word in words)


def _parse_slots(data: dict) -> list[dict]:
    """
    Extract bookable appointment slots from the raw API response.

    Returns a sorted list of {"date": "YYYY-MM-DD", "time": "HH:MM"} dicts.
    """
    slots = []
    for day in data.get("timeslots", {}).values():
        for s in day:
            try:
                kind = int(s.get("timeslotType", -1))
            except (TypeError, ValueError):
                continue
            if kind not in (0, 1):
                continue
            term = s.get("term", "")
            if "T" not in term:
                continue
            date, time = term.split("T", 1)
            slots.append({"date": date, "time": time[:5]})
    return sorted(slots, key=lambda s: (s["date"], s["time"]))


# ── Public tools ──────────────────────────────────────────────────────────────

def get_locations() -> dict:
    """
    Return all clinic/office locations registered on mojtermin.mk.

    Returns a dict keyed by location ID, each value containing location metadata
    (name, address, etc.) as returned by the API.
    """
    try:
        return _cached("locations", "/api/pp/locations")
    except MojTerminError as e:
        return tool_error("network_error", str(e))


def get_location_by_name(name: str) -> dict | None:
    """
    Find a single location whose name contains the given string (case-insensitive,
    with Latin-to-Cyrillic normalization).

    Args:
        name: Partial or full location name to search for, e.g. "СТРУГА" or "STRUGA".

    Returns:
        The location dict if found, None if no match, or an error dict on failure.
    """
    data = get_locations()
    if isinstance(data, dict) and data.get("error"):
        return data
    pattern = _pat(name)
    return next(
        (loc for loc in data.values() if pattern.search(normalize(loc["name"]))),
        None,
    )


def get_specialties() -> list | dict:
    """
    Return a list of all medical specialties available on mojtermin.mk.

    Traverses the portal's side-navigation tree and collects every node
    whose type is "specialty".
    """
    try:
        return [n["name"] for n in _flat() if n.get("type") == "specialty"]
    except MojTerminError as e:
        return tool_error("network_error", str(e))


def get_doctors() -> list | dict:
    """
    Return a sorted, deduplicated list of all doctor names across the entire portal.

    Identifies doctors using the is_doctor() heuristic: resource nodes whose
    names are 2-3 fully uppercase words.
    """
    try:
        return sorted({
            n["name"] for n in _flat()
            if n.get("type") == "resource" and is_doctor(n["name"])
        })
    except MojTerminError as e:
        return tool_error("network_error", str(e))


def get_doctors_by_city(city_name: str) -> list | dict:
    """
    Return all doctors in a given city, along with their clinic name.

    Args:
        city_name: City to filter by, e.g. "СТРУГА". Case-insensitive,
                   supports Latin input (e.g. "Struga" → "Струга").

    Returns:
        List of dicts, each with keys: "doctor", "clinic", "city".
        Sorted alphabetically by doctor name.
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
                if is_doctor(r["name"]):
                    results.append({
                        "doctor": r["name"],
                        "clinic": clinic["name"],
                        "city": node["name"],
                    })
    results.sort(key=lambda x: x["doctor"])
    return results


def get_available_appointments_by_name(city: str, doctor_name: str, date: str) -> dict | str:
    """
    Return available appointment slots for a specific doctor on a given date.

    Args:
        city:        City name to narrow the search, e.g. "СТРУГА".
        doctor_name: Full or partial doctor name, e.g. "ЛИЛЈАНА СПАСЕВСКА".
        date:        Date in YYYY-MM-DD format, e.g. "2026-04-11".

    Returns:
        Dict with keys "doctor", "date", "available_slots" (list of "HH:MM" strings),
        or an error dict on failure.
    """
    try:
        flat = _flat()
    except MojTerminError as e:
        return tool_error("network_error", str(e))
    city_pat = _pat(city)
    doc_pat = _pat(doctor_name)
    doctor_id = None
    found_doctor = None
    for node in flat:
        if node.get("type") != "location" or not city_pat.search(normalize(node["name"])):
            continue
        for clinic in node.get("subsections", []):
            for resource in clinic.get("subsections", []):
                if is_doctor(resource["name"]) and doc_pat.search(normalize(resource["name"])):
                    doctor_id = resource.get("id")
                    found_doctor = resource["name"]
                    break
            if doctor_id:
                break
        if doctor_id:
            break
    if not doctor_id:
        return tool_error(
            "not_found",
            f"No doctor matching '{doctor_name}' was found in '{city}'. "
            "Try calling get_doctors_by_city() to see available doctors.",
        )
    try:
        slots_data = _get(f"/api/pp/resources/{doctor_id}/slots_availability")
    except MojTerminError as e:
        return tool_error("network_error", str(e))
    available = [s["time"] for s in _parse_slots(slots_data) if s["date"] == date]
    return {
        "doctor": found_doctor,
        "date": date,
        "available_slots": available,
    }
