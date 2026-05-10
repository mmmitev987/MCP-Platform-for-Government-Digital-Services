"""
institutions/uslugi/services/registry.py
────────────────────────────────────────────────────────────────────────────────
Service registry mapping every uslugi.gov.mk service to its portal identifier.

Each entry maps a human-readable function name to the apsUniqueName
(the identifier the portal API expects in every request payload).

The LLM never sees this file directly.  Tool functions in tools/services.py
use the lookup helpers at the bottom to resolve names.
"""

# ─────────────────────────────────────────────
# Народна банка на РСМ (ID: 1731)
# ─────────────────────────────────────────────
NBRSM = {
    "get_credit_registry_data": {
        "aps_unique_name": "NBRSM-5721",
        "service_id": 5721,
        "institution_id": 1731,
        "institution_name": "Народна банка на РСМ",
        "citizen_company": 1,
        "description": "Издавање податоци на физички лица од Кредитниот регистар на НБРСМ",
    },
}

# ─────────────────────────────────────────────
# Основни судови (Group ID: 53)
# ─────────────────────────────────────────────
SUDOVI = {
    "get_criminal_record_person": {
        "aps_unique_name": "OSS1-5234",
        "service_id": 5234,
        "institution_group_id": 53,
        "institution_name": "Основни судови",
        "citizen_company": 1,
        "description": "Издавање потврда од казнена евиденција за физички лица",
    },
    "get_criminal_record_company": {
        "aps_unique_name": "OSS1-5235",
        "service_id": 5235,
        "institution_group_id": 53,
        "institution_name": "Основни судови",
        "citizen_company": 2,
        "description": "Издавање потврда од казнена евиденција за правни лица",
    },
    "get_criminal_proceedings_person": {
        "aps_unique_name": "OSS1-5236",
        "service_id": 5236,
        "institution_group_id": 53,
        "institution_name": "Основни судови",
        "citizen_company": 1,
        "description": "Издавање уверение од кривична евиденција за физички лица",
    },
    "get_criminal_proceedings_company": {
        "aps_unique_name": "OSS1-5237",
        "service_id": 5237,
        "institution_group_id": 53,
        "institution_name": "Основни судови",
        "citizen_company": 2,
        "description": "Издавање уверение од кривична евиденција за правни лица",
    },
}

