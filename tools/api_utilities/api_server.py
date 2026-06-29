
import os
import json
import time
import uuid
import queue
import hashlib
import datetime
import collections
import threading
from concurrent.futures import ThreadPoolExecutor
from typing import Any, List, Optional, Tuple

# Load .env file if present (must happen before any os.environ.get calls)
try:
    from dotenv import load_dotenv as _load_dotenv
    _load_dotenv(override=False)   # env vars already set in the OS take priority
except ImportError:
    pass  # python-dotenv not installed — env vars must be set manually

# Setup centralized logging FIRST
from tools.logging_config import setup_logging, get_logger
setup_logging("api_server", os.environ.get("ORS_LOG_LEVEL", "INFO"))

from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from pydantic import BaseModel
from starlette.middleware.base import BaseHTTPMiddleware
import jwt as pyjwt
try:
    from socketio import AsyncServer, ASGIApp
    SOCKETIO_AVAILABLE = True
except ImportError:
    SOCKETIO_AVAILABLE = False
    log = None
    AsyncServer = None
    ASGIApp = None

# Check if running with Gunicorn (WSGI) or uvicorn (ASGI)
import sys
_RUNNING_WITH_GUNICORN = "gunicorn" in sys.modules or any("gunicorn" in arg for arg in sys.argv)

from tools.db_connect_pooled import DatabaseManagerPooled
from tools.error_tracker import error_tracker, audit_logger, log_exception, log_audit
from notification_manager import notification_manager
import bcrypt


def _verify_password(password: str, hashed: str) -> bool:
    """bcrypt verify with legacy plaintext fallback."""
    if not password or not hashed:
        return False
    try:
        if hashed.startswith("$2b$") or hashed.startswith("$2a$"):
            return bcrypt.checkpw(password.encode("utf-8"), hashed.encode("utf-8"))
        return password == hashed  # legacy plaintext
    except Exception as exc:
        log.error("Password verification error: %s", exc)
        return False


API_KEY    = os.environ.get("ORS_API_KEY",    "")
SECRET_KEY = os.environ.get("ORS_SECRET_KEY", "")
API_HOST   = os.environ.get("ORS_API_HOST",   "0.0.0.0")
API_PORT   = int(os.environ.get("ORS_API_PORT", 5000))
JWT_HOURS  = int(os.environ.get("ORS_JWT_HOURS", 12))

if not SECRET_KEY:
    import sys as _sys
    print("FATAL: ORS_SECRET_KEY is not set. All JWT tokens would be signed with an empty key, "
          "allowing anyone to forge admin credentials. Set ORS_SECRET_KEY in your .env file.", flush=True)
    _sys.exit(1)
if not API_KEY:
    import sys as _sys
    print("FATAL: ORS_API_KEY is not set. The API is effectively open to anyone.", flush=True)
    _sys.exit(1)
CACHE_TTL   = int(os.environ.get("ORS_CACHE_TTL",  30))    # seconds; 0 = disabled
CACHE_MAX   = int(os.environ.get("ORS_CACHE_MAX",  2000))   # in-memory fallback max entries
REDIS_URL   = os.environ.get("ORS_REDIS_URL",  "redis://127.0.0.1:6379/0")

# ── Logging ───────────────────────────────────────────────────────────────────
log = get_logger("api_server")

# ── Shared DB pool ────────────────────────────────────────────────────────────
# One shared pool per Gunicorn worker — idle monitor disabled on the server.
_db = DatabaseManagerPooled(idle_timeout=0)
_db.connect()   # connect immediately on worker startup


_redis = None
_redis_ok = False

if CACHE_TTL > 0:
    try:
        import redis as _redis_lib
        _redis = _redis_lib.from_url(REDIS_URL, socket_connect_timeout=2, decode_responses=False)
        _redis.ping()
        _redis_ok = True
        log.info(f"Redis cache connected: {REDIS_URL}")
    except Exception as _re:
        log.warning(f"Redis unavailable ({_re}) — using in-memory fallback cache")

# In-memory fallback
_cache_lock   = threading.Lock()
_cache: dict  = {}          # key -> (expires_at, result)
_cache_hits   = 0
_cache_misses = 0


def _is_select(sql: str) -> bool:
    return sql.strip().upper().startswith("SELECT")


def _extract_table_name(sql: str) -> Optional[str]:
    """Extract table name from SQL query (basic extraction)."""
    sql_upper = sql.strip().upper()
    try:
        if "INSERT INTO" in sql_upper:
            start = sql_upper.find("INSERT INTO") + len("INSERT INTO")
            table = sql[start:].strip().split()[0].split("(")[0].strip("`\"")
            return table
        elif "UPDATE" in sql_upper:
            start = sql_upper.find("UPDATE") + len("UPDATE")
            table = sql[start:].strip().split()[0].strip("`\"")
            return table
        elif "DELETE FROM" in sql_upper:
            start = sql_upper.find("DELETE FROM") + len("DELETE FROM")
            table = sql[start:].strip().split()[0].strip("`\"")
            return table
        elif "SELECT" in sql_upper:
            start = sql_upper.find("FROM") + len("FROM")
            table = sql[start:].strip().split()[0].strip("`\"")
            return table
    except Exception:
        pass
    return "unknown"


# ── Row-Level Security ────────────────────────────────────────────────────────
# Tables that contain per-branch data. Non-admin clients can only access rows
# where the branch column matches the branch claim in their JWT token.
_BRANCH_SCOPED_TABLES = frozenset({
    "daily_reports", "daily_reports_brand_a",
    "payable_tbl", "payable_tbl_brand_a",
    "global_other_services_tbl", "other_services_tbl_brand_a",
    "cash_float_tbl", "pending_notifications",
})

_ADMIN_ROLES = frozenset({"admin", "super_admin"})


def _enforce_rls(payload: dict, sql: str, params) -> None:
    """Raise HTTP 403 if a non-admin client queries another branch's data.

    Skipped for:
      - api_key tokens (machine/service auth — no branch claim)
      - admin / super_admin roles
      - tables that are not branch-scoped
    """
    if payload.get("type") == "api_key":
        return
    if payload.get("role", "") in _ADMIN_ROLES:
        return

    token_branch = payload.get("branch", "")
    if not token_branch:
        return  # token has no branch claim — cannot enforce

    table = (_extract_table_name(sql) or "").lower()

    # Fail closed: if table name cannot be parsed but SQL mentions a scoped table
    # keyword, block the request rather than letting it through.
    if table == "unknown" or not table:
        sql_upper = sql.upper()
        if any(t.upper() in sql_upper for t in _BRANCH_SCOPED_TABLES):
            log.warning("RLS: unparseable SQL mentions a scoped table — blocked. role=%s sql=%.80s",
                        payload.get("role"), sql)
            raise HTTPException(status_code=403, detail="Access denied: query could not be validated.")
        return

    if table not in _BRANCH_SCOPED_TABLES:
        return  # not a branch-scoped table

    params_list = list(params) if params else []
    # Require both: token branch in params AND the SQL contains a branch filter.
    # This prevents embedding the branch as a non-filter param to satisfy the check.
    sql_upper = sql.upper()
    branch_in_sql = "BRANCH" in sql_upper
    if not branch_in_sql or token_branch not in params_list:
        log.warning(
            "RLS violation blocked: role=%s branch=%s table=%s branch_in_sql=%s params=%s",
            payload.get("role"), token_branch, table, branch_in_sql, params_list[:6],
        )
        raise HTTPException(
            status_code=403,
            detail="Access denied: you can only access your own branch data.",
        )


def _make_cache_key(sql: str, params) -> str:
    raw = f"{sql}|{params}"
    return "ors:" + hashlib.sha256(raw.encode()).hexdigest()


