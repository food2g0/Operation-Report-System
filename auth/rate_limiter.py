"""
auth.rate_limiter — brute-force login protection.

Extracted from security.py.  No global singletons here — callers create their
own instance (or use the module-level `login_rate_limiter` convenience export).

Key improvements over the old version:
- `is_locked` and `record_failed_attempt` share a single internal method
  instead of duplicating the cleanup + count logic.
- Thread-safe with a single Lock.
- `format_lockout_time` lives here (it logically belongs to the rate limiter).
"""
from __future__ import annotations

import time
from collections import defaultdict
from threading import Lock


class RateLimiter:
    """Block a username after too many failed login attempts."""

    def __init__(self, max_attempts: int = 5, lockout_seconds: int = 300) -> None:
        self.max_attempts    = max_attempts
        self.lockout_seconds = lockout_seconds
        self._attempts: dict[str, list[float]] = defaultdict(list)
        self._lock = Lock()

    # ── Public API ────────────────────────────────────────────────────────────

    def record_failed_attempt(self, username: str) -> tuple[bool, int, int]:
        """
        Log a failed attempt.
        Returns (is_locked, remaining_attempts, lockout_seconds_remaining).
        """
        with self._lock:
            self._prune(username)
            self._attempts[username.lower()].append(time.time())
            return self._status(username)

    def is_locked(self, username: str) -> tuple[bool, int]:
        """
        Check lock status without recording an attempt.
        Returns (is_locked, lockout_seconds_remaining).
        """
        with self._lock:
            self._prune(username)
            locked, remaining, lockout_secs = self._status(username)
            return locked, lockout_secs

    def reset(self, username: str) -> None:
        """Clear all failed attempts (call after successful login)."""
        with self._lock:
            self._attempts[username.lower()].clear()

    # ── Private ───────────────────────────────────────────────────────────────

    def _prune(self, username: str) -> None:
        """Remove attempts older than lockout_seconds (must hold lock)."""
        cutoff = time.time() - self.lockout_seconds
        key = username.lower()
        self._attempts[key] = [t for t in self._attempts[key] if t >= cutoff]

    def _status(self, username: str) -> tuple[bool, int, int]:
        key      = username.lower()
        attempts = self._attempts[key]
        count    = len(attempts)

        if count >= self.max_attempts:
            oldest       = min(attempts)
            lockout_left = max(0, int(self.lockout_seconds - (time.time() - oldest)))
            return True, 0, lockout_left

        return False, self.max_attempts - count, 0


def format_lockout_time(seconds: int) -> str:
    """Human-readable lockout countdown, e.g. '4 min 30 sec'."""
    if seconds < 60:
        return f"{seconds} seconds"
    m, s = divmod(seconds, 60)
    return f"{m} min {s} sec" if s else f"{m} minutes"


# Module-level singleton — same interface as the old security.login_rate_limiter
login_rate_limiter = RateLimiter(max_attempts=5, lockout_seconds=300)
