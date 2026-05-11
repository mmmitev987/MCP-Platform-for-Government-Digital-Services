"""
Agencija za Vrabotuvanje MCP module.

Provides:
- Authentication (eID via shared layer)
- HTTP client for portal requests
- Institution-specific tools (MCP layer)
"""

from .auth import browser_authenticator, session_manager
from .client import authenticated_client, SessionExpiredError

__all__ = [
    "browser_authenticator",
    "session_manager",
    "authenticated_client",
    "SessionExpiredError",
]