"""
institutions/uslugi/tools/fk_info.py
────────────────────────────────────────────────────────────────────────────────
Фармацевтска Комора на Македонија (FK) — public info tools.
All functions call POST /Services/GetServiceDetails — no auth required.
Institution ID on uslugi.gov.mk: 2359
"""

import re
import requests

_BASE_URL = "https://uslugi.gov.mk"
_HEADERS = {"Content-Type": "application/json", "from-angular": "true"}


def _strip_html(html: str | None) -> str | None:
    if not html:
        return None
    text = re.sub(r"<[^>]+>", "", html)
    text = text.replace("&nbsp;", " ").replace("&amp;", "&")
    text = text.replace("&ldquo;", '"').replace("&rdquo;", '"')
    return text.strip() or None


def _build_info(service_id: int) -> dict:
    try:
        resp = requests.post(
            f"{_BASE_URL}/Services/GetServiceDetails",
            json={"id": service_id},
            headers=_HEADERS,
            timeout=15,
        )
        resp.raise_for_status()
        if "json" not in resp.headers.get("content-type", ""):
            return {"serviceId": service_id, "error": "API недостапно"}
        api = resp.json()
    except Exception as exc:
        return {"serviceId": service_id, "error": str(exc)}

    first_group = (api.get("StateGroupDetails") or [{}])[0]
    process_docs = [d["DocumentName"] for d in first_group.get("InProcessDocuments", [])]
    proof_docs = [d["DocumentName"] for d in first_group.get("InProofDocuments", [])]
    requirements = process_docs + proof_docs

    conditions = [
        c["EvidenceProofDocument"]["DocumentNameMK"]
        for c in api.get("ApsConditions", [])
        if c.get("EvidenceProofDocument")
    ]

    prices = [
        {
            "label": p["Value"],
            "amount": p["Price"],
            "currency": "MKD",
            "purpose": slip.get("PurposeOfPayment"),
        }
        for slip in api.get("ApsPaymentSlips", [])
        for p in slip.get("PriceList", [])
    ]

    deadline_entry = next(
        (d for d in api.get("DeadLines", []) if d.get("StateFromId") == 3), None
    )
    deadline_days = deadline_entry["DaysValue"] if deadline_entry else None

    is_electronic = (api.get("ServiceApplicationType") or {}).get("Key") == 1
    ext_link = api.get("ServiceExternalApplicationLink")

    return {
        "serviceId": api.get("Id"),
        "name": api.get("AdministrativeProcedureServiceName"),
        "description": _strip_html(api.get("AdministrativeProcedureServiceDescription")),
        "intro": _strip_html(api.get("AdministrativeProcedureServiceIntro")),
        "isElectronic": is_electronic,
        "applyUrl": f"{_BASE_URL}{ext_link}" if is_electronic and ext_link else None,
        "note": None if is_electronic else "Само физичко поднесување",
        "eIdLevel": (api.get("ApsEidLevelType") or {}).get("Value"),
        "requirements": requirements,
        "conditions": conditions,
        "prices": prices,
        "deadlineDays": deadline_days,
        "institution": (api.get("InstituionOwner") or {}).get("InstitutionName"),
        "regulations": [r["RegulationName"] for r in api.get("Regulations", [])],
    }


# ── ЛИЦЕНЦИ ЗА РАБОТА ────────────────────────────────────────────────────────

def info_fk_license_pharmacist_mk():              return _build_info(5064)
def info_fk_license_pharmacist_foreign_edu():     return _build_info(5601)
def info_fk_license_pharmacist_foreign_license(): return _build_info(5604)
def info_fk_license_pharmacist_foreign_citizen(): return _build_info(5605)
def info_fk_license_renewal():                    return _build_info(5112)
def info_fk_license_extend():                     return _build_info(5611)
def info_fk_license_reacquire():                  return _build_info(5612)


# ── РЕГИСТАР НА ФАРМАЦЕВТИ ────────────────────────────────────────────────────

def info_fk_register_pharmacist():      return _build_info(5111)
def info_fk_update_personal_data():     return _build_info(5621)
def info_fk_update_professional_data(): return _build_info(5652)


# ── СТРУЧЕН ИСПИТ И ОБУКА ─────────────────────────────────────────────────────

def info_fk_professional_exam():      return _build_info(5617)
def info_fk_additional_training():    return _build_info(5618)
def info_fk_recognize_foreign_exam(): return _build_info(5619)


# ── ПОТВРДИ И ДОКУМЕНТИ ───────────────────────────────────────────────────────

def info_fk_confirmation():         return _build_info(5620)
def info_fk_confirmation_abroad():  return _build_info(5622)
def info_fk_license_duplicate():    return _build_info(5624)


# ── ПРОБНА РАБОТА ────────────────────────────────────────────────────────────

def info_fk_probation_work(): return _build_info(5613)
