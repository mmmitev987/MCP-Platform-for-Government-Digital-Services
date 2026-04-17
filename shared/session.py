"""
shared/session.py
────────────────────────────────────────────────────────────────────────────────
Generic, institution-agnostic secure cookie persistence.

A fresh Fernet key is generated on every server startup.  This means sessions
are ephemeral: if the server restarts, the old .enc file cannot be decrypted
(different key) and is treated as absent — the user simply logs in again.
No key management or .env entries are required.

Encryption:
  Cookies are encrypted with Fernet (AES-128-CBC + HMAC-SHA256) before
  being written to disk.

On-disk cookie format (before encryption):
  {
    "cookies": { "<name>": "<value>", ... },
    "saved_at": "<ISO-8601 UTC timestamp>"
  }
  The JSON blob is Fernet-encrypted → stored as base64 bytes in the .enc file.
"""

import json
from datetime import datetime, timezone
from pathlib import Path

from cryptography.fernet import Fernet, InvalidToken


class SessionManager:
    """
    Saves and loads encrypted session cookies for a single institution.

    A fresh Fernet key is generated every time the server starts.  Sessions
    are intentionally ephemeral: if the server restarts, the .enc file from
    the previous run cannot be decrypted (different key) and is treated as
    absent — the user simply logs in again.

    Args:
        session_file:   Absolute Path to the .enc file on disk.
        institution_id: Short label used in log messages (e.g. "uslugi").

    Usage:
        sm = SessionManager(session_file=..., institution_id="uslugi")
        sm.save({"session_id": "abc123"})
        cookies = sm.load()   # → dict | None
        sm.clear()            # logout
    """

    def __init__(self, session_file: Path, institution_id: str):
        self._session_file = session_file
        self._institution_id = institution_id

        # Generate a fresh random key every startup.  No persistence needed —
        # if the .enc file exists from a previous run it will fail to decrypt
        # and be treated as a missing session (user logs in again).
        self._fernet = Fernet(Fernet.generate_key())

    # ── Public API ────────────────────────────────────────────────────────────

    def save(self, cookies: dict) -> None:
        """
        Encrypt and persist a cookie dict to the institution's session file.

        Args:
            cookies: Plain dict of { cookie_name: cookie_value }.
        """
        payload = {
            "cookies": cookies,
            # Timestamp lets us reason about session age later (e.g., warn if
            # cookies are many days old).
            "saved_at": datetime.now(timezone.utc).isoformat(),
        }

        # Serialize to JSON bytes, then encrypt with Fernet.
        # Fernet output is a base64-encoded authenticated ciphertext token.
        plaintext = json.dumps(payload).encode()
        ciphertext = self._fernet.encrypt(plaintext)

        # Make sure the storage directory exists (e.g. storage/ on first run).
        self._session_file.parent.mkdir(parents=True, exist_ok=True)

        # Write the encrypted token to disk.
        self._session_file.write_bytes(ciphertext)
        print(f"[SessionManager:{self._institution_id}] Session saved to {self._session_file}")

    def load(self) -> dict | None:
        """
        Load and decrypt the stored cookie dict.

        Returns:
            Dict of { cookie_name: cookie_value } on success.
            None if the file is missing, the key is wrong, or data is corrupt.
        """
        if not self._session_file.exists():
            return None

        try:
            ciphertext = self._session_file.read_bytes()
            # Fernet.decrypt() also verifies the HMAC — raises InvalidToken if
            # the data has been tampered with or the key is wrong.
            plaintext = self._fernet.decrypt(ciphertext)
            payload = json.loads(plaintext)
            return payload.get("cookies", {})

        except InvalidToken:
            # Possible causes: wrong COOKIE_ENCRYPTION_KEY in .env, or
            # the session file was corrupted / created by a different key.
            print(
                f"[SessionManager:{self._institution_id}] WARNING: "
                "Could not decrypt session file (wrong key or corrupted data). "
                "Treating session as absent."
            )
            return None

        except Exception as exc:
            print(f"[SessionManager:{self._institution_id}] ERROR loading session: {exc}")
            return None

    def clear(self) -> None:
        """Delete the session file from disk (logout)."""
        if self._session_file.exists():
            self._session_file.unlink()
            print(f"[SessionManager:{self._institution_id}] Session file deleted (logged out).")
        else:
            print(f"[SessionManager:{self._institution_id}] No session file to delete.")

    def is_present(self) -> bool:
        """Return True if a session file exists on disk (not validity-checked)."""
        return self._session_file.exists()

    def saved_at(self) -> str | None:
        """
        Return the ISO-8601 UTC timestamp when this session was saved, or None.

        Decrypts the file just to read the timestamp.  We accept the small
        overhead here; it's called only by check_session() which is infrequent.
        """
        if not self._session_file.exists():
            return None
        try:
            ciphertext = self._session_file.read_bytes()
            plaintext = self._fernet.decrypt(ciphertext)
            payload = json.loads(plaintext)
            return payload.get("saved_at")
        except Exception:
            return None