# ─────────────────────────────────────────────
# Фонд на ПИОСМ (ID: 1732)
# ─────────────────────────────────────────────
PIOM = {
    "get_pension_registry_certificate": {
        "aps_unique_name": "PIOM-1826",
        "service_id": 1826,
        "institution_id": 1732,
        "institution_name": "Фонд на ПИОСМ",
        "citizen_company": 1,
        "description": "Уверение за регистрирани податоци во матична евиденција",
    },
    "get_work_capacity_assessment": {
        "aps_unique_name": "PIOM-5535",
        "service_id": 5535,
        "institution_id": 1732,
        "institution_name": "Фонд на ПИОСМ",
        "citizen_company": 1,
        "description": "Издавање наод, оценка и мислење за оцена на работната способност",
    },
    "get_pension_payments_periods": {
        "aps_unique_name": "PIOM-5545",
        "service_id": 5545,
        "institution_id": 1732,
        "institution_name": "Фонд на ПИОСМ",
        "citizen_company": 1,
        "description": "Потврда за исплатени пензии во периоди",
    },
    "get_pension_tax_overview": {
        "aps_unique_name": "PIOM-5546",
        "service_id": 5546,
        "institution_id": 1732,
        "institution_name": "Фонд на ПИОСМ",
        "citizen_company": 1,
        "description": "Преглед за пресметан и платен данок од доход за пензиски примања",
    },
    "get_pension_deductions": {
        "aps_unique_name": "PIOM-5547",
        "service_id": 5547,
        "institution_id": 1732,
        "institution_name": "Фонд на ПИОСМ",
        "citizen_company": 1,
        "description": "Потврда за исплатени пензии и спроведени задршки од пензија",
    },
    "get_bank_account_certificate": {
        "aps_unique_name": "PIOM-5550",
        "service_id": 5550,
        "institution_id": 1732,
        "institution_name": "Фонд на ПИОСМ",
        "citizen_company": 1,
        "description": "Потврда за сметка во банка",
    },
    "apply_insured_status_posted_workers": {
        "aps_unique_name": "PIOM-5544",
        "service_id": 5544,
        "institution_id": 1732,
        "institution_name": "Фонд на ПИОСМ",
        "citizen_company": 1,
        "description": "Барање за утврдување својство на осигуреник - упатени работници",
    },
    "apply_insured_status_abroad": {
        "aps_unique_name": "PIOM-5552",
        "service_id": 5552,
        "institution_id": 1732,
        "institution_name": "Фонд на ПИОСМ",
        "citizen_company": 1,
        "description": "Барање за утврдување својство на осигуреник - вработени во странство",
    },
    "apply_insured_status_religious": {
        "aps_unique_name": "PIOM-5553",
        "service_id": 5553,
        "institution_id": 1732,
        "institution_name": "Фонд на ПИОСМ",
        "citizen_company": 1,
        "description": "Барање за утврдување својство на осигуреник - верски службени лица",
    },
    "apply_insured_status_farmer": {
        "aps_unique_name": "PIOM-5554",
        "service_id": 5554,
        "institution_id": 1732,
        "institution_name": "Фонд на ПИОСМ",
        "citizen_company": 1,
        "description": "Барање за утврдување својство на осигуреник - индивидуален земјоделец",
    },
    "apply_insured_status_continued": {
        "aps_unique_name": "PIOM-5555",
        "service_id": 5555,
        "institution_id": 1732,
        "institution_name": "Фонд на ПИОСМ",
        "citizen_company": 1,
        "description": "Барање за утврдување својство на осигуреник - продолжено осигурување",
    },
    "apply_work_rights_assessment": {
        "aps_unique_name": "PIOM-5557",
        "service_id": 5557,
        "institution_id": 1732,
        "institution_name": "Фонд на ПИОСМ",
        "citizen_company": 1,
        "description": "Барање за наод, оцена и мислење за права од Законот за работни односи",
    },
    "apply_retirement_pension": {
        "aps_unique_name": "PIOM-5560",
        "service_id": 5560,
        "institution_id": 1732,
        "institution_name": "Фонд на ПИОСМ",
        "citizen_company": 1,
        "description": "Барање за остварување на право на старосна пензија",
    },
    "get_pension_status_certificate": {
        "aps_unique_name": "PIOM-5651",
        "service_id": 5651,
        "institution_id": 1732,
        "institution_name": "Фонд на ПИОСМ",
        "citizen_company": 1,
        "description": "Потврда за пензионирање без податоци за плаќање",
    },
}

