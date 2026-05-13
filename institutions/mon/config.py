"""
institutions/mon/config.py
────────────────────────────────────────────────────────────────────────────────
Configuration for the Ministry of Education and Science (MON) institution.

All data is scraped from the public mon.gov.mk website — no authentication needed.
"""

BASE_URL: str = "https://mon.gov.mk"
COMPETITIONS_URL: str = f"{BASE_URL}/mk-MK/konkursi-i-stipendii/konkursi-mon"
SCHOLARSHIPS_URL: str = f"{BASE_URL}/mk-MK/konkursi-i-stipendii/stipendii-mon"
