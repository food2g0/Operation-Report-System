
import os
import json
import time
import uuid
import queue
import hashlib
import logging
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

from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from starlette.middleware.base import BaseHTTPMiddleware
import jwt as pyjwt


from db_connect_pooled import DatabaseManagerPooled


API_KEY    = os.environ.get("ORS_API_KEY",    "")
SECRET_KEY = os.environ.get("ORS_SECRET_KEY", "")
API_HOST   = os.environ.get("ORS_API_HOST",   "0.0.0.0")
API_PORT   = int(os.environ.get("ORS_API_PORT", 5000))
JWT_HOURS  = int(os.environ.get("ORS_JWT_HOURS", 12))
CACHE_TTL   = int(os.environ.get("ORS_CACHE_TTL",  30))    # seconds; 0 = disabled
CACHE_MAX   = int(os.environ.get("ORS_CACHE_MAX",  2000))   # in-memory fallback max entries
REDIS_URL   = os.environ.get("ORS_REDIS_URL",  "redis://127.0.0.1:6379/0")

# ── Logging ───────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
log = logging.getLogger("api_server")

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
        # Invalidate cache for any related SELECT keys after a write
        if not _is_select(task.sql):
            # Best-effort: clear full cache so stale reads don't linger
            _cache_set.__doc__  # no-op, just a check
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
    "/api/enqueue",
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
app = FastAPI(title="Operation Report System API", docs_url=None, redoc_url=None)
app.add_middleware(_TrackingMiddleware)


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


# ── Auth helpers ──────────────────────────────────────────────────────────────

def _make_token() -> str:
    payload = {
        "iat": datetime.datetime.utcnow(),
        "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=JWT_HOURS),
    }
    return pyjwt.encode(payload, SECRET_KEY, algorithm="HS256")


def _require_token(request: Request) -> None:
    """FastAPI dependency: validate JWT in Authorization header."""
    auth  = request.headers.get("Authorization", "")
    token = auth.replace("Bearer ", "").strip()
    if not token:
        raise HTTPException(status_code=401, detail="Missing token")
    try:
        pyjwt.decode(token, SECRET_KEY, algorithms=["HS256"])
    except pyjwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except pyjwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")


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

class TokenRequest(BaseModel):
    api_key: str


class ExecRequest(BaseModel):
    sql: str
    params: Optional[List[Any]] = None
    ttl: Optional[int] = None   # per-query cache TTL override (seconds); None = use server default


class BatchItem(BaseModel):
    sql: str
    params: Optional[List[Any]] = None
    ttl: Optional[int] = None   # per-query cache TTL override


class BatchRequest(BaseModel):
    queries: List[BatchItem]


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

    with _stats_lock, _cache_lock:
        return {
            "uptime":       f"{h}h {m}m {s}s",
            "total_hits":   dict(_counters),
            "total_errors": dict(_errors),
            "recent":       list(reversed(_recent)),  # newest first
            "cache": {
                "backend":      "redis" if _redis_ok else "memory",
                "redis_url":    REDIS_URL if _redis_ok else None,
                "ttl_seconds":  CACHE_TTL,
                "entries":      redis_entries if _redis_ok else len(_cache),
                "hits":         _cache_hits,
                "misses":       _cache_misses,
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
                    {"ip": ip, "expires_in": max(0, int(exp - time.monotonic()))}
                    for ip, exp in list(_token_locked.items())
                ],
            },
            "exec_rate_limiter": {
                "window_secs":  _EXEC_WINDOW,
                "limit":        _EXEC_LIMIT,
                "ban_secs":     _EXEC_BAN_SECS,
                "banned_count": sum(
                    1 for exp in _exec_banned_until.values() if exp > time.monotonic()
                ),
                "banned_ips": [
                    {"ip": ip, "expires_in": max(0, int(exp - time.monotonic()))}
                    for ip, exp in list(_exec_banned_until.items())
                    if exp > time.monotonic()
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


@app.post("/api/exec")
def exec_query(body: ExecRequest, request: Request, _: None = Depends(_require_token)):

    remote = request.client.host if request.client else "unknown"
    _exec_rate_check(remote)
    _check_blocked(body.sql, remote)

    params = tuple(body.params) if body.params else None

    if CACHE_TTL > 0 and _is_select(body.sql):
        key = _make_cache_key(body.sql, params)
        hit, cached = _cache_get(key)
        if hit:
            return {"result": cached, "error": None, "cached": True}

    try:
        result = _db.execute_query(body.sql, params)
        if CACHE_TTL > 0 and _is_select(body.sql):
            _cache_set(key, result, ttl=body.ttl)
        return {"result": result, "error": None, "cached": False}
    except Exception as e:
        log.error(f"Query error: {e} | SQL: {body.sql[:120]}")
        return JSONResponse(content={"result": None, "error": str(e)}, status_code=500)


@app.post("/api/exec_safe")
def exec_query_safe(body: ExecRequest, request: Request, _: None = Depends(_require_token)):

    remote = request.client.host if request.client else "unknown"
    _exec_rate_check(remote)
    _check_blocked(body.sql)

    params = tuple(body.params) if body.params else None

    if CACHE_TTL > 0 and _is_select(body.sql):
        key = _make_cache_key(body.sql, params)
        hit, cached = _cache_get(key)
        if hit:
            return {"result": cached, "exec_error": None, "error_type": None, "error_code": None, "cached": True}

    result, err = _db.execute_query_with_exception(body.sql, params)
    if CACHE_TTL > 0 and _is_select(body.sql) and not err:
        _cache_set(key, result, ttl=body.ttl)
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
def exec_batch(body: BatchRequest, request: Request, _: None = Depends(_require_token)):
    """Execute multiple SQL statements in one HTTP round-trip.

    Each item may include an optional ``ttl`` to extend caching for
    static lookups (e.g. branch/corporation lists).  Returns results in
    the same order as the input queries.
    """
    remote = request.client.host if request.client else "unknown"
    _exec_rate_check(remote)
    results = []
    for item in body.queries:
        _check_blocked(item.sql, remote)
        params = tuple(item.params) if item.params else None
        # Try cache for SELECT statements
        if CACHE_TTL > 0 and _is_select(item.sql):
            key = _make_cache_key(item.sql, params)
            hit, cached = _cache_get(key)
            if hit:
                results.append({"result": cached, "error": None, "cached": True})
                continue
        result, err = _db.execute_query_with_exception(item.sql, params)
        if CACHE_TTL > 0 and _is_select(item.sql) and not err:
            _cache_set(key, result, ttl=item.ttl)
        results.append({
            "result": result,
            "error":  str(err) if err else None,
            "cached": False,
        })
    return {"results": results}


@app.post("/api/enqueue")
def enqueue(body: ExecRequest, _: None = Depends(_require_token)):

    _check_blocked(body.sql)
    if _is_select(body.sql):
        raise HTTPException(status_code=400, detail="Use /api/exec for SELECT queries")
    if _task_queue.full():
        raise HTTPException(status_code=503, detail="Task queue full, try again shortly")

    task_id = str(uuid.uuid4())
    params  = tuple(body.params) if body.params else ()
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


if __name__ == "__main__":
    import uvicorn
    log.info(f"Starting ORS API Server on {API_HOST}:{API_PORT}")
    log.info(f"API Key: {API_KEY[:8]}... (set ORS_API_KEY env var to change)")
    uvicorn.run(
        app,
        host=API_HOST,
        port=API_PORT,
        # Allow enough threads to serve 400+ concurrent sync handlers
        # without queuing behind the default anyio limit of 40.
        limit_concurrency=500,
    )
