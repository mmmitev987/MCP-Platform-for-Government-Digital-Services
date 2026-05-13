"""
institutions/mon/tools/_scraper.py
────────────────────────────────────────────────────────────────────────────────
Shared HTML scraping helpers for mon.gov.mk listing and detail pages.

mon.gov.mk is a Livewire v3 (Laravel) app. The listing pages render 9 items
per page on the server side; subsequent pages are fetched via POST to
/livewire/update using the component snapshot + X-XSRF-TOKEN header.
"""

import json
import re
from html import unescape
from urllib.parse import unquote

import requests
from bs4 import BeautifulSoup

from institutions.shared.errors import tool_error

BASE_URL = "https://mon.gov.mk"
_LIVEWIRE_UPDATE = f"{BASE_URL}/livewire/update"
_MAX_PAGES = 30  # safety cap

_UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/124.0.0.0 Safari/537.36"
)
_DATE_RE = re.compile(r"\d{2}/\d{2}/\d{4}")
_FILE_RE = re.compile(r"\.(pdf|doc|docx|xlsx|zip|rar)(\?.*)?$", re.I)
_URL_RE  = re.compile(r"^https?://")


def _new_session() -> requests.Session:
    s = requests.Session()
    s.headers.update({"User-Agent": _UA, "Accept-Language": "mk,en;q=0.9"})
    return s


def _extract_items(html: str, section_slug: str) -> list[dict]:
    """Parse competition/scholarship items from a rendered HTML fragment."""
    soup = BeautifulSoup(html, "html.parser")
    pattern = re.compile(
        rf"/mk-MK/konkursi-i-stipendii/{re.escape(section_slug)}/.+"
    )

    url_to_anchors: dict[str, list] = {}
    for a in soup.find_all("a", href=pattern):
        href = a["href"]
        if not href.startswith("http"):
            href = BASE_URL + href
        url_to_anchors.setdefault(href, []).append(a)

    items: list[dict] = []
    for href, anchors in url_to_anchors.items():
        title_anchor = next((a for a in anchors if a.find("h3")), None)
        if title_anchor is None:
            title_anchor = next(
                (a for a in anchors if a.get_text(strip=True) not in ("Прочитај повеќе", "")),
                anchors[0],
            )

        h3 = title_anchor.find("h3")
        title = (h3 or title_anchor).get_text(strip=True)
        if not title or title == "Прочитај повеќе":
            continue

        date = ""
        node = title_anchor.parent
        for _ in range(6):
            if node is None:
                break
            m = _DATE_RE.search(node.get_text(" "))
            if m:
                date = m.group()
                break
            node = node.parent

        desc = ""
        parent = title_anchor.parent
        if parent:
            for sib in parent.next_siblings:
                if not hasattr(sib, "get_text"):
                    continue
                t = sib.get_text(strip=True)
                if t and t != "Прочитај повеќе" and len(t) > 20:
                    desc = t[:300]
                    break

        items.append({"title": title, "date": date, "url": href, "description": desc})

    return items


def scrape_listing(url: str, section_slug: str) -> list[dict] | dict:
    """
    Scrape ALL pages of a mon.gov.mk listing (competitions or scholarships).

    Uses the Livewire v3 /livewire/update endpoint to paginate through all
    pages after the first, combining results into a single list.
    """
    sess = _new_session()

    try:
        r = sess.get(url, timeout=15)
        r.raise_for_status()
    except requests.RequestException as exc:
        return tool_error("network_error", f"Could not reach mon.gov.mk: {exc}")

    soup = BeautifulSoup(r.text, "html.parser")

    snapshot = None
    for tag in soup.find_all(attrs={"wire:snapshot": True}):
        try:
            data = json.loads(unescape(tag["wire:snapshot"]))
        except json.JSONDecodeError:
            continue
        if data.get("memo", {}).get("name") == "public.subcategory":
            snapshot = data
            break

    all_items = _extract_items(r.text, section_slug)

    if snapshot is None:
        return all_items

    # XSRF token must be URL-decoded before sending as X-XSRF-TOKEN header
    xsrf = unquote(sess.cookies.get("XSRF-TOKEN", ""))

    seen_urls = {item["url"] for item in all_items}

    for page_num in range(2, _MAX_PAGES + 1):
        payload = {
            "components": [{
                "snapshot": json.dumps(snapshot),
                "updates": {},
                "calls": [{"method": "gotoPage", "params": [page_num, "page"]}],
            }]
        }
        try:
            resp = sess.post(
                _LIVEWIRE_UPDATE,
                json=payload,
                headers={
                    "X-XSRF-TOKEN": xsrf,
                    "X-Livewire": "true",
                    "Accept": "application/json",
                    "Referer": url,
                    "Origin": BASE_URL,
                },
                timeout=15,
            )
            resp.raise_for_status()
        except requests.RequestException:
            break

        try:
            resp_data = resp.json()
        except ValueError:
            break

        components = resp_data.get("components")
        if not isinstance(resp_data, dict) or not isinstance(components, list) or not components:
            break

        comp = components[0]
        if not isinstance(comp, dict):
            break

        html = comp.get("effects", {}).get("html", "")
        if not html:
            break

        page_items = _extract_items(html, section_slug)
        new_items = [i for i in page_items if i["url"] not in seen_urls]
        if not new_items:
            break

        all_items.extend(new_items)
        seen_urls.update(i["url"] for i in new_items)

        try:
            snapshot = json.loads(comp.get("snapshot", "{}"))
        except (json.JSONDecodeError, KeyError):
            break

    return all_items


def scrape_detail(url: str) -> dict:
    """
    Scrape a mon.gov.mk detail page (competition or scholarship).

    Returns { url, title, date, body, attachments }.
    """
    if not url.startswith("http"):
        url = BASE_URL + url

    try:
        r = requests.get(url, headers={"User-Agent": _UA}, timeout=15)
        r.raise_for_status()
    except requests.RequestException as exc:
        return tool_error("network_error", f"Could not fetch page: {exc}")

    soup = BeautifulSoup(r.text, "html.parser")

    h1 = soup.find("h1")
    title = h1.get_text(strip=True) if h1 else ""

    date = ""
    m = _DATE_RE.search(soup.get_text(" "))
    if m:
        date = m.group()

    body = ""
    if h1:
        parts = []
        for el in h1.next_siblings:
            if not hasattr(el, "name"):
                continue
            if el.name in ("script", "style", "nav", "header", "footer"):
                continue
            text = el.get_text("\n", strip=True)
            if text:
                parts.append(text)
        body = "\n".join(parts)

    if not body:
        for tag in soup(["script", "style", "nav", "header", "footer"]):
            tag.decompose()
        body = soup.get_text("\n", strip=True)

    attachments = []
    seen: set[str] = set()
    for a in soup.find_all("a", href=_FILE_RE):
        href = a["href"]
        if not href.startswith("http"):
            href = BASE_URL + href
        if href in seen:
            continue
        seen.add(href)
        name = a.get_text(strip=True)
        if not name or _URL_RE.match(name):
            name = href.split("/")[-1].split("?")[0]
        attachments.append({"name": name, "url": href})

    return {
        "url": url,
        "title": title,
        "date": date,
        "body": body[:4000],
        "attachments": attachments,
    }
