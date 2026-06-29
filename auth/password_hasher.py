"""
auth.password_hasher — bcrypt password operations.

Extracted from security.py.  The old module had these functions at module
level with no class wrapper, making them hard to mock in tests.  Same
behaviour, cleaner interface.
"""
from __future__ import annotations

import logging

import bcrypt

log = logging.getLogger(__name__)


def hash_password(password: str) -> str:
    """Hash a plain-text password with bcrypt (12 rounds)."""
    if not password:
        raise ValueError("Cannot hash an empty password")
    salt   = bcrypt.gensalt(rounds=12)
    hashed = bcrypt.hashpw(password.encode("utf-8"), salt)
    return hashed.decode("utf-8")


def verify_password(password: str, stored: str) -> bool:
    """
    Verify password against a stored bcrypt hash or legacy plaintext.
    Logs a warning for legacy plaintext matches — migrate those accounts.
    """
    if not password or not stored:
        return False
    try:
        if stored.startswith("$2b$") or stored.startswith("$2a$"):
            return bcrypt.checkpw(password.encode("utf-8"), stored.encode("utf-8"))
        # Legacy plaintext fallback
        if password == stored:
            log.warning("Plaintext password match — account should be migrated to bcrypt")
            return True
        return False
    except Exception as exc:
        log.error("Password verification error: %s", exc)
        return False


def is_password_hashed(password: str) -> bool:
    """Return True if the string looks like a bcrypt hash."""
    return bool(password and (
        password.startswith("$2b$") or password.startswith("$2a$")
    ))


def validate_password_strength(password: str) -> tuple[bool, str]:
    """
    Check minimum password requirements.
    Returns (is_valid, message).
    """
    if not password:
        return False, "Password is required"
    if len(password) < 8:
        return False, "Password must be at least 8 characters"
    if not any(c.isupper() for c in password):
        return False, "Password must contain at least one uppercase letter"
    if not any(c.islower() for c in password):
        return False, "Password must contain at least one lowercase letter"
    if not any(c.isdigit() for c in password):
        return False, "Password must contain at least one number"
    return True, "Password is strong"
