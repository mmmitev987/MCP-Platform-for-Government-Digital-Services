"""
institutions/uslugi/tools/services.py
────────────────────────────────────────────────────────────────────────────────
MCP tool implementations for uslugi.gov.mk e-services.

These functions are registered as MCP tools in institutions/uslugi/main.py.
The gateway namespaces them as uslugi__<name> so the LLM sees:
  uslugi__list_services, uslugi__apply_service, uslugi__get_service_config, etc.

Architecture:
  LLM calls uslugi__apply_service(service_name="get_credit_registry_data")
    -> gateway routes to institutions/uslugi/main.py
    -> main.py dispatches to apply_service() below
    -> apply_service() looks up NBRSM-5721 in registry
    -> calls apply_service.apply_for_service("NBRSM-5721")
    -> which uses authenticated_client.post() for the actual HTTP calls
"""

import requests

from institutions.uslugi.services.registry import (
    ALL_SERVICES,
    ALL_REGISTRIES,
    get_service,
    list_services_for_institution,
)
from institutions.uslugi.services.apply_service import (
    apply_for_service as _apply,
    get_service_config as _get_config,
    prefill_form as _prefill,
)
from institutions.uslugi.client.http_client import SessionExpiredError
from institutions.uslugi.config import PORTAL_BASE_URL


# ═══════════════════════════════════════════════════════════════════════════════
# DISCOVERY TOOLS (no auth required for list, auth required for config/prefill)
# ═══════════════════════════════════════════════════════════════════════════════

def list_services(institution: str = "") -> dict:
    """
    List available e-services on uslugi.gov.mk.

    Args:
        institution: Filter by institution slug (e.g. "piom", "sudovi",
                     "nbrsm", "sluzhben_vesnik", "vrabotuvanje", "mdt",
                     "pravda", "fzo", "vlada", "kultura", "film").
                     Leave empty to list all institutions and their service counts.

    Returns:
        { "institutions": [...] } or { "services": [...] }
    """
    if not institution:
        result = []
        for slug, registry in ALL_REGISTRIES.items():
            first = next(iter(registry.values()), {})
            result.append({
                "slug": slug,
                "institution_name": first.get("institution_name", slug),
                "service_count": len(registry),
                "services": list(registry.keys()),
            })
        return {"institutions": result, "total_services": len(ALL_SERVICES)}

    try:
        registry = list_services_for_institution(institution)
        services = []
        for name, svc in registry.items():
            services.append({
                "name": name,
                "description": svc["description"],
                "citizen_company": svc["citizen_company"],
                "aps_unique_name": svc["aps_unique_name"],
            })
        return {"institution": institution, "services": services}
    except ValueError as e:
        return {"error": str(e)}


def get_service_details(service_id: str) -> dict:
    """
    Fetch detailed information about a specific service from the portal API.

    This is a PUBLIC endpoint — no authentication required.

    Args:
        service_id: The numeric service ID (e.g. "5721" for credit registry).

    Returns:
        Dict with service name, description, requirements, deadlines, etc.
    """
    import re

    url = f"{PORTAL_BASE_URL}/Services/GetServiceDetails"
    headers = {
        "Content-Type": "application/json;charset=UTF-8",
        "from-angular": "true",
    }
    payload = {"id": str(service_id), "serviceUniqueId": None}

    try:
        response = requests.post(url, json=payload, headers=headers, timeout=15)
        response.raise_for_status()
        d = response.json()

        description = re.sub(
            r"<[^>]+>", "",
            d.get("AdministrativeProcedureServiceDescription", ""),
        ).strip()

        state_groups = d.get("StateGroupDetails", [])
        documents = []
        if state_groups:
            documents = [
                doc["DocumentName"]
                for doc in state_groups[0].get("InProofDocuments", [])
            ]

        conditions = [
            c["EvidenceProofDocument"]["DocumentNameMK"]
            for c in d.get("ApsConditions", [])
            if c.get("EvidenceProofDocument")
        ]

        return {
            "serviceId": d.get("Id"),
            "name": d.get("AdministrativeProcedureServiceName"),
            "description": description,
            "requirements": documents,
            "conditions": conditions,
            "contact": d.get("ApsContactInfo", {}).get("OfficePhone"),
        }
    except Exception as e:
        return {"error": f"Failed to fetch service details: {str(e)}"}


# ═══════════════════════════════════════════════════════════════════════════════
# GENERIC APPLY/GET TOOL (auth required)
# ═══════════════════════════════════════════════════════════════════════════════

def apply_service(
    service_name: str,
    phone: str = "",
    email: str = "",
    company_uin: str = "0",
) -> dict:
    """
    Apply for or request a specific e-service on uslugi.gov.mk.

    Requires an active login session.  Call 'login' first if not authenticated.

    The service_name must match one of the registered services.
    Call list_services() to see all available service names.

    Common service names:
      - get_credit_registry_data          (Народна банка - кредитен регистар)
      - get_criminal_record_person        (Основни судови - казнена евиденција)
      - get_criminal_proceedings_person    (Основни судови - кривична евиденција)
      - get_pension_registry_certificate   (ПИОСМ - матична евиденција)
      - get_employment_history             (Вработување - историјат на работни односи)
      - get_unemployed_person_certificate  (Вработување - потврда за невработен)
      - get_health_insurance_status        (ФЗО - здравствено осигурување)
      - get_personal_data_certificate      (МДТ - лични податоци од ЦРН)
      - apply_invalid_diploma              (Службен весник - неважечка диплома)

    Args:
        service_name: Registered service function name (see list_services).
        phone: Optional phone number in +389XXXXXXXX format.
        email: Optional email address.
        company_uin: Company UIN for legal entity services (default "0").

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
        svc = get_service(service_name)
    except ValueError as e:
        return {
            "success": False,
            "message": str(e),
            "service": service_name,
            "data": None,
            "error": "unknown_service",
        }

    return _apply(
        aps_unique_name=svc["aps_unique_name"],
        phone=phone or None,
        email=email or None,
        company_uin=company_uin,
    )


# ═══════════════════════════════════════════════════════════════════════════════
# SERVICE CONFIG INSPECTION (auth required, read-only, safe for testing)
# ═══════════════════════════════════════════════════════════════════════════════

def inspect_service(service_name: str) -> dict:
    """
    Inspect a service's configuration and form schema (read-only, safe).

    Use this to check what fields a service requires before applying.
    Requires an active login session.

    Args:
        service_name: Registered service function name.

    Returns:
        Dict with service config, form fields, and pre-filled user data.
    """
    try:
        svc = get_service(service_name)
    except ValueError as e:
        return {"error": str(e)}

    aps = svc["aps_unique_name"]

    try:
        config = _get_config(aps)
        prefilled = _prefill(aps)

        import json
        form_schema = {}
        if config.get("ServiceJsonForm"):
            try:
                form_schema = json.loads(config["ServiceJsonForm"])
            except json.JSONDecodeError:
                pass

        fields = list(
            form_schema
            .get("properties", {})
            .get("data", {})
            .get("properties", {})
            .keys()
        )

        return {
            "service_name": service_name,
            "aps_unique_name": aps,
            "portal_name": config.get("AdministrativeProcedureServiceName"),
            "is_chargeable": config.get("IsChargable", False),
            "can_apply_for_self": config.get("CanApplyForHimself", True),
            "form_fields": fields,
            "prefilled_data": prefilled,
        }

    except SessionExpiredError:
        return {"error": "Session expired. Please call 'login' first."}
    except Exception as e:
        return {"error": f"Failed to inspect service: {str(e)}"}
