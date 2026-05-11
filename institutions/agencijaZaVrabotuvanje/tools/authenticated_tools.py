import base64
import time
from typing import Any

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from institutions.agencijaZaVrabotuvanje.client import (
    authenticated_client,
    SessionExpiredError,
)
from institutions.agencijaZaVrabotuvanje.config import (
    PORTAL_BASE_URL,
    PROTECTED_HOME_URL,
    EDIT_CV_LIST_URL,
    CV_CREATE_EDIT_URL,
    CV_PRINT_URL,
    COOKIE_DOMAIN,
)
from institutions.agencijaZaVrabotuvanje.parsers.jobs_parser import parse_favourite_jobs
from institutions.agencijaZaVrabotuvanje.auth.session import session_manager
from institutions.agencijaZaVrabotuvanje.parsers.dashboard_parser import parse_dashboard
from institutions.agencijaZaVrabotuvanje.parsers.cv_parser import (
    parse_cv_list,
    parse_cv_edit_page,
)


def _looks_like_login_page(html: str, final_url: str = "") -> bool:
    html_lower = (html or "").lower()
    url_lower = (final_url or "").lower()

    return (
        "eid.mk" in url_lower
        or "signin" in url_lower
        or "login" in url_lower
        or "најави" in html_lower
        or "signin" in html_lower
    )


def _session_expired_response() -> dict:
    return {
        "success": False,
        "authenticated": False,
        "error": "Session expired or missing. Please login again.",
    }


def _unexpected_error_response(error: Exception) -> dict:
    return {
        "success": False,
        "authenticated": None,
        "error": str(error),
    }


def _normalize_cookies(raw_cookies) -> list[dict]:
    """
    Normalize cookies for Selenium driver injection.
    
    Note: This is kept separate from authenticated_client because Selenium
    requires a different cookie format (list of dicts with domain/path/expiry)
    than requests.Session (which uses a simple dict).
    """
    if not raw_cookies:
        return []

    if isinstance(raw_cookies, dict):
        return [
            {
                "name": name,
                "value": value,
                "domain": COOKIE_DOMAIN,
                "path": "/",
            }
            for name, value in raw_cookies.items()
        ]

    if isinstance(raw_cookies, list):
        normalized = []
        for cookie in raw_cookies:
            if not isinstance(cookie, dict):
                continue

            name = cookie.get("name")
            value = cookie.get("value")

            if not name or value is None:
                continue

            normalized.append({
                "name": name,
                "value": value,
                "domain": cookie.get("domain") or COOKIE_DOMAIN,
                "path": cookie.get("path", "/"),
                "expiry": cookie.get("expiry"),
            })

        return normalized

    return []


def _get_session_cookies() -> list[dict]:
    """Get session cookies in Selenium format."""
    raw_cookies = session_manager.load()

    cookies = _normalize_cookies(raw_cookies)

    if not cookies:
        raise SessionExpiredError("No saved session cookies.")

    return cookies


def _get_driver() -> webdriver.Chrome:
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")

    return webdriver.Chrome(options=options)


def _load_session_cookies_into_driver(driver: webdriver.Chrome) -> None:
    driver.get(PORTAL_BASE_URL)

    cookies = _get_session_cookies()

    for cookie in cookies:
        clean_cookie = {
            "name": cookie["name"],
            "value": cookie["value"],
            "domain": cookie.get("domain") or COOKIE_DOMAIN,
            "path": cookie.get("path", "/"),
        }

        if cookie.get("expiry"):
            clean_cookie["expiry"] = int(cookie["expiry"])

        try:
            driver.add_cookie(clean_cookie)
        except Exception:
            pass


def _safe_set_text(driver: webdriver.Chrome, element_id: str, value: Any) -> bool:
    if value is None:
        return False

    try:
        el = driver.find_element(By.ID, element_id)
        el.clear()
        el.send_keys(str(value))
        return True
    except Exception:
        return False


def _safe_click(driver: webdriver.Chrome, element_id: str) -> bool:
    try:
        el = driver.find_element(By.ID, element_id)
        driver.execute_script("arguments[0].click();", el)
        time.sleep(1)
        return True
    except Exception:
        return False


