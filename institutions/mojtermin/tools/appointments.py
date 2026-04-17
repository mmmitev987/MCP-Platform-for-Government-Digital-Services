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


# ── Private helpers ───────────────────────────────────────────────────────────

def _get_json(path: str):
    """
    Perform a plain GET to mojtermin.mk and return the parsed JSON body.

    Args:
        path: URL path starting with "/", e.g. "/api/pp/side_navigation".
    """
    url = "https://mojtermin.mk" + path
    headers = {
        "Accept": "application/json",
        "User-Agent": "Mozilla/5.0",
    }
    response = requests.get(url, headers=headers)
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
    url = "https://mojtermin.mk/api/pp/locations"
    return requests.get(url).json()


def get_location_by_name(name: str) -> dict | None:
    """
    Find a single location whose name contains the given string (case-insensitive).

    Args:
        name: Partial or full location name to search for, e.g. "СТРУГА".

    Returns:
        The location dict if found, or None if no match.
    """
    data = get_locations()

    for loc in data.values():
        if name.lower() in loc["name"].lower():
            return loc

    return None


def get_specialties() -> list[str]:
    """
    Return a list of all medical specialties available on mojtermin.mk.

    Traverses the portal's side-navigation tree and collects every node
    whose type is "specialty".
    """
    data = _get_json("/api/pp/side_navigation")

    specialties = []

    def traverse(items):
        for item in items:
            if item.get("type") == "specialty":
                specialties.append(item["name"])
            if "subsections" in item:
                traverse(item["subsections"])

    traverse(data)
    return specialties


def get_doctors() -> list[str]:
    """
    Return a sorted, deduplicated list of all doctor names across the entire portal.

    Identifies doctors using the is_doctor() heuristic: resource nodes whose
    names are 2–3 fully uppercase words.
    """
    data = _get_json("/api/pp/side_navigation")

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


def get_doctors_by_city(city_name: str) -> list[dict]:
    """
    Return all doctors in a given city, along with their clinic name.

    Args:
        city_name: City to filter by, e.g. "СТРУГА". Case-insensitive.

    Returns:
        List of dicts, each with keys: "doctor", "clinic", "city".
        Sorted alphabetically by doctor name.
    """
    data = _get_json("/api/pp/side_navigation")

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
        or the string "Doctor not found" if no match.
    """
    data = _get_json("/api/pp/side_navigation")

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
        return "Doctor not found"

    # Fetch the slot availability calendar for this doctor.
    url = f"https://mojtermin.mk/api/pp/resources/{doctor_id}/slots_availability"
    headers = {"Accept": "application/json", "User-Agent": "Mozilla/5.0"}
    slots_data = requests.get(url, headers=headers).json()

    available = []

    for key in slots_data["timeslots"]:
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