def _cache_get(key: str) -> Tuple[bool, Any]:
    global _cache_hits, _cache_misses
    # ── Redis path ────────────────────────────────────────────────────────────
    if _redis_ok and _redis is not None:
        try:
            raw = _redis.get(key)
            if raw is not None:
                _cache_hits += 1
                return True, json.loads(raw)
            _cache_misses += 1
            return False, None
        except Exception:
            pass  # Redis error — fall through to in-memory
    # ── In-memory fallback ───────────────────────────────────────────────────
    with _cache_lock:
        entry = _cache.get(key)
        if entry and entry[0] > time.monotonic():
            _cache_hits += 1
            return True, entry[1]
        if entry:
            del _cache[key]
        _cache_misses += 1
        return False, None


def _cache_set(key: str, result: Any, ttl: int = None) -> None:
    effective_ttl = ttl if ttl is not None else CACHE_TTL
    if effective_ttl <= 0:
        return
    # ── Redis path ────────────────────────────────────────────────────────────
    if _redis_ok and _redis is not None:
        try:
            _redis.setex(key, effective_ttl, json.dumps(result, default=str))
            return
        except Exception:
            pass  # Redis error — fall through to in-memory
    # ── In-memory fallback ───────────────────────────────────────────────────
    with _cache_lock:
        if len(_cache) >= CACHE_MAX:
            now = time.monotonic()
            expired = [k for k, (exp, _) in _cache.items() if exp <= now]
            for k in expired:
                del _cache[k]
        _cache[key] = (time.monotonic() + effective_ttl, result)


def _cache_clear_all() -> None:
    """Clear all cached query results to ensure fresh reads after writes."""
    global _cache
    if _redis_ok and _redis is not None:
        try:
            # SCAN is non-blocking; KEYS blocks the Redis event loop for O(N) time
            cursor = 0
            while True:
                cursor, keys = _redis.scan(cursor, match="ors:*", count=200)
                if keys:
                    _redis.delete(*keys)
                if cursor == 0:
                    break
        except Exception:
            pass
    with _cache_lock:
        _cache.clear()



_task_queue:   queue.Queue = queue.Queue(maxsize=500)
_task_results: dict        = {}   # task_id -> {status, result, error, finished_at}
_task_lock                 = threading.Lock()
_task_executor             = ThreadPoolExecutor(max_workers=2, thread_name_prefix="ors-bg")


class BackgroundTask:
    """Wrapper for a SQL statement to run in the background."""
    def __init__(self, task_id: str, sql: str, params: tuple):
        self.task_id = task_id
        self.sql     = sql
        self.params  = params


def _run_background_task(task: BackgroundTask) -> None:
    try:
        result = _db.execute_query(task.sql, task.params)
        # Clear cache after writes to ensure fresh reads
        if not _is_select(task.sql):
            _cache_clear_all()
        with _task_lock:
            _task_results[task.task_id] = {
                "status":      "done",
                "result":      result,
                "error":       None,
                "finished_at": datetime.datetime.utcnow().isoformat(),
            }
        log.debug(f"Background task {task.task_id} completed")
    except Exception as e:
        log.error(f"Background task {task.task_id} failed: {e}")
        with _task_lock:
            _task_results[task.task_id] = {
                "status":      "error",
                "result":      None,
                "error":       str(e),
                "finished_at": datetime.datetime.utcnow().isoformat(),
            }


def _queue_worker() -> None:
    """Drain the task queue and submit jobs to the thread pool."""
    while True:
        task = _task_queue.get()
        if task is None:
            break
        _task_executor.submit(_run_background_task, task)


_queue_thread = threading.Thread(target=_queue_worker, daemon=True, name="ors-queue")
_queue_thread.start()



_stats_lock   = threading.Lock()
_counters     = collections.defaultdict(int)   # endpoint -> hit count
_errors       = collections.defaultdict(int)   # endpoint -> error count
_recent       = collections.deque(maxlen=200)  # last 200 requests
_server_start = datetime.datetime.utcnow()

# ── Known valid API paths (bots probing anything else get strike-counted) ─────
_KNOWN_PATHS = frozenset({
    "/api/token", "/api/exec", "/api/exec_safe", "/api/batch",
    "/api/health", "/api/stats", "/api/config", "/api/cache/clear",
    "/api/enqueue", "/api/task",
    "/api/notify/pending", "/api/notify/reset_entry", "/api/notify/stats", "/api/notify/capabilities",
    "/api/machine/status", "/api/machine/list", "/api/machine/register",
    "/docs", "/openapi.json", "/redoc",
})

# ── Permanent IP blocklist ────────────────────────────────────────────────────
# Add IPs or CIDR prefixes to block unconditionally.
# Set ORS_IP_BLOCKLIST env var as comma-separated IPs to override at runtime.
_IP_BLOCKLIST: set = set(filter(None, os.environ.get("ORS_IP_BLOCKLIST", "").split(",")))

# Known scanner/bot IPs discovered from access logs
_IP_BLOCKLIST.update({
    "139.162.3.141",
    "172.93.106.153",
    "104.243.35.92",
    "83.168.89.181",
    "185.2.103.100",
    "168.100.9.75",
    "89.185.81.112",
    "89.169.47.115",
    "80.241.223.232",
    "69.5.169.112",
    "66.94.124.248",
    "51.102.248.238",
    "45.143.21.60",
    "2.26.109.12",
    "223.15.246.7",
    "207.180.222.68",
    "185.241.32.124",
})

_ip_blocklist_lock = threading.Lock()


def _is_ip_blocked(ip: str) -> bool:
    with _ip_blocklist_lock:
        return ip in _IP_BLOCKLIST


# ── Token endpoint rate limiter ───────────────────────────────────────────────
# Allows ORS_TOKEN_LIMIT attempts per ORS_TOKEN_WINDOW seconds per IP.
# After exceeding the limit the IP is locked out for ORS_TOKEN_LOCKOUT seconds.
_TOKEN_WINDOW   = int(os.environ.get("ORS_TOKEN_WINDOW",   "60"))   # sliding window (s)
_TOKEN_LIMIT    = int(os.environ.get("ORS_TOKEN_LIMIT",    "5"))    # max attempts
_TOKEN_LOCKOUT  = int(os.environ.get("ORS_TOKEN_LOCKOUT",  "900"))  # lockout duration (s) = 15 min

_token_rl_lock    = threading.Lock()
_token_attempts: dict = {}   # ip -> deque of attempt timestamps
_token_locked:   dict = {}   # ip -> lockout_expires_at (monotonic)


def _token_rate_check(ip: str) -> None:
    """Raise HTTP 429 if ip is rate-limited or locked out on /api/token."""
    if _bot_is_whitelisted(ip):
        return
    now = time.monotonic()
    with _token_rl_lock:
        # Check existing lockout
        locked_until = _token_locked.get(ip)
        if locked_until:
            if now < locked_until:
                retry_in = int(locked_until - now)
                log.warning(f"[token-rl] Locked-out IP {ip} retried /api/token (retry_after={retry_in}s)")
                raise HTTPException(
                    status_code=429,
                    detail=f"Too many failed attempts. Try again in {retry_in}s.",
                    headers={"Retry-After": str(retry_in)},
                )
            else:
                del _token_locked[ip]

        # Sliding window of attempt timestamps
        attempts = _token_attempts.setdefault(ip, collections.deque())
        attempts.append(now)
        while attempts and attempts[0] < now - _TOKEN_WINDOW:
            attempts.popleft()

        if len(attempts) > _TOKEN_LIMIT:
            _token_locked[ip] = now + _TOKEN_LOCKOUT
            del _token_attempts[ip]
            log.warning(
                f"[token-rl] Locked out {ip} for {_TOKEN_LOCKOUT}s "
                f"after {_TOKEN_LIMIT} attempts in {_TOKEN_WINDOW}s"
            )
            raise HTTPException(
                status_code=429,
                detail=f"Too many attempts. Locked out for {_TOKEN_LOCKOUT}s.",
                headers={"Retry-After": str(_TOKEN_LOCKOUT)},
            )


def _token_rate_clear(ip: str) -> None:
    """Clear attempt history for ip after a successful token request."""
    with _token_rl_lock:
        _token_attempts.pop(ip, None)
        _token_locked.pop(ip, None)


