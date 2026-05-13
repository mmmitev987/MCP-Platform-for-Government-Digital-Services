"""
institutions/mon/tools/competitions.py
────────────────────────────────────────────────────────────────────────────────
Tools for browsing MON competitions (Конкурси) from mon.gov.mk.
"""

from institutions.mon.config import COMPETITIONS_URL
from institutions.mon.tools._scraper import scrape_listing, scrape_detail

_COMPETITIONS_URL = COMPETITIONS_URL
_SECTION = _COMPETITIONS_URL.rstrip("/").rsplit("/", 1)[-1]


def list_mon_competitions() -> dict:
    """
    List all MON competitions (Конкурси) scraped from mon.gov.mk.

    All pages are fetched automatically via the Livewire pagination API.
    No login required.

    Returns:
        {
            "competitions": list of {
                "title":       str,
                "date":        str,   # DD/MM/YYYY
                "url":         str,   # detail page URL
                "description": str,   # short excerpt
            },
            "total": int,
        }
    """
    items = scrape_listing(_COMPETITIONS_URL, _SECTION)
    if isinstance(items, dict) and items.get("error"):
        return items
    return {"competitions": items, "total": len(items)}


def get_mon_competition_details(url: str) -> dict:
    """
    Fetch full details for a specific MON competition.

    Args:
        url: Full URL of the competition detail page, as returned in the
             "url" field of list_mon_competitions().

    Returns:
        {
            "url":         str,
            "title":       str,
            "date":        str,
            "body":        str,         # full competition text (up to 4000 chars)
            "attachments": list of { "name": str, "url": str },
        }
    """
    return scrape_detail(url)