def _validate_cv_exists(cv_id: str) -> dict | None:
    response = authenticated_client.get(EDIT_CV_LIST_URL)
    html = response.text
    final_url = getattr(response, "url", "")

    if _looks_like_login_page(html, final_url):
        raise SessionExpiredError("Session expired.")

    cvs = parse_cv_list(html)
    return next((cv for cv in cvs if str(cv.get("cv_id")) == str(cv_id)), None)

def _select_cv(cv_id: str | None = None) -> tuple[dict | None, dict | None]:
    response = authenticated_client.get(EDIT_CV_LIST_URL)
    html = response.text
    final_url = getattr(response, "url", "")

    if _looks_like_login_page(html, final_url):
        raise SessionExpiredError("Session expired.")

    cvs = parse_cv_list(html)

    if not cvs:
        return None, {
            "success": False,
            "authenticated": True,
            "error": "No CVs found. Please create a CV first.",
        }

    if cv_id:
        selected_cv = next(
            (cv for cv in cvs if str(cv.get("cv_id")) == str(cv_id)),
            None,
        )

        if not selected_cv:
            return None, {
                "success": False,
                "authenticated": True,
                "error": f"CV with id {cv_id} was not found.",
            }

        return selected_cv, None

    if len(cvs) == 1:
        return cvs[0], None

    return None, {
        "success": False,
        "authenticated": True,
        "requires_selection": True,
        "message": "Multiple CVs found. Please choose which CV to use.",
        "cvs": [
            {
                "cv_id": cv.get("cv_id"),
                "name": cv.get("name"),
                "modified": cv.get("modified"),
                "completeness": cv.get("completeness"),
                "status": cv.get("status"),
            }
            for cv in cvs
        ],
    }

# Retrieves dashboard data for the logged-in user.
def get_user_dashboard() -> dict:
    try:
        response = authenticated_client.get(PROTECTED_HOME_URL)
        html = response.text
        final_url = getattr(response, "url", "")

        if _looks_like_login_page(html, final_url):
            return _session_expired_response()

        return {
            "success": True,
            "authenticated": True,
            "dashboard": parse_dashboard(html),
        }

    except SessionExpiredError:
        return _session_expired_response()

    except Exception as e:
        return _unexpected_error_response(e)


# Returns all CVs belonging to the logged-in user.
def view_cv() -> dict:
    try:
        response = authenticated_client.get(EDIT_CV_LIST_URL)
        html = response.text
        final_url = getattr(response, "url", "")

        if _looks_like_login_page(html, final_url):
            return _session_expired_response()

        cvs = parse_cv_list(html)

        return {
            "success": True,
            "authenticated": True,
            "cvs": cvs,
            "count": len(cvs),
        }

    except SessionExpiredError:
        return _session_expired_response()

    except Exception as e:
        return _unexpected_error_response(e)


# Downloads a selected CV, or auto-selects it if only one CV exists.
def download_cv(cv_id: str | None = None) -> dict:
    try:
        selected_cv, error = _select_cv(cv_id)

        if error:
            return error

        cv_id = selected_cv.get("cv_id")

        response = authenticated_client.get(f"{CV_PRINT_URL}?CvId={cv_id}")
        final_url = getattr(response, "url", "")

        try:
            html_preview = response.text[:500]
        except Exception:
            html_preview = ""

        if _looks_like_login_page(html_preview, final_url):
            return _session_expired_response()

        if response.status_code != 200:
            return {
                "success": False,
                "authenticated": True,
                "error": f"Failed to download CV. Status code: {response.status_code}",
            }

        content_type = response.headers.get("Content-Type", "")

        return {
            "success": True,
            "authenticated": True,
            "cv_id": str(cv_id),
            "cv": selected_cv,
            "filename": f"cv_{cv_id}.doc",
            "content_type": content_type,
            "content_base64": base64.b64encode(response.content).decode("utf-8"),
        }

    except SessionExpiredError:
        return _session_expired_response()

    except Exception as e:
        return _unexpected_error_response(e)


