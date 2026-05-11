import re
from bs4 import BeautifulSoup


CV_GRID_ID = "MainContent_gridViewCvByLicnost"


def parse_cv_list(html: str) -> list[dict]:
    soup = BeautifulSoup(html, "html.parser")
    table = soup.find("table", {"id": f"{CV_GRID_ID}_DXMainTable"})

    if not table:
        return []

    if table.select_one("tr.dxgvEmptyDataRow"):
        return []

    cvs = []

    for row in table.find_all("tr"):
        row_id = row.get("id", "")
        if "DXDataRow" not in row_id:
            continue

        cells = row.find_all("td", recursive=False)
        if len(cells) < 7:
            continue

        name = cells[0].get_text(" ", strip=True)
        created = cells[1].get_text(" ", strip=True)
        modified = cells[2].get_text(" ", strip=True)
        completeness = cells[3].get_text(" ", strip=True)

        status_img = cells[4].find("img")
        status = status_img.get("title", "") if status_img else ""

        download_link = cells[6].find("a", href=True)
        download_url = download_link.get("href", "") if download_link else ""

        cv_id = None
        match = re.search(r"CvId=(\d+)", download_url)
        if match:
            cv_id = match.group(1)

        cvs.append({
            "cv_id": cv_id,
            "name": name,
            "created": created,
            "modified": modified,
            "completeness": completeness,
            "status": status,
            "download_url": download_url,
        })

    return cvs


def parse_cv_edit_page(html: str) -> dict:
    soup = BeautifulSoup(html, "html.parser")

    def text_by_id(element_id: str) -> str:
        el = soup.find(id=element_id)
        return el.get_text(" ", strip=True) if el else ""

    def value_by_id(element_id: str) -> str:
        el = soup.find(id=element_id)
        return el.get("value", "") if el else ""

    return {
        "completeness": text_by_id("MainContent_progressBarComplete_ctl01_VIC"),
        "active_tab": value_by_id("MainContent_ASPxPageControl_cvATI"),
        "personal_data": {
            "first_name": text_by_id("MainContent_ASPxPageControl_cv_CallbackPanelPromeniPodatoci_labelIme"),
            "father_name": text_by_id("MainContent_ASPxPageControl_cv_CallbackPanelPromeniPodatoci_labelTatkovoIme"),
            "last_name": text_by_id("MainContent_ASPxPageControl_cv_CallbackPanelPromeniPodatoci_labelPrezime"),
            "gender": text_by_id("MainContent_ASPxPageControl_cv_CallbackPanelPromeniPodatoci_labelPol"),
            "birth_date": text_by_id("MainContent_ASPxPageControl_cv_CallbackPanelPromeniPodatoci_labelDatumRaganje"),
            "birth_place": text_by_id("MainContent_ASPxPageControl_cv_CallbackPanelPromeniPodatoci_labelMestoRaganje"),
            "address": text_by_id("MainContent_ASPxPageControl_cv_CallbackPanelPromeniPodatoci_labelAdresa"),
            "living_place": text_by_id("MainContent_ASPxPageControl_cv_CallbackPanelPromeniPodatoci_labelMesto"),
            "email": text_by_id("MainContent_ASPxPageControl_cv_CallbackPanelPromeniPodatoci_labelEmail"),
            "nationality": text_by_id("MainContent_ASPxPageControl_cv_CallbackPanelPromeniPodatoci_labelNacionalnost"),
        },
    }