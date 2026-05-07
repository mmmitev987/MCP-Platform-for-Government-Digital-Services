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

import requests
from datetime import datetime

from institutions.shared.errors import tool_error


# ── Private helpers ───────────────────────────────────────────────────────────

def _get_json(path: str):
    """
    Perform a plain GET to mojtermin.mk and return the parsed JSON body.

    Args:
        path: URL path starting with "/", e.g. "/api/pp/side_navigation".

    Raises:
        requests.RequestException on network errors.
        ValueError on JSON parse errors.
    """
    url = "https://mojtermin.mk" + path
    headers = {
        "Accept": "application/json",
        "User-Agent": "Mozilla/5.0",
    }
    response = requests.get(url, headers=headers, timeout=15)
    response.raise_for_status()
    return response.json()


def is_doctor(name: str) -> bool:
    """
    Heuristic: a resource is a doctor if its name is 2–3 all-uppercase words.
    Filters out rooms, equipment, and other non-person resources in the nav tree.

    Examples:
        "ЛИЛЈАНА СПАСЕВСКА"  → True   (2 uppercase words)
        "ИВАН ПЕТРОВ ПОПОВ"  → True   (3 uppercase words)
        "Ординација 1"       → False  (mixed case)
        "МРИ"                → False  (1 word)
    """
    words = name.strip().split()
    return 2 <= len(words) <= 3 and all(word.isupper() for word in words)


# ── Public tools ──────────────────────────────────────────────────────────────

def get_locations() -> dict:
    """
    Return all clinic/office locations registered on mojtermin.mk.

    Returns a dict keyed by location ID, each value containing location metadata
    (name, address, etc.) as returned by the API.
    """
    try:
        url = "https://mojtermin.mk/api/pp/locations"
        response = requests.get(url, timeout=15)
        response.raise_for_status()
        return response.json()
    except requests.Timeout:
        return tool_error("network_error", "mojtermin.mk did not respond in time. Please try again.")
    except requests.ConnectionError:
        return tool_error("network_error", "Could not connect to mojtermin.mk. Check your internet connection.")
    except requests.HTTPError as exc:
        return tool_error("network_error", f"mojtermin.mk returned an error: {exc}")
    except Exception as exc:
        return tool_error("unexpected_error", f"An unexpected error occurred while fetching locations: {exc}")


def get_location_by_name(name: str) -> dict | None:
    """
    Find a single location whose name contains the given string (case-insensitive).

    Args:
        name: Partial or full location name to search for, e.g. "СТРУГА".

    Returns:
        The location dict if found, None if no match, or an error dict on failure.
    """
    try:
        data = get_locations()
    except Exception as exc:
        return tool_error("unexpected_error", f"Could not fetch locations: {exc}")

    # Propagate error dict from get_locations
    if isinstance(data, dict) and data.get("error"):
        return data

    for loc in data.values():
        if name.lower() in loc["name"].lower():
            return loc

    return None


def get_specialties() -> list[str] | dict:
    """
    Return a list of all medical specialties available on mojtermin.mk.

    Traverses the portal's side-navigation tree and collects every node
    whose type is "specialty".
    """
    try:
        data = _get_json("/api/pp/side_navigation")
    except requests.Timeout:
        return tool_error("network_error", "mojtermin.mk did not respond in time. Please try again.")
    except requests.ConnectionError:
        return tool_error("network_error", "Could not connect to mojtermin.mk. Check your internet connection.")
    except requests.HTTPError as exc:
        return tool_error("network_error", f"mojtermin.mk returned an error: {exc}")
    except Exception as exc:
        return tool_error("unexpected_error", f"An unexpected error occurred while fetching specialties: {exc}")

    specialties = []

    def traverse(items):
        for item in items:
            if item.get("type") == "specialty":
                specialties.append(item["name"])
            if "subsections" in item:
                traverse(item["subsections"])

    traverse(data)
    return specialties


def get_doctors() -> list[str] | dict:
    """
    Return a sorted, deduplicated list of all doctor names across the entire portal.

    Identifies doctors using the is_doctor() heuristic: resource nodes whose
    names are 2–3 fully uppercase words.
    """
    try:
        data = _get_json("/api/pp/side_navigation")
    except requests.Timeout:
        return tool_error("network_error", "mojtermin.mk did not respond in time. Please try again.")
    except requests.ConnectionError:
        return tool_error("network_error", "Could not connect to mojtermin.mk. Check your internet connection.")
    except requests.HTTPError as exc:
        return tool_error("network_error", f"mojtermin.mk returned an error: {exc}")
    except Exception as exc:
        return tool_error("unexpected_error", f"An unexpected error occurred while fetching doctors: {exc}")

    doctors = []

    def traverse(items):
        for item in items:
            if item.get("type") == "resource":
                name = item["name"]
                if is_doctor(name):
                    doctors.append(name)
            if "subsections" in item:
                traverse(item["subsections"])

    traverse(data)
    return sorted(set(doctors))