# Opens or updates an existing CV using the provided data.
def edit_cv(cv_id: str | None = None, data: dict | None = None) -> dict:
    driver = None

    try:
        selected_cv, error = _select_cv(cv_id)

        if error:
            return error

        cv_id = selected_cv.get("cv_id")

        driver = _get_driver()
        _load_session_cookies_into_driver(driver)

        driver.get(CV_CREATE_EDIT_URL)

        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.ID, "MainContent_ASPxPageControl_cv"))
        )

        html = driver.page_source
        final_url = driver.current_url

        if _looks_like_login_page(html, final_url):
            return _session_expired_response()

        if not data:
            return {
                "success": True,
                "authenticated": True,
                "cv_id": str(cv_id),
                "cv": selected_cv,
                "edit_page": parse_cv_edit_page(html),
                "editable": True,
            }

        personal = data.get("personal_data", {})

        if personal:
            _safe_click(
                driver,
                "MainContent_ASPxPageControl_cv_CallbackPanelPromeniPodatoci_ASPxButton1",
            )

            time.sleep(1)

            _safe_set_text(
                driver,
                "MainContent_popupUpdateLicniPodatoci_CallBackPromeniPodatoci_textPodatociIme_I",
                personal.get("first_name"),
            )
            _safe_set_text(
                driver,
                "MainContent_popupUpdateLicniPodatoci_CallBackPromeniPodatoci_textPodatociPrezime_I",
                personal.get("last_name"),
            )
            _safe_set_text(
                driver,
                "MainContent_popupUpdateLicniPodatoci_CallBackPromeniPodatoci_textPodatociTatkovoIme_I",
                personal.get("father_name"),
            )
            _safe_set_text(
                driver,
                "MainContent_popupUpdateLicniPodatoci_CallBackPromeniPodatoci_textPodatociAdresa_I",
                personal.get("address"),
            )
            _safe_set_text(
                driver,
                "MainContent_popupUpdateLicniPodatoci_CallBackPromeniPodatoci_textBoxPodatociEmail_I",
                personal.get("email"),
            )
            _safe_set_text(
                driver,
                "MainContent_popupUpdateLicniPodatoci_CallBackPromeniPodatoci_dateEditPodatociDatumRaganje_I",
                personal.get("birth_date"),
            )
            _safe_set_text(
                driver,
                "MainContent_popupUpdateLicniPodatoci_CallBackPromeniPodatoci_textBoxpodatociMestoRaganje_I",
                personal.get("birth_place"),
            )

            for button_id in [
                "MainContent_popupUpdateLicniPodatoci_CallBackPromeniPodatoci_ButtonZacuvajPodatoci",
                "MainContent_popupUpdateLicniPodatoci_CallBackPromeniPodatoci_buttonZacuvajPodatoci",
                "MainContent_popupUpdateLicniPodatoci_ButtonZacuvaj",
            ]:
                if _safe_click(driver, button_id):
                    break

            time.sleep(2)

        profile_type = data.get("profile_type")
        if profile_type:
            driver.execute_script("aspxTCTClick(event, 'MainContent_ASPxPageControl_cv', 10);")
            time.sleep(1)

            profile_map = {
                "locked": [
                    "MainContent_ASPxPageControl_cv_RadioButtonListCvTip_0",
                    "MainContent_ASPxPageControl_cv_radioButtonListCvTip_0",
                ],
                "public": [
                    "MainContent_ASPxPageControl_cv_RadioButtonListCvTip_1",
                    "MainContent_ASPxPageControl_cv_radioButtonListCvTip_1",
                ],
                "anonymous": [
                    "MainContent_ASPxPageControl_cv_RadioButtonListCvTip_2",
                    "MainContent_ASPxPageControl_cv_radioButtonListCvTip_2",
                ],
            }

            for option_id in profile_map.get(profile_type, []):
                if _safe_click(driver, option_id):
                    break

        if data.get("cv_name"):
            for field_id in [
                "MainContent_ASPxPageControl_cv_textBoxCvNaziv_I",
                "MainContent_ASPxPageControl_cv_ASPxTextBoxCvNaziv_I",
                "MainContent_ASPxPageControl_cv_TextBoxCvNaziv_I",
            ]:
                if _safe_set_text(driver, field_id, data["cv_name"]):
                    break

        try:
            driver.execute_script("aspxTCTClick(event, 'MainContent_ASPxPageControl_cv', 11);")
            time.sleep(1)
        except Exception:
            pass

        saved = _safe_click(driver, "MainContent_ASPxPageControl_cv_ButtonZacuvajCv")

        time.sleep(3)

        return {
            "success": saved,
            "authenticated": True,
            "cv_id": str(cv_id),
            "message": (
                "CV saved successfully."
                if saved
                else "CV edit page opened, but save button was not found/clicked."
            ),
        }

    except SessionExpiredError:
        return _session_expired_response()

    except Exception as e:
        return _unexpected_error_response(e)

    finally:
        if driver:
            driver.quit()


