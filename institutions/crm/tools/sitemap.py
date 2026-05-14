"""
institutions/crm/tools/sitemap.py
────────────────────────────────────────────────────────────────────────────────
One-time Playwright crawl of crm.com.mk service pages at MCP server startup.
All content is cached in SERVICES — every tool call reads from memory, no live
scraping per request.

Build sequence (runs once via build_services_cache()):
  1. Playwright fetches /mk/mapa-na-sajtot (Angular-rendered)
  2. All /mk/ links with ≥4 path segments are collected
  3. Each page is visited; those with a "процедура" heading are kept
  4. Procedure content + service name are stored in SERVICES

After startup, list_services() and get_service_procedure() are instant dict reads.
"""

import difflib
import sys
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup, Tag

BASE_URL = "https://www.crm.com.mk"
SITEMAP_URL = f"{BASE_URL}/mk/mapa-na-sajtot"

# Populated once by build_services_cache(); never mutated after that.
# Shape: { category_name: { service_name: { "url": str, "procedure": list[str] } } }
SERVICES: dict[str, dict[str, dict]] = {}

_USLUGI_SLUG_TO_NAME: dict[str, str] = {
    "izvrsham-upis-ili-zavrsham-obvrska":         "Сакам да извршам упис или да завршам обврска",
    "dobijam-potvrda-ili-informatsija":            "Сакам да добијам потврда или информација",
    "sakam-da-dobijam-potvrda-ili-informatsija":   "Сакам да добијам потврда или информација",
}

_TOP_SLUG_TO_NAME: dict[str, str] = {
    "za-tsrrsm":              "За ЦРРСМ",
    "otvoreni-podatotsi":     "Отворени податоци",
    "profesionalni-korisnitsi": "Професионални корисници",
}


def _category_from_url(url: str) -> str:
    parts = url.replace(BASE_URL, "").strip("/").split("/")
    # parts[0] = "mk", parts[1] = top-level slug
    if len(parts) < 2:
        return "Останато"
    top = parts[1]
    if top == "uslugi" and len(parts) >= 3:
        return _USLUGI_SLUG_TO_NAME.get(parts[2], parts[2])
    return _TOP_SLUG_TO_NAME.get(top, top)


def _is_procedure_heading(tag: Tag) -> bool:
    text = tag.get_text(strip=True).lower()
    return "процедура" in text or "инструкц" in text


def _extract_procedure(soup: BeautifulSoup) -> list[str]:
    """
    Find the procedure heading and collect all text lines beneath it until
    the next heading of equal or higher rank.
    """
    headings = soup.find_all(["h2", "h3", "h4"])
    proc_heading = next((h for h in headings if _is_procedure_heading(h)), None)
    if proc_heading is None:
        return []

    # Determine which tags mark the end of this section
    _rank = {"h2": 2, "h3": 3, "h4": 4}
    rank = _rank.get(proc_heading.name, 3)
    stop_tags = {tag for tag, r in _rank.items() if r <= rank}

    steps: list[str] = []
    for sibling in proc_heading.find_next_siblings():
        if sibling.name in stop_tags:
            break
        for line in sibling.get_text(separator="\n", strip=True).splitlines():
            line = line.strip()
            if line:
                steps.append(line)

    return steps