# ── Exec endpoint rate limiter ────────────────────────────────────────────────
# Limits how many /api/exec|exec_safe|batch calls a single IP can make per
# minute, preventing a stolen token from being used to dump the database.
# Whitelisted IPs (loopback, LAN) are never throttled.
_EXEC_WINDOW  = int(os.environ.get("ORS_EXEC_WINDOW",  "60"))    # sliding window (s)
_EXEC_LIMIT   = int(os.environ.get("ORS_EXEC_LIMIT",   "1000"))  # max requests per window (raised for 400+ clients)
_EXEC_BAN_SECS= int(os.environ.get("ORS_EXEC_BAN",     "120"))   # temporary ban duration (s)

_exec_rl_lock    = threading.Lock()
_exec_hits: dict = {}   # ip -> deque of hit timestamps
_exec_banned_until: dict = {}  # ip -> ban_expires_at (monotonic)


def _exec_rate_check(ip: str) -> None:
    """Raise HTTP 429 if ip exceeds the exec endpoint rate limit."""
    if _bot_is_whitelisted(ip):
        return
    now = time.monotonic()
    with _exec_rl_lock:
        # Check existing ban
        ban_exp = _exec_banned_until.get(ip)
        if ban_exp:
            if now < ban_exp:
                retry_in = int(ban_exp - now)
                raise HTTPException(
                    status_code=429,
                    detail=f"Rate limit exceeded. Try again in {retry_in}s.",
                    headers={"Retry-After": str(retry_in)},
                )
            else:
                del _exec_banned_until[ip]

        hits = _exec_hits.setdefault(ip, collections.deque())
        hits.append(now)
        while hits and hits[0] < now - _EXEC_WINDOW:
            hits.popleft()

        if len(hits) > _EXEC_LIMIT:
            _exec_banned_until[ip] = now + _EXEC_BAN_SECS
            del _exec_hits[ip]
            log.warning(
                f"[exec-rl] Banned {ip} for {_EXEC_BAN_SECS}s "
                f"after {_EXEC_LIMIT} exec calls in {_EXEC_WINDOW}s"
            )
            raise HTTPException(
                status_code=429,
                detail=f"Rate limit exceeded. Banned for {_EXEC_BAN_SECS}s.",
                headers={"Retry-After": str(_EXEC_BAN_SECS)},
            )


def _cleanup_stale_rate_limit_entries():
    """Remove stale rate-limit entries older than 1 hour (prevents memory leak)."""
    now = time.monotonic()
    cutoff = now - 3600  # 1 hour

    try:
        # Clean token rate-limit entries
        with _token_rl_lock:
            for ip in list(_token_attempts.keys()):
                hits = _token_attempts[ip]
                # Remove old entries from deque
                while hits and hits[0] < cutoff:
                    hits.popleft()
                # Remove empty deques
                if not hits:
                    del _token_attempts[ip]

        # Clean exec rate-limit entries
        with _exec_rl_lock:
            for ip in list(_exec_hits.keys()):
                hits = _exec_hits[ip]
                # Remove old entries from deque
                while hits and hits[0] < cutoff:
                    hits.popleft()
                # Remove empty deques and expired bans
                if not hits:
                    del _exec_hits[ip]
                    _exec_banned_until.pop(ip, None)

            # Also remove expired bans
            for ip in list(_exec_banned_until.keys()):
                if _exec_banned_until[ip] < now:
                    del _exec_banned_until[ip]
    except Exception as e:
        log.error(f"Error in cleanup_stale_rate_limit_entries: {e}")


def _cleanup_old_tasks():
    """Remove completed tasks older than 1 hour (prevents memory leak)."""
    now = time.monotonic()
    cutoff = now - 3600  # 1 hour

    try:
        with _task_lock:
            for task_id in list(_task_results.keys()):
                task_info = _task_results[task_id]
                finished_at = task_info.get('finished_at')
                if finished_at and finished_at < cutoff:
                    del _task_results[task_id]
    except Exception as e:
        log.error(f"Error in cleanup_old_tasks: {e}")


# ── Bot-blocker state ─────────────────────────────────────────────────────────
# IPs in this set are whitelisted and never blocked (loopback + internal nets).
_BOT_WHITELIST_PREFIXES = ("127.", "::1", "10.", "172.16.", "172.17.",
                            "172.18.", "172.19.", "172.20.", "172.21.",
                            "172.22.", "172.23.", "172.24.", "172.25.",
                            "172.26.", "172.27.", "172.28.", "172.29.",
                            "172.30.", "172.31.", "192.168.",
                            "222.127.90.")  # local network machines

_BOT_WINDOW_SECS  = int(os.environ.get("ORS_BOT_WINDOW",   "60"))   # sliding window
_BOT_PROBE_LIMIT  = int(os.environ.get("ORS_BOT_LIMIT",    "10"))   # unknown-path hits
_BOT_BAN_SECS     = int(os.environ.get("ORS_BOT_BAN_SECS", "600"))  # ban duration (10 min)

_bot_lock         = threading.Lock()
_bot_probes: dict = {}   # ip -> deque of timestamps (unknown-path hits)
_bot_banned: dict = {}   # ip -> ban_expires_at (monotonic)


def _bot_is_whitelisted(ip: str) -> bool:
    return any(ip.startswith(p) for p in _BOT_WHITELIST_PREFIXES)


def _bot_record_probe(ip: str) -> bool:
    """Record an unknown-path hit for ip. Returns True if ip should be banned."""
    if _bot_is_whitelisted(ip):
        return False
    now = time.monotonic()
    with _bot_lock:
        # Check existing ban
        ban_exp = _bot_banned.get(ip)
        if ban_exp and now < ban_exp:
            return True  # still banned

        # Sliding window of probe timestamps
        probes = _bot_probes.setdefault(ip, collections.deque())
        probes.append(now)
        # Evict entries outside the window
        while probes and probes[0] < now - _BOT_WINDOW_SECS:
            probes.popleft()

        if len(probes) >= _BOT_PROBE_LIMIT:
            _bot_banned[ip] = now + _BOT_BAN_SECS
            del _bot_probes[ip]
            log.warning(
                f"[bot-block] Banned {ip} for {_BOT_BAN_SECS}s "
                f"after {_BOT_PROBE_LIMIT} unknown-path probes in {_BOT_WINDOW_SECS}s"
            )
            return True
    return False


def _bot_is_banned(ip: str) -> bool:
    if _bot_is_whitelisted(ip):
        return False
    now = time.monotonic()
    with _bot_lock:
        ban_exp = _bot_banned.get(ip)
        if ban_exp is None:
            return False
        if now >= ban_exp:
            del _bot_banned[ip]
            return False
        return True