# Creates a new CV through the authenticated browser flow.
def create_cv(data: dict) -> dict:
    driver = None

    try:
        driver = _get_driver()
        _load_session_cookies_into_driver(driver)

        driver.get(EDIT_CV_LIST_URL)

        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.ID, "MainContent_gridViewCvByLicnost"))
        )

        html = driver.page_source
        if _looks_like_login_page(html, driver.current_url):
            return _session_expired_response()

        clicked_new = (
            _safe_click(driver, "MainContent_ButtonNovoCv")
            or _safe_click(driver, "MainContent_gridViewCvByLicnost_header7_ButtonVnesiCv_7")
        )

        if not clicked_new:
            return {
                "success": False,
                "authenticated": True,
                "error": "Could not find the new CV button.",
            }

        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.ID, "MainContent_ASPxPageControl_cv"))
        )

        personal = data.get("personal_data", {})

        if personal:
            _safe_click(
                driver,
                "MainContent_ASPxPageControl_cv_CallbackPanelPromeniPodatoci_ASPxButton1",
            )
            time.sleep(1)

            _safe_set_text(
                driver,
                "MainContent_popupUpdateLicniPodatoci_CallBackPromeniPodatoci_textPodatociIme_I",
                personal.get("first_name"),
            )
            _safe_set_text(
                driver,
                "MainContent_popupUpdateLicniPodatoci_CallBackPromeniPodatoci_textPodatociPrezime_I",
                personal.get("last_name"),
            )
            _safe_set_text(
                driver,
                "MainContent_popupUpdateLicniPodatoci_CallBackPromeniPodatoci_textPodatociTatkovoIme_I",
                personal.get("father_name"),
            )
            _safe_set_text(
                driver,
                "MainContent_popupUpdateLicniPodatoci_CallBackPromeniPodatoci_textPodatociAdresa_I",
                personal.get("address"),
            )
            _safe_set_text(
                driver,
                "MainContent_popupUpdateLicniPodatoci_CallBackPromeniPodatoci_textBoxPodatociEmail_I",
                personal.get("email"),
            )

            for button_id in [
                "MainContent_popupUpdateLicniPodatoci_CallBackPromeniPodatoci_ButtonZacuvajPodatoci",
                "MainContent_popupUpdateLicniPodatoci_CallBackPromeniPodatoci_buttonZacuvajPodatoci",
                "MainContent_popupUpdateLicniPodatoci_ButtonZacuvaj",
            ]:
                if _safe_click(driver, button_id):
                    break

            time.sleep(2)

        if data.get("cv_name"):
            for field_id in [
                "MainContent_ASPxPageControl_cv_textBoxCvNaziv_I",
                "MainContent_ASPxPageControl_cv_ASPxTextBoxCvNaziv_I",
                "MainContent_ASPxPageControl_cv_TextBoxCvNaziv_I",
            ]:
                if _safe_set_text(driver, field_id, data["cv_name"]):
                    break

        profile_type = data.get("profile_type", "locked")
        try:
            driver.execute_script("aspxTCTClick(event, 'MainContent_ASPxPageControl_cv', 10);")
            time.sleep(1)
        except Exception:
            pass

        profile_map = {
            "locked": [
                "MainContent_ASPxPageControl_cv_RadioButtonListCvTip_0",
                "MainContent_ASPxPageControl_cv_radioButtonListCvTip_0",
            ],
            "public": [
                "MainContent_ASPxPageControl_cv_RadioButtonListCvTip_1",
                "MainContent_ASPxPageControl_cv_radioButtonListCvTip_1",
            ],
            "anonymous": [
                "MainContent_ASPxPageControl_cv_RadioButtonListCvTip_2",
                "MainContent_ASPxPageControl_cv_radioButtonListCvTip_2",
            ],
        }

        for option_id in profile_map.get(profile_type, []):
            if _safe_click(driver, option_id):
                break

        try:
            driver.execute_script("aspxTCTClick(event, 'MainContent_ASPxPageControl_cv', 11);")
            time.sleep(1)
        except Exception:
            pass

        saved = _safe_click(driver, "MainContent_ASPxPageControl_cv_ButtonZacuvajCv")
        time.sleep(3)

        response = authenticated_client.get(EDIT_CV_LIST_URL)
        cvs = parse_cv_list(response.text)

        return {
            "success": saved,
            "authenticated": True,
            "message": (
                "CV created successfully."
                if saved
                else "CV creation attempted, but save button was not clicked."
            ),
            "cvs": cvs,
            "count": len(cvs),
        }

    except SessionExpiredError:
        return _session_expired_response()

    except Exception as e:
        return _unexpected_error_response(e)

    finally:
        if driver:
            driver.quit()

