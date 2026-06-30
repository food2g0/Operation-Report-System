"""
auth.login_service — authentication business logic.

This is the heart of the auth layer.  It is 100% Qt-free and testable in
isolation.  The old login.py crammed this logic inside the QWidget alongside
UI code; now it lives here and the widget just calls it.

Responsibilities:
  - Call the API's /api/auth/login endpoint
  - Parse and validate the response
  - Record failed attempts with the rate limiter
  - Cache credentials on success
  - Return a typed AuthResult (not raw dicts)

The widget (login_window.py) receives an AuthResult and decides what to show
the user and which dashboard to open.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Optional

from auth.rate_limiter import RateLimiter, login_rate_limiter
from auth.credential_store import CredentialStore, CachedUser

log = logging.getLogger(__name__)


# ── Result type ───────────────────────────────────────────────────────────────

@dataclass
class AuthResult:
    success:      bool
    username:     Optional[str]  = None
    role:         Optional[str]  = None
    branch:       Optional[str]  = None
    corporation:  Optional[str]  = None
    account_type: Optional[int]  = None
    os_group:     Optional[str]  = None
    token:        Optional[str]  = None  # JWT for client-mode connections
    is_offline:   bool           = False
    error_code:   Optional[str]  = None  # 'invalid_credentials' | 'locked' | 'network' | 'server'
    error_message: Optional[str] = None
    lockout_remaining: int       = 0
    attempts_remaining: int      = 0

    @property
    def is_admin_role(self) -> bool:
        return self.role in ("admin", "super_admin", "accounting", "compliance")


# ── Service ───────────────────────────────────────────────────────────────────

class LoginService:
    """
    Single entry point for all authentication flows.

    Inject a custom RateLimiter or CredentialStore for testing.
    """

    def __init__(
        self,
        api_url:          Optional[str]          = None,
        rate_limiter:     Optional[RateLimiter]  = None,
        credential_store: Optional[CredentialStore] = None,
        request_timeout:  int                    = 8,
    ) -> None:
        if api_url is None:
            try:
                from api_config import API_URL
                api_url = API_URL
            except ImportError:
                api_url = "http://127.0.0.1:5000"

        self._api_url          = api_url.rstrip("/")
        self._rate_limiter     = rate_limiter or login_rate_limiter
        self._store            = credential_store or CredentialStore()
        self._timeout          = request_timeout

    # ── Online login ──────────────────────────────────────────────────────────

    def authenticate(self, username: str, password: str) -> AuthResult:
        """
        Authenticate against the API server.

        Handles rate-limiting, caches credentials on success.
        """
        # Pre-flight rate limit check (before touching the network)
        locked, lockout_secs = self._rate_limiter.is_locked(username)
        if locked:
            return AuthResult(
                success=False,
                error_code="locked",
                error_message=f"Too many failed attempts. Please wait.",
                lockout_remaining=lockout_secs,
            )

        # Build machine fingerprint for the server's machine-registration check
        try:
            from machine_id import get_machine_info
            machine = get_machine_info()
        except Exception:
            machine = {}

        # Call the API
        try:
            import requests
            resp = requests.post(
                f"{self._api_url}/api/auth/login",
                json={
                    "username":    username,
                    "password":    password,
                    "machine_id":  machine.get("machine_id"),
                    "hostname":    machine.get("hostname"),
                    "mac_address": machine.get("mac_address"),
                    "cpu_info":    machine.get("cpu_info"),
                },
                timeout=self._timeout,
                verify=False,  # private LAN — self-signed cert
            )
        except Exception as exc:
            log.error("Auth API unreachable: %s", exc)
            return AuthResult(
                success=False,
                error_code="network",
                error_message=(
                    "Could not reach the authentication server.\n"
                    "Please check your network connection."
                ),
            )

        # Handle error responses
        if resp.status_code == 401:
            locked, remaining, lockout_secs = self._rate_limiter.record_failed_attempt(username)
            return AuthResult(
                success=False,
                error_code="locked" if locked else "invalid_credentials",
                error_message="Incorrect username or password.",
                lockout_remaining=lockout_secs,
                attempts_remaining=remaining,
            )

        if resp.status_code != 200:
            log.error("Auth API returned HTTP %s", resp.status_code)
            return AuthResult(
                success=False,
                error_code="server",
                error_message=f"Server returned an unexpected error (HTTP {resp.status_code}).",
            )

        # Success
        data = resp.json()
        result = AuthResult(
            success=True,
            username=data.get("username", username),
            role=data.get("role", "user"),
            branch=data.get("branch") or "",
            corporation=data.get("corporation") or "",
            account_type=int(data.get("account_type") or 2),
            os_group=data.get("os_group") or "",
            token=data.get("token"),
        )

        self._rate_limiter.reset(username)

        # Cache for offline fallback (non-admin roles only)
        if not result.is_admin_role:
            self._store.save(result.username, password, {
                "role":         result.role,
                "branch":       result.branch,
                "corporation":  result.corporation,
                "account_type": result.account_type,
                "os_group":     result.os_group,
            })

        log.info("Login success: %s role=%s", result.username, result.role)
        return result

    # ── Offline login ─────────────────────────────────────────────────────────

    def authenticate_offline(self, username: str, password: str) -> AuthResult:
        """
        Verify credentials against the local offline cache.
        Returns a failed result if cache is empty or password is wrong.
        """
        success, cached = self._store.verify(username, password)
        if not success or cached is None:
            has_cache = self._store.has_credentials(username)
            return AuthResult(
                success=False,
                error_code="invalid_credentials",
                error_message=(
                    "Incorrect password for cached credentials."
                    if has_cache else
                    "No cached credentials found for this user.\n\n"
                    "Please connect to the internet and log in at least once "
                    "to enable offline mode."
                ),
            )

        log.warning("Offline login success: %s (network unavailable)", username)
        return AuthResult(
            success=True,
            username=cached.username,
            role=cached.role,
            branch=cached.branch,
            corporation=cached.corporation,
            account_type=cached.account_type,
            os_group=cached.os_group,
            is_offline=True,
        )
