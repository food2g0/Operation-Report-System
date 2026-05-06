
import os
import time
import threading
import logging
from sqlalchemy import create_engine, text, pool
from sqlalchemy.engine import Engine
from config import DB_CONFIG
from functools import lru_cache
from typing import List, Dict, Any, Optional, Tuple


class DatabaseManagerPooled:

    def __init__(self, idle_timeout=60, lazy_connect=True):

        self.engine: Optional[Engine] = None
        self.idle_timeout = idle_timeout
        self.last_used = time.time()
        self.lock = threading.Lock()
        self._is_disconnected_for_idle = False
        self._idle_monitor_started = False
        
        self.setup_logging()
        
        if not lazy_connect:
            self.connect()
            self.start_idle_monitor()

    def setup_logging(self):
        self.logger = logging.getLogger("DatabaseManagerPooled")

    def connect(self):

        try:
            connection_string = (
                f"mysql+pymysql://{DB_CONFIG['user']}:{DB_CONFIG['password']}"
                f"@{DB_CONFIG['host']}:{DB_CONFIG['port']}"
                f"/{DB_CONFIG['database']}?charset=utf8mb4"
            )

            self.engine = create_engine(
                connection_string,
                poolclass=pool.QueuePool,
                pool_size=int(os.environ.get("ORS_POOL_SIZE",    "50")),   # 50 persistent connections
                max_overflow=int(os.environ.get("ORS_POOL_OVERFLOW", "150")),  # +150 burst connections (200 total)
                pool_timeout=int(os.environ.get("ORS_POOL_TIMEOUT",  "30")),  # wait up to 30s for a slot
                pool_recycle=1800,
                pool_pre_ping=True,
                echo=False,
                connect_args={
                    'connect_timeout': 5,
                    'read_timeout': 30,
                    'write_timeout': 30,
                }
            )
            

            with self.engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            
            self.last_used = time.time()
            self._is_disconnected_for_idle = False
            self.logger.info("MySQL connection pool created successfully")
            return True

        except ImportError as e:
            self.engine = None
            self.logger.error(f"Missing database driver: {e}")
            return False
        except Exception as e:
            self.engine = None
            error_msg = str(e).lower()
            

            if "can't connect" in error_msg or "connection refused" in error_msg:
                self.logger.error(f"Cannot connect to database server. Check internet connection or server status: {e}")
            elif "access denied" in error_msg or "authentication" in error_msg:
                self.logger.error(f"Database authentication failed. Check username/password in .env file: {e}")
            elif "unknown database" in error_msg:
                self.logger.error(f"Database does not exist. Check database name in .env file: {e}")
            elif "timeout" in error_msg or "timed out" in error_msg:
                self.logger.error(f"Connection timeout. Check internet connection and firewall settings: {e}")
            elif "name resolution" in error_msg or "getaddrinfo failed" in error_msg:
                self.logger.error(f"Cannot resolve database hostname. Check internet connection: {e}")
            else:
                self.logger.error(f"MySQL connection pool failed: {e}")
            
            return False

    def get_user_friendly_error(self, exception: Exception) -> str:

        error_msg = str(exception).lower()
        
        if "can't connect" in error_msg or "connection refused" in error_msg:
            return "Cannot connect to database server. Please check your internet connection."
        elif "access denied" in error_msg or "authentication" in error_msg:
            return "Database login failed. Please contact your system administrator."
        elif "unknown database" in error_msg:
            return "Database configuration error. Please contact your system administrator."
        elif "timeout" in error_msg or "timed out" in error_msg:
            return "Connection timeout. Please check your internet connection and try again."
        elif "name resolution" in error_msg or "getaddrinfo failed" in error_msg:
            return "Cannot reach database server. Please check your internet connection."
        elif "lost connection" in error_msg or "server has gone away" in error_msg:
            return "Lost connection to database. Please check your internet connection and try again."
        elif "too many connections" in error_msg:
            return "Database server is busy. Please try again in a moment."
        else:
            return f"Database error occurred. Please try again or contact support."


    def start_idle_monitor(self):

        if self._idle_monitor_started:
            return
        self._idle_monitor_started = True
        
        def monitor():
            while True:
                time.sleep(30) 
                if self.idle_timeout <= 0:
                    continue  # idle disconnect disabled
                with self.lock:
                    if (
                        self.engine
                        and time.time() - self.last_used > self.idle_timeout
                    ):
                        try:
                            self.logger.info(f"Idle timeout ({self.idle_timeout}s) reached — disconnecting from database")
                            self.engine.dispose()
                            self.engine = None
                            self._is_disconnected_for_idle = True
                        except Exception as e:
                            self.logger.error(f"Error during idle disconnect: {e}")

        thread = threading.Thread(target=monitor, daemon=True, name="IdleMonitor")
        thread.start()
        self.logger.info(f"Idle monitor started (timeout: {self.idle_timeout}s)")

    def reconnect_if_needed(self) -> bool:

        if not self.engine:
            if self._is_disconnected_for_idle:
                self.logger.info("Reconnecting after idle disconnect...")
            result = self.connect()
            if result:
                self.start_idle_monitor() 
            return result
        
        try:
            with self.engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            return True
        except Exception:
            self.logger.warning("Connection lost — reconnecting...")
            result = self.connect()
            if result:
                self.start_idle_monitor()
            return result

    def _prepare_params(self, query: str, params):
        """Convert %s-style params to SQLAlchemy :paramN style."""
        if params and isinstance(params, (tuple, list)):
            modified_query = query
            param_dict = {}
            for i, param_value in enumerate(params):
                param_name = f"param{i}"
                modified_query = modified_query.replace("%s", f":{param_name}", 1)
                param_dict[param_name] = param_value
            return modified_query, param_dict
        return query, params or {}

    def execute_query(self, query: str, params: Optional[tuple] = None) -> Optional[Any]:

        with self.lock:

            if not self.reconnect_if_needed():
                self.logger.error("Failed to connect to database")
                return None

            self.last_used = time.time() 

        try:
            prepared_query, param_dict = self._prepare_params(query, params)
            with self.engine.connect() as conn:
                result = conn.execute(text(prepared_query), param_dict)
                
                if query.strip().upper().startswith("SELECT"):
                    return [dict(row._mapping) for row in result]
                else:
                    conn.commit()
                    return result.rowcount

        except Exception as e:
            error_msg = str(e).lower()
            
  
            if any(keyword in error_msg for keyword in ["can't connect", "connection refused", "timeout", "timed out", "lost connection", "name resolution"]):
                self.logger.error(f"Network/Connection error: {e}")
            else:
                self.logger.error(f"Query failed: {e}\nQuery: {query}\nParams: {params}")
            
            return None

    def execute_query_with_exception(self, query: str, params: Optional[tuple] = None) -> Tuple[Optional[Any], Optional[Exception]]:

        with self.lock:

            if not self.reconnect_if_needed():
                return None, Exception("Failed to connect to database")

            self.last_used = time.time()  

        try:
            prepared_query, param_dict = self._prepare_params(query, params)
            with self.engine.connect() as conn:
                result = conn.execute(text(prepared_query), param_dict)
                
                if query.strip().upper().startswith("SELECT"):
                    data = [dict(row._mapping) for row in result]
                    return data, None
                else:
                    conn.commit()
                    return result.rowcount, None

        except Exception as e:
            self.logger.error(f"Query failed: {e}")
            return None, e

    @lru_cache(maxsize=128)
    def execute_cached_query(self, query: str, params_tuple: Optional[tuple] = None) -> Optional[List[Dict[str, Any]]]:
  
        if not query.strip().upper().startswith("SELECT"):
            self.logger.warning("Cached queries only support SELECT statements")
            return self.execute_query(query, params_tuple)
        
        return self.execute_query(query, params_tuple)

    def clear_cache(self):
        """Clear the query cache"""
        self.execute_cached_query.cache_clear()
        self.logger.info("Query cache cleared")

    def execute_many(self, query: str, params_list: List[tuple], chunk_size: int = 100) -> Optional[int]:

        if not params_list:
            return 0
            
        with self.lock:
            if not self.reconnect_if_needed():
                self.logger.error("Failed to connect to database")
                return None
            self.last_used = time.time()

        try:
            modified_query, _ = self._prepare_params(query, tuple(range(query.count("%s"))))

            param_dicts = []
            for params in params_list:
                param_dict = {f"param{i}": val for i, val in enumerate(params)}
                param_dicts.append(param_dict)
            
            total_rows = 0
            with self.engine.connect() as conn:
                for i in range(0, len(param_dicts), chunk_size):
                    chunk = param_dicts[i:i + chunk_size]
                    for param_dict in chunk:
                        result = conn.execute(text(modified_query), param_dict)
                        total_rows += result.rowcount
                    conn.commit()
            
            return total_rows

        except Exception as e:
            self.logger.error(f"Batch query failed: {e}\nQuery: {query}")
            return None

    def test_connection(self) -> bool:

        with self.lock:
            if not self.reconnect_if_needed():
                return False
            self.last_used = time.time()
        
        try:
            with self.engine.connect() as conn:
                result = conn.execute(text("SELECT 1 AS test"))
                row = result.fetchone()
                return row and row[0] == 1
        except Exception as e:
            self.logger.error(f"Connection test failed: {e}")
            return False

    def get_connection_status(self) -> dict:

        idle_seconds = time.time() - self.last_used
        return {
            'connected': self.engine is not None,
            'idle_seconds': round(idle_seconds, 1),
            'idle_timeout': self.idle_timeout,
            'will_disconnect_in': max(0, round(self.idle_timeout - idle_seconds, 1)) if self.engine else 0
        }

    def shutdown(self):

        if self.engine:
            try:
                self.engine.dispose()
                self.logger.info("Connection pool disposed")
            except Exception as e:
                self.logger.error(f"Error disposing engine: {e}")
            finally:
                self.engine = None