class _TrackingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        ip = request.client.host if request.client else "unknown"

        # ── Permanent IP blocklist ────────────────────────────────────────
        if _is_ip_blocked(ip):
            log.warning(f"[ip-block] Rejected blocked IP {ip} -> {request.url.path}")
            return JSONResponse(status_code=403, content={"detail": "Forbidden"})

        # ── Bot-blocker: reject banned IPs immediately ────────────────────
        if _bot_is_banned(ip):
            return JSONResponse(
                status_code=429,
                content={"detail": "Too many requests"},
                headers={"Retry-After": str(_BOT_BAN_SECS)},
            )

        # ── Request body size cap (1 MB) ─────────────────────────────────
        MAX_BODY = int(os.environ.get("ORS_MAX_BODY_BYTES", str(1 * 1024 * 1024)))
        content_length = request.headers.get("content-length")
        if content_length and int(content_length) > MAX_BODY:
            log.warning(f"[size-cap] Rejected oversized request ({content_length}B) from {ip}")
            return JSONResponse(
                status_code=413,
                content={"detail": "Request body too large (max 1 MB)"},
            )

        # ── Request ID — use Nginx-generated ID or create one as fallback ──
        req_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        request.state.request_id = req_id

        start    = datetime.datetime.utcnow()
        response = await call_next(request)
        ms       = int((datetime.datetime.utcnow() - start).total_seconds() * 1000)

        # Echo the request ID back to the client so they can report it
        response.headers["X-Request-ID"] = req_id

        endpoint = request.url.path
        is_error = response.status_code >= 400

        # ── Bot-blocker: count probes on unknown paths ────────────────────
        if response.status_code == 404 and endpoint not in _KNOWN_PATHS:
            _bot_record_probe(ip)

        # Structured log line — grep by request_id to trace any request
        log.info(
            f"rid={req_id} method={request.method} path={endpoint} "
            f"status={response.status_code} ms={ms} ip={ip}"
        )
        if is_error:
            log.warning(f"rid={req_id} error response {response.status_code} from {ip} on {endpoint}")

        with _stats_lock:
            _counters[endpoint] += 1
            if is_error:
                _errors[endpoint] += 1
            # Long-poll endpoints intentionally hold the connection open for up to 29 s.
            # Including them in latency percentiles would make P95/P99 meaningless.
            if endpoint != "/api/notify/pending":
                _recent.append({
                    "request_id": req_id,
                    "time":       start.strftime("%Y-%m-%d %H:%M:%S"),
                    "method":     request.method,
                    "path":       endpoint,
                    "status":     response.status_code,
                    "ms":         ms,
                    "ip":         ip,
                })
        return response


# ── FastAPI app ───────────────────────────────────────────────────────────────
_ENABLE_API_DOCS = os.environ.get("ORS_API_DOCS", "false").lower() == "true"
app = FastAPI(
    title="Operation Report System API",
    docs_url="/docs" if _ENABLE_API_DOCS else None,
    redoc_url=None,
    openapi_url="/openapi.json" if _ENABLE_API_DOCS else None,
)
app.add_middleware(_TrackingMiddleware)

# ── Socket.IO Configuration ────────────────────────────────────────────────────
_sio = None
if SOCKETIO_AVAILABLE:
    try:
        _sio = AsyncServer(
            async_mode="asgi",
            cors_allowed_origins="*",
            ping_timeout=60,
            ping_interval=25,
        )
        notification_manager.set_sio(_sio)
        log.info("Socket.IO server initialized for real-time notifications")
    except Exception as e:
        log.warning(f"Failed to initialize Socket.IO: {e}")
        _sio = None
else:
    log.warning("Socket.IO not available - notifications will be disabled")


# ── Socket.IO Event Handlers ──────────────────────────────────────────────────
if _sio and SOCKETIO_AVAILABLE and not _RUNNING_WITH_GUNICORN:
    @_sio.on("connect")
    async def on_connect(sid, environ):
        """Handle client connection."""
        log.info(f"Client {sid} connected")

    @_sio.on("disconnect")
    async def on_disconnect(sid):
        """Handle client disconnection."""
        notification_manager.unregister_client(sid)
        log.info(f"Client {sid} disconnected")

    @_sio.on("register_branch")
    async def on_register_branch(sid, data):
        """Client registers for notifications on a specific branch."""
        try:
            branch = data.get("branch")
            if branch:
                notification_manager.register_client(sid, branch)
                await _sio.emit("register_success", {"branch": branch}, to=sid)
                log.info(f"Client {sid} registered for branch: {branch}")
            else:
                await _sio.emit("error", {"message": "Branch not provided"}, to=sid)
        except Exception as e:
            log.error(f"Error registering branch for {sid}: {e}")
            await _sio.emit("error", {"message": str(e)}, to=sid)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle Pydantic validation errors with detailed error messages."""
    errors = []
    for error in exc.errors():
        field = ".".join(str(x) for x in error["loc"][1:]) if len(error["loc"]) > 1 else "body"
        errors.append({
            "field": field,
            "message": error["msg"],
            "type": error["type"]
        })
    log.warning(f"Validation error from {request.client.host if request.client else 'unknown'}: {errors}")
    return JSONResponse(
        status_code=400,
        content={
            "error": "Request validation failed",
            "details": errors
        }
    )


def _cleanup_expired_notifications():
    """Delete pending_notifications rows whose 48-hour TTL has passed."""
    try:
        _db.execute_query(
            "DELETE FROM pending_notifications WHERE expires_at <= NOW()", []
        )
    except Exception:
        pass  # Table may not exist yet; suppress silently


def _start_background_cleanup():
    """Start background cleanup thread for memory leak prevention."""
    def cleanup_loop():
        while True:
            try:
                time.sleep(300)  # Run every 5 minutes
                _cleanup_stale_rate_limit_entries()
                _cleanup_old_tasks()
                _cleanup_expired_notifications()
            except Exception as e:
                log.error(f"Background cleanup error: {e}")

    cleanup_thread = threading.Thread(target=cleanup_loop, daemon=True, name="ors-cleanup")
    cleanup_thread.start()
    log.info("Background cleanup thread started (runs every 5 minutes)")


@app.on_event("startup")
async def _raise_thread_limiter():
    """Raise anyio's default thread pool cap (40) so 400+ concurrent sync
    route handlers don't queue waiting for a thread slot."""
    try:
        import anyio
        limiter = anyio.from_thread.current_default_thread_limiter()
        limiter.total_tokens = int(os.environ.get("ORS_THREAD_LIMIT", "500"))
        log.info(f"anyio thread limiter set to {limiter.total_tokens}")
    except Exception as exc:
        log.warning(f"Could not raise thread limiter: {exc}")

    # Start background cleanup (memory leak prevention)
    _start_background_cleanup()

    # Create notifications table once at startup per worker — avoids the race
    # where multiple concurrent first-requests all see _notifications_table_ready=False
    # and all call CREATE TABLE IF NOT EXISTS simultaneously.
    import asyncio as _asyncio
    await _asyncio.to_thread(_ensure_notifications_table)
    global _notifications_table_ready
    _notifications_table_ready = True


# ── Auth helpers ──────────────────────────────────────────────────────────────

def _make_token() -> str:
    """API-key-level token (machine/service auth, no user claims)."""
    payload = {
        "type": "api_key",
        "iat":  datetime.datetime.utcnow(),
        "exp":  datetime.datetime.utcnow() + datetime.timedelta(hours=JWT_HOURS),
    }
    return pyjwt.encode(payload, SECRET_KEY, algorithm="HS256")


def _make_user_token(user: dict) -> str:
    """User-level token — embeds role and identity claims."""
    payload = {
        "type":         "user",
        "sub":          str(user["id"]),
        "username":     user["username"],
        "role":         user["role"],
        "branch":       user.get("branch") or "",
        "corporation":  user.get("corporation") or "",
        "account_type": user.get("account_type") or 2,
        "os_group":     user.get("os_group") or "",
        "iat":          datetime.datetime.utcnow(),
        "exp":          datetime.datetime.utcnow() + datetime.timedelta(hours=JWT_HOURS),
    }
    return pyjwt.encode(payload, SECRET_KEY, algorithm="HS256")


def _decode_token(request: Request) -> dict:
    """Decode and return the JWT payload; raise 401 on any failure."""
    auth  = request.headers.get("Authorization", "")
    token = auth.replace("Bearer ", "").strip()
    if not token:
        raise HTTPException(status_code=401, detail="Missing token")
    try:
        return pyjwt.decode(token, SECRET_KEY, algorithms=["HS256"])
    except pyjwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except pyjwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")


def _require_token(request: Request) -> dict:
    """FastAPI dependency: validate any JWT and return the decoded payload."""
    return _decode_token(request)


def _require_role(*roles: str):
    """FastAPI dependency factory: allow only user tokens whose role is in *roles*."""
    def _dep(request: Request) -> dict:
        payload = _decode_token(request)
        if payload.get("type") != "user":
            raise HTTPException(status_code=403, detail="User authentication required")
        if payload.get("role") not in roles:
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        return payload
    return _dep


