"""
API-backed database manager — drop-in replacement for DatabaseManagerPooled.

Routes all SQL queries through the ORS REST API (api_server.py) instead of
connecting to MySQL directly.  Client machines need only HTTP access to the
API server; no direct database credentials or MySQL driver required.

All wire-protocol logic lives in api_client_base._APIClientBase.  This
subclass adds the two things that differ for branch-machine deployments:

  1. SSL certificate verification is disabled (self-signed cert on private LAN).
  2. The token refresh strategy is reactive only (no proactive TTL tracking)
     because branch clients have a single active session and hit /api/exec_safe
     which returns 401 on expiry anyway.

Usage (automatic — controlled by api_config.API_MODE):
    from Client.api_db_manager import APIDbManager
    db = APIDbManager()
    db.connect()          # obtains a JWT from /api/token
    rows = db.execute_query("SELECT ...", params)
    result, err = db.execute_query_with_exception("INSERT ...", params)
"""
from __future__ import annotations

import logging
import threading

from api_client_base import _APIClientBase

log = logging.getLogger("APIDbManager")


class APIDbManager(_APIClientBase):

    def __init__(
        self,
        base_url: str | None = None,
        api_key: str | None = None,
        timeout: int = 30,
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
            verify_ssl=False,  # private-network self-signed cert
        )


# ── Shared singleton ──────────────────────────────────────────────────────────
# All pages that do `from Client.api_db_manager import db_manager` share this
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
    from db_connect_pooled import db_manager  # noqa: F401