def get_doctors_by_city(city_name: str) -> list[dict] | dict:
    """
    Return all doctors in a given city, along with their clinic name.

    Args:
        city_name: City to filter by, e.g. "СТРУГА". Case-insensitive.

    Returns:
        List of dicts, each with keys: "doctor", "clinic", "city".
        Sorted alphabetically by doctor name.
    """
    try:
        data = _get_json("/api/pp/side_navigation")
    except requests.Timeout:
        return tool_error("network_error", "mojtermin.mk did not respond in time. Please try again.")
    except requests.ConnectionError:
        return tool_error("network_error", "Could not connect to mojtermin.mk. Check your internet connection.")
    except requests.HTTPError as exc:
        return tool_error("network_error", f"mojtermin.mk returned an error: {exc}")
    except Exception as exc:
        return tool_error("unexpected_error", f"An unexpected error occurred while fetching doctors by city: {exc}")

    results = []

    def traverse(items):
        for item in items:
            # Match a location node whose name contains the city.
            if item.get("type") == "location" and city_name.lower() in item["name"].lower():
                for clinic in item.get("subsections", []):
                    clinic_name = clinic["name"]
                    for resource in clinic.get("subsections", []):
                        name = resource["name"]
                        if is_doctor(name):
                            results.append({
                                "doctor": name,
                                "clinic": clinic_name,
                                "city": item["name"],
                            })
            if "subsections" in item:
                traverse(item["subsections"])

    traverse(data)
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
        data = _get_json("/api/pp/side_navigation")
    except requests.Timeout:
        return tool_error("network_error", "mojtermin.mk did not respond in time. Please try again.")
    except requests.ConnectionError:
        return tool_error("network_error", "Could not connect to mojtermin.mk. Check your internet connection.")
    except requests.HTTPError as exc:
        return tool_error("network_error", f"mojtermin.mk returned an error: {exc}")
    except Exception as exc:
        return tool_error("unexpected_error", f"An unexpected error occurred while searching for the doctor: {exc}")

    doctor_id = None
    found_doctor = None

    def traverse(items):
        nonlocal doctor_id, found_doctor

        for item in items:
            if item.get("type") == "location" and city.lower() in item["name"].lower():
                for clinic in item.get("subsections", []):
                    for resource in clinic.get("subsections", []):
                        name = resource["name"]
                        if is_doctor(name) and doctor_name.lower() in name.lower():
                            doctor_id = resource.get("id")
                            found_doctor = name
                            return
            if "subsections" in item:
                traverse(item["subsections"])

    traverse(data)

    if not doctor_id:
        return tool_error(
            "not_found",
            f"No doctor matching '{doctor_name}' was found in '{city}'. "
            "Try calling get_doctors_by_city() to see available doctors."
        )

    # Fetch the slot availability calendar for this doctor.
    try:
        url = f"https://mojtermin.mk/api/pp/resources/{doctor_id}/slots_availability"
        headers = {"Accept": "application/json", "User-Agent": "Mozilla/5.0"}
        slots_response = requests.get(url, headers=headers, timeout=15)
        slots_response.raise_for_status()
        slots_data = slots_response.json()
    except requests.Timeout:
        return tool_error("network_error", "mojtermin.mk did not respond in time while fetching appointment slots.")
    except requests.ConnectionError:
        return tool_error("network_error", "Could not connect to mojtermin.mk while fetching appointment slots.")
    except requests.HTTPError as exc:
        return tool_error("network_error", f"mojtermin.mk returned an error while fetching slots: {exc}")
    except Exception as exc:
        return tool_error("unexpected_error", f"An unexpected error occurred while fetching appointment slots: {exc}")

    available = []

    for key in slots_data.get("timeslots", {}):
        for slot in slots_data["timeslots"][key]:
            slot_date = slot["term"].split("T")[0]

            # timeslotType 0 and 1 are bookable (0 = normal, 1 = first visit).
            if slot_date == date and slot["timeslotType"] in [0, 1]:
                time = slot["term"].split("T")[1][:5]
                available.append(time)

    return {
        "doctor": found_doctor,
        "date": date,
        "available_slots": available,
    }