# ── Blocked DDL ───────────────────────────────────────────────────────────────
_BLOCKED_DDL = (
    "DROP TABLE", "DROP DATABASE", "TRUNCATE",
    "ALTER TABLE DROP", "ALTER TABLE RENAME",
    "CREATE USER", "GRANT ", "REVOKE ", "FLUSH ",
    "DROP USER", "DROP INDEX",
)


def _check_blocked(sql: str, remote: str = "") -> None:
    sql_upper = sql.strip().upper()
    for keyword in _BLOCKED_DDL:
        if sql_upper.startswith(keyword) or f" {keyword}" in sql_upper:
            if remote:
                log.warning(f"Blocked DDL from {remote}: {sql[:80]}")
            raise HTTPException(
                status_code=403,
                detail=f"Statement type not allowed: {keyword.strip()}"
            )


# ── Request/Response models ───────────────────────────────────────────────────
from pydantic import Field, validator

class TokenRequest(BaseModel):
    api_key: str = Field(..., min_length=1, max_length=256, description="API key for authentication")

    @validator('api_key')
    def api_key_not_empty(cls, v):
        if not v or not v.strip():
            raise ValueError("API key cannot be empty or whitespace")
        return v.strip()


class ExecRequest(BaseModel):
    sql: str = Field(..., min_length=1, max_length=100000, description="SQL query to execute")
    params: Optional[List[Any]] = Field(None, max_items=1000, description="Query parameters")
    ttl: Optional[int] = Field(None, ge=0, le=86400, description="Cache TTL in seconds (0-86400)")

    @validator('sql')
    def sql_not_empty(cls, v):
        if not v or not v.strip():
            raise ValueError("SQL query cannot be empty")
        return v.strip()

    @validator('params')
    def params_valid(cls, v):
        if v is not None:
            # Ensure params is a list of basic types
            for i, param in enumerate(v):
                if not isinstance(param, (str, int, float, bool, type(None))):
                    raise ValueError(f"Parameter {i} has unsupported type: {type(param).__name__}")
        return v


class BatchItem(BaseModel):
    sql: str = Field(..., min_length=1, max_length=100000, description="SQL query")
    params: Optional[List[Any]] = Field(None, max_items=1000, description="Query parameters")
    ttl: Optional[int] = Field(None, ge=0, le=86400, description="Cache TTL in seconds")

    @validator('sql')
    def sql_not_empty(cls, v):
        if not v or not v.strip():
            raise ValueError("SQL query cannot be empty")
        return v.strip()


class BatchRequest(BaseModel):
    queries: List[BatchItem] = Field(..., min_items=1, max_items=100, description="List of queries to execute")

    @validator('queries')
    def queries_not_empty(cls, v):
        if not v or len(v) == 0:
            raise ValueError("At least one query is required")
        return v


# ── Endpoints ─────────────────────────────────────────────────────────────────

@app.get("/api/stats")
def stats(_: None = Depends(_require_token)):
    """Live request stats — JWT required."""
    uptime_s = int((datetime.datetime.utcnow() - _server_start).total_seconds())
    h, rem   = divmod(uptime_s, 3600)
    m, s     = divmod(rem, 60)
    total_cache = _cache_hits + _cache_misses
    hit_rate    = round(_cache_hits / total_cache * 100, 1) if total_cache else 0
    # Redis key count (best-effort)
    redis_entries = None
    if _redis_ok and _redis is not None:
        try:
            redis_entries = _redis.dbsize()
        except Exception:
            pass
    # ── DB pool stats ─────────────────────────────────────────────────────
    pool_stats = {"available": None, "checked_out": None, "overflow": None, "pool_size": None}
    try:
        if _db.engine is not None:
            p = _db.engine.pool
            pool_stats = {
                "pool_size":   p.size(),
                "checked_out": p.checkedout(),
                "overflow":    max(p.overflow(), 0),  # SQLAlchemy returns -1 when none in use
                "available":   p.checkedin(),
            }
    except Exception:
        pass

    # ── Bot-blocker snapshot ──────────────────────────────────────────────
    now = time.monotonic()
    with _bot_lock:
        banned_list = [
            {
                "ip":         ip,
                "expires_in": max(0, int(exp - now)),
            }
            for ip, exp in _bot_banned.items()
            if exp > now
        ]
        probing_list = [
            {
                "ip":          ip,
                "probe_count": len(ts),
                "window_secs": _BOT_WINDOW_SECS,
                "limit":       _BOT_PROBE_LIMIT,
            }
            for ip, ts in _bot_probes.items()
            if ts
        ]

    # Snapshot shared state under the lock, build the response dict outside.
    # Holding _stats_lock while constructing a large dict with list comprehensions
    # blocks _TrackingMiddleware from appending to _recent on every request.
    with _stats_lock, _cache_lock:
        snap_counters = dict(_counters)
        snap_errors   = dict(_errors)
        snap_recent   = list(reversed(_recent))
        snap_cache_entries = len(_cache)
        snap_hits     = _cache_hits
        snap_misses   = _cache_misses

    now = time.monotonic()
    return {
        "uptime":       f"{h}h {m}m {s}s",
        "total_hits":   snap_counters,
        "total_errors": snap_errors,
        "recent":       snap_recent,
        "cache": {
            "backend":      "redis" if _redis_ok else "memory",
            "redis_url":    REDIS_URL if _redis_ok else None,
            "ttl_seconds":  CACHE_TTL,
            "entries":      redis_entries if _redis_ok else snap_cache_entries,
            "hits":         snap_hits,
            "misses":       snap_misses,
            "hit_rate_pct": hit_rate,
        },
        "db_pool":      pool_stats,
        "bot_blocker": {
            "window_secs":   _BOT_WINDOW_SECS,
            "probe_limit":   _BOT_PROBE_LIMIT,
            "ban_secs":      _BOT_BAN_SECS,
            "banned_count":  len(banned_list),
            "banned":        banned_list,
            "probing_count": len(probing_list),
            "probing":       probing_list,
        },
        "ip_blocklist": {
            "blocked_count": len(_IP_BLOCKLIST),
            "blocked_ips":   sorted(_IP_BLOCKLIST),
        },
        "token_rate_limiter": {
            "window_secs":    _TOKEN_WINDOW,
            "limit":          _TOKEN_LIMIT,
            "lockout_secs":   _TOKEN_LOCKOUT,
            "locked_out_count": len(_token_locked),
            "locked_out_ips": [
                {"ip": ip, "expires_in": max(0, int(exp - now))}
                for ip, exp in list(_token_locked.items())
            ],
        },
        "exec_rate_limiter": {
            "window_secs":  _EXEC_WINDOW,
            "limit":        _EXEC_LIMIT,
            "ban_secs":     _EXEC_BAN_SECS,
            "banned_count": sum(1 for exp in _exec_banned_until.values() if exp > now),
            "banned_ips": [
                {"ip": ip, "expires_in": max(0, int(exp - now))}
                for ip, exp in list(_exec_banned_until.items())
                if exp > now
            ],
        },
    }


@app.post("/api/cache/clear")
def cache_clear(_: None = Depends(_require_token)):
    """Flush the entire query cache — JWT required."""
    global _cache_hits, _cache_misses
    count = 0
    # ── Redis ────────────────────────────────────────────────────────────────
    if _redis_ok and _redis is not None:
        try:
            keys = _redis.keys("ors:*")
            if keys:
                count = _redis.delete(*keys)
        except Exception as e:
            log.warning(f"Redis clear error: {e}")
    # ── In-memory fallback ───────────────────────────────────────────────────
    with _cache_lock:
        count += len(_cache)
        _cache.clear()
        _cache_hits   = 0
        _cache_misses = 0
    log.info(f"Cache cleared: {count} entries removed")
    return {"cleared": count, "backend": "redis" if _redis_ok else "memory"}


@app.get("/api/health")
def health():
    """Health check — no auth required."""
    ok = _db.test_connection()
    return JSONResponse(
        content={"status": "ok" if ok else "db_error", "db": ok},
        status_code=200 if ok else 503,
    )


