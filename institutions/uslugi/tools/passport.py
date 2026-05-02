"""
institutions/uslugi/tools/passport.py
────────────────────────────────────────────────────────────────────────────────
MCP tool: info_passport_renewal

Fetches detailed information about the passport renewal administrative
procedure (service ID 5200) from the uslugi.gov.mk portal API.

This endpoint is PUBLICLY accessible — no authentication required.
We use a plain requests.post() (not the authenticated client) so the tool
works even before the user has logged in.

The raw API response contains nested JSON with HTML fragments and Macedonian
text.  This function cleans and flattens it into a dict that is easy for
the LLM to read and summarise.
"""

import re

import requests


from institutions.uslugi.tools.service_details import (
    get_service_details,
)


def info_passport_renewal():
    return get_service_details(5200)