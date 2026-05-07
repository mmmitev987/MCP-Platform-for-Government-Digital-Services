"""
institutions/mon/tools/document_tools.py
────────────────────────────────────────────────────────────────────────────────
Informational tools that tell you what you need in order to obtain an
official document from MON — required documents, conditions, fees, and
where to apply.

All functions are public — no authentication required.
"""

from institutions.shared.errors import tool_error

_DOCUMENT_CATALOG: dict[str, dict] = {
    "потврда_за_запис": {
        "name": "Потврда за запис (Certificate of Enrollment)",
        "description": "Official confirmation that you are currently enrolled at a higher-education institution.",
        "documents_required": [
            "Индекс или студентска легитимација",
            "Барање / молба до деканатот",
        ],
        "conditions": ["Активен студентски статус"],
        "fee": "Без надомест (besplatno)",
        "where_to_apply": "Студентска служба на вашиот факултет или преку е-uslugi.mon.gov.mk",
    },
    "уверение_за_завршено": {
        "name": "Уверение за завршено образование (Graduation Certificate)",
        "description": "Confirms successful completion of a study programme.",
        "documents_required": [
            "Индекс со сите положени испити",
            "Барање / молба до деканатот",
            "Доказ за уплатена административна такса (ако се бара)",
        ],
        "conditions": ["Положени сите предмети и одбранета дипломска/магистерска работа"],
        "fee": "Административна такса според тарифник на факултетот",
        "where_to_apply": "Студентска служба на вашиот факултет",
    },
    "нострификација": {
        "name": "Нострификација на диплома (Diploma Recognition)",
        "description": "Official recognition of a foreign diploma by the Ministry of Education.",
        "documents_required": [
            "Оригинална странска диплома + заверен превод на македонски",
            "Транскрипт на оценки + заверен превод",
            "Пасош или лична карта (копија)",
            "Барање до МОН",
            "Доказ за уплатена такса",
        ],
        "conditions": [
            "Дипломата мора да е издадена од акредитирана странска установа",
        ],
        "fee": "Според важечки тарифник на МОН",
        "where_to_apply": "Министерство за образование и наука — Одделение за нострификација, или преку е-uslugi.mon.gov.mk",
    },
    "уверение_стипендија": {
        "name": "Уверение за добиена стипендија (Scholarship Confirmation Letter)",
        "description": "Confirms that you are a recipient of a state or MON-administered scholarship.",
        "documents_required": [
            "Лична карта или пасош",
            "Барање до МОН / стипендирачкото тело",
            "Уверение за запис за тековната учебна година",
        ],
        "conditions": ["Активен статус на стипендист"],
        "fee": "Без надомест",
        "where_to_apply": "МОН — Одделение за стипендии, или преку е-uslugi.mon.gov.mk",
    },
    "уверение_оценки": {
        "name": "Уверение за положени испити / оценки (Transcript of Records)",
        "description": "Official list of all passed exams with grades.",
        "documents_required": [
            "Индекс",
            "Барање до деканатот / студентска служба",
        ],
        "conditions": ["Активен или завршен студентски статус"],
        "fee": "Административна такса според тарифник (обично 50–150 ден.)",
        "where_to_apply": "Студентска служба на вашиот факултет",
    },
}


def list_mon_document_types() -> dict:
    """
    List official document types that can be obtained through MON or faculty
    administration, along with a brief description of each.

    No arguments needed.

    Returns:
        {
            "document_types": list of { "type", "name", "description" }
        }
    """
    return {
        "document_types": [
            {
                "type":        key,
                "name":        info["name"],
                "description": info["description"],
            }
            for key, info in _DOCUMENT_CATALOG.items()
        ]
    }


def get_mon_document_requirements(document_type: str) -> dict:
    """
    Get everything you need in order to obtain a specific official document
    from MON or a higher-education institution.

    Args:
        document_type: One of the type keys returned by list_mon_document_types().
                       Examples:
                           "потврда_за_запис"     — Certificate of enrollment
                           "уверение_за_завршено" — Graduation certificate
                           "нострификација"       — Diploma recognition
                           "уверение_стипендија"  — Scholarship confirmation
                           "уверение_оценки"      — Transcript of records

    Returns:
        {
            "document_type":      str,
            "name":               str,
            "description":        str,
            "documents_required": list[str],
            "conditions":         list[str],
            "fee":                str,
            "where_to_apply":     str,
        }
    """
    info = _DOCUMENT_CATALOG.get(document_type)

    if info is None:
        available = list(_DOCUMENT_CATALOG.keys())
        return tool_error(
            "not_found",
            f"Unknown document type '{document_type}'. "
            f"Available types: {available}. "
            "Call list_mon_document_types() to see all options."
        )

    return {
        "document_type":      document_type,
        "name":               info["name"],
        "description":        info["description"],
        "documents_required": info["documents_required"],
        "conditions":         info["conditions"],
        "fee":                info["fee"],
        "where_to_apply":     info["where_to_apply"],
    }
