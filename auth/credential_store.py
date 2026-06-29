"""
auth.credential_store — offline credential persistence.

Extracted from offline_manager.py (credential-only methods).
The pending-entry queue logic stays in offline_manager.py because it is
about report posting, not authentication.

Key improvements:
- Structured dataclass return instead of raw dict
- No print() statements — uses logging
- Explicit expiry check (7-day TTL)
- Salt is constant but clearly documented
"""
from __future__ import annotations

import hashlib
import json
import logging
import os
import sys
import time
from dataclasses import dataclass
from typing import Optional

log = logging.getLogger(__name__)

_CACHE_TTL_SECONDS = 7 * 24 * 3600  # 7 days
_LOCAL_SALT        = "ORS_OFFLINE_2024"  # same salt as old offline_manager


@dataclass
class CachedUser:
    username:     str
    role:         str
    branch:       str
    corporation:  str
    account_type: Optional[int] = None
    os_group:     Optional[str] = None


def _data_dir() -> str:
    base = (
        os.path.dirname(sys.executable)
        if getattr(sys, "frozen", False)
        else os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    )
    d = os.path.join(base, "offline_data")
    os.makedirs(d, exist_ok=True)
    return d


def _credentials_path() -> str:
    return os.path.join(_data_dir(), "cached_credentials.json")


def _hash(password: str) -> str:
    raw = f"{_LOCAL_SALT}{password}{_LOCAL_SALT}".encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


class CredentialStore:
    """Read/write offline credential cache for branch users."""

    def save(self, username: str, password: str, user_data: dict) -> bool:
        """Cache credentials after a successful online login."""
        try:
            path   = _credentials_path()
            cached = self._load_all()

            cached[username.lower()] = {
                "password_hash": _hash(password),
                "username":      username,
                "role":          str(user_data.get("role", "user")),
                "branch":        str(user_data.get("branch", "")),
                "corporation":   str(user_data.get("corporation", "")),
                "account_type":  user_data.get("account_type"),
                "os_group":      user_data.get("os_group"),
                "cached_at":     time.time(),
            }

            with open(path, "w", encoding="utf-8") as f:
                json.dump(cached, f, indent=2)

            log.info("Offline credentials cached for: %s", username)
            return True
        except Exception as exc:
            log.error("Failed to cache credentials for %s: %s", username, exc)
            return False

    def verify(
        self, username: str, password: str
    ) -> tuple[bool, Optional[CachedUser]]:
        """
        Verify credentials against the local cache.
        Returns (success, CachedUser | None).
        """
        try:
            entry = self._load_all().get(username.lower())
            if not entry:
                return False, None

            # cached_at missing in credentials written by old offline_manager — treat as fresh
            cached_at = entry.get("cached_at")
            if cached_at is not None and time.time() - cached_at > _CACHE_TTL_SECONDS:
                log.warning("Cached credentials expired for: %s", username)
                return False, None

            if _hash(password) != entry.get("password_hash"):
                return False, None

            return True, CachedUser(
                username=entry["username"],
                role=entry.get("role", "user"),
                branch=entry.get("branch", ""),
                corporation=entry.get("corporation", ""),
                account_type=entry.get("account_type"),
                os_group=entry.get("os_group"),
            )
        except Exception as exc:
            log.error("Offline credential verification error: %s", exc)
            return False, None

    def has_credentials(self, username: Optional[str] = None) -> bool:
        try:
            cached = self._load_all()
            if username:
                return username.lower() in cached
            return bool(cached)
        except Exception:
            return False

    # ── Private ───────────────────────────────────────────────────────────────

    @staticmethod
    def _load_all() -> dict:
        path = _credentials_path()
        if not os.path.isfile(path):
            return {}
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            return {}
