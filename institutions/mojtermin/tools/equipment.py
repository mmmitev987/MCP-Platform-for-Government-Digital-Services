"""
institutions/mojtermin/tools/equipment.py
────────────────────────────────────────────────────────────────────────────────
MCP tool implementations for mojtermin.mk equipment/apparatus browsing.

Tree structure under the "Апарат" root:
  Апарат  (type: "")
    └── ЕХО  (type: "equipment")
          └── Град Скопје  (type: "location")
                └── ЈЗУ УИ за Радиологија  (type: "clinic")
                      └── Ехо Томографија Возрасни  (type: "resource", id: 1003)
    └── РТГ  (type: "equipment")
          └── ...

Available tools:
  • get_equipment_types()                      — list all equipment type names
  • get_equipment_in_city(type, city)          — list all tools of a type in a city
  • get_equipment_slots(resource_name, city)   — available slots for a specific tool
"""

from concurrent.futures import ThreadPoolExecutor, as_completed

from institutions.mojtermin.tools.appointments import (
    _get,
    _nav,
    _pat,
    _parse_slots,
    normalize,
    MojTerminError,
)
from institutions.shared.errors import tool_error


def _aparat_root() -> dict | None:
    """Return the 'Апарат' root node from the nav tree (uses cached _nav())."""
    try:
        nav = _nav()
    except MojTerminError as e:
        raise e
    return next((n for n in nav if n.get("name") == "Апарат"), None)


# ── Public tools ──────────────────────────────────────────────────────────────

def get_equipment_types() -> list[str] | dict:
    """
    Return all equipment/apparatus type names available on mojtermin.mk.

    Examples: "ЕХО", "РТГ", "ЕЕГ", "Магнетна резонанца (МР)", "Гастроскопија" ...
    """
    try:
        root = _aparat_root()
    except MojTerminError as e:
        return tool_error("network_error", str(e))

    if not root:
        return tool_error("not_found", "Could not find the Апарат section in the nav tree.")

    return [eq["name"] for eq in root.get("subsections", [])]


def get_equipment_in_city(equipment_type: str, city: str | None = None) -> list[dict] | dict:
    """
    Return all specific tools of a given equipment type, optionally filtered by city.

    Both arguments support case-insensitive matching with Latin-to-Cyrillic
    normalization (e.g. "EHO" matches "ЕХО", "Skopje" matches "Скопје").

    Args:
        equipment_type: Equipment category, e.g. "ЕХО" or "RTG".
        city:           Optional city to narrow results, e.g. "Скопје".
                        If omitted, returns tools from all cities.

    Returns:
        Sorted list of dicts with keys:
            "resource"    — specific tool name (e.g. "Ехо Томографија Возрасни"),
            "resource_id" — internal API id for fetching slots,
            "clinic"      — clinic/hospital name,
            "city"        — city name.
        On error: { "error": true, "code": str, "message": str }
    """
    try:
        root = _aparat_root()
    except MojTerminError as e:
        return tool_error("network_error", str(e))

    if not root:
        return tool_error("not_found", "Could not find the Апарат section in the nav tree.")

    eq_pat = _pat(equipment_type)
    eq_node = next(
        (eq for eq in root.get("subsections", [])
         if eq_pat.search(normalize(eq["name"]))),
        None,
    )

    if not eq_node:
        return tool_error(
            "not_found",
            f"No equipment type matching '{equipment_type}' found. "
            "Try get_equipment_types() to see all available types.",
        )

    city_pat = _pat(city) if city else None
    results = []

    for loc in eq_node.get("subsections", []):
        if city_pat and not city_pat.search(normalize(loc["name"])):
            continue
        for clinic in loc.get("subsections", []):
            for resource in clinic.get("subsections", []):
                results.append({
                    "resource": resource["name"],
                    "resource_id": resource["id"],
                    "clinic": clinic["name"],
                    "city": loc["name"],
                })

    if not results:
        msg = f"No '{equipment_type}' equipment found"
        msg += f" in '{city}'." if city else "."
        return tool_error("not_found", msg)

    return sorted(results, key=lambda x: (x["city"], x["clinic"], x["resource"]))


def get_equipment_slots(resource_name: str, city: str | None = None) -> list[dict] | dict:
    """
    Return available appointment slots for a specific equipment resource.

    Because the same resource name (e.g. "Ехо на абдомен") can exist in multiple
    clinics and cities, this returns a list — one entry per matching resource.
    Pass city to narrow down to a single location.

    Args:
        resource_name: Specific tool/procedure name, e.g. "Ехо на абдомен"
                       or "РТГ апарат". Case-insensitive, Latin input supported.
        city:          Optional city to narrow results, e.g. "Скопје".

    Returns:
        List of dicts, each with keys:
            "resource"      — canonical resource name,
            "resource_id"   — internal API id,
            "clinic"        — clinic/hospital name,
            "city"          — city name,
            "slots_by_date" — dict mapping date → list of "HH:MM" strings.
        Only resources with at least one future slot are included.
        On error: { "error": true, "code": str, "message": str }
    """
    try:
        root = _aparat_root()
    except MojTerminError as e:
        return tool_error("network_error", str(e))

    if not root:
        return tool_error("not_found", "Could not find the Апарат section in the nav tree.")

    res_pat = _pat(resource_name)
    city_pat = _pat(city) if city else None

    # Collect all matching resource nodes
    candidates = []
    for eq_node in root.get("subsections", []):
        for loc in eq_node.get("subsections", []):
            if city_pat and not city_pat.search(normalize(loc["name"])):
                continue
            for clinic in loc.get("subsections", []):
                for resource in clinic.get("subsections", []):
                    if res_pat.search(normalize(resource["name"])):
                        candidates.append({
                            "resource": resource["name"],
                            "resource_id": resource["id"],
                            "clinic": clinic["name"],
                            "city": loc["name"],
                        })

    if not candidates:
        msg = f"No equipment matching '{resource_name}' found"
        msg += f" in '{city}'." if city else "."
        return tool_error("not_found", msg)

    _TIMEOUT = object()  # sentinel: network error, not "no slots"

    def _fetch_one(candidate: dict):
        try:
            slots = _parse_slots(_get(f"/api/pp/resources/{candidate['resource_id']}/slots_availability"))
            slots_by_date: dict[str, list[str]] = {}
            for s in slots:
                slots_by_date.setdefault(s["date"], []).append(s["time"])
            if not slots_by_date:
                return None  # responded, genuinely no slots
            return {**candidate, "slots_by_date": slots_by_date}
        except MojTerminError:
            return _TIMEOUT  # network/timeout error

    results = []
    failed = 0
    with ThreadPoolExecutor(max_workers=8) as pool:
        futures = [pool.submit(_fetch_one, c) for c in candidates]
        for future in as_completed(futures):
            out = future.result()
            if out is _TIMEOUT:
                failed += 1
            elif out is not None:
                results.append(out)

    if not results and failed > 0:
        return tool_error(
            "network_error",
            f"Could not retrieve slots for '{resource_name}'"
            + (f" in '{city}'" if city else "")
            + " — the portal did not respond in time. Please try again in a moment.",
        )

    results.sort(key=lambda x: (x["city"], x["clinic"], x["resource"]))
    return results
