"""
institutions/mon/tools/services.py
────────────────────────────────────────────────────────────────────────────────
Public information tools for the Ministry of Education and Science (MON).

All endpoints used here are publicly accessible — no authentication required.
Data is fetched from the central uslugi.gov.mk portal API which aggregates
services from all government institutions including MON.

Available tools:
  • info_mon_services(category)        — list MON services by education category
  • info_mon_service_details(service_id) — full details for a specific service
"""

import re
import requests

from institutions.mon.config import USLUGI_BASE_URL, MON_SUBCATEGORY_IDS

_HEADERS = {
    "Content-Type": "application/json;charset=UTF-8",
    "from-angular": "true",
}


def _post(endpoint: str, payload: dict) -> dict:
    url = f"{USLUGI_BASE_URL}/{endpoint}"
    resp = requests.post(url, json=payload, headers=_HEADERS, timeout=15)
    resp.raise_for_status()
    return resp.json()


def _strip_html(text: str) -> str:
    return re.sub(r"<[^>]+>", "", text or "").strip()


def info_mon_services(category: str = "visoko_obrazovanie") -> dict:
    """
    List MON (Ministry of Education and Science) services from uslugi.gov.mk,
    filtered by education category.

    Args:
        category: One of:
            "pretshkolska"        — Preschool services
            "skolska"             — Primary/secondary school services
            "visoko_obrazovanie"  — Higher education services (default)
            "stipendii"           — Scholarship services
            "obuki"               — Training services
            "nauka"               — Science services

    Returns:
        {
            "category":  str,
            "services":  list of { "id", "uniqueName", "name", "institution", "fee" }
        }
    """
    subcategory_id = MON_SUBCATEGORY_IDS.get(category)
    if subcategory_id is None:
        return {
            "error": f"Unknown category '{category}'. "
                     f"Valid values: {list(MON_SUBCATEGORY_IDS.keys())}",
        }

    payload = {
        "subCategoryId": subcategory_id,
        "page": 1,
        "pageSize": 100,
    }

    try:
        data = _post("Services/GetServicesBySubCategory", payload)
    except requests.RequestException as exc:
        return {"error": f"Portal unavailable: {exc}"}

    services = [
        {
            "id":          s.get("Id"),
            "uniqueName":  s.get("UniqueServiceName"),
            "name":        s.get("AdministrativeProcedureServiceName") or s.get("Name"),
            "institution": s.get("InstitutionName") or s.get("Institution"),
            "fee":         s.get("Fee"),
        }
        for s in (data if isinstance(data, list) else data.get("Services", []))
    ]

    return {"category": category, "services": services}


def info_mon_service_details(service_id: str) -> dict:
    """
    Fetch full details for a specific MON service from uslugi.gov.mk.

    Args:
        service_id: Numeric ID (e.g. "5200") or unique name (e.g. "MON-1234")
                    of the service. Use info_mon_services() first to find IDs.

    Returns:
        {
            "serviceId":    int | str,
            "name":         str,
            "description":  str,
            "requirements": list[str],   # documents to bring
            "conditions":   list[str],   # eligibility conditions
            "deadlines":    list[str],   # processing time per stage
            "delivery_in":  list[str],   # how to submit
            "delivery_out": list[str],   # how result is delivered
            "fee":          str | None,
            "contact":      str | None,
            "applyUrl":     str,
        }
    """
    # Accept either numeric ID or unique name like "MON-1234"
    if service_id.isdigit():
        payload = {"id": int(service_id), "serviceUniqueId": None}
    else:
        payload = {"id": None, "serviceUniqueId": service_id}

    try:
        d = _post("Services/GetServiceDetails", payload)
    except requests.RequestException as exc:
        return {"error": f"Portal unavailable: {exc}"}

    if not d:
        return {"error": f"Service '{service_id}' not found."}

    description = _strip_html(d.get("AdministrativeProcedureServiceDescription", ""))

    state_groups = d.get("StateGroupDetails", [])
    documents: list[str] = []
    delivery_in: list[str] = []
    delivery_out: list[str] = []

    if state_groups:
        first = state_groups[0]
        documents    = [doc["DocumentName"] for doc in first.get("InProofDocuments", [])]
        delivery_in  = [x["Value"] for x in first.get("InDeliveryTypes", [])]
        delivery_out = [x["Value"] for x in first.get("OutDeliveryTypes", [])]

    conditions = [
        c["EvidenceProofDocument"].get("DocumentNameMK", "")
        for c in d.get("ApsConditions", [])
        if c.get("EvidenceProofDocument")
    ]

    deadlines = [
        (
            f"{dl.get('StateFromName', '').strip()} → "
            f"{dl.get('StateToName', '').strip()}: "
            f"{dl.get('DaysValue')} {dl.get('PeriodTypeName')}"
        )
        for dl in d.get("DeadLines", [])
        if dl.get("DaysValue")
    ]

    unique_name = d.get("UniqueServiceName", "")
    apply_url = (
        f"https://uslugi.gov.mk/apply-for-service.nspx?apsUniqueName={unique_name}"
        if unique_name
        else "https://e-uslugi.mon.gov.mk"
    )

    return {
        "serviceId":    d.get("Id"),
        "name":         d.get("AdministrativeProcedureServiceName"),
        "description":  description,
        "requirements": documents,
        "conditions":   conditions,
        "deadlines":    deadlines,
        "delivery_in":  delivery_in,
        "delivery_out": delivery_out,
        "fee":          d.get("Fee"),
        "contact":      d.get("ApsContactInfo", {}).get("OfficePhone"),
        "applyUrl":     apply_url,
    }