# Opens the Favourite Jobs tab inside the job search page.
def _open_favourite_jobs_tab(driver: webdriver.Chrome) -> None:
    driver.execute_script(
        """
        if (window.PageControlPrebaruvanje) {
            PageControlPrebaruvanje.SetActiveTabIndex(1);
        } else if (window.ASPxClientControl) {
            var pc = ASPxClientControl.GetControlCollection().GetByName(
                'MainContent_CallBackSearchCv_PageControlPrebaruvanje'
            );
            if (pc) {
                pc.SetActiveTabIndex(1);
            }
        }
        """
    )
    time.sleep(2)

# Adds a job ad to the user's favourite jobs list.
def save_job_favourite(oglas_id: str, favourite_name: str | None = None) -> dict:
    driver = None

    try:
        driver = _get_driver()
        _load_session_cookies_into_driver(driver)

        driver.get(f"{PORTAL_BASE_URL}/OglasSearch.aspx")

        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located(
                (By.ID, "MainContent_CallBackSearchCv_PageControlPrebaruvanje")
            )
        )

        if _looks_like_login_page(driver.page_source, driver.current_url):
            return _session_expired_response()

        details_links = driver.find_elements(
            By.XPATH,
            f"//a[contains(@onclick, 'OglasPPRId={oglas_id}')]",
        )

        if not details_links:
            return {
                "success": False,
                "authenticated": True,
                "error": f"Job ad with id {oglas_id} was not found on the current page.",
            }

        job_container = details_links[0].find_element(
            By.XPATH,
            "./ancestor::td[contains(@class, 'dxdvItem')]",
        )

        favourite_button = job_container.find_element(
            By.XPATH,
            ".//a[contains(@id, 'changeStatus')]",
        )

        driver.execute_script("arguments[0].click();", favourite_button)

        WebDriverWait(driver, 10).until(
            EC.visibility_of_element_located(
                (By.ID, "MainContent_CallBackSearchCv_popUpOmileno_PW-1")
            )
        )

        if favourite_name:
            name_input = driver.find_element(
                By.ID,
                "MainContent_CallBackSearchCv_popUpOmileno_TextBoxImeOmilenoCv_I",
            )
            name_input.clear()
            name_input.send_keys(favourite_name)

        create_button = driver.find_element(
            By.ID,
            "MainContent_CallBackSearchCv_popUpOmileno_buttonKreirajCV",
        )

        driver.execute_script("arguments[0].click();", create_button)
        time.sleep(2)

        return {
            "success": True,
            "authenticated": True,
            "oglas_id": str(oglas_id),
            "message": "Job ad was added to favourites.",
        }

    except SessionExpiredError:
        return _session_expired_response()

    except Exception as e:
        return _unexpected_error_response(e)

    finally:
        if driver:
            driver.quit()

# Returns all favourite job ads for the logged-in user.
def view_favourite_jobs() -> dict:
    driver = None

    try:
        driver = _get_driver()
        _load_session_cookies_into_driver(driver)

        driver.get(f"{PORTAL_BASE_URL}/OglasSearch.aspx")

        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located(
                (By.ID, "MainContent_CallBackSearchCv_PageControlPrebaruvanje")
            )
        )

        if _looks_like_login_page(driver.page_source, driver.current_url):
            return _session_expired_response()

        _open_favourite_jobs_tab(driver)

        favourites = parse_favourite_jobs(driver.page_source)

        return {
            "success": True,
            "authenticated": True,
            "favourite_jobs": favourites,
            "count": len(favourites),
        }

    except SessionExpiredError:
        return _session_expired_response()

    except Exception as e:
        return _unexpected_error_response(e)

    finally:
        if driver:
            driver.quit()

