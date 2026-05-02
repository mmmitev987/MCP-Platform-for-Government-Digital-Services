import re
import requests


BASE_URL = "https://uslugi.gov.mk/Services/GetServiceDetails"


def strip_html(text: str | None) -> str:
    if not text:
        return ""

    return re.sub(r"<[^>]+>", "", text).strip()


def get_service_details(service_id: int) -> dict:
    """
    Generic uslugi.gov.mk service fetcher.

    Works for ANY service ID.
    """

    headers = {
        "Content-Type": "application/json;charset=UTF-8",
        "from-angular": "true",
    }

    payload = {
        "id": str(service_id),
        "serviceUniqueId": None,
    }

    response = requests.post(
        BASE_URL,
        json=payload,
        headers=headers,
        timeout=20,
    )

    response.raise_for_status()

    d = response.json()

    state_groups = d.get("StateGroupDetails", [])

    documents = []
    delivery_in = []
    delivery_out = []

    if state_groups:
        first_group = state_groups[0]

        documents = [
            doc["DocumentName"]
            for doc in first_group.get("InProofDocuments", [])
        ]

        delivery_in = [
            x["Value"]
            for x in first_group.get("InDeliveryTypes", [])
        ]

        delivery_out = [
            x["Value"]
            for x in first_group.get("OutDeliveryTypes", [])
        ]

    conditions = [
        c["EvidenceProofDocument"]["DocumentNameMK"]
        for c in d.get("ApsConditions", [])
        if c.get("EvidenceProofDocument")
    ]

    deadlines = [
        (
            f"{dl.get('StateFromName', '').strip()} → "
            f"{dl.get('StateToName', '').strip()}: "
            f"{dl.get('DaysValue')} "
            f"{dl.get('PeriodTypeName')}"
        )
        for dl in d.get("DeadLines", [])
        if dl.get("DaysValue")
    ]

    return {
        "serviceId": d.get("Id"),
        "name": d.get("AdministrativeProcedureServiceName"),
        "description": strip_html(
            d.get("AdministrativeProcedureServiceDescription")
        ),
        "requirements": documents,
        "conditions": conditions,
        "deadlines": deadlines,
        "delivery_in": delivery_in,
        "delivery_out": delivery_out,
        "contact": (
            d.get("ApsContactInfo", {})
            .get("OfficePhone")
        ),
        "applyUrl": (
            f"https://uslugi.gov.mk/"
            f"service-details.nspx?serviceId={service_id}"
        ),
    }