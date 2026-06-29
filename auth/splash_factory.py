"""
auth.splash_factory — builds the branded splash screen shown while the
dashboard loads.

Extracted from login.py._make_splash().  Same visual output, isolated into
a single factory function so it can be reused without pulling in the whole
LoginWindow.
"""
from __future__ import annotations

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor, QFont, QPainter, QPixmap
from PyQt5.QtWidgets import QSplashScreen

from auth.login_service import AuthResult

_W, _H = 520, 200


def make_splash(result: AuthResult) -> QSplashScreen:
    """Return a branded QSplashScreen ready to be shown."""
    px = QPixmap(_W, _H)
    px.fill(QColor("#1a252f"))

    p = QPainter(px)
    p.setRenderHint(QPainter.Antialiasing)

    # Left accent bar
    p.fillRect(0, 0, 6, _H, QColor("#3498db"))

    # App title
    p.setPen(QColor("#ecf0f1"))
    p.setFont(QFont("Segoe UI", 18, QFont.Bold))
    p.drawText(24, 52, "Operation Report System")

    # Subtitle line
    subtitle = _build_subtitle(result)
    p.setFont(QFont("Segoe UI", 11))
    p.setPen(QColor("#bdc3c7"))
    p.drawText(24, 88, subtitle)

    # Loading text
    p.setPen(QColor("#7f8c8d"))
    p.setFont(QFont("Segoe UI", 10))
    p.drawText(24, _H - 28, "Loading dashboard, please wait…")

    # Animated dots (visual only — alpha gradient gives depth)
    dot_x = _W - 80
    for i, alpha in enumerate([255, 180, 100, 50]):
        p.setBrush(QColor(52, 152, 219, alpha))
        p.setPen(Qt.NoPen)
        p.drawEllipse(dot_x + i * 18, _H - 40, 10, 10)

    p.end()

    splash = QSplashScreen(px, Qt.WindowStaysOnTopHint)
    splash.setFont(QFont("Segoe UI", 10))
    return splash


def _build_subtitle(result: AuthResult) -> str:
    name = result.username or ""
    if result.role == "super_admin":
        return f"Welcome, {name}  —  Super Admin"
    if result.role == "admin":
        brand      = "Brand A" if result.account_type == 1 else "Brand B"
        group_part = f"  ·  {result.os_group}" if result.os_group else ""
        return f"Welcome, {name}  —  {brand} Admin{group_part}"
    # user / accounting / offline
    parts = [p for p in (result.branch, result.corporation) if p]
    detail = "  ·  ".join(parts) if parts else ""
    return f"Welcome, {name}  —  {detail}" if detail else f"Welcome, {name}!"
