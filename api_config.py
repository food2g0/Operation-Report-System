# ─────────────────────────────────────────────────────────────────────────────
# ORS API Client Configuration
# ─────────────────────────────────────────────────────────────────────────────
# Set API_MODE = True to route all database queries through the API server
# (api_server.py) instead of connecting to MySQL directly.
#
# HOW TO USE:
#   1. On the SERVER machine: run  python api_server.py
#   2. On each CLIENT machine: set API_MODE = True and fill in API_URL below
#   3. Restart the client app — no other changes needed
#
# Set API_MODE = False to go back to direct database connection at any time.
# ─────────────────────────────────────────────────────────────────────────────

import os

API_MODE = os.environ.get("ORS_API_MODE", "true").lower() == "true"

# The IP address and port of the machine running api_server.py
API_URL  = os.environ.get("ORS_API_URL", "http://222.127.90.218:5000")

# ── API key: read from encrypted config (single source of truth) ──────────────
# The key is stored inside db_config.enc alongside DB credentials.
# To update: run  python secure_config.py generate  and redistribute db_config.enc.
# Env var ORS_API_KEY overrides (useful for server-side where no .enc file exists).
def _load_api_key() -> str:
    env_key = os.environ.get("ORS_API_KEY", "")
    if env_key:
        return env_key
    try:
        from secure_config import decrypt_config
        cfg = decrypt_config()
        if cfg and cfg.get("api_key"):
            return cfg["api_key"]
    except Exception:
        pass
    return ""

API_KEY = _load_api_key()
