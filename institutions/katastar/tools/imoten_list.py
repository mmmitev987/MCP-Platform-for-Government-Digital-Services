"""
institutions/katastar/tools/imoten_list.py
────────────────────────────────────────────────────────────────────────────────
MCP tool implementations for e-uslugi.katastar.gov.mk — Имотен Лист.

API endpoints:

  search_municipality
    GET /api/v2/cadastreMunicipalities/search?searchString=КУМАНОВО

  get_cadastre_department
    GET /api/v2/cadastreDepartments/{department_id}

  get_cadastre_municipality
    GET /api/v2/cadastreMunicipalities/{department_id}/{municipality_id}

  find_parcels
    GET /api/v2/propertyCertificates/findParcels/{dept_id}/{mun_id}
        ?propertyCertificate=14&page=0&size=10

  get_parcel_geometry
    GET /api/v2/geo/parcelGeometryByParcelID?parcelID=6121651

  check_property_favorited
    POST /api/v2/favorites/checkIfPropertyIsFavorited
    Body: { "id": 591908 }

Typical agent flow:
  katastar__login
    → katastar__search_municipality("КУМАНОВО")       # dept=17, mun=52
    → katastar__find_parcels(17, 52, "14")            # list parcels
    → katastar__get_parcel_geometry(parcelID)         # map geometry
"""

from institutions.katastar.client.http_client import (
    authenticated_client,
    SessionExpiredError,
)
from institutions.katastar.config import PORTAL_BASE_URL


def _err(e: Exception) -> dict:
    if isinstance(e, SessionExpiredError):
        return {
            "error": str(e),
            "action": "Call katastar__login to authenticate first.",
        }
    return {"error": str(e)}


def search_municipality(search_string: str) -> dict:
    """
    Search for a cadastre municipality by name (Macedonian or Latin script).

    Returns departmentID and municipalityID — required for all other tools.

    Args:
        search_string: e.g. "КУМАНОВО", "SKOPJE", "БИТОЛА"
    """
    try:
        results = authenticated_client.get(
            f"{PORTAL_BASE_URL}/api/v2/cadastreMunicipalities/search",
            params={"searchString": search_string},
        ).json()

        if not results:
            return {"error": f"No municipality found for '{search_string}'."}
        return results[0]

    except Exception as e:
        return _err(e)


def get_cadastre_department(department_id: int) -> dict:
    """
    Return details for a cadastre department by its numeric ID.

    Args:
        department_id: e.g. 17 for Куманово department.
    """
    try:
        return authenticated_client.get(
            f"{PORTAL_BASE_URL}/api/v2/cadastreDepartments/{department_id}"
        ).json()
    except Exception as e:
        return _err(e)


def get_cadastre_municipality(department_id: int, municipality_id: int) -> dict:
    """
    Return details for a specific cadastre municipality.

    Args:
        department_id:   e.g. 17
        municipality_id: e.g. 52
    """
    try:
        return authenticated_client.get(
            f"{PORTAL_BASE_URL}/api/v2/cadastreMunicipalities"
            f"/{department_id}/{municipality_id}"
        ).json()
    except Exception as e:
        return _err(e)


def find_parcels(
    department_id: int,
    municipality_id: int,
    property_certificate: str,
    page: int = 0,
    size: int = 10,
) -> dict:
    """
    Return paginated parcels for a property certificate (имотен лист).

    Each parcel includes: parcelID, cadastre number, usage type,
    area (m²), location, propertyRight.

    Args:
        department_id:        e.g. 17
        municipality_id:      e.g. 52
        property_certificate: Imoten list number, e.g. "14"
        page:                 Zero-based page index (default 0)
        size:                 Results per page (default 10)

    Returns:
        {
            "parcels":       list[dict],
            "totalElements": int,
            "totalPages":    int,
            "currentPage":   int,
        }
    """
    try:
        data = authenticated_client.get(
            f"{PORTAL_BASE_URL}/api/v2/propertyCertificates/findParcels"
            f"/{department_id}/{municipality_id}",
            params={
                "propertyCertificate": property_certificate,
                "page": page,
                "size": size,
            },
        ).json()

        return {
            "parcels":       data.get("content", []),
            "totalElements": data.get("totalElements", 0),
            "totalPages":    data.get("totalPages", 1),
            "currentPage":   data.get("number", 0),
        }
    except Exception as e:
        return _err(e)





def check_property_favorited(property_certificate_id: int) -> dict:
    """
    Check whether a property certificate is in the user's favorites.

    Args:
        property_certificate_id: Internal certificate ID, e.g. 591908.
    """
    try:
        return authenticated_client.post(
            f"{PORTAL_BASE_URL}/api/v2/favorites/checkIfPropertyIsFavorited",
            json={"id": property_certificate_id},
        ).json()
    except Exception as e:
        return _err(e)




def find_buildings(
    department_id: int,
    municipality_id: int,
    property_certificate: str,
    page: int = 0,
    size: int = 10,
) -> dict:
    """
    Return paginated buildings for a property certificate (имотен лист).

    API endpoint:
        GET /api/v2/propertyCertificates/findBuildingsPageable/{dept_id}/{mun_id}
            ?propertyCertificate=14&page=0&size=10

    Args:
        department_id:        e.g. 17
        municipality_id:      e.g. 52
        property_certificate: Imoten list number, e.g. "14"
        page:                 Zero-based page index (default 0)
        size:                 Results per page (default 10)
    """
    try:
        data = authenticated_client.get(
            f"{PORTAL_BASE_URL}/api/v2/propertyCertificates/findBuildingsPageable"
            f"/{department_id}/{municipality_id}",
            params={
                "propertyCertificate": property_certificate,
                "page": page,
                "size": size,
            },
        ).json()

        return {
            "buildings":     data.get("content", []),
            "totalElements": data.get("totalElements", 0),
            "totalPages":    data.get("totalPages", 1),
            "currentPage":   data.get("number", 0),
        }
    except Exception as e:
        return _err(e)



def get_total_parcel_area(
    department_id: int,
    municipality_id: int,
    property_certificate: str,
) -> dict:
    """
    Return document type and total parcel area for a property certificate.

    API endpoint:
        GET /api/v2/propertyCertificates/checkDocumentTypeAndGetTotalParcelArea
            /{dept_id}/{mun_id}?propertyCertificate=14

    Args:
        department_id:        e.g. 17
        municipality_id:      e.g. 52
        property_certificate: Imoten list number, e.g. "14"
    """
    try:
        data = authenticated_client.get(
            f"{PORTAL_BASE_URL}/api/v2/propertyCertificates"
            f"/checkDocumentTypeAndGetTotalParcelArea"
            f"/{department_id}/{municipality_id}",
            params={"propertyCertificate": property_certificate},
        ).json()

        return {
            "propertyCertificate": property_certificate,
            "documentType":        data.get("documentType"),
            "totalParcelArea":     data.get("totalParcelArea"),
            "raw":                 data,
        }
    except Exception as e:
        return _err(e)