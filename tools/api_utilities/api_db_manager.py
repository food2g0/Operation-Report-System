

import logging
import threading
import time
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

log = logging.getLogger("APIDbManager")


class APIDbManager:


    def __init__(self, base_url: str = None, api_key: str = None, timeout: int = 1):
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
        self._token_time = 0  # Track when token was obtained
        self._token_ttl = 3500  # Tokens expire in ~1 hour (3600s), refresh at 3500s to be safe
        self._session = _requests.Session()
        retry = Retry(
            total=1,
            connect=1,
            read=1,
            backoff_factor=0.3,
            # 503 = server busy — retrying immediately makes overload worse.
            # 500 = server error — may be transient but also often not; skip retry.
            # Keep 502/504 (gateway timeouts) which are reliably transient.
            status_forcelist=[429, 502, 504],
            allowed_methods=["GET", "POST"],
        )
        adapter = HTTPAdapter(max_retries=retry)
        self._session.mount("http://", adapter)
        self._session.mount("https://", adapter)
        self._session.headers.update({"Content-Type": "application/json"})

    def __del__(self):
        """Clean up HTTP session when object is garbage collected."""
        try:
            if self._session:
                self._session.close()
        except Exception:
            pass  # Ignore errors during cleanup

    def close(self):
        """Explicitly close the HTTP session."""
        try:
            if self._session:
                self._session.close()
                self._session = None
        except Exception:
            pass

    # ── Authentication ────────────────────────────────────────────────────────

    def connect(self) -> bool:
        """Obtain a JWT token from /api/token (equivalent to DB connect)."""
        import requests as _requests
        try:
            resp = self._session.post(
                f"{self.base_url}/api/token",
                json={"api_key": self.api_key},
                timeout=(5, self.timeout),
            )
            if resp.status_code == 200:
                self._token = resp.json().get("token")
                self._token_time = time.time()  # Record when token was obtained
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
                f"{self.base_url}/api/health", timeout=(3, self.timeout)
            )
            return resp.status_code == 200 and resp.json().get("status") == "ok"
        except Exception:
            return False

    # ── Internal helpers ──────────────────────────────────────────────────────

    def _ensure_token(self) -> None:
        """Ensure we have a valid token, refreshing if expired."""
        now = time.time()
        token_age = now - self._token_time

        # Refresh if no token or token is too old
        if not self._token or token_age >= self._token_ttl:
            if token_age >= self._token_ttl and self._token:
                self.logger.debug(f"Token expired (age={token_age:.0f}s), refreshing...")
            self.connect()

    @staticmethod
    def _normalise_params(params) -> list:
        if params is None:
            return []
        return list(params)

    def _post_exec(self, endpoint: str, sql: str, params) -> object:
        import requests as _requests
        payload = {"sql": sql, "params": self._normalise_params(params)}
        resp = None
        for attempt in range(2):
            try:
                resp = self._session.post(
                    f"{self.base_url}{endpoint}", json=payload, timeout=(5, self.timeout)
                )
                break
            except (_requests.Timeout, _requests.ConnectionError) as exc:
                # RetryError means the HTTPAdapter already exhausted its retries —
                # don't loop again on top of that.
                if isinstance(exc, _requests.exceptions.RetryError) or attempt >= 1:
                    raise
                wait_s = 0.8
                self.logger.warning("Transient network error, retrying in %.1fs: %s", wait_s, exc)
                time.sleep(wait_s)
        if resp is not None and resp.status_code == 401:
            self.logger.warning("Token expired, refreshing...")
            if not self.connect():
                raise RuntimeError("API authentication failed during token refresh")
            resp = self._session.post(
                f"{self.base_url}{endpoint}", json=payload, timeout=(5, self.timeout)
            )
        if resp is None:
            raise RuntimeError("No response from API server")
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
            if resp.status_code >= 500:
                raise RuntimeError(f"API server error ({resp.status_code})")
            data = resp.json()
            if data.get("error"):
                raise RuntimeError(data["error"])
            return data.get("result")
        except ValueError:
            raise RuntimeError(f"Unexpected API response (HTTP {resp.status_code})")
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
            if resp.status_code >= 500:
                return None, RuntimeError(f"API server error ({resp.status_code})")
            data = resp.json()
            exec_error = data.get("exec_error")
            error_code = data.get("error_code")
            if exec_error:
                err = RuntimeError(exec_error)
                if error_code is not None:
                    err.args = (error_code, exec_error)
                return None, err
            return data.get("result"), None
        except ValueError:
            return None, RuntimeError(f"Unexpected API response (HTTP {resp.status_code})")
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
                timeout=(5, self.timeout),
            )
            if resp.status_code == 401:
                self.logger.warning("Token expired, refreshing...")
                if not self.connect():
                    return [{"result": None, "error": "API authentication failed", "cached": False} for _ in queries]
                resp = self._session.post(
                    f"{self.base_url}/api/batch",
                    json={"queries": payload_queries},
                    timeout=(5, self.timeout),
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
