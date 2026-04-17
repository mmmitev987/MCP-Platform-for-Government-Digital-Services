"""
institutions/uslugi/tools/session_tools.py
────────────────────────────────────────────────────────────────────────────────
MCP tool implementations for session lifecycle on uslugi.gov.mk:
  • login()         — authenticate and persist session cookies
  • logout()        — delete stored cookies
  • check_session() — report whether a session exists on disk

Security contract (the LLM must never touch credentials or cookies):
  ───────────────────────────────────────────────────────────────────
  • login() takes NO credential parameters — the LLM can call it but
    cannot pass a username or password.
  • User types credentials in the Chromium window — Python and the LLM
    never see them.
  • Cookies are encrypted on disk and NEVER included in tool return values.
"""

from institutions.uslugi.auth.browser_auth import browser_authenticator
from institutions.uslugi.auth.session import session_manager


def login() -> dict:
    """
    Authenticate the user on uslugi.gov.mk via browser and persist the session.

    Opens a Chromium window for the user to complete the eid.mk SSO login.

    Returns:
        {
            "success":        bool,
            "message":        str,
            "strategy_used":  str,
            "cookies_saved":  int,
        }
    """
    cookies = browser_authenticator.run()

    if not cookies:
        return {
            "success": False,
            "message": "Browser authentication failed or timed out.",
            "strategy_used": "browser",
            "cookies_saved": 0,
        }

    session_manager.save(cookies)
    return {
        "success": True,
        "message": "Browser authentication successful. Session saved.",
        "strategy_used": "browser",
        "cookies_saved": len(cookies),
    }


def logout() -> dict:
    """
    Delete the stored uslugi.gov.mk session cookies (log out).

    Returns:
        { "success": bool, "message": str }
    """
    had_session = session_manager.is_present()
    session_manager.clear()

    if had_session:
        return {"success": True, "message": "Logged out. Session cookies deleted."}
    return {"success": True, "message": "No active session to log out from."}


def check_session() -> dict:
    """
    Report whether a valid session exists on disk for uslugi.gov.mk.

    This is a LOCAL check only — it does not make a network request.
    A session can exist on disk but already be rejected by the server
    (e.g. after a server-side logout or token expiry).  For a hard check,
    call authenticated_get on a protected endpoint and watch for errors.

    Returns:
        {
            "active":   bool,
            "saved_at": str | None,   # ISO-8601 UTC timestamp of last login
            "message":  str,
        }
    """
    active = session_manager.is_present()
    saved_at = session_manager.saved_at() if active else None

    message = (
        f"Session is active (saved at {saved_at})."
        if active
        else "No active session. Call 'login' first."
    )

    return {"active": active, "saved_at": saved_at, "message": message}


