import time

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from institutions.agencijaZaVrabotuvanje.config import OGLASI_URL, DETALI_URL
from institutions.agencijaZaVrabotuvanje.parsers.jobs_parser import (
    parse_oglasi,
    parse_total_pages,
    parse_job_details,
)


def get_driver():
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")

    return webdriver.Chrome(options=options)

# Returns a list of job ads
def view_jobs(page: int = 1) -> dict:
    driver = get_driver()
    current_page = 1

    try:
        driver.get(OGLASI_URL)

        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "td.dxdvItem"))
        )

        if page > 1:
            for _ in range(page - 1):
                try:
                    next_button = driver.find_element(
                        By.CSS_SELECTOR,
                        "a.dxp-button img.dxWeb_pNext"
                    )
                    next_button.find_element(By.XPATH, "..").click()
                    time.sleep(2)
                except Exception:
                    break
                current_page += 1

        html = driver.page_source
        total_pages = parse_total_pages(html)

        return {
            "success": True,
            "oglasi": parse_oglasi(html),
            "total_pages": total_pages,
            "current_page": current_page,
            "requested_page": page,
            "page_reached": current_page == page,
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "oglasi": [],
            "total_pages": 0,
            "current_page": current_page,
            "requested_page": page,
            "page_reached": False,
        }

    finally:
        driver.quit()

# Performs filtered job search using occupation, center, and municipality
def search_jobs(
    zanimanje: str = "",
    centar: str = "",
    opstina: str = "",
    page: int = 1,
) -> dict:
    driver = get_driver()
    current_page = 1

    try:
        driver.get(OGLASI_URL)

        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "td.dxdvItem"))
        )

        if zanimanje:
            el = driver.find_element(
                By.ID,
                "MainContent_CallBackSearchCv_PageControlPrebaruvanje_ASPxTextBoxZanimanjeOsnovno_I",
            )
            el.clear()
            el.send_keys(zanimanje)

        if centar:
            el = driver.find_element(
                By.ID,
                "MainContent_CallBackSearchCv_PageControlPrebaruvanje_ComboBoxCentarOsnovno_I",
            )
            el.clear()
            el.send_keys(centar)
            time.sleep(1)

        if opstina:
            el = driver.find_element(
                By.ID,
                "MainContent_CallBackSearchCv_PageControlPrebaruvanje_ComboBoxOpshtinaOsnovno_I",
            )
            el.clear()
            el.send_keys(opstina)
            time.sleep(1)

        driver.find_element(
            By.ID,
            "MainContent_CallBackSearchCv_PageControlPrebaruvanje_ButtonSearchOsnovno",
        ).click()

        time.sleep(3)

        if page > 1:
            for _ in range(page - 1):
                try:
                    next_button = driver.find_element(
                        By.CSS_SELECTOR,
                        "a.dxp-button img.dxWeb_pNext"
                    )
                    next_button.find_element(By.XPATH, "..").click()
                    time.sleep(2)
                except Exception:
                    break
                current_page += 1

        html = driver.page_source
        total_pages = parse_total_pages(html)

        return {
            "success": True,
            "oglasi": parse_oglasi(html),
            "total_pages": total_pages,
            "current_page": current_page,
            "requested_page": page,
            "page_reached": current_page == page,
            "filter": {
                "zanimanje": zanimanje,
                "centar": centar,
                "opstina": opstina,
            },
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "oglasi": [],
            "total_pages": 0,
            "current_page": current_page,
            "requested_page": page,
            "page_reached": False,
            "filter": {
                "zanimanje": zanimanje,
                "centar": centar,
                "opstina": opstina,
            },
        }

    finally:
        driver.quit()

# Retrieves full details for a specific job ad by oglas_id
def get_job_details(oglas_id: str) -> dict:
    driver = get_driver()

    try:
        driver.get(f"{DETALI_URL}?OglasPPRId={oglas_id}")

        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "fieldset.fieldset"))
        )

        html = driver.page_source
        details = parse_job_details(html, oglas_id)

        return {
            "success": True,
            "details": details,
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "details": None,
        }

    finally:
        driver.quit()
