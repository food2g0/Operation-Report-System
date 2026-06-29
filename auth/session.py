"""
auth.session — user session timeout tracking.

Extracted from security.py.  SessionManager is used by:
  - admin_dashboard.py
  - super_admin_dashboard.py
  - Client/dashboard/core.py

Same public API as before so those files need zero changes.
"""
from __future__ import annotations

import time


class SessionManager:
    """Auto-logout after a configurable period of inactivity."""

    def __init__(self, inactivity_timeout: int = 1800) -> None:
        self.inactivity_timeout = inactivity_timeout  # seconds (default: 30 min)
        self._last_activity     = time.time()
        self._active            = True

    def update_activity(self) -> None:
        """Reset the inactivity timer.  Call on any user interaction."""
        self._last_activity = time.time()

    def check_timeout(self) -> bool:
        """Return True if the session has expired."""
        if not self._active:
            return True
        if time.time() - self._last_activity >= self.inactivity_timeout:
            self._active = False
            return True
        return False

    def get_remaining_time(self) -> int:
        """Seconds until timeout (0 if already timed out)."""
        return max(0, int(
            self.inactivity_timeout - (time.time() - self._last_activity)
        ))

    def logout(self) -> None:
        """Mark session as ended."""
        self._active = False

    @property
    def is_active(self) -> bool:
        return self._active

    @is_active.setter
    def is_active(self, value: bool) -> None:
        self._active = value
