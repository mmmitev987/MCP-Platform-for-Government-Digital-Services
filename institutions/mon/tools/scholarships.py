"""
institutions/mon/tools/scholarships.py
────────────────────────────────────────────────────────────────────────────────
Tools for browsing MON scholarships (Стипендии) from mon.gov.mk.
"""

from institutions.mon.config import SCHOLARSHIPS_URL
from institutions.mon.tools._scraper import scrape_listing, scrape_detail

_SCHOLARSHIPS_URL = SCHOLARSHIPS_URL
_SECTION = _SCHOLARSHIPS_URL.rstrip("/").rsplit("/", 1)[-1]


def list_mon_scholarships() -> dict:
    """
    List all MON scholarships (Стипендии) scraped from mon.gov.mk.

    All pages are fetched automatically via the Livewire pagination API.
    No login required.

    Returns:
        {
            "scholarships": list of {
                "title":       str,
                "date":        str,   # DD/MM/YYYY
                "url":         str,   # detail page URL
                "description": str,   # short excerpt
            },
            "total": int,
        }
    """
    items = scrape_listing(_SCHOLARSHIPS_URL, _SECTION)
    if isinstance(items, dict) and items.get("error"):
        return items
    return {"scholarships": items, "total": len(items)}


def get_mon_scholarship_details(url: str) -> dict:
    """
    Fetch full details for a specific MON scholarship.

    Args:
        url: Full URL of the scholarship detail page, as returned in the
             "url" field of list_mon_scholarships().

    Returns:
        {
            "url":         str,
            "title":       str,
            "date":        str,
            "body":        str,         # full scholarship text (up to 4000 chars)
            "attachments": list of { "name": str, "url": str },
        }
    """
    return scrape_detail(url)
