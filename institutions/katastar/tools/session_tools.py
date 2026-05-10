"""
institutions/katastar/tools/session_tools.py
────────────────────────────────────────────────────────────────────────────────
MCP tool implementations for session lifecycle on e-uslugi.katastar.gov.mk:
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

from institutions.katastar.auth.browser_auth import browser_authenticator
from institutions.katastar.auth.session import session_manager


def login() -> dict:
    """
    Authenticate the user on e-uslugi.katastar.gov.mk via browser
    and persist the session.

    Opens a Chromium window for the user to complete the login.

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
    Delete the stored e-uslugi.katastar.gov.mk session cookies (log out).

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
    Report whether a valid session exists on disk for e-uslugi.katastar.gov.mk.

    This is a LOCAL check only — it does not make a network request.

    Returns:
        {
            "active":   bool,
            "saved_at": str | None,
            "message":  str,
        }
    """
    active = session_manager.is_present()
    saved_at = session_manager.saved_at() if active else None

    message = (
        f"Katastar session is active (saved at {saved_at})."
        if active
        else "No active katastar session. Call 'katastar__login' first."
    )

    return {"active": active, "saved_at": saved_at, "message": message}