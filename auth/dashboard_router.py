"""
auth.dashboard_router — maps an AuthResult to the correct dashboard widget.

Extracted from login.py._authenticate_via_api (the if/elif role block).
Lazy imports prevent circular dependencies and speed up startup — the
heavy dashboard modules only load when actually needed.
"""
from __future__ import annotations

import logging
from typing import Optional

from PyQt5.QtWidgets import QWidget

from auth.login_service import AuthResult

log = logging.getLogger(__name__)


def open_dashboard(result: AuthResult) -> Optional[QWidget]:
    """
    Instantiate and return the correct dashboard widget for the given role.

    Returns None and logs an error if the role is unrecognised or the
    dashboard fails to load.  The caller (LoginWindow) is responsible for
    calling .showMaximized() and connecting the logout signal.
    """
    try:
        role = result.role

        if role == "super_admin":
            from admin.super_dashboard import SuperAdminDashboard
            return SuperAdminDashboard()

        if role == "admin":
            from admin.dashboard import AdminDashboard
            return AdminDashboard(
                account_type=result.account_type,
                os_group=result.os_group,
            )

        if role == "accounting":
            from admin.accounting import AccountingDashboard
            return AccountingDashboard(
                branch=result.branch,
                corporation=result.corporation,
            )

        # role == 'user' (branch client) — connects via API, not direct DB
        from Client.api_db_manager import APIDbManager
        client_db = APIDbManager()
        if not client_db.connect():
            log.error("Client API connect() failed for user: %s", result.username)
            return None

        from Client.client_dashboard import ClientDashboard
        return ClientDashboard(
            result.username,
            result.branch,
            result.corporation,
            client_db,
            offline_mode=result.is_offline,
        )

    except Exception as exc:
        log.error(
            "Failed to open dashboard for role=%s user=%s: %s",
            result.role, result.username, exc,
            exc_info=True,
        )
        return None


def open_offline_dashboard(result: AuthResult) -> Optional[QWidget]:
    """Client dashboard in offline mode (no API token, no network)."""
    try:
        # Offline users see the client dashboard backed by whatever DB is available
        try:
            from tools.db_connect_pooled import db_manager as _db
        except ImportError:
            _db = None

        from Client.client_dashboard import ClientDashboard
        return ClientDashboard(
            result.username,
            result.branch,
            result.corporation,
            _db,
            offline_mode=True,
        )
    except Exception as exc:
        log.error("Failed to open offline dashboard: %s", exc, exc_info=True)
        return None
