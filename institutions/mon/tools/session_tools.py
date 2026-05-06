"""
institutions/mon/tools/session_tools.py
────────────────────────────────────────────────────────────────────────────────
Session lifecycle tools for e-uslugi.mon.gov.mk.

The portal uses JWT tokens stored in localStorage. After browser login the
token is captured and stored encrypted on disk so subsequent tool calls can
use it without re-opening the browser.
"""

from institutions.mon.auth.browser_auth import browser_authenticator
from institutions.mon.auth.session import session_manager


def login() -> dict:
    data = browser_authenticator.run()

    if not data or not data.get("access_token"):
        return {
            "success": False,
            "message": "Browser authentication failed or timed out.",
        }

    session_manager.save(data)
    return {
        "success": True,
        "message": "Logged in to e-uslugi.mon.gov.mk. Session saved.",
    }


def logout() -> dict:
    had_session = session_manager.is_present()
    session_manager.clear()

    if had_session:
        return {"success": True, "message": "Logged out. MON session deleted."}
    return {"success": True, "message": "No active MON session to log out from."}


def check_session() -> dict:
    active = session_manager.is_present()
    saved_at = session_manager.saved_at() if active else None

    message = (
        f"MON session is active (saved at {saved_at})."
        if active
        else "No active MON session. Call login_mon first."
    )
    return {"active": active, "saved_at": saved_at, "message": message}
