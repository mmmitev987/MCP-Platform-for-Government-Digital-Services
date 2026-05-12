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

Typical agent flow (no login required for public tools):

  By имотен лист:
    katastar__search_property(municipality_name="КУМАНОВО", property_certificate="14")

  By парцела number:
    katastar__search_property(municipality_name="КУМАНОВО", parcel_number="18421/1")

  Login only needed for favorites:
    katastar__login → katastar__check_property_favorited(591908)
"""

import re
import requests
from pyproj import Transformer as _Transformer

# EPSG:6316 = MGI 1901 / Balkans zone 7  (exactly what the katastar website uses)
# Proj4: +proj=tmerc +lon_0=21 +k=0.9999 +x_0=7500000 +y_0=0
#        +ellps=bessel +towgs84=682,-203,480,0,0,0,0
# always_xy=True → input (easting, northing), output (longitude, latitude)
_GK_TO_WGS84 = _Transformer.from_crs("EPSG:6316", "EPSG:4326", always_xy=True)

from institutions.katastar.client.http_client import (
    authenticated_client,
    SessionExpiredError,
)
from institutions.katastar.config import PORTAL_BASE_URL
from institutions.shared.errors import tool_error

_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "mk-MK,mk;q=0.9,en;q=0.8",
    "Origin": PORTAL_BASE_URL,
    "Referer": PORTAL_BASE_URL + "/",
}


def _public_get(url: str, **kwargs) -> requests.Response:
    """Plain GET — no session cookies required."""
    try:
        response = requests.get(url, headers=_HEADERS, timeout=20, **kwargs)
        response.raise_for_status()
        return response
    except requests.RequestException as e:
        raise RuntimeError(f"Public GET failed for {url}: {e}") from e


def _gk_to_wgs84(x: float, y: float) -> tuple[float, float]:
    """
    Convert Macedonian Gauss-Krüger zone 7 (EPSG:6316) coordinates to WGS84.

    Uses pyproj with the exact CRS definition from the katastar website:
      EPSG:6316 = MGI 1901 / Balkans zone 7
      +proj=tmerc +lon_0=21 +k=0.9999 +x_0=7500000 +y_0=0
      +ellps=bessel +towgs84=682,-203,480,0,0,0,0

    Args:
        x: Easting with zone prefix, e.g. 7537777.34
        y: Northing, e.g. 4660014.29

    Returns:
        (latitude, longitude) in decimal degrees (WGS84)
    """
    lon, lat = _GK_TO_WGS84.transform(x, y)
    return round(lat, 7), round(lon, 7)


def _parse_polygon_wgs84(wkt: str) -> dict | None:
    """
    Parse a WKT POLYGON in GK coordinates and return WGS84 polygon + centroid.

    Returns:
        {
            "polygon": [[lat, lon], ...],   # for Leaflet Polygon
            "centroid": [lat, lon],          # for map centering
        }
        or None if parsing fails.
    """
    try:
        pairs = re.findall(r"([\d.]+)\s+([\d.]+)", wkt)
        if not pairs:
            return None
        wgs_points = [_gk_to_wgs84(float(x), float(y)) for x, y in pairs]
        # Remove duplicate closing point if polygon is closed
        if wgs_points[0] == wgs_points[-1]:
            wgs_points = wgs_points[:-1]
        centroid_lat = sum(p[0] for p in wgs_points) / len(wgs_points)
        centroid_lon = sum(p[1] for p in wgs_points) / len(wgs_points)
        return {
            "polygon":  wgs_points,
            "centroid": [round(centroid_lat, 7), round(centroid_lon, 7)],
        }
    except Exception:
        return None


def _err(e: Exception) -> dict:
    if isinstance(e, SessionExpiredError):
        return tool_error("auth_required", "Call katastar__login to authenticate first.")
    return tool_error("unexpected_error", str(e))


def search_municipality(search_string: str) -> dict:
    """
    Search for a cadastre municipality by name (Macedonian or Latin script).

    Returns departmentID and municipalityID — required for all other tools.

    Args:
        search_string: e.g. "КУМАНОВО", "SKOPJE", "БИТОЛА"
    """
    try:
        results = _public_get(
            f"{PORTAL_BASE_URL}/api/v2/cadastreMunicipalities/search",
            params={"searchString": search_string},
        ).json()

        if not results:
            return tool_error("not_found", f"No municipality found for '{search_string}'.")
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
        return _public_get(
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
        return _public_get(
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
        data = _public_get(
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
        data = _public_get(
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
        data = _public_get(
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


def search_property(
    municipality_name: str,
    property_certificate: str | None = None,
    parcel_number: str | None = None,
) -> dict:
    """
    Search for property data by катастарска општина + имотен лист OR парцела number.

    This is the main combined search tool — it resolves the municipality name
    automatically and returns parcels, buildings and total area in one call.

    Provide exactly ONE of property_certificate or parcel_number:

      • municipality_name + property_certificate
            → returns all parcels and buildings for that имотен лист.

      • municipality_name + parcel_number  (e.g. "45", "18421/1")
            → looks up which имотен лист contains that парцела
              and returns its full data.

    Args:
        municipality_name:    Cadastral municipality name, e.g. "КУМАНОВО",
                              "ЦЕНТАР", "БИТОЛА". Latin script also accepted.
        property_certificate: Имотен лист number, e.g. "14".
        parcel_number:        Cadastral parcel number, e.g. "18421/1".

    Returns:
        {
            "municipality":        { departmentID, municipalityID, name },
            "property_certificate": str,
            "right_holders":       list[{ firstAndLastName, city, street, partOwned }],
            "parcels":             list[{ parcel, usageName, usageFullName, area, location, propertyRight }],
            "objects":             list[{ usageName, usageFullName, area, floor, entrance, apartmentNumber, propertyRight }],
            "totalParcelArea":     float | None,
            "documentType":        str | None,
            "certificate_price":   { amount, currency, product_name } | None,
            "geometry":            { polygon: [[lat,lon],...], centroid: [lat,lon] } | None,
        }
        On error: { "error": True, "code": str, "message": str }
    """
    if not property_certificate and not parcel_number:
        return tool_error("invalid_input", "Provide either property_certificate or parcel_number.")
    if property_certificate and parcel_number:
        return tool_error("invalid_input", "Provide only one of property_certificate or parcel_number, not both.")

    try:
        # ── Step 1: resolve municipality name → IDs ───────────────────────────
        mun_results = _public_get(
            f"{PORTAL_BASE_URL}/api/v2/cadastreMunicipalities/search",
            params={"searchString": municipality_name},
        ).json()

        if not mun_results:
            return tool_error("not_found", f"Municipality '{municipality_name}' not found.")

        mun = mun_results[0]
        dept_id = mun["departmentID"]
        mun_id  = mun["municipalityID"]

        # ── Step 2: resolve parcel_number → property_certificate via API ────────
        if parcel_number:
            # Step 2a: get parcelID from parcel number
            parcel_resp = _public_get(
                f"{PORTAL_BASE_URL}/api/v2/parcels/findByParcelNumber"
                f"/{dept_id}/{mun_id}",
                params={"parcelNumber": parcel_number},
            ).json()

            if not parcel_resp or "id" not in parcel_resp:
                return tool_error(
                    "not_found",
                    f"Parcel '{parcel_number}' not found in municipality '{municipality_name}'."
                )

            parcel_id = parcel_resp["id"]

            # Step 2b: get имотен лист number from parcelID
            cert_resp = _public_get(
                f"{PORTAL_BASE_URL}/api/v2/propertyCertificates/getPropertyCertificate"
                f"/{dept_id}/{mun_id}",
                params={"parcelID": parcel_id},
            ).json()

            if not cert_resp or "propertyCertificate" not in cert_resp:
                return tool_error(
                    "not_found",
                    f"Could not find имотен лист for parcel '{parcel_number}'."
                )

            property_certificate = cert_resp["propertyCertificate"]

        # ── Step 3: fetch parcels, right holders and area ────────────────────
        parcels_data = _public_get(
            f"{PORTAL_BASE_URL}/api/v2/propertyCertificates/findParcels"
            f"/{dept_id}/{mun_id}",
            params={"propertyCertificate": property_certificate, "page": 0, "size": 50},
        ).json()

        right_holders_data = _public_get(
            f"{PORTAL_BASE_URL}/api/v2/propertyCertificates/findRightHoldersPageable"
            f"/{dept_id}/{mun_id}",
            params={"propertyCertificate": property_certificate, "page": 0, "size": 50},
        ).json()

        area_data = _public_get(
            f"{PORTAL_BASE_URL}/api/v2/propertyCertificates"
            f"/checkDocumentTypeAndGetTotalParcelArea"
            f"/{dept_id}/{mun_id}",
            params={"propertyCertificate": property_certificate},
        ).json()

        # ── Step 4: fetch objects ────────────────────────────────────────────────
        # Strategy A (land parcel exists): use parcels/findBuildingsPageable per
        #   parcel number — richer data (floor, entrance, apt number, etc.)
        # Strategy B (apartment-only, no land parcels): fall back to
        #   propertyCertificates/findBuildingsPageable which always has data.
        parcels_list = parcels_data.get("content", [])
        unique_parcel_numbers = list({p["parcel"] for p in parcels_list if p.get("parcel")})

        all_objects = []
        for pnum in unique_parcel_numbers:
            try:
                obj_data = _public_get(
                    f"{PORTAL_BASE_URL}/api/v2/parcels/findBuildingsPageable"
                    f"/{dept_id}/{mun_id}",
                    params={"parcelNumber": pnum, "page": 0, "size": 50},
                ).json()
                for obj in obj_data.get("content", []):
                    if str(obj.get("propertyCertificate")) == str(property_certificate):
                        all_objects.append(obj)
            except Exception:
                continue

        # Fallback: apartment/building-only certificates have no land parcels
        # but propertyCertificates/findBuildingsPageable always works.
        if not all_objects:
            try:
                cert_bld = _public_get(
                    f"{PORTAL_BASE_URL}/api/v2/propertyCertificates/findBuildingsPageable"
                    f"/{dept_id}/{mun_id}",
                    params={"propertyCertificate": property_certificate, "page": 0, "size": 50},
                ).json()
                all_objects = cert_bld.get("content", [])
            except Exception:
                pass

        # ── Step 5: fetch parcel geometry and convert to WGS84 ───────────────
        # Prefer a parcelID from land parcels; fall back to one from buildings
        # (apartment blocks share the land parcel of the building they're in).
        geometry = None
        first_parcel_id = next(
            (p.get("parcelID") for p in parcels_list if p.get("parcelID")), None
        )
        if not first_parcel_id:
            # Apartment-only: grab parcelID from the buildings list
            first_parcel_id = next(
                (o.get("parcelID") for o in all_objects if o.get("parcelID")), None
            )
        if not first_parcel_id and parcel_number:
            # parcel_number path: we have the parcelID from step 2a
            first_parcel_id = parcel_id  # noqa: F821 — set earlier in parcel_number branch

        if first_parcel_id:
            try:
                geo_resp = requests.post(
                    f"{PORTAL_BASE_URL}/api/v2/geo/parcelGeometryByParcelID",
                    headers=_HEADERS,
                    data=str(first_parcel_id),
                    timeout=10,
                )
                geo_data = geo_resp.json()
                wkt = geo_data.get("GEOMETRY", "")
                if wkt:
                    geometry = _parse_polygon_wgs84(wkt)
            except Exception:
                pass  # geometry is optional — don't fail the whole request

        # Extract price from area_data product info
        product = area_data.get("product", {})

        return {
            "municipality": {
                "departmentID":   dept_id,
                "municipalityID": mun_id,
                "name":           mun.get("municipalityName", municipality_name),
            },
            "property_certificate": property_certificate,
            "right_holders":        right_holders_data.get("content", []),
            "parcels":              parcels_list,
            "objects":              all_objects,
            "totalParcelArea":      area_data.get("totalParcelArea"),
            "documentType":         area_data.get("documentType"),
            "certificate_price": {
                "amount":      product.get("unitPrice"),
                "currency":    "MKD",
                "product_name": product.get("productName"),
            } if product else None,
            "geometry": geometry,  # { polygon: [[lat,lon],...], centroid: [lat,lon] }
        }

    except Exception as e:
        return _err(e)