@app.post("/api/token")
def get_token(body: TokenRequest, request: Request):
    """Exchange API key for a JWT.  Called once per client session."""
    remote = request.client.host if request.client else "unknown"

    # Rate-limit before checking the key to prevent brute force
    _token_rate_check(remote)

    if body.api_key != API_KEY:
        log.warning(f"Bad API key attempt from {remote}")
        raise HTTPException(status_code=401, detail="Invalid API key")

    # Successful auth — clear failed attempt history
    _token_rate_clear(remote)
    token = _make_token()
    log.info(f"Token issued to {remote}")
    return {"token": token, "expires_hours": JWT_HOURS}


# ── User authentication ───────────────────────────────────────────────────────

class UserLoginRequest(BaseModel):
    username:    str
    password:    str
    # Optional machine info — if provided, the machine record is updated
    # server-side so the client doesn't need a separate _update_machine_record call.
    machine_id:  Optional[str] = None
    hostname:    Optional[str] = None
    mac_address: Optional[str] = None
    cpu_info:    Optional[str] = None

_VALID_ROLES = {"super_admin", "admin", "user", "accounting"}

@app.post("/api/auth/login")
def user_login(body: UserLoginRequest, request: Request):
    """Authenticate a user and return a role-bearing JWT.
    Also updates the machine record (branch + username) when machine_id is supplied,
    so the client needs zero extra calls after a successful login.
    """
    remote = request.client.host if request.client else "unknown"
    _token_rate_check(remote)

    rows = _db.execute_query(
        """SELECT id, username, password, branch, corporation, role,
                  account_type, COALESCE(os_group,'') AS os_group
           FROM users
           WHERE username = %s AND role IN ('admin','super_admin','user','accounting')
           LIMIT 1""",
        [body.username],
    )
    if not rows:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    user = rows[0]
    if not _verify_password(body.password, user["password"]):
        log.warning("Failed login for user '%s' from %s", body.username, remote)
        raise HTTPException(status_code=401, detail="Invalid credentials")

    if user.get("role") not in _VALID_ROLES:
        raise HTTPException(status_code=403, detail="Role not permitted")

    # Update machine record with now-known username + branch (fire-and-forget, non-fatal)
    if body.machine_id:
        try:
            _db.execute_query(
                """UPDATE machines
                   SET username = %s, branch = %s, last_seen = NOW()
                   WHERE machine_id = %s""",
                [user["username"], user.get("branch") or "", body.machine_id],
            )
        except Exception as _e:
            log.warning("Machine record update failed during login: %s", _e)

    _token_rate_clear(remote)
    token = _make_user_token(user)
    log.info("User '%s' (role=%s) authenticated from %s", body.username, user["role"], remote)
    return {
        "token":        token,
        "user_id":      user["id"],
        "username":     user["username"],
        "role":         user["role"],
        "branch":       user.get("branch") or "",
        "corporation":  user.get("corporation") or "",
        "account_type": user.get("account_type") or 2,
        "os_group":     user.get("os_group") or "",
        "expires_hours": JWT_HOURS,
    }


@app.get("/api/auth/verify")
def verify_user_token(payload: dict = Depends(_require_role(
    "super_admin", "admin", "user", "accounting"
))):
    """Verify that a user JWT is still valid and return its claims."""
    return {
        "valid":    True,
        "username": payload.get("username"),
        "role":     payload.get("role"),
        "branch":   payload.get("branch"),
    }


@app.post("/api/exec")
def exec_query(body: ExecRequest, request: Request, token: dict = Depends(_require_token)):

    remote = request.client.host if request.client else "unknown"
    _exec_rate_check(remote)
    _check_blocked(body.sql, remote)

    params = tuple(body.params) if body.params else None
    _enforce_rls(token, body.sql, params)
    is_write = not _is_select(body.sql)
    operation = "INSERT" if "INSERT" in body.sql.upper() else "UPDATE" if "UPDATE" in body.sql.upper() else "DELETE" if "DELETE" in body.sql.upper() else "SELECT"
    table_name = _extract_table_name(body.sql)

    if CACHE_TTL > 0 and not is_write:
        key = _make_cache_key(body.sql, params)
        hit, cached = _cache_get(key)
        if hit:
            return {"result": cached, "error": None, "cached": True}

    start_time = time.time()
    try:
        result = _db.execute_query(body.sql, params)
        duration_ms = (time.time() - start_time) * 1000

        # execute_query() swallows exceptions and returns None on failure.
        # For writes, rowcount is always an int on success — None means the
        # query failed (e.g. lock timeout 1205).  Return 503 so clients retry.
        if is_write and result is None:
            log.warning(f"{operation} on {table_name} returned None (likely lock timeout) from {remote}")
            return JSONResponse(
                content={"result": None, "error": "Write failed — database may be busy", "cached": False},
                status_code=503,
                headers={"Retry-After": "2"},
            )

        # Log audit trail for writes
        if is_write:
            affected_rows = result if isinstance(result, int) else 0
            log_audit(operation, table_name, body.sql, remote_ip=remote, affected_rows=affected_rows, duration_ms=duration_ms)

        if CACHE_TTL > 0:
            if not is_write:
                _cache_set(key, result, ttl=body.ttl)
            else:
                _cache_clear_all()

        log.debug(f"{operation} on {table_name}: {duration_ms:.1f}ms from {remote}")
        return {"result": result, "error": None, "cached": False}
    except Exception as e:
        duration_ms = (time.time() - start_time) * 1000
        error_id = log_exception(e, source="api_exec", remote_ip=remote)
        log.error(f"Query error (ID:{error_id}): {e} | SQL: {body.sql[:120]}")

        if is_write:
            log_audit(operation, table_name, body.sql, remote_ip=remote, status="error", error_msg=str(e), duration_ms=duration_ms)

        return JSONResponse(content={"result": None, "error": str(e), "error_id": error_id}, status_code=500)


@app.post("/api/exec_safe")
def exec_query_safe(body: ExecRequest, request: Request, token: dict = Depends(_require_token)):

    remote = request.client.host if request.client else "unknown"
    _exec_rate_check(remote)
    _check_blocked(body.sql, remote)

    params = tuple(body.params) if body.params else None
    _enforce_rls(token, body.sql, params)

    # FIX: Define key outside conditional to avoid NameError
    key = None
    if CACHE_TTL > 0 and _is_select(body.sql):
        key = _make_cache_key(body.sql, params)
        hit, cached = _cache_get(key)
        if hit:
            return {"result": cached, "exec_error": None, "error_type": None, "error_code": None, "cached": True}

    result, err = _db.execute_query_with_exception(body.sql, params)
    if CACHE_TTL > 0 and key is not None:
        if _is_select(body.sql) and not err:
            _cache_set(key, result, ttl=body.ttl)
        elif not _is_select(body.sql) and not err:
            # Clear cache after successful writes so fresh reads don't get stale data
            _cache_clear_all()
    return {
        "result":     result,
        "exec_error": str(err) if err else None,
        "error_type": type(err).__name__ if err else None,
        # Pass deadlock error code so client retry logic works
        "error_code": err.args[0] if err and hasattr(err, "args") and err.args else None,
        "cached":     False,
    }



# ── Entry point ───────────────────────────────────────────────────────────────

