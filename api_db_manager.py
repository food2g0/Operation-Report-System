"""
Shared API-backed database manager.

When API_MODE=True  → exports a shared APIDbManager singleton as `db_manager`.
                      All admin pages use the same instance (one JWT token,
                      one persistent HTTP session — no duplicate connections).
When API_MODE=False → re-exports the direct DatabaseManagerPooled as `db_manager`,
                      so every existing `from api_db_manager import db_manager`
                      continues to work without any other changes.

Usage in admin pages (replaces `from db_connect_pooled import db_manager`):
    from api_db_manager import db_manager
"""

import logging
import threading

log = logging.getLogger("APIDbManager")


class APIDbManager:
    """Drop-in replacement for DatabaseManagerPooled that sends every
    execute_query / execute_query_with_exception call through the REST API.

    Public interface matches DatabaseManagerPooled:
        .execute_query(sql, params)                → rows or row-count
        .execute_query_with_exception(sql, params) → (result, exception|None)
        .test_connection()                         → bool
        .connect()                                 → bool
        .logger                                    → logging.Logger
    """

    def __init__(self, base_url: str = None, api_key: str = None, timeout: int = 30):
        import requests as _requests
        try:
            from api_config import API_URL, API_KEY
            _default_url = API_URL
            _default_key = API_KEY
        except ImportError:
            _default_url = "http://127.0.0.1:5000"
            _default_key = ""

        self.base_url = (base_url or _default_url).rstrip("/")
        self.api_key  = api_key or _default_key
        self.timeout  = timeout
        self.logger   = logging.getLogger("APIDbManager")

        self._token   = None
        self._session = _requests.Session()
        self._session.headers.update({"Content-Type": "application/json"})

    # ── Authentication ────────────────────────────────────────────────────────

    def connect(self) -> bool:
        """Obtain a JWT token from /api/token (equivalent to DB connect)."""
        import requests as _requests
        try:
            resp = self._session.post(
                f"{self.base_url}/api/token",
                json={"api_key": self.api_key},
                timeout=self.timeout,
            )
            if resp.status_code == 200:
                self._token = resp.json().get("token")
                self._session.headers.update(
                    {"Authorization": f"Bearer {self._token}"}
                )
                self.logger.info("API token obtained from %s", self.base_url)
                return True
            self.logger.error(
                "Token request failed: %s %s", resp.status_code, resp.text[:200]
            )
            return False
        except Exception as exc:
            self.logger.error("connect() error: %s", exc)
            return False

    def test_connection(self) -> bool:
        """Check API + DB health via /api/health."""
        try:
            resp = self._session.get(
                f"{self.base_url}/api/health", timeout=self.timeout
            )
            return resp.status_code == 200 and resp.json().get("status") == "ok"
        except Exception:
            return False

    # ── Internal helpers ──────────────────────────────────────────────────────

    def _ensure_token(self) -> None:
        if not self._token:
            self.connect()

    @staticmethod
    def _normalise_params(params) -> list:
        if params is None:
            return []
        return list(params)

    def _post_exec(self, endpoint: str, sql: str, params) -> object:
        import requests as _requests
        payload = {"sql": sql, "params": self._normalise_params(params)}
        resp = self._session.post(
            f"{self.base_url}{endpoint}", json=payload, timeout=self.timeout
        )
        if resp.status_code == 401:
            self.logger.warning("Token expired, refreshing…")
            self.connect()
            resp = self._session.post(
                f"{self.base_url}{endpoint}", json=payload, timeout=self.timeout
            )
        return resp

    # ── Public interface (mirrors DatabaseManagerPooled) ─────────────────────

    def execute_query(self, sql: str, params=None):
        """Execute SQL via the API.

        Returns rows (list[dict]) for SELECT, or affected-row count (int)
        for INSERT/UPDATE/DELETE.  Raises RuntimeError on SQL errors.
        """
        import requests as _requests
        self._ensure_token()
        try:
            resp = self._post_exec("/api/exec", sql, params)
            data = resp.json()
            if data.get("error"):
                raise RuntimeError(data["error"])
            return data.get("result")
        except _requests.RequestException as exc:
            self.logger.error("execute_query network error: %s", exc)
            raise

    def execute_query_with_exception(self, sql: str, params=None):
        """Execute SQL via the API.

        Returns (result, None) on success or (None, exception) on error.
        Never raises.  Preserves MySQL error codes (e.g. 1062, 1213) in
        exception.args[0] so retry logic in callers works correctly.
        """
        import requests as _requests
        self._ensure_token()
        try:
            resp = self._post_exec("/api/exec_safe", sql, params)
            data = resp.json()
            exec_error = data.get("exec_error")
            error_code = data.get("error_code")
            if exec_error:
                err = RuntimeError(exec_error)
                if error_code is not None:
                    err.args = (error_code, exec_error)
                return None, err
            return data.get("result"), None
        except _requests.RequestException as exc:
            self.logger.error(
                "execute_query_with_exception network error: %s", exc
            )
            return None, exc

    def execute_batch(self, queries: list) -> list:
        """Execute multiple SQL statements in a single HTTP round-trip.

        queries: list of dicts, each with keys:
            "sql"    (str)           — required
            "params" (list|None)     — optional
            "ttl"    (int|None)      — optional per-query cache TTL override

        Returns a list of dicts (same order as input):
            {"result": ..., "error": str|None, "cached": bool}

        Falls back gracefully: if the batch endpoint is unavailable, returns
        error entries for each query rather than raising.
        """
        import requests as _requests
        self._ensure_token()
        # Normalise params to lists for JSON serialisation
        payload_queries = [
            {
                "sql":    q["sql"],
                "params": list(q["params"]) if q.get("params") else None,
                "ttl":    q.get("ttl"),
            }
            for q in queries
        ]
        try:
            resp = self._session.post(
                f"{self.base_url}/api/batch",
                json={"queries": payload_queries},
                timeout=self.timeout,
            )
            if resp.status_code == 401:
                self.logger.warning("Token expired, refreshing…")
                self.connect()
                resp = self._session.post(
                    f"{self.base_url}/api/batch",
                    json={"queries": payload_queries},
                    timeout=self.timeout,
                )
            return resp.json().get("results", [])
        except _requests.RequestException as exc:
            self.logger.error("execute_batch network error: %s", exc)
            return [{"result": None, "error": str(exc), "cached": False} for _ in queries]


# ── Shared singleton ──────────────────────────────────────────────────────────
# All admin pages that do `from api_db_manager import db_manager` share this
# single instance → one JWT token, one persistent HTTP session.

_shared_instance: "APIDbManager | None" = None
_shared_lock = threading.Lock()


def _get_shared_instance() -> "APIDbManager":
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
    from db_connect_pooled import db_manager  # noqa: F401