# ─────────────────────────────────────────────
# ЈП Службен весник на РСМ (ID: 1617)
# ─────────────────────────────────────────────
SLV = {
    "apply_invalid_military_booklet": {"aps_unique_name": "SLV-1893", "service_id": 1893, "institution_id": 1617, "institution_name": "Службен весник", "citizen_company": 1, "description": "Објавување на неважечка воена книшка"},
    "apply_invalid_certificate": {"aps_unique_name": "SLV-1894", "service_id": 1894, "institution_id": 1617, "institution_name": "Службен весник", "citizen_company": 1, "description": "Објавување на неважечко свидетелство"},
    "apply_invalid_index": {"aps_unique_name": "SLV-1896", "service_id": 1896, "institution_id": 1617, "institution_name": "Службен весник", "citizen_company": 1, "description": "Објавување на неважечки индекс"},
    "apply_invalid_weapon_permit": {"aps_unique_name": "SLV-1897", "service_id": 1897, "institution_id": 1617, "institution_name": "Службен весник", "citizen_company": 1, "description": "Објавување на неважечка дозвола за оружје"},
    "apply_invalid_diploma": {"aps_unique_name": "SLV-1898", "service_id": 1898, "institution_id": 1617, "institution_name": "Службен весник", "citizen_company": 1, "description": "Објавување на неважечка диплома"},
    "apply_invalid_student_id": {"aps_unique_name": "SLV-1899", "service_id": 1899, "institution_id": 1617, "institution_name": "Службен весник", "citizen_company": 1, "description": "Објавување на неважечка студентска легитимација"},
    "apply_invalid_booklet_other": {"aps_unique_name": "SLV-1900", "service_id": 1900, "institution_id": 1617, "institution_name": "Службен весник", "citizen_company": 1, "description": "Објавување на неважечка легитимација, книшка и друго"},
    "apply_invalid_savings_booklet": {"aps_unique_name": "SLV-1901", "service_id": 1901, "institution_id": 1617, "institution_name": "Службен весник", "citizen_company": 1, "description": "Објавување на неважечка штедна книшка"},
    "apply_invalid_military_id": {"aps_unique_name": "SLV-1902", "service_id": 1902, "institution_id": 1617, "institution_name": "Службен весник", "citizen_company": 1, "description": "Објавување на неважечка воена легитимација"},
    "apply_invalid_attestation": {"aps_unique_name": "SLV-1903", "service_id": 1903, "institution_id": 1617, "institution_name": "Службен весник", "citizen_company": 1, "description": "Објавување на неважечко уверение"},
    "apply_invalid_forex_savings": {"aps_unique_name": "SLV-1904", "service_id": 1904, "institution_id": 1617, "institution_name": "Службен весник", "citizen_company": 1, "description": "Објавување на неважечка девизна штедна книшка"},
    "apply_invalid_tax_card": {"aps_unique_name": "SLV-1905", "service_id": 1905, "institution_id": 1617, "institution_name": "Службен весник", "citizen_company": 1, "description": "Објавување на неважечка даночна картичка"},
    "apply_invalid_permit_other": {"aps_unique_name": "SLV-1906", "service_id": 1906, "institution_id": 1617, "institution_name": "Службен весник", "citizen_company": 1, "description": "Објавување на неважечка дозвола (други видови)"},
    "apply_invalid_cemt_permit": {"aps_unique_name": "SLV-1907", "service_id": 1907, "institution_id": 1617, "institution_name": "Службен весник", "citizen_company": 1, "description": "Објавување на неважечка цемт дозвола"},
    "apply_invalid_adr_permit": {"aps_unique_name": "SLV-1908", "service_id": 1908, "institution_id": 1617, "institution_name": "Службен весник", "citizen_company": 1, "description": "Објавување на неважечка адр дозвола/потврда"},
    "apply_invalid_certificate_doc": {"aps_unique_name": "SLV-1909", "service_id": 1909, "institution_id": 1617, "institution_name": "Службен весник", "citizen_company": 1, "description": "Објавување на неважечки сертификат"},
    "apply_invalid_policy": {"aps_unique_name": "SLV-1910", "service_id": 1910, "institution_id": 1617, "institution_name": "Службен весник", "citizen_company": 1, "description": "Објавување на неважечка полиса"},
    "apply_invalid_craft_license": {"aps_unique_name": "SLV-1912", "service_id": 1912, "institution_id": 1617, "institution_name": "Службен весник", "citizen_company": 1, "description": "Објавување на неважечко решение за занаетчиска дејност"},
}

# ─────────────────────────────────────────────
# Министерство за култура и туризам (ID: 912)
# ─────────────────────────────────────────────
KULTURA = {
    "apply_culture_city_competition": {"aps_unique_name": "MK-5537", "service_id": 5537, "institution_id": 912, "institution_name": "М. Култура и туризам", "citizen_company": 2, "description": "Конкурс Град на културата"},
    "apply_artist_monthly_allowance_2026": {"aps_unique_name": "MK-6081", "service_id": 6081, "institution_id": 912, "institution_name": "М. Култура и туризам", "citizen_company": 2, "description": "Конкурс за месечни надоместоци на самостојни уметници 2026"},
}

