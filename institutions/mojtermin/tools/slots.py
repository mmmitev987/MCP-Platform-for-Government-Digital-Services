"""
institutions/mojtermin/tools/slots.py
────────────────────────────────────────────────────────────────────────────────
MCP tool implementations for mojtermin.mk slot/availability queries.

All endpoints here are public — no authentication required.

Available tools:
  • get_available_slots(name, date)          — bookable times for a resource on a date
  • get_slots_range(name, start, end)        — slots across a date range
  • get_first_available(name, days_ahead)    — earliest open slot
  • get_availability_summary(name, days)     — daily slot counts as a mini calendar
  • get_slots_for_city(city, date)           — all slots across every resource in a city
"""

from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta

from institutions.mojtermin.tools.appointments import (
    _get,
    _flat,
    _pat,
    _parse_slots,
    MojTerminError,
    normalize,
)
from institutions.shared.errors import tool_error


def _find_resource(name: str) -> dict | None:
    """Find a single resource node by name (case-insensitive, Latin-aware)."""
    try:
        flat = _flat()
    except MojTerminError as e:
        raise e  # let caller (public functions) turn it into tool_error
    pattern = _pat(name)
    return next(
        (n for n in flat if n.get("id") and pattern.search(normalize(n["name"]))),
        None,
    )


def _fetch_slots(name: str) -> tuple[dict | None, list[dict]]:
    """Shared lookup + fetch used by every slot function.

    Returns (resource_node, parsed_slots) or (None, []) if not found.
    Raises MojTerminError on network/API errors.
    """
    resource = _find_resource(name)
    if not resource:
        return None, []
    return resource, _parse_slots(_get(f"/api/pp/resources/{resource['id']}/slots_availability"))


# ── Public tools ──────────────────────────────────────────────────────────────

def get_available_slots(name: str, date: str) -> dict:
    """
    Return available appointment slots for a named resource on a specific date.

    Works with doctors, clinics, and any other resource on mojtermin.mk.

    Args:
        name: Resource name, e.g. "Амбуланта по интерна медицина- ЗД Ресен"
              or a doctor name like "ЛИЛЈАНА СПАСЕВСКА".
        date: Date in YYYY-MM-DD format, e.g. "2026-04-11".

    Returns:
        Dict with keys:
            "resource"       — canonical resource name,
            "resource_id"    — internal API id,
            "date"           — the requested date,
            "available_slots" — list of "HH:MM" strings (empty if none).
        If the resource is not found, returns { "error": true, "code": "not_found", "message": str }.
        On network error: { "error": true, "code": str, "message": str }
    """
    try:
        resource, slots = _fetch_slots(name)
    except MojTerminError as e:
        return tool_error("network_error", str(e))
    if not resource:
        return tool_error("not_found", f"Resource not found: '{name}'")
    return {
        "resource": resource["name"],
        "resource_id": resource["id"],
        "date": date,
        "available_slots": [s["time"] for s in slots if s["date"] == date],
    }


def get_slots_range(name: str, start_date: str, end_date: str) -> dict:
    """
    Return available slots for a resource across a date range (inclusive).

    Args:
        name:        Resource name (doctor or institution).
        start_date:  Start date in YYYY-MM-DD format.
        end_date:    End date in YYYY-MM-DD format.

    Returns:
        Dict with keys:
            "resource"       — canonical resource name,
            "resource_id"    — internal API id,
            "slots_by_date"  — dict mapping each date with slots to a list of "HH:MM" strings.
        If the resource is not found, returns { "error": true, "code": "not_found", "message": str }.
        On network error: { "error": true, "code": str, "message": str }
    """
    try:
        resource, slots = _fetch_slots(name)
    except MojTerminError as e:
        return tool_error("network_error", str(e))
    if not resource:
        return tool_error("not_found", f"Resource not found: '{name}'")
    by_date: dict[str, list] = defaultdict(list)
    for s in slots:
        if start_date <= s["date"] <= end_date:
            by_date[s["date"]].append(s["time"])
    return {
        "resource": resource["name"],
        "resource_id": resource["id"],
        "slots_by_date": dict(by_date),
    }


