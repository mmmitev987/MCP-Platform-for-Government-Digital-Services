import re
import requests

BASE_URL = "https://uslugi.gov.mk/Services"
HEADERS = {"Content-Type": "application/json;charset=UTF-8", "from-angular": "true"}

def _clean_html(raw_html: str) -> str:
    if not raw_html: return ""
    return re.sub(r"<[^>]+>", "", raw_html).strip()

def search_portal(query: str) -> list[dict]:
    """Search for services or groups by keyword."""
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
    r = requests.post(f"{BASE_URL}/GetServices", json=payload, headers=HEADERS)
    r.raise_for_status()
    items = r.json().get("Items", [])

    return [{
        "id": i.get("Id"),
        "name": i.get("AdministrativeProcedureServiceName"),
        "is_group": i.get("IsGroup"), # CRITICAL: If true, use get_group_contents
        "intro": _clean_html(i.get("AdministrativeProcedureServiceIntro"))[:200]
    } for i in items]

def get_group_contents(group_id: int) -> list[dict]:
    """If a search result is a group (is_group: true), use this to see its services."""
    payload = {"groupApsServiceId": str(group_id)}
    r = requests.post(f"{BASE_URL}/GetGroupServiceDetails", json=payload, headers=HEADERS)
    r.raise_for_status()
    services = r.json().get("AdministrativeProcedureServices", [])

    return [{
        "id": s.get("Id"),
        "name": s.get("AdministrativeProcedureServiceName"),
        "is_electronic": s.get("IsElectronicService"),
        "intro": _clean_html(s.get("AdministrativeProcedureServiceIntro"))
    } for s in services]
def get_service_details(service_id: int) -> dict:
    """Fetch requirements and applyUrl for a specific service ID."""
    payload = {"id": str(service_id), "serviceUniqueId": None}
    r = requests.post(f"{BASE_URL}/GetServiceDetails", json=payload, headers=HEADERS)
    r.raise_for_status()
    d = r.json()

    # --- 1. Find the Unique ID for the link ---
    # We try ApsUniqueName first, then try to extract it from the external link field
    unique_name = d.get("ApsUniqueName")

    ext_link = d.get("ServiceExternalApplicationLink") or ""
    if not unique_name and "apsUniqueName=" in ext_link:
        # Extracts 'MVR-5217' from '/apply-for-service.nspx?apsUniqueName=MVR-5217'
        unique_name = ext_link.split("apsUniqueName=")[-1]

    if not unique_name:
        # Fallback to the abbreviation if both above fail
        unique_name = d.get("ApsNameAbbrivation")

    # --- 2. Extract Documents ---
    state_groups = d.get("StateGroupDetails", [])
    docs = []
    if state_groups:
        # Usually, documents are in the first group's 'InProofDocuments'
        docs = [doc["DocumentName"] for doc in state_groups[0].get("InProofDocuments", [])]

    return {
        "id": d.get("Id"),
        "name": d.get("AdministrativeProcedureServiceName"),
        "description": _clean_html(d.get("AdministrativeProcedureServiceDescription")),
        "requirements": docs,
        "is_electronic": d.get("IsElectronicService"),
        "applyUrl": f"https://uslugi.gov.mk/apply-for-service.nspx?apsUniqueName={unique_name}" if unique_name else None
    }
