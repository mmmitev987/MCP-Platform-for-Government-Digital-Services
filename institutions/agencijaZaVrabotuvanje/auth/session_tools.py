from institutions.agencijaZaVrabotuvanje.auth.browser_auth import browser_authenticator
from institutions.agencijaZaVrabotuvanje.auth.session import session_manager


def login() -> dict:
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
    had_session = session_manager.is_present()
    session_manager.clear()

    if had_session:
        return {"success": True, "message": "Logged out. Session cookies deleted."}

    return {"success": True, "message": "No active session to log out from."}


def check_session() -> dict:
    active = session_manager.is_present()
    saved_at = session_manager.saved_at() if active else None

    return {
        "active": active,
        "saved_at": saved_at,
        "message": (
            f"Session is active. Saved at {saved_at}."
            if active
            else "No active session. Call login first."
        ),
    }