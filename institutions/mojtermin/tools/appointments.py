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
  • get_doctors(city, specialty)                     — doctors filtered by city and/or specialty
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
    Heuristic: a resource is a doctor if its name is 2-3 all-uppercase words,
    optionally followed by a specialty suffix after a dash.

    Examples:
        "ЛИЛЈАНА СПАСЕВСКА"              → True
        "ИВАН ПЕТРОВ ПОПОВ"              → True
        "НИКОЛИНА ЗДРАВЕСКА - НЕОНАТОЛОГ"→ True  (suffix stripped)
        "Ординација 1"                   → False (mixed case)
        "МРИ"                            → False (1 word)
    """
    base = re.split(r"\s*-\s*", name)[0].strip()
    words = base.split()
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


def get_doctors(city: str | None = None, specialty: str | None = None) -> list | dict:
    """
    Return doctors, optionally filtered by city and/or specialty.

    All combinations are supported:
      get_doctors()                              → all doctors portal-wide
      get_doctors(city="СКОПЈЕ")                → all doctors in Skopje
      get_doctors(specialty="Кардиологија")     → all cardiologists countrywide
      get_doctors(city="СКОПЈЕ",
                  specialty="Кардиологија")     → cardiologists in Skopje

    Args:
        city:      City name, case-insensitive, Latin input supported
                   (e.g. "Skopje" → "Скопје"). Optional.
        specialty: Medical specialty name, case-insensitive, Latin input
                   supported (e.g. "Kardiologija" → "Кардиологија"). Optional.

    Returns:
        Sorted list of dicts with keys: "doctor", "specialty", "clinic", "city".
        On error: { "error": true, "code": str, "message": str }
    """
    try:
        nav = _nav()
    except MojTerminError as e:
        return tool_error("network_error", str(e))

    city_pat = _pat(city) if city else None
    spec_pat = _pat(specialty) if specialty else None

    results = []
    seen = set()

    for root in nav:
        for spec_node in root.get("subsections", []):
            if spec_node.get("type") != "specialty":
                continue
            if spec_pat and not spec_pat.search(normalize(spec_node["name"])):
                continue
            for loc_node in spec_node.get("subsections", []):
                if loc_node.get("type") != "location":
                    continue
                if city_pat and not city_pat.search(normalize(loc_node["name"])):
                    continue
                for clinic_node in loc_node.get("subsections", []):
                    for resource in clinic_node.get("subsections", []):
                        if not is_doctor(resource["name"]):
                            continue
                        key = (resource["name"], spec_node["name"], clinic_node["name"])
                        if key in seen:
                            continue
                        seen.add(key)
                        results.append({
                            "doctor": resource["name"],
                            "specialty": spec_node["name"],
                            "clinic": clinic_node["name"],
                            "city": loc_node["name"],
                        })

    results.sort(key=lambda x: x["doctor"])
    return results


def get_available_appointments_by_name(doctor_name: str) -> dict | str:
    """
    Return all available appointment slots for a specific doctor, grouped by date.

    Args:
        doctor_name: Full or partial doctor name, e.g. "ЛИЛЈАНА СПАСЕВСКА".

    Returns:
        Dict with keys "doctor" and "slots_by_date" (dict mapping each date that
        has availability to a list of "HH:MM" strings), or an error dict on failure.
    """
    try:
        flat = _flat()
    except MojTerminError as e:
        return tool_error("network_error", str(e))

    doc_pat = _pat(doctor_name)
    resource = next(
        (n for n in flat
         if n.get("type") == "resource"
         and is_doctor(n["name"])
         and doc_pat.search(normalize(n["name"]))),
        None,
    )

    if not resource:
        return tool_error(
            "not_found",
            f"No doctor matching '{doctor_name}' was found. "
            "Try calling get_doctors() to see available doctors.",
        )
    try:
        slots_data = _get(f"/api/pp/resources/{resource['id']}/slots_availability")
    except MojTerminError as e:
        return tool_error("network_error", str(e))

    slots_by_date: dict[str, list[str]] = {}
    for s in _parse_slots(slots_data):
        slots_by_date.setdefault(s["date"], []).append(s["time"])

    return {
        "doctor": resource["name"],
        "slots_by_date": slots_by_date,
    }
