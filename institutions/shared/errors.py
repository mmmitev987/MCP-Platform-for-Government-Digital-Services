"""
institutions/shared/errors.py
────────────────────────────────────────────────────────────────────────────────
Shared helper for building well-structured error responses that MCP tools
return on failure, so the LLM agent can surface clear, actionable messages
to the user.

Error format:
    {
        "error":   True,           # always True — lets the agent check quickly
        "code":    "snake_case",   # machine-readable error category
        "message": "Human text",   # human-readable description
    }

Common error codes
──────────────────
    network_error       — could not reach the remote service (timeout, DNS, etc.)
    auth_required       — an active session is needed; call the login tool first
    not_found           — the requested resource does not exist
    parse_error         — the service returned an unexpected / malformed response
    browser_error       — Playwright / browser initialisation problem
    unexpected_error    — catch-all for unclassified exceptions
"""


def tool_error(code: str, message: str) -> dict:
    """
    Return a structured error dict for use in MCP tool return values.

    Args:
        code:    Machine-readable error category (e.g. "network_error").
        message: Human-readable description to surface to the user via the LLM.

    Returns:
        { "error": True, "code": code, "message": message }
    """
    return {"error": True, "code": code, "message": message}