@app.post("/api/batch")
def exec_batch(body: BatchRequest, request: Request, token: dict = Depends(_require_token)):
    """Execute multiple SQL statements in one HTTP round-trip.

    Each item may include an optional ``ttl`` to extend caching for
    static lookups (e.g. branch/corporation lists).  Returns results in
    the same order as the input queries.
    """
    remote = request.client.host if request.client else "unknown"
    _exec_rate_check(remote)
    results = []
    has_writes = False
    for item in body.queries:
        _check_blocked(item.sql, remote)
        params = tuple(item.params) if item.params else None
        _enforce_rls(token, item.sql, params)
        # Try cache for SELECT statements
        if CACHE_TTL > 0 and _is_select(item.sql):
            key = _make_cache_key(item.sql, params)
            hit, cached = _cache_get(key)
            if hit:
                results.append({"result": cached, "error": None, "cached": True})
                continue
        result, err = _db.execute_query_with_exception(item.sql, params)
        if CACHE_TTL > 0:
            if _is_select(item.sql) and not err:
                _cache_set(key, result, ttl=item.ttl)
            elif not _is_select(item.sql) and not err:
                has_writes = True
        results.append({
            "result": result,
            "error":  str(err) if err else None,
            "cached": False,
        })
    # Clear cache after batch if any writes occurred
    if has_writes and CACHE_TTL > 0:
        _cache_clear_all()
    return {"results": results}


@app.post("/api/enqueue")
def enqueue(body: ExecRequest, request: Request, token: dict = Depends(_require_token)):

    _check_blocked(body.sql, request.client.host if request.client else "unknown")
    params = tuple(body.params) if body.params else None
    _enforce_rls(token, body.sql, params)
    if _is_select(body.sql):
        raise HTTPException(status_code=400, detail="Use /api/exec for SELECT queries")
    if _task_queue.full():
        raise HTTPException(status_code=503, detail="Task queue full, try again shortly")

    task_id = str(uuid.uuid4())
    with _task_lock:
        _task_results[task_id] = {"status": "queued", "result": None, "error": None, "finished_at": None}
    _task_queue.put(BackgroundTask(task_id, body.sql, params))
    log.debug(f"Task {task_id} queued: {body.sql[:60]}")
    return {"task_id": task_id, "status": "queued"}


