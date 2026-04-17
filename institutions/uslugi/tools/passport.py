"""
institutions/uslugi/tools/passport.py
────────────────────────────────────────────────────────────────────────────────
MCP tool: info_passport_renewal

Fetches detailed information about the passport renewal administrative
procedure (service ID 5200) from the uslugi.gov.mk portal API.

This endpoint is PUBLICLY accessible — no authentication required.
We use a plain requests.post() (not the authenticated client) so the tool
works even before the user has logged in.

The raw API response contains nested JSON with HTML fragments and Macedonian
text.  This function cleans and flattens it into a dict that is easy for
the LLM to read and summarise.
"""

import re

import requests


def info_passport_renewal() -> dict:
    """
    Return structured information about the passport renewal service.

    Returns:
        {
            "serviceId":    int,
            "name":         str,          # Service name in Macedonian
            "description":  str,          # HTML-stripped plain text description
            "requirements": list[str],    # Documents the citizen must provide
            "conditions":   list[str],    # Eligibility conditions
            "deadlines":    list[str],    # Processing time per stage
            "delivery_in":  list[str],    # How to submit the request
            "delivery_out": list[str],    # How the result is delivered
            "contact":      str | None,   # Office phone number
            "applyUrl":     str,          # Direct URL to start the service
        }
    """

    # ── API call ──────────────────────────────────────────────────────────────
    # This is the internal Angular API used by the portal front-end.
    # The "from-angular" header is required — the server rejects requests
    # without it (it uses it to distinguish API calls from page loads).
    url = "https://uslugi.gov.mk/Services/GetServiceDetails"
    headers = {
        "Content-Type": "application/json;charset=UTF-8",
        "from-angular": "true",
    }
    payload = {
        "id": "5200",            # Numeric ID of the passport renewal service
        "serviceUniqueId": None, # Only needed when using a string unique ID
    }

    response = requests.post(url, json=payload, headers=headers, timeout=15)
    response.raise_for_status()
    d = response.json()

    # ── Strip HTML from description ───────────────────────────────────────────
    # The description contains inline HTML (<p>, <br>, <strong>, etc.).
    # We strip tags so the LLM receives clean prose without any markup.
    description = re.sub(
        r"<[^>]+>",
        "",
        d.get("AdministrativeProcedureServiceDescription", ""),
    ).strip()

    # ── Extract documents and delivery types from the first state group ───────
    # The service is divided into StateGroupDetails (processing stages).
    # The first group represents the initial submission ("Барање" / Request).
    state_groups = d.get("StateGroupDetails", [])
    documents: list[str] = []
    delivery_in: list[str] = []
    delivery_out: list[str] = []

    if state_groups:
        first_group = state_groups[0]
        # InProofDocuments: what the citizen must bring or attach.
        documents = [doc["DocumentName"] for doc in first_group.get("InProofDocuments", [])]
        # InDeliveryTypes: how the citizen can submit the request.
        delivery_in = [x["Value"] for x in first_group.get("InDeliveryTypes", [])]
        # OutDeliveryTypes: how the institution delivers the result back.
        delivery_out = [x["Value"] for x in first_group.get("OutDeliveryTypes", [])]

    # ── Eligibility conditions ────────────────────────────────────────────────
    # ApsConditions lists documents the citizen must already possess.
    conditions = [
        c["EvidenceProofDocument"]["DocumentNameMK"]
        for c in d.get("ApsConditions", [])
        if c.get("EvidenceProofDocument")
    ]

    # ── Processing deadlines ──────────────────────────────────────────────────
    # Each DeadLine entry maps "Stage A → Stage B" to a duration.
    deadlines = [
        (
            f"{dl.get('StateFromName', '').strip()} → "
            f"{dl.get('StateToName', '').strip()}: "
            f"{dl.get('DaysValue')} {dl.get('PeriodTypeName')}"
        )
        for dl in d.get("DeadLines", [])
        if dl.get("DaysValue")
    ]

    return {
        "serviceId":    d.get("Id"),
        "name":         d.get("AdministrativeProcedureServiceName"),
        "description":  description,
        "requirements": documents,
        "conditions":   conditions,
        "deadlines":    deadlines,
        "delivery_in":  delivery_in,
        "delivery_out": delivery_out,
        "contact":      d.get("ApsContactInfo", {}).get("OfficePhone"),
        "applyUrl":     "https://uslugi.gov.mk/apply-for-service.nspx?apsUniqueName=MVR-5200",
    }
