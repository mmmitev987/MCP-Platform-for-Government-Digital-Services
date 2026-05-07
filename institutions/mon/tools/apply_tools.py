"""
institutions/mon/tools/apply_tools.py
────────────────────────────────────────────────────────────────────────────────
Tools for browsing MON services and finding out what you need to apply.

  • list_mon_services()                — public, no login required
  • get_mon_service_requirements(id)  — requires login_mon() first
"""

import json
import requests

from institutions.shared.errors import tool_error
from institutions.mon.auth.session import session_manager
from institutions.mon.config import PORTAL_BASE_URL

_REST = f"{PORTAL_BASE_URL}/rest/"
_PUBLIC_HEADERS = {"app_id": "euslugi", "Accept": "application/json"}


def _auth_headers() -> dict | None:
    data = session_manager.load()
    if not data:
        return None
    token = data.get("access_token")
    if not token:
        return None
    return {
        "Authorization": f"Bearer {token}",
        "Accept-Language": "MK",
        "app_id": "euslugi",
    }


def list_mon_services(page: int = 0, size: int = 20) -> dict:
    """
    List all currently active MON services and contests.

    No login required.

    Args:
        page: Page number (0-based). Default 0.
        size: Number of results per page. Default 20.

    Returns:
        {
            "services": list of {
                "id":               int,
                "name":             str,
                "reference_number": str,
                "active_from":      str,
                "active_to":        str,
                "apply_url":        str,
            },
            "count": int,
        }
        or on error: { "error": True, "code": str, "message": str }
    """
    try:
        resp = requests.get(
            f"{_REST}public/form-instances/active",
            params={"page": page, "size": size},
            headers=_PUBLIC_HEADERS,
            timeout=15,
        )
        resp.raise_for_status()
        items = resp.json()
    except requests.Timeout:
        return tool_error("network_error", "e-uslugi.mon.gov.mk did not respond in time. Please try again.")
    except requests.ConnectionError:
        return tool_error("network_error", "Could not connect to e-uslugi.mon.gov.mk. Check your internet connection.")
    except requests.HTTPError as exc:
        return tool_error("network_error", f"e-uslugi.mon.gov.mk returned an error: {exc}")
    except Exception as exc:
        return tool_error("unexpected_error", f"An unexpected error occurred while listing MON services: {exc}")

    raw = items if isinstance(items, list) else items.get("content", [])
    services = [
        {
            "id":               s.get("id"),
            "name":             s.get("display_name") or s.get("name"),
            "reference_number": s.get("reference_number"),
            "active_from":      s.get("active_from"),
            "active_to":        s.get("active_to"),
            "apply_url":        s.get("link") or f"https://e-uslugi.mon.gov.mk/#/published/{s.get('id')}/apply",
        }
        for s in raw
    ]

    return {
        "services":      services,
        "count":         len(services),
        "total":         items.get("totalElements") if isinstance(items, dict) else len(services),
        "total_pages":   items.get("totalPages") if isinstance(items, dict) else 1,
    }


def get_mon_service_requirements(service_id: int) -> dict:
    """
    Get everything you need to apply for a specific MON service or contest.

    Requires an active session — call login_mon() first.

    Args:
        service_id: The numeric ID of the service, from list_mon_services().

    Returns:
        {
            "service_id":         int,
            "name":               str,
            "reference_number":   str,
            "active_from":        str,
            "active_to":          str,
            "can_apply":          bool,
            "documents_required": list[str],
            "apply_url":          str,
        }
        or on error: { "error": True, "code": str, "message": str }
    """
    headers = _auth_headers()
    if not headers:
        return tool_error(
            "auth_required",
            "You are not logged in to e-uslugi.mon.gov.mk. Please call login_mon() first."
        )

    try:
        resp = requests.get(
            f"{_REST}formInstance/{service_id}",
            headers=headers,
            timeout=15,
        )
        resp.raise_for_status()
        data = json.loads(resp.text)
    except requests.Timeout:
        return tool_error("network_error", "e-uslugi.mon.gov.mk did not respond in time. Please try again.")
    except requests.ConnectionError:
        return tool_error("network_error", "Could not connect to e-uslugi.mon.gov.mk. Check your internet connection.")
    except requests.HTTPError as exc:
        status = exc.response.status_code if exc.response is not None else "unknown"
        if status == 401 or status == 403:
            return tool_error("auth_required", "Your MON session has expired. Please call login_mon() to log in again.")
        if status == 404:
            return tool_error("not_found", f"MON service with ID {service_id} was not found.")
        return tool_error("network_error", f"e-uslugi.mon.gov.mk returned an error (HTTP {status}).")
    except json.JSONDecodeError as exc:
        return tool_error("parse_error", f"e-uslugi.mon.gov.mk returned an unexpected response format: {exc}")
    except Exception as exc:
        return tool_error("unexpected_error", f"An unexpected error occurred while fetching MON service requirements: {exc}")

    # Extract document upload fields from the form definition
    documents_required = []
    form = data.get("form") or {}
    for region in form.get("regions", []):
        for field in region.get("children", []):
            field_type = (field.get("field_type") or "").lower()
            if "file" in field_type:
                label = field.get("display_name") or field.get("name", "")
                if label:
                    documents_required.append(label)

    return {
        "service_id":         service_id,
        "name":               data.get("display_name") or data.get("name"),
        "reference_number":   data.get("reference_number"),
        "active_from":        data.get("active_from"),
        "active_to":          data.get("active_to"),
        "can_apply":          data.get("can_apply", False),
        "documents_required": documents_required,
        "apply_url":          f"https://e-uslugi.mon.gov.mk/#/published/{service_id}/apply",
    }