async def build_services_cache() -> None:
    """
    One-time Playwright crawl. Populates the module-level SERVICES dict.
    Called from the FastMCP lifespan on server startup.
    The browser is closed when the scrape finishes — it is not kept open.
    """
    global SERVICES

    async with async_playwright() as pw:
        browser = await pw.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-dev-shm-usage"],
        )
        context = await browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            ),
            locale="mk-MK",
        )
        page = await context.new_page()

        # ── Step 1: collect candidate URLs from the sitemap ───────────────────
        print("[crm/sitemap] Fetching sitemap page...", file=sys.stderr, flush=True)
        await page.goto(SITEMAP_URL, wait_until="networkidle")
        sitemap_html = await page.content()
        sitemap_soup = BeautifulSoup(sitemap_html, "html.parser")

        candidate_urls: list[str] = []
        seen: set[str] = set()
        for a in sitemap_soup.find_all("a", href=True):
            href: str = a["href"]
            if not href.startswith("/mk/"):
                continue
            # Skip self-links and anchors
            if href in ("/mk/mapa-na-sajtot", "/mk/prebaruvanje") or "#" in href:
                continue
            # Only keep paths with ≥4 segments (leaf pages, not top-level categories)
            path_parts = href.strip("/").split("/")
            if len(path_parts) < 4:
                continue
            full_url = BASE_URL + href
            if full_url not in seen:
                seen.add(full_url)
                candidate_urls.append(full_url)

        print(
            f"[crm/sitemap] {len(candidate_urls)} candidate pages to scrape",
            file=sys.stderr, flush=True,
        )

        # ── Step 2: visit each page, extract procedure if present ─────────────
        for i, url in enumerate(candidate_urls, 1):
            label = url.split("/mk/", 1)[-1]
            print(
                f"[crm/sitemap] Scraping {i}/{len(candidate_urls)}: {label}...",
                end=" ", file=sys.stderr, flush=True,
            )
            try:
                await page.goto(url, wait_until="networkidle", timeout=30_000)
                html = await page.content()
                page_soup = BeautifulSoup(html, "html.parser")

                procedure = _extract_procedure(page_soup)
                if not procedure:
                    print("(no procedure)", file=sys.stderr, flush=True)
                    continue

                # First <h2> in the page is the service name
                h2_tags = page_soup.find_all("h2")
                service_name = h2_tags[0].get_text(strip=True) if h2_tags else label

                category = _category_from_url(url)
                SERVICES.setdefault(category, {})[service_name] = {
                    "url": url,
                    "procedure": procedure,
                }
                print(f"✓ {len(procedure)} steps", file=sys.stderr, flush=True)

            except Exception as exc:
                print(f"ERROR: {exc}", file=sys.stderr, flush=True)

        await browser.close()

    total = sum(len(v) for v in SERVICES.values())
    print(
        f"[crm/sitemap] Done — {total} services with procedures "
        f"across {len(SERVICES)} categories",
        file=sys.stderr, flush=True,
    )


# ── Tool functions ─────────────────────────────────────────────────────────────

def list_services() -> dict:
    """
    Return all CRM portal services grouped by category.

    Call this when the user asks what they can do on the CRM portal, asks for
    a list or menu of available services, or asks what procedures are available.
    Returns service names only (not full procedures) to keep the response concise.

    Returns:
        {
            "Сакам да извршам упис или да завршам обврска": [
                "Проверка и резервација на ime на субјект",
                "Самостојна регистрација на субјект",
                ...
            ],
            "Сакам да добијам потврда или информација": [...],
            ...
        }
        Or { "message": "..." } if the cache has not been built yet.
    """
    if not SERVICES:
        return {"message": "Service directory not yet loaded. Please try again in a moment."}
    return {category: list(services.keys()) for category, services in SERVICES.items()}


def get_service_procedure(query: str) -> dict:
    """
    Return the step-by-step procedure for a specific CRM service.

    Call this when the user asks how to do something on the CRM portal — e.g.
    how to register a company, how to check a name reservation, how to submit
    an annual report. The query can be a full service name or a partial keyword.
    Fuzzy matching handles typos and partial inputs.

    Args:
        query: Service name or keyword, e.g. "регистрација на субјект",
               "резервација на ime", "годишна сметка електронски".

    Returns:
        On match:
            {
                "service":   "Full official service name",
                "category":  "Category name",
                "url":       "https://www.crm.com.mk/...",
                "procedure": ["Step 1 text", "Step 2 text", ...]
            }
        On no match:
            {
                "message": "No matching service found. ...",
                "available_services": [<flat list of all service names>]
            }
    """
    if not SERVICES:
        return {"message": "Service directory not yet loaded. Please try again in a moment."}

    # Build flat list: (service_name, category)
    all_entries = [
        (name, cat)
        for cat, services in SERVICES.items()
        for name in services
    ]
    all_names = [name for name, _ in all_entries]

    matches = difflib.get_close_matches(query, all_names, n=1, cutoff=0.3)
    if not matches:
        return {
            "message": (
                "No matching service found. "
                "Ask for list_services() to see all available services."
            ),
            "available_services": all_names,
        }

    service_name = matches[0]
    category = next(cat for name, cat in all_entries if name == service_name)
    data = SERVICES[category][service_name]
    return {
        "service": service_name,
        "category": category,
        "url": data["url"],
        "procedure": data["procedure"],
    }
