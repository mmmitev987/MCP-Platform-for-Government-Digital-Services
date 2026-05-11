from bs4 import BeautifulSoup


CV_VIEWS_GRID_ID = "MainContent_ctl00_gridViewCvByLicnost"
CV_FAVOURITES_GRID_ID = "MainContent_ctl00_GridViewCVasAFavorite"
RECOMMENDED_JOBS_GRID_ID = "MainContent_ctl00_GridViewPreporacaniOglasi"


def _is_empty_grid(grid) -> bool:
    if grid is None:
        return True

    empty_row = grid.select_one("tr.dxgvEmptyDataRow")
    if empty_row and "Нема записи" in empty_row.get_text(" ", strip=True):
        return True

    return False


def _get_main_grid_table(soup: BeautifulSoup, grid_id: str):
    return soup.find("table", {"id": f"{grid_id}_DXMainTable"})


def _extract_grid_rows(soup: BeautifulSoup, grid_id: str) -> list[list[str]]:
    grid = soup.find("table", {"id": grid_id})
    if _is_empty_grid(grid):
        return []

    main_table = _get_main_grid_table(soup, grid_id)
    if main_table is None:
        return []

    rows = []

    for tr in main_table.find_all("tr"):
        tr_id = tr.get("id", "")

        if "DXHeadersRow" in tr_id or "DXEmptyRow" in tr_id:
            continue

        cells = tr.find_all("td", recursive=False)

        values = []
        for cell in cells:
            text = cell.get_text(" ", strip=True)
            if text and text != "\xa0":
                values.append(text)

        if values:
            rows.append(values)

    return rows


def _parse_cv_views(soup: BeautifulSoup) -> list[dict]:
    rows = _extract_grid_rows(soup, CV_VIEWS_GRID_ID)
    result = []

    for row in rows:
        if len(row) < 4:
            continue

        result.append({
            "cv_name": row[0],
            "weekly_views": row[1],
            "monthly_views": row[2],
            "total_views": row[3],
        })

    return result


def _parse_favourite_companies(soup: BeautifulSoup) -> list[dict]:
    rows = _extract_grid_rows(soup, CV_FAVOURITES_GRID_ID)
    result = []

    for row in rows:
        if len(row) < 7:
            continue

        result.append({
            "company_name": row[0],
            "address": row[1],
            "email": row[2],
            "phone": row[3],
            "municipality": row[4],
            "city": row[5],
            "cv_document": row[6],
        })

    return result


def _parse_recommended_jobs(soup: BeautifulSoup) -> list[dict]:
    rows = _extract_grid_rows(soup, RECOMMENDED_JOBS_GRID_ID)
    result = []

    for row in rows:
        if len(row) < 7:
            continue

        result.append({
            "occupation": row[0],
            "company_name": row[1],
            "address": row[2],
            "email": row[3],
            "phone": row[4],
            "municipality": row[5],
            "city": row[6],
        })

    return result


def parse_dashboard(html: str) -> dict:
    soup = BeautifulSoup(html, "html.parser")

    cv_views = _parse_cv_views(soup)
    favourite_companies = _parse_favourite_companies(soup)
    recommended_jobs = _parse_recommended_jobs(soup)

    return {
        "cv_views": cv_views,
        "favourite_companies": favourite_companies,
        "recommended_jobs": recommended_jobs,
        "summary": {
            "cv_views_count": len(cv_views),
            "favourite_companies_count": len(favourite_companies),
            "recommended_jobs_count": len(recommended_jobs),
        },
    }