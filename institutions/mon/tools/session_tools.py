"""
institutions/mon/tools/session_tools.py
────────────────────────────────────────────────────────────────────────────────
Session lifecycle tools for e-uslugi.mon.gov.mk.

The portal uses JWT tokens stored in localStorage. After browser login the
token is captured and stored encrypted on disk so subsequent tool calls can
use it without re-opening the browser.
"""

from institutions.shared.errors import tool_error
from institutions.mon.auth.browser_auth import browser_authenticator
from institutions.mon.auth.session import session_manager


def login() -> dict:
    """
    Log in to e-uslugi.mon.gov.mk via browser and save the session.

    Returns:
        { "success": bool, "message": str }
        or on error: { "error": True, "code": str, "message": str }
    """
    try:
        data = browser_authenticator.run()
    except Exception as exc:
        return tool_error("browser_error", f"Failed to launch the authentication browser: {exc}")

    if not data or not data.get("access_token"):
        return {
            "success": False,
            "message": "Browser authentication failed or timed out.",
        }

    try:
        session_manager.save(data)
    except Exception as exc:
        return tool_error("unexpected_error", f"Authentication succeeded but failed to save session: {exc}")

    return {
        "success": True,
        "message": "Logged in to e-uslugi.mon.gov.mk. Session saved.",
    }


def logout() -> dict:
    """
    Log out of e-uslugi.mon.gov.mk by deleting the stored session.

    Returns:
        { "success": bool, "message": str }
        or on error: { "error": True, "code": str, "message": str }
    """
    try:
        had_session = session_manager.is_present()
        session_manager.clear()
    except Exception as exc:
        return tool_error("unexpected_error", f"Failed to clear the MON session: {exc}")

    if had_session:
        return {"success": True, "message": "Logged out. MON session deleted."}
    return {"success": True, "message": "No active MON session to log out from."}


def check_session() -> dict:
    """
    Check whether an active MON session exists.

    Returns:
        { "active": bool, "saved_at": str | None, "message": str }
        or on error: { "error": True, "code": str, "message": str }
    """
    try:
        active = session_manager.is_present()
        saved_at = session_manager.saved_at() if active else None
    except Exception as exc:
        return tool_error("unexpected_error", f"Failed to read MON session state: {exc}")

    message = (
        f"MON session is active (saved at {saved_at})."
        if active
        else "No active MON session. Call login_mon first."
    )
    return {"active": active, "saved_at": saved_at, "message": message}
