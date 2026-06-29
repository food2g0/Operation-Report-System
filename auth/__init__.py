"""
auth — clean authentication layer.

Everything that was tangled inside login.py / security.py / offline_manager.py
is now split by responsibility.  All files in this package are pure Python
(no Qt) except login_window.py, splash_factory.py, and dashboard_router.py.

Import map for callers that used the old modules:

  OLD                                     NEW
  ─────────────────────────────────────── ───────────────────────────────────────
  from security import hash_password      from auth.password_hasher import hash_password
  from security import SessionManager     from auth.session import SessionManager
  from security import login_rate_limiter from auth.rate_limiter import login_rate_limiter
  from login import LoginWindow           from auth.login_window import LoginWindow
"""
from .login_window import LoginWindow

__all__ = ["LoginWindow"]
