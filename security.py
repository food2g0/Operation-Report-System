"""
security.py — backward-compatibility shim.

The real implementations now live in the auth/ package.
This file is kept so existing callers (admin_dashboard.py, admin_manage.py,
user_management_page.py, Client/dashboard/core.py) continue to work without
any changes.

Do NOT add new logic here — put it in the appropriate auth/ submodule.
"""
# Re-export everything callers expect from this module
from auth.password_hasher import (          # noqa: F401
    hash_password,
    verify_password,
    is_password_hashed,
    validate_password_strength,
)
from auth.rate_limiter import (             # noqa: F401
    RateLimiter,
    login_rate_limiter,
    format_lockout_time,
)
from auth.session import SessionManager     # noqa: F401
