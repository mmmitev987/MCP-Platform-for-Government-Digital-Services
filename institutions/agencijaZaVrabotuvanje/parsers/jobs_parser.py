from bs4 import BeautifulSoup


def parse_oglasi(html: str) -> list[dict]:
    soup = BeautifulSoup(html, "html.parser")
    oglasi = []

    for item in soup.select("td.dxdvItem"):
        oglas = {}

        for row in item.select("table tr"):
            cells = row.find_all("td")
            if len(cells) < 2:
                continue

            label = cells[0].get_text(strip=True)
            value = cells[1].get_text(" ", strip=True)

            if "Занимање" in label:
                oglas["zanimanje"] = value
            elif "Објавен на" in label:
                oglas["objaven_na"] = value
            elif "Валиден до" in label:
                oglas["validen_do"] = value
            elif "Правно лице" in label:
                oglas["kompanija"] = value
            elif "Место" in label:
                oglas["mesto"] = value
            elif "Општина" in label:
                oglas["opstina"] = value
            elif "Адреса" in label:
                oglas["adresa"] = value
            elif "E-mail" in label:
                oglas["email"] = value
            elif "Телефон" in label:
                oglas["telefon"] = value
            elif "Забелешка" in label:
                oglas["zabeleska"] = value

        link = item.find("a", onclick=True)
        if link:
            onclick = link.get("onclick", "")
            if "OglasPPRId=" in onclick:
                oglas_id = onclick.split("OglasPPRId=")[1].split("'")[0]
                oglas_id = oglas_id.split(")")[0].split(";")[0].strip()
                oglas["oglas_id"] = oglas_id

        if oglas:
            oglasi.append(oglas)

    return oglasi


def parse_total_pages(html: str) -> int:
    soup = BeautifulSoup(html, "html.parser")
    summary = soup.select_one("b.dxp-summary")

    if not summary:
        return 1

    text = summary.get_text(" ", strip=True)

    try:
        return int(text.split("од")[-1].strip())
    except Exception:
        return 1


def parse_job_details(html: str, oglas_id: str) -> dict:
    soup = BeautifulSoup(html, "html.parser")

    def get_span(span_id: str) -> str:
        el = soup.find("span", {"id": span_id})
        return el.get_text(" ", strip=True) if el else ""

    return {
        "oglas_id": oglas_id,
        "objaven_na": get_span("lblOglasDatum"),
        "validen_do": get_span("lblOglasRok"),
        "zanimanje_nkz": get_span("lblZanimanjeNaziv"),
        "rabotno_mesto": get_span("lblRabotnoMesto"),
        "tip_rabotno_mesto": get_span("lblRabotnoMestoTipNaziv"),
        "posebni_ovlastuvanja": get_span("lblRabotnoMestoSoPosebniOvlastuvanja"),
        "raboten_odnos_tip": get_span("lblRabotenOdnosTipNaziv"),
        "potrebno_iskustvo": get_span("lblPotrebnoIskustvo"),
        "broj_mesta": get_span("lblBrojNaMesta"),
        "slobodni_mesta": get_span("lblSlobodniMesta"),
        "raspored_rabotno_vreme": get_span("LblRabotnoVremeTip"),
        "rabotno_vreme": get_span("LblRabotnoVreme"),
        "nedelno_casovi": get_span("lblNedelnoCasovi"),
        "osnovna_plata": get_span("LblOsnovnaPlata"),
        "zabeleska": get_span("lblZabeleska"),
        "stranski_jazici": get_span("lblStranskiJazici"),
        "vestini": get_span("lblVestini"),
        "obuki": get_span("lblObuki"),
        "vozacki": get_span("lblVozacki"),
    }

def parse_favourite_jobs(html: str) -> list[dict]:
    import re
    from bs4 import BeautifulSoup

    soup = BeautifulSoup(html, "html.parser")

    table = soup.find(
        "table",
        {
            "id": "MainContent_CallBackSearchCv_PageControlPrebaruvanje_GridViewFavoritOglas_DXMainTable"
        },
    )

    if not table:
        return []

    if table.select_one("tr.dxgvEmptyDataRow"):
        return []

    favourites = []

    for row in table.find_all("tr"):
        row_id = row.get("id", "")

        if "DXDataRow" not in row_id:
            continue

        row_html = str(row)
        cells = row.find_all("td", recursive=False)
        values = [cell.get_text(" ", strip=True) for cell in cells]

        oglas_id = None
        match = re.search(r"OglasPPRId=(\d+)", row_html)
        if match:
            oglas_id = match.group(1)

        favourites.append({
            "oglas_id": oglas_id,
            "values": values,
        })

    return favourites