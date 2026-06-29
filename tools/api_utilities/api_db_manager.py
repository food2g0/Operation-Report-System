"""
API-backed database manager for server-side admin tools.

All wire-protocol logic lives in api_client_base._APIClientBase.  This
subclass adds proactive token-TTL tracking so long-running admin sessions
never hit an expired-token error mid-operation.

Usage:
    from tools.api_utilities.api_db_manager import db_manager
    rows = db_manager.execute_query("SELECT ...", params)
"""
from __future__ import annotations

import logging
import threading
import time

from tools.api_client_base import _APIClientBase

log = logging.getLogger("APIDbManager")


class APIDbManager(_APIClientBase):

    # Admin tools may stay open for hours — refresh 100 s before the 1-hour expiry.
    _TOKEN_TTL = 3500

    def __init__(
        self,
        base_url: str | None = None,
        api_key: str | None = None,
        timeout: int = 1,
    ) -> None:
        try:
            from api_config import API_URL, API_KEY
            _default_url = API_URL
            _default_key = API_KEY
        except ImportError:
            _default_url = "http://127.0.0.1:5000"
            _default_key = ""

        super().__init__(
            base_url=base_url or _default_url,
            api_key=api_key or _default_key,
            timeout=timeout,
            verify_ssl=True,
        )
        self._token_time: float = 0.0

    def connect(self) -> bool:
        """Obtain a JWT token and record the time for TTL tracking."""
        ok = super().connect()
        if ok:
            self._token_time = time.time()
        return ok

    def _ensure_token(self) -> None:
        """Proactively refresh the token before it expires."""
        age = time.time() - self._token_time
        if not self._token or age >= self._TOKEN_TTL:
            if self._token:
                self.logger.debug(
                    "Token age %.0fs >= TTL %ds — proactive refresh", age, self._TOKEN_TTL
                )
            self.connect()


# ── Shared singleton ──────────────────────────────────────────────────────────
# All admin pages that do `from api_db_manager import db_manager` share this
# single instance → one JWT token, one persistent HTTP session.

_shared_instance: APIDbManager | None = None
_shared_lock = threading.Lock()


def _get_shared_instance() -> APIDbManager:
    global _shared_instance
    if _shared_instance is None:
        with _shared_lock:
            if _shared_instance is None:
                _shared_instance = APIDbManager()
    return _shared_instance


# ── Module-level `db_manager` export ─────────────────────────────────────────
try:
    from api_config import API_MODE as _API_MODE
except ImportError:
    _API_MODE = False

if _API_MODE:
    db_manager = _get_shared_instance()
else:
    # Fall back to direct DB — zero behaviour change when API_MODE is off.
    from tools.db_connect_pooled import db_manager  # noqa: F401