# ─────────────────────────────────────────────
# Агенција за вработување (ID: 880)
# Prefix: INFERRED - needs verification
# ─────────────────────────────────────────────
AVRSM = {
    "get_unemployed_person_certificate": {"aps_unique_name": "AVRSM-4963", "service_id": 4963, "institution_id": 880, "institution_name": "А. Вработување", "citizen_company": 1, "description": "Издавање потврда за евидентирано невработено лице"},
    "get_jobseeker_certificate": {"aps_unique_name": "AVRSM-4964", "service_id": 4964, "institution_id": 880, "institution_name": "А. Вработување", "citizen_company": 1, "description": "Издавање потврда за друго лице кое бара работа"},
    "get_m1m2_extract": {"aps_unique_name": "AVRSM-5010", "service_id": 5010, "institution_id": 880, "institution_name": "А. Вработување", "citizen_company": 1, "description": "Издавање извод од компјутерски запис - образец М1/М2"},
    "get_employment_history": {"aps_unique_name": "AVRSM-5011", "service_id": 5011, "institution_id": 880, "institution_name": "А. Вработување", "citizen_company": 3, "description": "Издавање историјат на работни односи"},
    "get_active_registrations_count": {"aps_unique_name": "AVRSM-5229", "service_id": 5229, "institution_id": 880, "institution_name": "А. Вработување", "citizen_company": 2, "description": "Потврда за број на активни пријави во социјално осигурување"},
    "get_active_registrations_view": {"aps_unique_name": "AVRSM-5230", "service_id": 5230, "institution_id": 880, "institution_name": "А. Вработување", "citizen_company": 2, "description": "Преглед на активни пријави во социјално осигурување"},
    "get_open_balkan_certificate": {"aps_unique_name": "AVRSM-5603", "service_id": 5603, "institution_id": 880, "institution_name": "А. Вработување", "citizen_company": 1, "description": "Потврда за слободен пристап до пазар на труд (Отворен Балкан)"},
}

# ─────────────────────────────────────────────
# Министерство за дигитална трансформација (ID: 1192)
# Prefix: INFERRED - needs verification
# ─────────────────────────────────────────────
MDT = {
    "get_personal_data_certificate": {"aps_unique_name": "MDT-5021", "service_id": 5021, "institution_id": 1192, "institution_name": "М. Дигитална трансформација", "citizen_company": 1, "description": "Потврда за содржани лични податоци во ЦРН"},
    "get_data_access_logs": {"aps_unique_name": "MDT-5056", "service_id": 5056, "institution_id": 1192, "institution_name": "М. Дигитална трансформација", "citizen_company": 1, "description": "Увид во листа на логови за пристап до лични податоци"},
    "apply_unpaid_internship": {"aps_unique_name": "MDT-5973", "service_id": 5973, "institution_id": 1192, "institution_name": "М. Дигитална трансформација", "citizen_company": 1, "description": "Пријавување за неплатена практикантска работа во МДТ"},
}

# ─────────────────────────────────────────────
# Министерство за правда (ID: 1751)
# Prefix: INFERRED - needs verification
# ─────────────────────────────────────────────
PRAVDA = {
    "apply_bar_exam": {"aps_unique_name": "MP-5277", "service_id": 5277, "institution_id": 1751, "institution_name": "М. Правда", "citizen_company": 1, "description": "Полагање на правосуден испит"},
    "apply_bar_exam_additional": {"aps_unique_name": "MP-5276", "service_id": 5276, "institution_id": 1751, "institution_name": "М. Правда", "citizen_company": 1, "description": "Дополнително полагање на правосудни испити"},
    "apply_translator_exam": {"aps_unique_name": "MP-5328", "service_id": 5328, "institution_id": 1751, "institution_name": "М. Правда", "citizen_company": 1, "description": "Пријавување на испит за судски преведувачи"},
    "apply_translator_change": {"aps_unique_name": "MP-5752", "service_id": 5752, "institution_id": 1751, "institution_name": "М. Правда", "citizen_company": 1, "description": "Промена на решение за судски преведувачи"},
    "apply_macedonia_name_usage_company": {"aps_unique_name": "MP-5282", "service_id": 5282, "institution_id": 1751, "institution_name": "М. Правда", "citizen_company": 2, "description": "Одобрение за употреба на зборот Македонија - организација"},
    "apply_macedonia_name_usage_person": {"aps_unique_name": "MP-5751", "service_id": 5751, "institution_id": 1751, "institution_name": "М. Правда", "citizen_company": 1, "description": "Одобрение за употреба на зборот Македонија - физичко лице"},
    "apply_donation_public_interest": {"aps_unique_name": "MP-5290", "service_id": 5290, "institution_id": 1751, "institution_name": "М. Правда", "citizen_company": 3, "description": "Решение за потврдување јавен интерес на донација"},
    "apply_donation_public_interest_person": {"aps_unique_name": "MP-5750", "service_id": 5750, "institution_id": 1751, "institution_name": "М. Правда", "citizen_company": 1, "description": "Решение за јавен интерес на донација - физичко лице"},
}

