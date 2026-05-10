"""
institutions/uslugi/services/apply_service.py
────────────────────────────────────────────────────────────────────────────────
Core service application logic for uslugi.gov.mk.

Uses the existing authenticated_client (from institutions/uslugi/client/)
to execute the portal's 5-step application flow:

  1. GetApsConfiguration     -> service metadata + form schema
  2. CanApplyDependingOnFrequency -> check frequency limits
  3. PreFillForm             -> auto-fill from eID (name, EMBG, address)
  4. Merge user-provided fields (phone, email, etc.)
  5. SubmitApplication       -> POST the complete form

IMPORTANT — API_BASE_PATH:
  The exact URL path between the domain and the endpoint names must be
  verified from the browser.  In DevTools Network tab, right-click any
  API call like GetApsConfiguration > Copy > Copy URL.

  Common patterns:
    https://uslugi.gov.mk/api/ApplyForServiceApi/GetApsConfiguration
    https://uslugi.gov.mk/ApplyForServiceApi/GetApsConfiguration

  Update API_BASE_PATH below to match what you see.
"""

import json
from datetime import datetime

from institutions.uslugi.client.http_client import authenticated_client, SessionExpiredError
from institutions.uslugi.config import PORTAL_BASE_URL

# ── API path — VERIFY THIS FROM YOUR BROWSER ──────────────────────────────────
# Right-click GetApsConfiguration in DevTools Network tab > Copy > Copy URL
# Then extract the path between the domain and the endpoint name.
API_BASE_PATH = "/api/ApplyForServiceApi"

# Common headers required by the Angular frontend API
ANGULAR_HEADERS = {
    "Content-Type": "application/json;charset=UTF-8",
    "from-angular": "true",
}


def _api_url(endpoint: str) -> str:
    """Build full API URL for an endpoint."""
    return f"{PORTAL_BASE_URL}{API_BASE_PATH}/{endpoint}"


def get_service_config(aps_unique_name: str) -> dict:
    """
    Fetch the service configuration (form schema, metadata).

    This is a read-only call — safe to use for testing.

    Returns:
        Raw dict from GetApsConfiguration response.

    Raises:
        SessionExpiredError: If the user is not logged in.
    """
    response = authenticated_client.post(
        _api_url("GetApsConfiguration"),
        json={
            "apsUniqueName": aps_unique_name,
            "instanceId": 0,
            "languageId": "2",
        },
        headers=ANGULAR_HEADERS,
    )
    return response.json()


def prefill_form(aps_unique_name: str) -> dict:
    """
    Get pre-filled form data from the authenticated user's eID profile.

    Returns fields like embg, firstName, lastName, address, submissionDate.

    Returns:
        Dict with pre-filled form data.

    Raises:
        SessionExpiredError: If the user is not logged in.
    """
    response = authenticated_client.post(
        _api_url("PreFillForm"),
        json={
            "apsUniqueName": aps_unique_name,
            "apsInstanceId": 0,
        },
        headers=ANGULAR_HEADERS,
    )
    return response.json()


def can_apply(aps_unique_name: str) -> bool:
    """
    Check if the user can currently apply (frequency/period limits).

    Returns:
        True if the user can apply, False otherwise.

    Raises:
        SessionExpiredError: If the user is not logged in.
    """
    response = authenticated_client.post(
        _api_url("CanApplyDependingOnFrequency"),
        json={
            "apsUniqueName": aps_unique_name,
            "apsInstanceId": 0,
        },
        headers=ANGULAR_HEADERS,
    )
    result = response.json()
    if isinstance(result, bool):
        return result
    return True


