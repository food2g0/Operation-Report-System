"""
Gunicorn configuration for ORS API Server with WebSocket Support
Run with: gunicorn -c gunicorn.conf.py api_server:app
"""

import multiprocessing
import os

# ── Server Socket ──────────────────────────────────────────────────────────
bind = os.environ.get("ORS_API_HOST", "0.0.0.0") + ":" + os.environ.get("ORS_API_PORT", "5000")
backlog = 2048

# ── Worker Processes ───────────────────────────────────────────────────────
# Use Uvicorn workers for ASGI (required for WebSocket support)
worker_class = "uvicorn.workers.UvicornWorker"
workers = int(os.environ.get("ORS_WORKERS", multiprocessing.cpu_count() * 2))
worker_connections = int(os.environ.get("ORS_WORKER_CONNECTIONS", 5000))

# ── Timeouts ───────────────────────────────────────────────────────────────
timeout = int(os.environ.get("ORS_TIMEOUT", 120))
graceful_timeout = int(os.environ.get("ORS_GRACEFUL_TIMEOUT", 30))

# ── Request Handling ───────────────────────────────────────────────────────
# With 400+ clients each polling every 60s, expect ~300-500 req/min per worker.
# max_requests=50000 → worker restarts every ~1.5-3 hours (prevents slow memory leaks
# without restarting so often that connections are constantly being dropped).
max_requests = int(os.environ.get("ORS_MAX_REQUESTS", 50000))
max_requests_jitter = int(os.environ.get("ORS_MAX_REQUESTS_JITTER", 500))

# ── Logging ────────────────────────────────────────────────────────────────
accesslog = os.environ.get("ORS_ACCESS_LOG", "-")
errorlog = os.environ.get("ORS_ERROR_LOG", "-")
loglevel = os.environ.get("ORS_LOG_LEVEL", "info")
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'

# ── Process Naming ─────────────────────────────────────────────────────────
proc_name = "ors-api"

# ── Server Mechanics ───────────────────────────────────────────────────────
daemon = False
pidfile = None
preload_app = False
keepalive = 5

# ── SSL (if needed) ────────────────────────────────────────────────────────
# Uncomment if using SSL:
# certfile = "/path/to/cert.pem"
# keyfile = "/path/to/key.pem"

# ── Application specific settings ──────────────────────────────────────────
# Uvicorn worker options
raw_env = [
    "ORS_API_HOST=0.0.0.0",
    "ORS_API_PORT=5000",
    "ORS_LOG_LEVEL=INFO",
]

print(f"[ORS] Gunicorn configuration loaded")
print(f"[ORS] Workers: {workers} (Uvicorn worker type)")
print(f"[ORS] Worker connections: {worker_connections}")
print(f"[ORS] WebSocket notifications: ENABLED")