def get_first_available(name: str, days_ahead: int = 30) -> dict:
    """
    Find the earliest available appointment slot for a resource.

    Args:
        name:       Resource name (doctor or institution).
        days_ahead: How many days into the future to search (default 30).

    Returns:
        Dict with keys "resource", "resource_id", "date", "time" for the first
        available slot, or a message dict if no slots are found within the window.
        If the resource is not found, returns { "error": true, "code": "not_found", "message": str }.
        On network error: { "error": true, "code": str, "message": str }
    """
    try:
        resource, slots = _fetch_slots(name)
    except MojTerminError as e:
        return tool_error("network_error", str(e))
    if not resource:
        return tool_error("not_found", f"Resource not found: '{name}'")
    now = datetime.today()
    today = str(now.date())
    end   = str((now + timedelta(days=days_ahead)).date())
    first = next((s for s in slots if today <= s["date"] <= end), None)
    if not first:
        return {"message": f"No slots in the next {days_ahead} days for '{resource['name']}'"}
    return {
        "resource": resource["name"],
        "resource_id": resource["id"],
        **first,
    }


def get_availability_summary(name: str, days_ahead: int = 14) -> dict:
    """
    Return a day-by-day count of available slots for a resource.

    Useful for a mini-calendar view of availability density.

    Args:
        name:       Resource name (doctor or institution).
        days_ahead: Number of days to include starting from today (default 14).

    Returns:
        Dict with keys:
            "resource"    — canonical resource name,
            "resource_id" — internal API id,
            "summary"     — list of {"date": str, "count": int} for each day.
        If the resource is not found, returns { "error": true, "code": "not_found", "message": str }.
        On network error: { "error": true, "code": str, "message": str }
    """
    try:
        resource, slots = _fetch_slots(name)
    except MojTerminError as e:
        return tool_error("network_error", str(e))
    if not resource:
        return tool_error("not_found", f"Resource not found: '{name}'")
    today = datetime.today().date()
    end   = today + timedelta(days=days_ahead)
    counts: dict[str, int] = defaultdict(int)
    for s in slots:
        if str(today) <= s["date"] <= str(end):
            counts[s["date"]] += 1
    dates = [str(today + timedelta(days=i)) for i in range(days_ahead + 1)]
    summary = [{"date": d, "count": counts.get(d, 0)} for d in dates]
    return {
        "resource": resource["name"],
        "resource_id": resource["id"],
        "summary": summary,
    }


def get_slots_for_city(
    city_name: str,
    date: str,
    max_resources: int = 50,
    max_workers: int = 10,
) -> list[dict] | dict:
    """
    Return available slots for all resources in a city on a given date.

    Queries resources concurrently using a thread pool for speed.
    May be slow for large cities — use max_resources to cap the query count.

    Args:
        city_name:    City name, e.g. "Скопје" or "Skopje" (Latin supported).
        date:         Date in YYYY-MM-DD format.
        max_resources: Max resources to query (default 50). Pass 0 for unlimited.
        max_workers:  Thread pool size (default 10).

    Returns:
        List of dicts, each with keys:
            "resource"    — resource name,
            "resource_id" — internal API id,
            "clinic"      — parent clinic name,
            "slots"       — list of "HH:MM" strings available on the date.
        Only resources with at least one slot are included.
        On network error: { "error": true, "code": str, "message": str }
    """
    from institutions.mojtermin.tools.resources import get_resources_by_city

    try:
        resources = get_resources_by_city(city_name)
    except MojTerminError as e:
        return tool_error("network_error", str(e))
    if isinstance(resources, dict) and resources.get("error"):
        return resources

    if max_resources > 0:
        resources = resources[:max_resources]

    def _fetch_one(r: dict) -> dict | None:
        try:
            slots = [
                s["time"]
                for s in _parse_slots(_get(f"/api/pp/resources/{r['id']}/slots_availability"))
                if s["date"] == date
            ]
            if slots:
                return {
                    "resource": r["name"],
                    "resource_id": r["id"],
                    "clinic": r["clinic"],
                    "slots": slots,
                }
            return None
        except MojTerminError:
            return {"_error": True}

    total = len(resources)
    results = []
    failures = 0

    with ThreadPoolExecutor(max_workers=max_workers) as pool:
        futures = {pool.submit(_fetch_one, r): r for r in resources}
        for future in as_completed(futures):
            out = future.result()
            if out is None:
                continue
            if isinstance(out, dict) and out.get("_error"):
                failures += 1
            else:
                results.append(out)

    if total > 0 and failures == total:
        return tool_error(
            "network_error",
            f"All {total} resource(s) in '{city_name}' failed to respond. "
            "The mojtermin.mk portal may be temporarily unavailable.",
        )

    results.sort(key=lambda x: x["resource"])
    return results
