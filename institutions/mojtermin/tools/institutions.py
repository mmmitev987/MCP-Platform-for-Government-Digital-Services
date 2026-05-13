"""
DODADENO OD MATEJ
institutions/mojtermin/tools/institutions.py
────────────────────────────────────────────────────────────────────────────────
MCP tool implementations for mojtermin.mk institution browsing.

Tree structure under the "Установи" root:
  Установи  (type: "")
    └── Универзитетски клиники  (type: "department")
          └── ЈЗУ УК за Нефрологија  (type: "institution", id: 123)
    └── Заводи  (type: "department")
          └── ...

Contact info is fetched from /api/pp/institutions/{id}.

Available tools:
  • get_institution_types()          — list all department type names
  • get_institutions_by_type(type)   — list institutions under a type
  • get_institution_info(name)       — contact info for a specific institution
"""

from institutions.mojtermin.tools.appointments import (
    _get,
    _nav,
    _pat,
    normalize,
    MojTerminError,
)
from institutions.shared.errors import tool_error


def _ustanovi_root() -> dict | None:
    """Return the 'Установи' root node from the nav tree."""
    try:
        nav = _nav()
    except MojTerminError as e:
        raise e
    return next((n for n in nav if n.get("name") == "Установи"), None)


def get_institution_types() -> list[str] | dict:
    """
    Return all institution department type names under the 'Установи' section.

    Examples of returned names:
        "Универзитетски клиники", "Клинички болници", "Заводи", "Институти" ...
    """
    try:
        root = _ustanovi_root()
    except MojTerminError as e:
        return tool_error("network_error", str(e))

    if not root:
        return tool_error("not_found", "Could not find the Установи section in the nav tree.")

    return [dept["name"] for dept in root.get("subsections", [])]


def get_institutions_by_type(type_name: str) -> list[dict] | dict:
    """
    Return all institutions of a given department type.

    Args:
        type_name: Department type name, e.g. "Универзитетски клиники".
                   Case-insensitive, Latin input supported.

    Returns:
        Sorted list of dicts with keys: "name", "id".
        On error: { "error": true, "code": str, "message": str }
    """
    try:
        root = _ustanovi_root()
    except MojTerminError as e:
        return tool_error("network_error", str(e))

    if not root:
        return tool_error("not_found", "Could not find the Установи section in the nav tree.")

    pattern = _pat(type_name)
    dept = next(
        (d for d in root.get("subsections", [])
         if pattern.search(normalize(d["name"]))),
        None,
    )

    if not dept:
        return tool_error(
            "not_found",
            f"No department type matching '{type_name}' found. "
            "Try get_institution_types() to see all available types.",
        )

    return sorted(
        [{"name": inst["name"], "id": inst["id"]} for inst in dept.get("subsections", [])],
        key=lambda x: x["name"],
    )


def get_institution_info(name: str) -> dict:
    """
    Return contact information and sections for a specific institution.

    Fetches phone, address, email, work hours, and lists of doctors,
    ambulances, and other sections registered under the institution.

    Args:
        name: Full or partial institution name, e.g. "УК за Нефрологија".
              Case-insensitive, Latin input supported.

    Returns:
        Dict with keys: "name", "phone", "street", "email", "workTime",
        "sections" (list of section groups, each with "name", "type", "items").
        On error: { "error": true, "code": str, "message": str }
    """
    try:
        root = _ustanovi_root()
    except MojTerminError as e:
        return tool_error("network_error", str(e))

    if not root:
        return tool_error("not_found", "Could not find the Установи section in the nav tree.")

    pattern = _pat(name)
    institution = None
    for dept in root.get("subsections", []):
        for inst in dept.get("subsections", []):
            if pattern.search(normalize(inst["name"])):
                institution = inst
                break
        if institution:
            break

    if not institution:
        return tool_error(
            "not_found",
            f"No institution matching '{name}' found. "
            "Try get_institutions_by_type() to browse available institutions.",
        )

    try:
        data = _get(f"/api/pp/institutions/{institution['id']}")
    except MojTerminError as e:
        return tool_error("network_error", str(e))

    return {
        "name": data.get("name", institution["name"]),
        "phone": data.get("phone"),
        "street": data.get("street"),
        "email": data.get("email"),
        "workTime": data.get("workTime"),
        "sections": data.get("sections", []),
    }
