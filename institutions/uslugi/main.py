"""
institutions/uslugi/main.py
────────────────────────────────────────────────────────────────────────────────
FastMCP server entry point for uslugi.gov.mk.

This file wires together all tools for this institution and exposes them via
the MCP stdio transport.  It is designed to be run as a subprocess by the
gateway (gateway/main.py), but can also be run standalone for testing:

    python -m institutions.uslugi.main

Architecture in context:
  gateway/main.py
    └── spawns this as a subprocess
    └── connects via MCP stdio
    └── exposes tools to the agent under the "uslugi__" namespace

Adding new tools:
  1. Create the tool function in institutions/uslugi/tools/<file>.py.
  2. Import it here and decorate the wrapper with @mcp.tool().
  3. Write a clear docstring — it becomes the tool description shown to the LLM.
"""

from mcp.server.fastmcp import FastMCP

from institutions.uslugi.service_registry import SERVICES
from institutions.uslugi.tools.service_details import (
    get_service_details,
)

mcp = FastMCP("uslugi")

for service_id, slug in SERVICES.items():
    def make_tool(sid, sslug):
        @mcp.tool(
            name=f"info_{sslug}",
            description=f"Get information for {sslug}",
        )
        def tool():
            return get_service_details(sid)

        return tool


    make_tool(service_id, slug)

if __name__ == "__main__":
    mcp.run()