db_manager = DatabaseManagerPooled()


# ── Remote (API-mode) database manager ───────────────────────────────────────
# When API_MODE is enabled in config, db_manager is replaced with this class.
# It has the EXACT same interface as DatabaseManagerPooled so no other code
# in the project needs to change at all.

class RemoteDatabaseManager:
    """
    Drop-in replacement for DatabaseManagerPooled that routes all queries
    through the ORS API server (api_server.py) instead of connecting to
    MySQL directly.

    Usage: set API_MODE=True in your api_config.py (see below).
    The app automatically uses this class instead of DatabaseManagerPooled.
    """

    def __init__(self, api_url: str, api_key: str):
        import logging
        import requests as _req

        self._api_url = api_url.rstrip("/")
        self._api_key = api_key
        self._token   = None
        self._session = _req.Session()
        self._session.headers.update({"Content-Type": "application/json"})
        self.logger   = logging.getLogger("RemoteDatabaseManager")

    # ── Token management ──────────────────────────────────────────────────

    def _refresh_token(self):
        import requests as _req
        try:
            resp = self._session.post(
                f"{self._api_url}/api/token",
                json={"api_key": self._api_key},
                timeout=10,
            )
            if resp.status_code == 200:
                self._token = resp.json()["token"]
                self._session.headers["Authorization"] = f"Bearer {self._token}"
                return True
            self.logger.error(f"Token refresh failed: {resp.status_code} {resp.text}")
            return False
        except Exception as e:
            self.logger.error(f"Token refresh error: {e}")
            return False

    def _ensure_token(self) -> bool:
        if self._token:
            return True
        return self._refresh_token()

    def _call(self, endpoint: str, sql: str, params=None):
        """POST to endpoint, auto-refresh token on 401."""
        if not self._ensure_token():
            return None, Exception("Could not obtain API token")

        payload = {"sql": sql}
        if params is not None:
            payload["params"] = list(params)

        for attempt in range(2):
            try:
                resp = self._session.post(
                    f"{self._api_url}{endpoint}",
                    json=payload,
                    timeout=30,
                )
                if resp.status_code == 401 and attempt == 0:
                    # Token expired — refresh and retry once
                    self._token = None
                    self._refresh_token()
                    continue
                return resp, None
            except Exception as e:
                return None, e

        return None, Exception("API call failed after retry")

    # ── Public interface (mirrors DatabaseManagerPooled) ──────────────────

    def _json_or_error(self, resp):
        """Safely decode JSON; raises ValueError with status info on failure."""
        import time as _time
        if resp.status_code == 429:
            # Rate-limited — wait and signal caller to retry
            raise _RateLimitError(resp)
        try:
            return resp.json(), None
        except Exception as e:
            return None, Exception(
                f"Non-JSON response (HTTP {resp.status_code}): {resp.text[:200]}"
            )

    def execute_query(self, query: str, params=None):
        import time as _time
        for attempt in range(3):
            resp, err = self._call("/api/exec", query, params)
            if err:
                self.logger.error(f"execute_query error: {err}")
                return None
            try:
                data, decode_err = self._json_or_error(resp)
            except _RateLimitError:
                wait = 2 * (attempt + 1)
                self.logger.warning(f"Rate limited (429) — retrying in {wait}s")
                _time.sleep(wait)
                continue
            if decode_err:
                self.logger.error(str(decode_err))
                return None
            if data.get("error"):
                self.logger.error(f"Server error: {data['error']}")
                return None
            return data.get("result")
        self.logger.error("execute_query: still rate-limited after 3 attempts")
        return None

    def execute_query_with_exception(self, query: str, params=None):
        import time as _time
        for attempt in range(3):
            resp, err = self._call("/api/exec_safe", query, params)
            if err:
                return None, err
            try:
                data, decode_err = self._json_or_error(resp)
            except _RateLimitError:
                wait = 2 * (attempt + 1)
                self.logger.warning(f"Rate limited (429) — retrying in {wait}s")
                _time.sleep(wait)
                continue
            if decode_err:
                return None, decode_err
            if data.get("exec_error"):
                # Reconstruct a minimal exception with error code for deadlock detection
                exc = Exception(data["exec_error"])
                code = data.get("error_code")
                if code is not None:
                    exc.args = (code, data["exec_error"])
                return None, exc
        return data.get("result"), None

    def test_connection(self) -> bool:
        try:
            import requests as _req
            resp = _req.get(f"{self._api_url}/api/health", timeout=5)
            return resp.status_code == 200 and resp.json().get("db") is True
        except Exception:
            return False

    def execute_cached_query(self, query: str, params_tuple=None):
        return self.execute_query(query, params_tuple)

    def clear_cache(self):
        pass  # no local cache in remote mode

    def execute_many(self, query: str, params_list, chunk_size: int = 100):
        # Send in chunks to avoid oversized payloads
        total = 0
        for i in range(0, len(params_list), chunk_size):
            chunk = params_list[i:i + chunk_size]
            for p in chunk:
                result = self.execute_query(query, p)
                if isinstance(result, int):
                    total += result
        return total

    def get_connection_status(self) -> dict:
        connected = self.test_connection()
        return {"connected": connected, "mode": "remote_api", "api_url": self._api_url}

    def shutdown(self):
        self._session.close()


class _RateLimitError(Exception):
    """Raised internally when the server returns HTTP 429."""
    def __init__(self, resp):
        self.resp = resp
        super().__init__("HTTP 429 rate limited")


# ── Auto-select local vs remote db_manager ───────────────────────────────────
# Create api_config.py in the project root to enable API mode:
#
#   API_MODE    = True
#   API_URL     = "http://192.168.1.100:5000"   # your server's IP
#   API_KEY     = "ORS-API-KEY-CHANGE-ME-12345" # must match api_server.py
#
# When API_MODE = False (or api_config.py is missing), the app connects to
# MySQL directly as before — no behaviour change.

try:
    import api_config as _api_cfg
    if getattr(_api_cfg, "API_MODE", False):
        db_manager = RemoteDatabaseManager(
            api_url=_api_cfg.API_URL,
            api_key=_api_cfg.API_KEY,
        )
        import logging as _log
        _log.getLogger("RemoteDatabaseManager").info(
            f"API mode enabled — connecting via {_api_cfg.API_URL}"
        )
except ImportError:
    pass  # no api_config.py — stay in direct-DB mode (default)