# Removes a job ad from the user's favourite jobs list.
def remove_favourite_job(oglas_id: str) -> dict:
    driver = None

    try:
        driver = _get_driver()
        _load_session_cookies_into_driver(driver)

        driver.get(f"{PORTAL_BASE_URL}/OglasSearch.aspx")

        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located(
                (By.ID, "MainContent_CallBackSearchCv_PageControlPrebaruvanje")
            )
        )

        if _looks_like_login_page(driver.page_source, driver.current_url):
            return _session_expired_response()

        _open_favourite_jobs_tab(driver)

        row_link = driver.find_elements(
            By.XPATH,
            f"//*[contains(text(), '{oglas_id}') or contains(@onclick, 'OglasPPRId={oglas_id}')]",
        )

        if not row_link:
            return {
                "success": False,
                "authenticated": True,
                "error": f"Favourite job with id {oglas_id} was not found.",
            }

        row = row_link[0].find_element(By.XPATH, "./ancestor::tr")
        delete_button = row.find_element(By.XPATH, ".//a[contains(@id, 'DXCBtn')]")

        driver.execute_script("arguments[0].click();", delete_button)
        time.sleep(2)

        return {
            "success": True,
            "authenticated": True,
            "oglas_id": str(oglas_id),
            "message": "Favourite job was removed.",
        }

    except SessionExpiredError:
        return _session_expired_response()

    except Exception as e:
        return _unexpected_error_response(e)

    finally:
        if driver:
            driver.quit()

# Sends an invitation/application message for a selected job ad.
def send_job_invitation(
    oglas_id: str,
    message: str = "",
    show_personal_data: bool = True,
) -> dict:
    driver = None

    try:
        driver = _get_driver()
        _load_session_cookies_into_driver(driver)

        driver.get(f"{PORTAL_BASE_URL}/OglasSearch.aspx")

        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located(
                (By.ID, "MainContent_CallBackSearchCv_PageControlPrebaruvanje")
            )
        )

        if _looks_like_login_page(driver.page_source, driver.current_url):
            return _session_expired_response()

        details_links = driver.find_elements(
            By.XPATH,
            f"//a[contains(@onclick, 'OglasPPRId={oglas_id}')]",
        )

        if not details_links:
            return {
                "success": False,
                "authenticated": True,
                "error": f"Job ad with id {oglas_id} was not found on the current page.",
            }

        job_container = details_links[0].find_element(
            By.XPATH,
            "./ancestor::td[contains(@class, 'dxdvItem')]",
        )

        invite_button = job_container.find_element(
            By.XPATH,
            ".//a[contains(@id, 'ButtonPokani')]",
        )

        driver.execute_script("arguments[0].click();", invite_button)

        WebDriverWait(driver, 10).until(
            EC.visibility_of_element_located(
                (By.ID, "MainContent_CallBackSearchCv_PopupControlPokana_PW-1")
            )
        )

        personal_data_text = "Да" if show_personal_data else "Не"
        personal_data_value = "0" if show_personal_data else "1"

        driver.execute_script(
            """
            if (window.ComboBoxPrikaziPodatoci) {
                ComboBoxPrikaziPodatoci.SetValue(arguments[0]);
                ComboBoxPrikaziPodatoci.SetText(arguments[1]);
            }
            """,
            personal_data_value,
            personal_data_text,
        )

        if message:
            if len(message) > 400:
                message = message[:400]

            memo = driver.find_element(
                By.ID,
                "MainContent_CallBackSearchCv_PopupControlPokana_MemoPoraka_I",
            )
            memo.clear()
            memo.send_keys(message)

        submit_button = driver.find_element(
            By.ID,
            "MainContent_CallBackSearchCv_PopupControlPokana_ButtonVnesiPokana",
        )

        driver.execute_script("arguments[0].click();", submit_button)

        time.sleep(3)

        return {
            "success": True,
            "authenticated": True,
            "oglas_id": str(oglas_id),
            "show_personal_data": show_personal_data,
            "message_sent": bool(message),
            "message": "Job invitation was sent.",
        }

    except SessionExpiredError:
        return _session_expired_response()

    except Exception as e:
        return _unexpected_error_response(e)

    finally:
        if driver:
            driver.quit()