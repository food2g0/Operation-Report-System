"""
login.py — backward-compatibility shim.

LoginWindow now lives in auth/login_window.py.
This file is kept so any caller using `from login import LoginWindow`
continues to work unchanged.

Do NOT add new logic here.
"""
from auth.login_window import LoginWindow   # noqa: F401

__all__ = ["LoginWindow"]
