"""
API-backed database manager — drop-in replacement for DatabaseManagerPooled.

Routes all SQL queries through the ORS REST API (api_server.py) instead of
connecting to MySQL directly.  Client machines need only HTTP access to the
API server; no direct database credentials or MySQL driver required.

Usage (automatic — controlled by api_config.API_MODE):
    from Client.api_db_manager import APIDbManager
    db = APIDbManager()
    db.connect()          # obtains a JWT from /api/token
    rows = db.execute_query("SELECT ...", params)
    result, err = db.execute_query_with_exception("INSERT ...", params)
"""

import logging
import requests

log = logging.getLogger("APIDbManager")


class APIDbManager:
    """Drop-in replacement for DatabaseManagerPooled that sends every
    execute_query / execute_query_with_exception call to the API server.

    The public interface matches DatabaseManagerPooled:
        .execute_query(sql, params)              → rows or row-count
        .execute_query_with_exception(sql, params) → (result, exception|None)
        .test_connection()                       → bool
        .connect()                               → bool
        .logger                                  → logging.Logger
    """

    def __init__(self, base_url: str = None, api_key: str = None, timeout: int = 30):
        # Lazy-import api_config so the module can be imported even if
        # api_config is not present (e.g. unit tests).
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
        self._session = requests.Session()
        # Keep the session alive across calls
        self._session.headers.update({"Content-Type": "application/json"})

    # ── Authentication ────────────────────────────────────────────────────────

    def connect(self) -> bool:
        """Obtain a JWT token from /api/token (equivalent to DB connect)."""
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
        """Convert params tuple/list/None to a JSON-serialisable list."""
        if params is None:
            return []
        return list(params)

    def _post_exec(self, endpoint: str, sql: str, params) -> dict:
        """POST to /api/exec or /api/exec_safe and handle token refresh."""
        payload = {"sql": sql, "params": self._normalise_params(params)}
        resp = self._session.post(
            f"{self.base_url}{endpoint}", json=payload, timeout=self.timeout
        )
        if resp.status_code == 401:
            # Token expired — refresh once and retry
            self.logger.warning("Token expired, refreshing…")
            self.connect()
            resp = self._session.post(
                f"{self.base_url}{endpoint}", json=payload, timeout=self.timeout
            )
        return resp

    # ── Public interface (mirrors DatabaseManagerPooled) ──────────────────────

    def execute_query(self, sql: str, params=None):
        """Execute SQL via the API.

        Returns rows (list[dict]) for SELECT statements,
        or affected-row count (int) for INSERT/UPDATE/DELETE.
        Raises RuntimeError on server-side SQL errors (same as direct DB manager).
        """
        self._ensure_token()
        try:
            resp = self._post_exec("/api/exec", sql, params)
            data = resp.json()
            if data.get("error"):
                raise RuntimeError(data["error"])
            return data.get("result")
        except requests.RequestException as exc:
            self.logger.error("execute_query network error: %s", exc)
            raise

    def execute_query_with_exception(self, sql: str, params=None):
        """Execute SQL via the API.

        Returns (result, None) on success or (None, exception) on error.
        Never raises — mirrors DatabaseManagerPooled.execute_query_with_exception.
        The exception carries the original MySQL error code in args[0] so that
        deadlock (1213) and duplicate-key (1062) retry logic in client_dashboard
        continues to work correctly.
        """
        self._ensure_token()
        try:
            resp = self._post_exec("/api/exec_safe", sql, params)
            data = resp.json()
            exec_error = data.get("exec_error")
            error_code = data.get("error_code")
            if exec_error:
                err = RuntimeError(exec_error)
                if error_code is not None:
                    # Preserve the MySQL error code as args[0]
                    err.args = (error_code, exec_error)
                return None, err
            return data.get("result"), None
        except requests.RequestException as exc:
            self.logger.error(
                "execute_query_with_exception network error: %s", exc
            )
            return None, exc

    def execute_batch(self, queries: list) -> list:
        """Execute multiple SQL statements in a single HTTP round-trip.

        queries: list of dicts with keys:
            "sql"    (str)       — required
            "params" (list|None) — optional
            "ttl"    (int|None)  — optional per-query cache TTL override

        Returns a list of dicts (same order):
            {"result": ..., "error": str|None, "cached": bool}
        """
        self._ensure_token()
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
        except requests.RequestException as exc:
            self.logger.error("execute_batch network error: %s", exc)
            return [{"result": None, "error": str(exc), "cached": False} for _ in queries]