# ─────────────────────────────────────────────
# Фонд за здравствено осигурување (ID: 1927)
# Prefix: INFERRED - needs verification
# ─────────────────────────────────────────────
FZO = {
    "get_health_insurance_status": {"aps_unique_name": "FZO-6108", "service_id": 6108, "institution_id": 1927, "institution_name": "Фонд за ЗО", "citizen_company": 1, "description": "Потврда за осигурано/неосигурано лице и платен/неплатен придонес"},
    "get_health_insurance_company": {"aps_unique_name": "FZO-6109", "service_id": 6109, "institution_id": 1927, "institution_name": "Фонд за ЗО", "citizen_company": 2, "description": "Потврда за платен/неплатен придонес за правни лица"},
    "get_health_insurance_registrations": {"aps_unique_name": "FZO-6110", "service_id": 6110, "institution_id": 1927, "institution_name": "Фонд за ЗО", "citizen_company": 1, "description": "Потврда за пријави и одјави во здравствено осигурување"},
    "get_health_salary_compensation": {"aps_unique_name": "FZO-6111", "service_id": 6111, "institution_id": 1927, "institution_name": "Фонд за ЗО", "citizen_company": 1, "description": "Потврда за исплатен надоместок на плата"},
}

# ─────────────────────────────────────────────
# Влада на РСМ (ID: 887)
# ─────────────────────────────────────────────
VLADA = {
    "apply_student_voucher": {"aps_unique_name": "VLADA-5980", "service_id": 5980, "institution_id": 887, "institution_name": "Влада на РСМ", "citizen_company": 1, "description": "Јавен повик за вредносни ваучери за студенти"},
    "apply_student_voucher_manual": {"aps_unique_name": "VLADA-5983", "service_id": 5983, "institution_id": 887, "institution_name": "Влада на РСМ", "citizen_company": 1, "description": "Јавен повик за ваучери (студенти надвор од МОН регистар)"},
}

# ─────────────────────────────────────────────
# Агенција за филм (ID: 955)
# ─────────────────────────────────────────────
FILM = {
    "apply_film_training_support": {"aps_unique_name": "AF-6169", "service_id": 6169, "institution_id": 955, "institution_name": "А. Филм", "citizen_company": 1, "description": "Конкурс за стручно усовршување на кадри од областа на филмот"},
    "apply_film_international_membership": {"aps_unique_name": "AF-6170", "service_id": 6170, "institution_id": 955, "institution_name": "А. Филм", "citizen_company": 2, "description": "Конкурс за членство на РСМ во меѓународни филмски организации"},
}


# ─────────────────────────────────────────────
# Master lookup
# ─────────────────────────────────────────────
ALL_REGISTRIES = {
    "nbrsm": NBRSM,
    "sudovi": SUDOVI,
    "piom": PIOM,
    "sluzhben_vesnik": SLV,
    "kultura": KULTURA,
    "vrabotuvanje": AVRSM,
    "mdt": MDT,
    "pravda": PRAVDA,
    "fzo": FZO,
    "vlada": VLADA,
    "film": FILM,
}

ALL_SERVICES = {}
for _reg in ALL_REGISTRIES.values():
    ALL_SERVICES.update(_reg)


def get_service(name: str) -> dict:
    """Lookup a service by function name.  Raises ValueError if not found."""
    if name not in ALL_SERVICES:
        raise ValueError(f"Unknown service: {name}")
    return ALL_SERVICES[name]


def list_services_for_institution(institution_slug: str) -> dict:
    """Return all services for a given institution slug."""
    if institution_slug not in ALL_REGISTRIES:
        raise ValueError(
            f"Unknown institution: {institution_slug}. "
            f"Available: {list(ALL_REGISTRIES.keys())}"
        )
    return ALL_REGISTRIES[institution_slug]
