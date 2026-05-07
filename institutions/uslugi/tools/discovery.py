import re
import requests
from pathlib import Path

from institutions.shared.errors import tool_error

BASE_URL = "https://uslugi.gov.mk/Services"
HEADERS = {"Content-Type": "application/json;charset=UTF-8", "from-angular": "true"}

SERVICES_LIST_PATH = Path(__file__).parent.parent / "services_list.txt"

def _clean_html(raw_html: str) -> str:
    if not raw_html: return ""
    return re.sub(r"<[^>]+>", "", raw_html).strip()

def list_all_services() -> str | dict:
    """Return the full list of all services as a plain text string."""
    try:
        return SERVICES_LIST_PATH.read_text(encoding="utf-8")
    except FileNotFoundError:
        return tool_error("not_found", "The local services list file is missing. Please re-run the setup.")
    except Exception as exc:
        return tool_error("unexpected_error", f"Could not read the services list: {exc}")

def search_portal(query: str) -> list[dict]:
    """Search for services or groups by keyword. Query must be in Macedonian Cyrillic.
    IMPORTANT: If the result is empty or does not match what the user asked for,
    you MUST call list_all_services() next. NEVER tell the user a service is
    unavailable or unsupported without first calling list_all_services()."""
    payload = {
        "searchModel": {
            "CurrentPage": 1, "MaxSize": 10, "ItemsPerPage": 10,
            "SearchTerm": query, "SearchByLuceeneSearchTearm": False,
            "CitizenCompany": {"Key": 0, "Value": ""}, "LifeEvents": [],
            "EidLevels": [], "SubCategories": [], "Tags": [],
            "PortalUserType": {"Key": 0, "Value": ""},
            "ServiceApplicationType": {"Key": 0, "Value": ""}
        }
    }
    try:
        r = requests.post(f"{BASE_URL}/GetServices", json=payload, headers=HEADERS, timeout=15)
        r.raise_for_status()
        items = r.json().get("Items", [])
    except requests.Timeout:
        return [tool_error("network_error", "uslugi.gov.mk did not respond in time. Please try again.")]
    except requests.ConnectionError:
        return [tool_error("network_error", "Could not connect to uslugi.gov.mk. Check your internet connection.")]
    except requests.HTTPError as exc:
        return [tool_error("network_error", f"uslugi.gov.mk returned an error: {exc}")]
    except Exception as exc:
        return [tool_error("unexpected_error", f"An unexpected error occurred while searching: {exc}")]

    return [{
        "id": i.get("Id"),
        "name": i.get("AdministrativeProcedureServiceName"),
        "is_group": i.get("IsGroup"), # CRITICAL: If true, use get_group_contents
        "intro": _clean_html(i.get("AdministrativeProcedureServiceIntro"))[:200]
    } for i in items]

def get_group_contents(group_id: int) -> list[dict]:
    """If a search result is a group (is_group: true), use this to see its services."""
    payload = {"groupApsServiceId": str(group_id)}
    try:
        r = requests.post(f"{BASE_URL}/GetGroupServiceDetails", json=payload, headers=HEADERS, timeout=15)
        r.raise_for_status()
        services = r.json().get("AdministrativeProcedureServices", [])
    except requests.Timeout:
        return [tool_error("network_error", "uslugi.gov.mk did not respond in time. Please try again.")]
    except requests.ConnectionError:
        return [tool_error("network_error", "Could not connect to uslugi.gov.mk. Check your internet connection.")]
    except requests.HTTPError as exc:
        return [tool_error("network_error", f"uslugi.gov.mk returned an error: {exc}")]
    except Exception as exc:
        return [tool_error("unexpected_error", f"An unexpected error occurred while fetching group contents: {exc}")]

    return [{
        "id": s.get("Id"),
        "name": s.get("AdministrativeProcedureServiceName"),
        "is_electronic": s.get("IsElectronicService"),
        "intro": _clean_html(s.get("AdministrativeProcedureServiceIntro"))
    } for s in services]

def get_service_details(service_id: int) -> dict:
    """Fetch full details for a specific service ID — requirements, conditions, prices, deadlines, etc."""
    payload = {"id": str(service_id), "serviceUniqueId": None}
    try:
        r = requests.post(f"{BASE_URL}/GetServiceDetails", json=payload, headers=HEADERS, timeout=15)
        r.raise_for_status()
        d = r.json()
    except requests.Timeout:
        return tool_error("network_error", "uslugi.gov.mk did not respond in time. Please try again.")
    except requests.ConnectionError:
        return tool_error("network_error", "Could not connect to uslugi.gov.mk. Check your internet connection.")
    except requests.HTTPError as exc:
        status = exc.response.status_code if exc.response is not None else "unknown"
        if status == 404:
            return tool_error("not_found", f"Service ID {service_id} was not found on uslugi.gov.mk.")
        return tool_error("network_error", f"uslugi.gov.mk returned an error (HTTP {status}).")
    except Exception as exc:
        return tool_error("unexpected_error", f"An unexpected error occurred while fetching service details: {exc}")

    # Apply URL
    unique_name = d.get("ApsUniqueName")
    ext_link = d.get("ServiceExternalApplicationLink") or ""
    if not unique_name and "apsUniqueName=" in ext_link:
        unique_name = ext_link.split("apsUniqueName=")[-1]
    if not unique_name:
        unique_name = d.get("ApsNameAbbrivation")

    is_electronic = (d.get("ServiceApplicationType") or {}).get("Key") == 1

    # Documents
    first_group = (d.get("StateGroupDetails") or [{}])[0]
    process_docs = [doc["DocumentName"] for doc in first_group.get("InProcessDocuments", [])]
    proof_docs = [doc["DocumentName"] for doc in first_group.get("InProofDocuments", [])]
    requirements = process_docs + proof_docs

    # Conditions
    conditions = [
        c["EvidenceProofDocument"]["DocumentNameMK"]
        for c in d.get("ApsConditions", [])
        if c.get("EvidenceProofDocument")
    ]

    # Prices
    prices = [
        {
            "label": p["Value"],
            "amount": p["Price"],
            "currency": "MKD",
            "purpose": slip.get("PurposeOfPayment"),
        }
        for slip in d.get("ApsPaymentSlips", [])
        for p in slip.get("PriceList", [])
    ]

    # Deadline
    deadline_entry = next(
        (dl for dl in d.get("DeadLines", []) if dl.get("StateFromId") == 3), None
    )
    deadline_days = deadline_entry["DaysValue"] if deadline_entry else None

    return {
        "id": d.get("Id"),
        "name": d.get("AdministrativeProcedureServiceName"),
        "description": _clean_html(d.get("AdministrativeProcedureServiceDescription")),
        "intro": _clean_html(d.get("AdministrativeProcedureServiceIntro")),
        "is_electronic": is_electronic,
        "applyUrl": f"https://uslugi.gov.mk/apply-for-service.nspx?apsUniqueName={unique_name}" if unique_name else None,
        "note": None if is_electronic else "Само физичко поднесување",
        "eid_level": (d.get("ApsEidLevelType") or {}).get("Value"),
        "requirements": requirements,
        "conditions": conditions,
        "prices": prices,
        "deadline_days": deadline_days,
        "institution": (d.get("InstituionOwner") or {}).get("InstitutionName"),
        "regulations": [reg["RegulationName"] for reg in d.get("Regulations", [])],
    }
