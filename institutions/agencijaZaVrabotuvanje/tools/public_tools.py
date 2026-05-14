import os
import time
from pathlib import Path

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys

from institutions.agencijaZaVrabotuvanje.config import OGLASI_URL, DETALI_URL
from institutions.agencijaZaVrabotuvanje.parsers.jobs_parser import (
    parse_oglasi,
    parse_total_pages,
    parse_job_details,
)

# Chrome binary candidates (Windows — chrome is often not in PATH when
# running inside a subprocess chain spawned by the MCP gateway).
_CHROME_CANDIDATES = [
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    os.path.join(os.environ.get("LOCALAPPDATA", ""), r"Google\Chrome\Application\chrome.exe"),
]

# ChromeDriver in Selenium Manager's cache (~/.cache/selenium/chromedriver/…)
_CHROMEDRIVER_CACHE = Path.home() / ".cache" / "selenium" / "chromedriver"


def _find_chrome() -> str | None:
    for p in _CHROME_CANDIDATES:
        if p and os.path.exists(p):
            return p
    return None


def _find_chromedriver() -> str | None:
    if _CHROMEDRIVER_CACHE.exists():
        drivers = sorted(_CHROMEDRIVER_CACHE.rglob("chromedriver.exe"), reverse=True)
        if drivers:
            return str(drivers[0])
    return None


def get_driver():
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")

    chrome_bin = _find_chrome()
    if chrome_bin:
        options.binary_location = chrome_bin

    chromedriver_path = _find_chromedriver()
    if chromedriver_path:
        return webdriver.Chrome(service=Service(chromedriver_path), options=options)

    return webdriver.Chrome(options=options)


def _select_combobox(driver, input_id: str, value: str):
    """
    Select a value in a DevExpress ASPxComboBox via the client-side API.

    Uses aspxGetControlCollection().Get(id).SetText() which is the correct
    way to programmatically set a DevExpress combobox — it fires all internal
    events needed for the server-side filter to register the selection.
    """
    control_id = input_id[: -len("_I")]
    driver.execute_script(
        """
        var ctrl = aspxGetControlCollection().Get(arguments[0]);
        if (ctrl && ctrl.SetText) { ctrl.SetText(arguments[1]); }
        """,
        control_id,
        value,
    )
    time.sleep(0.3)


# Returns a list of job ads
def view_jobs(page: int = 1) -> dict:
    current_page = 1
    driver = None

    try:
        driver = get_driver()
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
        if driver:
            driver.quit()

# Performs filtered job search using occupation, center, and municipality
def search_jobs(
    zanimanje: str = "",
    centar: str = "",
    opstina: str = "",
    page: int = 1,
) -> dict:
    current_page = 1
    driver = None

    try:
        driver = get_driver()
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
            _select_combobox(
                driver,
                "MainContent_CallBackSearchCv_PageControlPrebaruvanje_ComboBoxCentarOsnovno_I",
                centar,
            )

        if opstina:
            _select_combobox(
                driver,
                "MainContent_CallBackSearchCv_PageControlPrebaruvanje_ComboBoxOpshtinaOsnovno_I",
                opstina,
            )

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
        if driver:
            driver.quit()

# Searches current listings and returns full details for the best name/title match
def find_job_details(query: str) -> dict:
    import concurrent.futures

    query_lower = query.lower().strip()

    def _score(job: dict) -> int:
        company = job.get("kompanija", "").lower()
        title = job.get("zanimanje", "").lower()
        combined = company + " " + title
        if query_lower in combined:
            return 100
        query_words = query_lower.split()
        combined_words = combined.split()
        return sum(
            1
            for qw in query_words
            if any(qw in cw or cw.startswith(qw[:5]) for cw in combined_words if len(qw) >= 3)
        )

    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
        f_view = executor.submit(view_jobs, 1)
        f_search = executor.submit(search_jobs, query)
        view_result = f_view.result()
        search_result = f_search.result()

    all_oglasi: list[dict] = []
    for r in (view_result, search_result):
        if r.get("success"):
            all_oglasi.extend(r.get("oglasi", []))

    # Deduplicate by oglas_id
    seen: set[str] = set()
    unique: list[dict] = []
    for job in all_oglasi:
        oid = job.get("oglas_id", "")
        if oid and oid not in seen:
            seen.add(oid)
            unique.append(job)

    if not unique:
        return {"success": False, "error": "No listings found to search through."}

    best = max(unique, key=_score)
    if _score(best) == 0:
        sample = [f"{j['zanimanje']} @ {j['kompanija']}" for j in unique[:5]]
        return {
            "success": False,
            "error": f"No job matching '{query}' found in current listings.",
            "sample_available": sample,
        }

    return get_job_details(best["oglas_id"])


# Retrieves full details for a specific job ad by oglas_id
def get_job_details(oglas_id: str) -> dict:
    driver = None

    try:
        driver = get_driver()
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
        if driver:
            driver.quit()