@app.get("/api/task/{task_id}")
def task_status(task_id: str, _: None = Depends(_require_token)):
    """Poll the result of a background task by task_id."""
    with _task_lock:
        result = _task_results.get(task_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Task not found")
    return result


# ── Notification Endpoints ─────────────────────────────────────────────────────

class NotificationRequest(BaseModel):
    branch: str
    date: str
    admin_name: str = "Administrator"


def _ensure_notifications_table():
    """Create pending_notifications table if it doesn't exist."""
    try:
        _db.execute_query(
            """CREATE TABLE IF NOT EXISTS pending_notifications (
                id INT AUTO_INCREMENT PRIMARY KEY,
                branch VARCHAR(255) NOT NULL,
                date VARCHAR(20) NOT NULL,
                admin_name VARCHAR(255) DEFAULT 'Administrator',
                created_at DATETIME DEFAULT NOW(),
                expires_at DATETIME NOT NULL,
                INDEX idx_branch (branch),
                INDEX idx_expires (expires_at)
            ) DEFAULT CHARSET=utf8mb4""",
            []
        )
    except Exception as e:
        log.warning(f"Could not create pending_notifications table: {e}")


_notifications_table_ready = False


@app.post("/api/notify/reset_entry")
def notify_reset_entry(body: NotificationRequest, request: Request, _: None = Depends(_require_token)):
    """Notify branch clients that their entry has been reset.
    Stores in DB for reliable delivery across all workers, and also
    broadcasts via Socket.IO for instant delivery when available.
    """
    global _notifications_table_ready
    clients_notified = 0

    # Persist to DB so any worker (and polling clients) can serve it
    try:
        if not _notifications_table_ready:
            _ensure_notifications_table()
            _notifications_table_ready = True
        _db.execute_query(
            "INSERT INTO pending_notifications (branch, date, admin_name, expires_at) "
            "VALUES (%s, %s, %s, DATE_ADD(NOW(), INTERVAL 48 HOUR))",
            [body.branch, body.date, body.admin_name]
        )
        log.info(f"Stored pending notification for branch {body.branch} on {body.date}")
    except Exception as e:
        log.warning(f"Could not store pending notification in DB: {e}")

    # Also broadcast via Socket.IO for instant delivery (best-effort)
    if _sio and not _RUNNING_WITH_GUNICORN:
        try:
            notification_data = {
                "type": "entry_reset",
                "branch": body.branch,
                "date": body.date,
                "admin_name": body.admin_name,
                "timestamp": datetime.datetime.utcnow().isoformat(),
            }
            clients_notified = notification_manager.broadcast_to_branch(
                body.branch, "entry_reset", notification_data
            )
            log.info(f"Socket.IO: notified {clients_notified} clients in branch {body.branch}")
        except Exception as e:
            log.warning(f"Socket.IO broadcast failed (non-fatal): {e}")

    return {
        "status": "success",
        "clients_notified": clients_notified,
        "branch": body.branch,
        "date": body.date,
        "persisted": True,
    }


@app.get("/api/notify/pending")
async def get_pending_notifications(branch: str, timeout: int = 0, token: dict = Depends(_require_token)):
    """Return and consume pending notifications for a branch.

    With timeout=0  → regular poll (returns immediately, empty or not).
    With timeout>0  → long poll: suspends (not blocks) for up to `timeout` seconds,
                       waking every 0.5 s. Capped at 29 s.

    Uses async def + asyncio.sleep so 400 simultaneous long-poll connections
    consume zero threads while waiting — previously each blocked a thread for
    up to 29 s, exhausting the sync thread pool and causing 25 s+ latency.
    """
    import asyncio

    # Non-admin clients may only poll their own branch's notifications
    if token.get("type") != "api_key" and token.get("role", "") not in _ADMIN_ROLES:
        token_branch = token.get("branch", "")
        if token_branch and token_branch != branch:
            raise HTTPException(status_code=403, detail="Access denied: you can only poll your own branch.")

    global _notifications_table_ready
    if not _notifications_table_ready:
        await asyncio.to_thread(_ensure_notifications_table)
        _notifications_table_ready = True

    max_wait = min(max(timeout, 0), 29)
    deadline = time.monotonic() + max_wait

    async def _fetch():
        try:
            rows = await asyncio.to_thread(
                _db.execute_query,
                "SELECT id, branch, date, admin_name, created_at FROM pending_notifications "
                "WHERE branch = %s AND expires_at > NOW() ORDER BY created_at",
                [branch],
            )
            if rows:
                ids = [r["id"] for r in rows]
                placeholders = ",".join(["%s"] * len(ids))
                await asyncio.to_thread(
                    _db.execute_query,
                    f"DELETE FROM pending_notifications WHERE id IN ({placeholders})",
                    ids,
                )
            return rows or []
        except Exception as e:
            log.warning(f"Could not fetch pending notifications: {e}")
            return []

    rows = await _fetch()
    while not rows and time.monotonic() < deadline:
        await asyncio.sleep(0.5)
        rows = await _fetch()

    notifications = [
        {
            "type": "entry_reset",
            "branch": r["branch"],
            "date": str(r["date"]),
            "admin_name": r["admin_name"],
            "timestamp": str(r["created_at"]),
        }
        for r in rows
    ]
    return {"notifications": notifications}


@app.get("/api/notify/capabilities")
def notify_capabilities():
    """Public endpoint — tells clients whether Socket.IO is available on this server.
    No auth required; contains no sensitive data."""
    return {
        "socketio": bool(_sio and not _RUNNING_WITH_GUNICORN),
        "polling": True,
    }


@app.get("/api/notify/stats")
def notification_stats(_: None = Depends(_require_token)):
    """Get Socket.IO connection statistics."""
    return notification_manager.get_connection_stats()


# ── Machine access control ────────────────────────────────────────────────────

class MachineStatusRequest(BaseModel):
    """Startup check: combine token fetch + machine register into a single call."""
    api_key:    str
    machine_id: str
    hostname:   Optional[str] = None
    mac_address: Optional[str] = None
    cpu_info:   Optional[str] = None


@app.post("/api/machine/status")
def machine_status(body: MachineStatusRequest, request: Request):
    """Single startup call: validate API key, register/refresh machine, return status.
    Replaces the two-step  POST /api/token  →  POST /api/machine/register  flow.

    Identity is based on PC name (hostname). A new machine_id whose hostname
    already belongs to a different registered machine is flagged 'duplicate' so
    super admin can investigate before granting access.
    """
    if body.api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key")

    existing = _db.execute_query(
        "SELECT status FROM machines WHERE machine_id = %s LIMIT 1",
        [body.machine_id],
    )
    if existing:
        _db.execute_query(
            "UPDATE machines SET last_seen = NOW(), hostname = %s WHERE machine_id = %s",
            [body.hostname, body.machine_id],
        )
        return {"status": existing[0]["status"]}

    # New machine_id — check whether the hostname is already taken by another machine.
    hostname_conflict = False
    if body.hostname:
        conflict_row = _db.execute_query(
            "SELECT machine_id FROM machines WHERE hostname = %s AND machine_id != %s LIMIT 1",
            [body.hostname, body.machine_id],
        )
        hostname_conflict = bool(conflict_row)

    if hostname_conflict:
        # Same PC name, different fingerprint → flag as duplicate for admin review.
        _db.execute_query(
            """INSERT INTO machines
               (machine_id, hostname, mac_address, cpu_info, status, registered_at, last_seen)
               VALUES (%s, %s, %s, %s, 'duplicate', NOW(), NOW())""",
            [body.machine_id, body.hostname, body.mac_address, body.cpu_info],
        )
        log.warning("Duplicate hostname registration: %s (machine_id=%s)", body.hostname, body.machine_id)
        return {"status": "duplicate"}

    # No conflict — respect ORS_MACHINE_AUTO_APPROVE.
    auto_approve = os.environ.get("ORS_MACHINE_AUTO_APPROVE", "false").lower() == "true"
    initial_status = "approved" if auto_approve else "pending"
    _db.execute_query(
        """INSERT INTO machines
           (machine_id, hostname, mac_address, cpu_info, status, registered_at, last_seen)
           VALUES (%s, %s, %s, %s, %s, NOW(), NOW())""",
        [body.machine_id, body.hostname, body.mac_address, body.cpu_info, initial_status],
    )
    return {"status": initial_status}


class MachineRegisterRequest(BaseModel):
    machine_id:  str
    hostname:    Optional[str] = None
    branch:      Optional[str] = None
    username:    Optional[str] = None
    mac_address: Optional[str] = None
    cpu_info:    Optional[str] = None


@app.post("/api/machine/register")
def machine_register(body: MachineRegisterRequest, _: None = Depends(_require_token)):
    """Register a machine on first login (auto-approved).
    If the machine is already revoked this call does NOT re-approve it.
    """
    existing = _db.execute_query(
        "SELECT status FROM machines WHERE machine_id = %s LIMIT 1",
        [body.machine_id]
    )
    if existing:
        # Update last_seen (and branch/username in case they changed)
        _db.execute_query(
            """UPDATE machines
               SET last_seen = NOW(), branch = %s, username = %s,
                   hostname = %s
               WHERE machine_id = %s""",
            [body.branch, body.username, body.hostname, body.machine_id]
        )
        return {"status": existing[0]["status"]}
    else:
        # ORS_MACHINE_AUTO_APPROVE=true  → first-time machines get 'approved' immediately
        #   (keep this ON until all existing clients have registered, then turn OFF)
        # ORS_MACHINE_AUTO_APPROVE=false → new machines get 'pending' until admin approves
        auto_approve = os.environ.get("ORS_MACHINE_AUTO_APPROVE", "false").lower() == "true"
        initial_status = "approved" if auto_approve else "pending"
        _db.execute_query(
            """INSERT INTO machines
               (machine_id, hostname, branch, username, mac_address, cpu_info,
                status, registered_at, last_seen)
               VALUES (%s, %s, %s, %s, %s, %s, %s, NOW(), NOW())""",
            [body.machine_id, body.hostname, body.branch, body.username,
             body.mac_address, body.cpu_info, initial_status]
        )
        return {"status": initial_status}


@app.get("/api/machine/verify/{machine_id}")
def machine_verify(machine_id: str, _: None = Depends(_require_token)):
    """Check whether a machine is approved. Returns {status: approved|revoked|unknown}."""
    rows = _db.execute_query(
        "SELECT status FROM machines WHERE machine_id = %s LIMIT 1",
        [machine_id]
    )
    if not rows:
        return {"status": "unknown"}
    return {"status": rows[0]["status"]}


@app.get("/api/machine/list")
def machine_list(_: None = Depends(_require_token)):
    """Return all registered machines for the super-admin dashboard."""
    rows = _db.execute_query(
        """SELECT id, machine_id, hostname, branch, username,
                  mac_address, cpu_info, status,
                  registered_at, last_seen, revoked_at, revoked_by, notes
           FROM machines
           ORDER BY registered_at DESC""",
        []
    )
    def _fmt(row):
        out = dict(row)
        for k in ("registered_at", "last_seen", "revoked_at"):
            v = out.get(k)
            out[k] = v.isoformat() if v else None
        return out
    return {"machines": [_fmt(r) for r in (rows or [])]}


@app.post("/api/machine/revoke/{machine_id}")
def machine_revoke(machine_id: str, body: dict = None, _: None = Depends(_require_token)):
    """Revoke a machine — it will be blocked on the next startup."""
    revoked_by = (body or {}).get("revoked_by", "super_admin")
    _db.execute_query(
        """UPDATE machines
           SET status = 'revoked', revoked_at = NOW(), revoked_by = %s
           WHERE machine_id = %s""",
        [revoked_by, machine_id]
    )
    return {"ok": True}


@app.post("/api/machine/approve/{machine_id}")
def machine_approve(machine_id: str, _: None = Depends(_require_token)):
    """Re-approve a previously revoked machine."""
    _db.execute_query(
        """UPDATE machines
           SET status = 'approved', revoked_at = NULL, revoked_by = NULL
           WHERE machine_id = %s""",
        [machine_id]
    )
    return {"ok": True}


# ── Mount Socket.IO to FastAPI ────────────────────────────────────────────────
# Only mount with uvicorn (ASGI). Gunicorn (WSGI) is incompatible.
if _sio and ASGIApp and not _RUNNING_WITH_GUNICORN:
    try:
        app = ASGIApp(_sio, app)
        log.info("Socket.IO mounted to FastAPI app (ASGI mode)")
    except Exception as e:
        log.warning(f"Failed to mount Socket.IO: {e}. Notifications will be unavailable.")
elif _sio and _RUNNING_WITH_GUNICORN:
    log.warning("Running with Gunicorn (WSGI). Socket.IO notifications are not supported in WSGI mode.")
    log.warning("To use notifications, run with: python api_server.py (uvicorn)")
    _sio = None  # Disable Socket.IO in Gunicorn


if __name__ == "__main__":
    import uvicorn
    import os as _os
    log.info(f"Starting ORS API Server on {API_HOST}:{API_PORT}")
    log.info(f"API Key: {API_KEY[:8]}... (set ORS_API_KEY env var to change)")

    # Check for SSL certificate files
    cert_file = _os.path.join(_os.path.dirname(__file__), "cert.pem")
    key_file = _os.path.join(_os.path.dirname(__file__), "key.pem")
    use_ssl = _os.path.exists(cert_file) and _os.path.exists(key_file)

    if use_ssl:
        log.info(f"Using HTTPS with self-signed certificate")
        log.info(f"⚠️  Certificate: {cert_file}")
    else:
        log.warning(f"No SSL certificate found. Using HTTP (not secure)")
        log.warning(f"To enable HTTPS, run: openssl req -x509 -newkey rsa:4096 -nodes -out cert.pem -keyout key.pem -days 365")

    uvicorn.run(
        app,
        host=API_HOST,
        port=API_PORT,
        # Allow enough threads to serve 400+ concurrent sync handlers
        # without queuing behind the default anyio limit of 40.
        limit_concurrency=500,
        ssl_keyfile=key_file if use_ssl else None,
        ssl_certfile=cert_file if use_ssl else None,
    )
