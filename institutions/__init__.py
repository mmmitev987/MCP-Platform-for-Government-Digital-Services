# institutions/ — One sub-package per institution (government portal).
#
# Each sub-package is a self-contained FastMCP server.  It:
#   • Has its own config.py (reads institution-specific env vars).
#   • Instantiates the shared/ infrastructure with its own settings.
#   • Registers MCP tools in its main.py.
#   • Can be run standalone:  python -m institutions.<slug>.main
#
# The gateway (gateway/main.py) spawns each institution server as a
# subprocess and aggregates their tools under namespaced names.
