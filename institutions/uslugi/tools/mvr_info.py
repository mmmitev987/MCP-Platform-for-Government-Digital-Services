"""
institutions/uslugi/tools/mvr_info.py
────────────────────────────────────────────────────────────────────────────────
MVR (Министерство за внатрешни работи) — public info tools.
All functions call GET /Services/GetServiceDetails — no auth required.
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


# ── ПАСОШ ────────────────────────────────────────────────────────────────────

def info_mvr_passport_renewal():    return _build_info(5200)
def info_mvr_passport_lost():       return _build_info(5201)
def info_mvr_passport_first_time(): return _build_info(5202)
def info_mvr_passport_minor():      return _build_info(5204)


# ── ЛИЧНА КАРТА ──────────────────────────────────────────────────────────────

def info_mvr_id_first_time(): return _build_info(5227)
def info_mvr_id_renewal():    return _build_info(5225)
def info_mvr_id_minor():      return _build_info(5226)


# ── ВОЗАЧКА ДОЗВОЛА ───────────────────────────────────────────────────────────

def info_mvr_license_first_time():     return _build_info(5208)
def info_mvr_license_driving_school(): return _build_info(2965)
def info_mvr_license_instructor():     return _build_info(2981)


# ── ВОЗИЛА ───────────────────────────────────────────────────────────────────

def info_mvr_vehicle_registration_new():  return _build_info(4452)
def info_mvr_vehicle_registration_used(): return _build_info(4268)
def info_mvr_vehicle_deregistration():    return _build_info(4472)
def info_mvr_vehicle_test_drive():        return _build_info(1960)


# ── УВЕРЕНИЈА И ПОТВРДИ ───────────────────────────────────────────────────────

def info_mvr_residence_certificate():   return _build_info(5737)
def info_mvr_citizenship_certificate(): return _build_info(5780)


# ── ОРУЖЈЕ ───────────────────────────────────────────────────────────────────

def info_mvr_weapon_permit_individual():  return _build_info(4044)
def info_mvr_weapon_permit_company():     return _build_info(4045)
def info_mvr_weapon_collector():          return _build_info(4046)
def info_mvr_weapon_ammo_permit():        return _build_info(4043)
def info_mvr_weapon_transport_import():   return _build_info(4048)
def info_mvr_weapon_transport_export():   return _build_info(4056)
def info_mvr_weapon_transport_transit():  return _build_info(4063)
def info_mvr_weapon_cross_border():       return _build_info(4064)


# ── ЖИВЕАЛИШТЕ И АДРЕСА ───────────────────────────────────────────────────────

def info_mvr_residence_registration():           return _build_info(1668)
def info_mvr_temporary_residence_registration(): return _build_info(1673)
def info_mvr_address_change():                   return _build_info(1674)


# ── ДРЖАВЈАНСТВО ─────────────────────────────────────────────────────────────

def info_mvr_citizenship_by_origin_both_parents():        return _build_info(1716)
def info_mvr_citizenship_by_origin_one_parent():          return _build_info(1717)
def info_mvr_citizenship_by_origin_born_abroad():         return _build_info(1623)
def info_mvr_citizenship_by_birth():                      return _build_info(1670)
def info_mvr_citizenship_naturalization():                return _build_info(5242)
def info_mvr_citizenship_naturalization_married():        return _build_info(5243)
def info_mvr_citizenship_naturalization_married_abroad(): return _build_info(5244)
def info_mvr_citizenship_naturalization_stateless():      return _build_info(5245)
def info_mvr_citizenship_naturalization_national_interest(): return _build_info(5246)
def info_mvr_citizenship_naturalization_sports():         return _build_info(5247)
def info_mvr_citizenship_naturalization_cultural():       return _build_info(5248)
def info_mvr_citizenship_naturalization_economic():       return _build_info(5249)
def info_mvr_citizenship_naturalization_scientific():     return _build_info(5250)
def info_mvr_citizenship_naturalization_diaspora():       return _build_info(5251)
def info_mvr_citizenship_renunciation():                  return _build_info(1685)


# ── ЛИЧНО ИМЕ И МАТИЧЕН БРОЈ ──────────────────────────────────────────────────

def info_mvr_name_change_adult():        return _build_info(1688)
def info_mvr_name_change_minor_over10(): return _build_info(5451)
def info_mvr_name_change_minor_under10():return _build_info(5452)
def info_mvr_embg_assign():              return _build_info(1699)
def info_mvr_embg_cancel():              return _build_info(1704)


# ── ВИЗИ И ПРИВРЕМЕН ПРЕСТОЈ ──────────────────────────────────────────────────

def info_mvr_visa_border():                     return _build_info(1919)
def info_mvr_temporary_stay_student_exchange(): return _build_info(5389)


# ── АЗИЛ И БЕГАЛЦИ ───────────────────────────────────────────────────────────

def info_mvr_asylum_regular():              return _build_info(1785)
def info_mvr_asylum_urgent():               return _build_info(1786)
def info_mvr_asylum_family_reunification(): return _build_info(1790)
def info_mvr_asylum_id_card():              return _build_info(1788)
def info_mvr_asylum_travel_document():      return _build_info(1789)
def info_mvr_asylum_applicant_id():         return _build_info(1787)


# ── ЛИЦЕНЦИ И ДОЗВОЛИ ЗА БИЗНИСИ ─────────────────────────────────────────────

def info_mvr_private_security_physical():          return _build_info(2994)
def info_mvr_private_security_technical():         return _build_info(3013)
def info_mvr_private_security_own_needs():         return _build_info(3015)
def info_mvr_detective_license():                  return _build_info(4068)
def info_mvr_technical_inspection_authorization(): return _build_info(4139)
def info_mvr_technical_inspection_license():       return _build_info(4468)
def info_mvr_test_drive_authorization():           return _build_info(4440)
def info_mvr_dangerous_goods_authorization():      return _build_info(4257)


# ── СООБРАЌАЈ И ПАТИШТА ───────────────────────────────────────────────────────

def info_mvr_sports_event_on_road():       return _build_info(2963)
def info_mvr_foreign_vehicle_permission(): return _build_info(2979)
def info_mvr_border_crossing_permit():     return _build_info(4240)
def info_mvr_border_zone_settlement():     return _build_info(4069)
