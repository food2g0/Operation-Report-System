"""
Shared HTTP client kernel for the ORS API layer.

Both Client/api_db_manager.py (branch machines) and
tools/api_utilities/api_db_manager.py (server-side admin tools) subclass
_APIClientBase.  All wire-protocol logic lives here; each subclass only
overrides the parts that differ for its deployment context.
"""
from __future__ import annotations

import logging
import time
from typing import Any

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


def _build_session(
    pool_connections: int = 4,
    pool_maxsize: int = 10,
    verify_ssl: bool = True,
) -> requests.Session:
    """Return a requests.Session with the standard ORS retry configuration."""
    retry = Retry(
        total=1,
        connect=1,
        read=1,
        backoff_factor=0.3,
        # 503 = server busy — retrying makes overload worse.
        # 500 = often non-transient, skip retry.
        # 502/504 = gateway timeouts, reliably transient.
        status_forcelist=[429, 502, 504],
        allowed_methods=["GET", "POST"],
    )
    adapter = HTTPAdapter(
        max_retries=retry,
        pool_connections=pool_connections,
        pool_maxsize=pool_maxsize,
    )
    session = requests.Session()
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    session.verify = verify_ssl
    if not verify_ssl:
        import urllib3
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    session.headers.update({"Content-Type": "application/json"})
    return session


class _APIClientBase:
    """
    Drop-in replacement for DatabaseManagerPooled that routes queries through
    the ORS REST API instead of connecting to MySQL directly.

    Subclasses must call super().__init__() and may override:
      - _ensure_token()  to add proactive TTL-based refresh
      - __init__()       to adjust session options (e.g. SSL verify)
    """

    def __init__(
        self,
        base_url: str,
        api_key: str,
        timeout: int = 30,
        verify_ssl: bool = True,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.api_key  = api_key
        self.timeout  = timeout
        self.logger   = logging.getLogger(type(self).__name__)

        self._token   = None
        self._session = _build_session(verify_ssl=verify_ssl)

    def __del__(self) -> None:
        try:
            if self._session:
                self._session.close()
        except Exception:
            pass

    def close(self) -> None:
        try:
            if self._session:
                self._session.close()
                self._session = None
        except Exception:
            pass

    # ── Authentication ────────────────────────────────────────────────────────

    def connect(self) -> bool:
        """Obtain a JWT token from /api/token."""
        try:
            resp = self._session.post(
                f"{self.base_url}/api/token",
                json={"api_key": self.api_key},
                timeout=(5, self.timeout),
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
                f"{self.base_url}/api/health", timeout=(3, self.timeout)
            )
            return resp.status_code == 200 and resp.json().get("status") == "ok"
        except Exception:
            return False

    def reset_connection(self) -> None:
        """Force token refresh on the next query (use after connection errors)."""
        self._token = None

    def _ensure_token(self) -> None:
        """Guarantee a live token is set; override for proactive TTL refresh."""
        if not self._token:
            self.connect()

    # ── Internal helpers ──────────────────────────────────────────────────────

    @staticmethod
    def _normalise_params(params) -> list:
        if params is None:
            return []
        return list(params)

    def _post_exec(self, endpoint: str, sql: str, params: Any) -> requests.Response:
        """POST to /api/exec or /api/exec_safe; retries once on transient errors
        and refreshes the token automatically on 401."""
        payload = {"sql": sql, "params": self._normalise_params(params)}
        resp = None
        for attempt in range(2):
            try:
                resp = self._session.post(
                    f"{self.base_url}{endpoint}",
                    json=payload,
                    timeout=(5, self.timeout),
                )
                break
            except (requests.Timeout, requests.ConnectionError) as exc:
                # RetryError = adapter already exhausted its retries — don't loop.
                if isinstance(exc, requests.exceptions.RetryError) or attempt >= 1:
                    raise
                wait_s = 0.8
                self.logger.warning(
                    "Transient network error, retrying in %.1fs: %s", wait_s, exc
                )
                time.sleep(wait_s)

        if resp is not None and resp.status_code == 401:
            self.logger.warning("Token expired, refreshing…")
            if not self.connect():
                raise RuntimeError("API authentication failed during token refresh")
            resp = self._session.post(
                f"{self.base_url}{endpoint}",
                json=payload,
                timeout=(5, self.timeout),
            )

        if resp is None:
            raise RuntimeError("No response from API server")
        return resp

    # ── Public query interface (mirrors DatabaseManagerPooled) ────────────────

    def execute_query(self, sql: str, params=None) -> Any:
        """Return rows (list[dict]) for SELECT, row-count (int) for DML.
        Raises RuntimeError on server-side SQL errors."""
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
        except requests.RequestException as exc:
            self.logger.error("execute_query network error: %s", exc)
            raise

    def execute_query_with_exception(self, sql: str, params=None):
        """Return (result, None) on success or (None, exception) on error.
        Never raises.  Preserves MySQL error codes in exception.args[0]."""
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
        except requests.RequestException as exc:
            self.logger.error("execute_query_with_exception network error: %s", exc)
            return None, exc

    def execute_batch(self, queries: list) -> list:
        """Execute multiple SQL statements in one HTTP round-trip.

        Each item in `queries` is a dict with keys:
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
        _error_row = lambda exc: {"result": None, "error": str(exc), "cached": False}
        try:
            resp = self._session.post(
                f"{self.base_url}/api/batch",
                json={"queries": payload_queries},
                timeout=(5, self.timeout),
            )
            if resp.status_code == 401:
                self.logger.warning("Token expired, refreshing…")
                if not self.connect():
                    return [_error_row("API authentication failed")] * len(queries)
                resp = self._session.post(
                    f"{self.base_url}/api/batch",
                    json={"queries": payload_queries},
                    timeout=(5, self.timeout),
                )
            return resp.json().get("results", [])
        except requests.RequestException as exc:
            self.logger.error("execute_batch network error: %s", exc)
            return [_error_row(exc) for _ in queries]