def submit_application(
    aps_unique_name: str,
    form_data: dict,
    embg: str,
    institution_id: str = "0",
    company_uin: str = "0",
    unit_id: str = "0",
    target_group_id: str = "0",
) -> dict:
    """
    Submit a service application to the portal.

    Args:
        aps_unique_name: Service identifier (e.g. "NBRSM-5721").
        form_data: Complete form data dict (e.g. {"data": {"embg": "...", ...}}).
        embg: Applicant's EMBG number.
        institution_id: Institution ID ("0" for default).
        company_uin: Company UIN for legal entity services ("0" for citizens).
        unit_id: Unit/branch ID ("0" for default).
        target_group_id: Target group ID ("0" for default).

    Returns:
        Response dict from the portal.

    Raises:
        SessionExpiredError: If the user is not logged in.
    """
    payload = {
        "model": {
            "LanguageId": "2",
            "Request": json.dumps(form_data, ensure_ascii=False),
            "ApplyForPersonalNumber": embg,
            "ApsUniqueName": aps_unique_name,
            "ApsInstanceId": 0,
            "ApplyInstitutionId": institution_id,
            "ResponseConfirmation": False,
            "TargetGroupId": target_group_id,
            "ContractIdentificator": None,
            "CompanyUin": company_uin,
            "UnitId": unit_id,
        }
    }
    response = authenticated_client.post(
        _api_url("SubmitApplication"),
        json=payload,
        headers=ANGULAR_HEADERS,
    )
    return response.json()


def apply_for_service(
    aps_unique_name: str,
    phone: str = None,
    email: str = None,
    company_uin: str = "0",
    extra_fields: dict = None,
) -> dict:
    """
    Execute the complete application flow for a service.

    This is the main entry point used by all MCP tool functions.

    Steps:
      1. Check if user can apply (frequency limits).
      2. Pre-fill form with eID data (name, EMBG, address).
      3. Merge user-provided fields (phone, email, custom fields).
      4. Submit the application.

    Args:
        aps_unique_name: Service identifier (e.g. "NBRSM-5721").
        phone: Optional phone number (+389XXXXXXXX format).
        email: Optional email address.
        company_uin: Company UIN for legal entity services ("0" for citizens).
        extra_fields: Additional form fields specific to the service.

    Returns:
        {
            "success": bool,
            "message": str,
            "service": str,
            "data": dict | None,
            "error": str | None,
        }
    """
    try:
        # Step 1: Check frequency limits
        if not can_apply(aps_unique_name):
            return {
                "success": False,
                "message": "Cannot apply: frequency or period limit reached for this service.",
                "service": aps_unique_name,
                "data": None,
                "error": None,
            }

        # Step 2: Pre-fill form with eID data
        prefilled = prefill_form(aps_unique_name)

        # Build the form data structure
        form_data = prefilled if isinstance(prefilled, dict) else {}
        if "data" not in form_data:
            form_data = {"data": form_data}

        # Step 3: Merge user-provided fields
        if phone:
            form_data["data"]["phone"] = phone
        if email:
            form_data["data"]["email"] = email
        if extra_fields:
            form_data["data"].update(extra_fields)

        # Add submission date if not already present
        if "submissionDate" not in form_data.get("data", {}):
            form_data["data"]["submissionDate"] = datetime.now().strftime("%d.%m.%Y")

        # Extract EMBG from pre-filled data
        embg = form_data.get("data", {}).get("embg", "")
        if not embg:
            return {
                "success": False,
                "message": "EMBG not found in pre-filled data. Is the session authenticated?",
                "service": aps_unique_name,
                "data": None,
                "error": "missing_embg",
            }

        # Step 4: Submit
        result = submit_application(
            aps_unique_name=aps_unique_name,
            form_data=form_data,
            embg=embg,
            company_uin=company_uin,
        )

        return {
            "success": True,
            "message": f"Application submitted successfully for {aps_unique_name}.",
            "service": aps_unique_name,
            "data": result,
            "error": None,
        }

    except SessionExpiredError:
        return {
            "success": False,
            "message": "Session expired. Please call the 'login' tool first.",
            "service": aps_unique_name,
            "data": None,
            "error": "session_expired",
        }
    except Exception as exc:
        return {
            "success": False,
            "message": f"Application failed: {str(exc)}",
            "service": aps_unique_name,
            "data": None,
            "error": str(exc),
        }
