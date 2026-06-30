"""
auth.login_window — thin Qt shell for the login screen.

All authentication logic lives in LoginService.  This widget is responsible
for three things only:
  1. Displaying the form and handling raw user input.
  2. Calling LoginService and translating the AuthResult into UI feedback.
  3. Showing the splash, opening the dashboard, and hiding itself.

If you find yourself putting business logic here, move it to LoginService or
one of the other auth submodules instead.
"""
from __future__ import annotations

import base64
import logging
import os

from PyQt5.QtCore import Qt, QSettings, QTimer
from PyQt5.QtGui import QFont, QPixmap
from PyQt5.QtWidgets import (
    QApplication, QCheckBox, QFrame, QHBoxLayout, QLabel,
    QLineEdit, QMessageBox, QPushButton, QSplashScreen,
    QVBoxLayout, QWidget,
)

from auth.login_service import LoginService, AuthResult
from auth.rate_limiter import format_lockout_time
from auth.splash_factory import make_splash
from auth.dashboard_router import open_dashboard

log = logging.getLogger(__name__)

try:
    from tools.db_connect_pooled import db_manager
    _DB_AVAILABLE = True
except ImportError:
    db_manager = None
    _DB_AVAILABLE = False

try:
    from offline_manager import offline_manager as _pending_store
    _OFFLINE_PENDING = True
except ImportError:
    _pending_store = None
    _OFFLINE_PENDING = False

try:
    from auto_updater import check_version_compliance, check_for_updates
    from version import __version__, CHECK_ON_STARTUP
    _AUTO_UPDATE = True
except ImportError:
    __version__ = "1.0.0"
    CHECK_ON_STARTUP = False
    check_version_compliance = None
    check_for_updates = None
    _AUTO_UPDATE = False


class LoginWindow(QWidget):
    def __init__(self, app: QApplication) -> None:
        super().__init__()
        self.app       = app
        self.dashboard = None
        self._version_blocked = False
        self._service  = LoginService()

        self.setWindowTitle("Operation Report System")
        self.setFixedSize(820, 500)
        self.settings = QSettings("OperationReportSystem", "ORS")

        self._setup_ui()
        self._apply_styles()
        self._load_saved_credentials()
        self._center_window()
        self._enforce_version_policy()

        if self._version_blocked:
            return
        self._check_connection()

    # ── Version enforcement ────────────────────────────────────────────────────

    def _enforce_version_policy(self) -> None:
        if not _AUTO_UPDATE:
            return
        try:
            compliance = check_version_compliance(timeout=8)
        except Exception as exc:
            log.warning("Version policy check failed: %s", exc)
            return

        if compliance.get("check_failed") or compliance.get("compliant", True):
            return

        self._version_blocked = True
        latest  = compliance.get("latest_version", "?")
        current = compliance.get("current_version", __version__)

        for w in (self.username_input, self.password_input,
                  self.remember_checkbox, self.show_pw_checkbox):
            w.setEnabled(False)

        self._set_status(
            f"Update required: v{current}  →  v{latest}", "#e74c3c"
        )
        self.login_btn.setEnabled(True)
        self.login_btn.setText("Update Now")
        self.login_btn.setStyleSheet(
            "QPushButton{background:#e67e22;color:white;border-radius:6px;"
            "font-weight:bold;}QPushButton:hover{background:#d35400;}"
        )
        try:
            self.login_btn.clicked.disconnect()
        except Exception:
            pass
        self.login_btn.clicked.connect(self._do_update)

        msg = QMessageBox(self)
        msg.setIcon(QMessageBox.Warning)
        msg.setWindowTitle("Update Required")
        msg.setText(
            "This version of the app is no longer supported.\n\n"
            f"Current version:  v{current}\n"
            f"Latest version:   v{latest}\n\n"
            "Click 'Update Now' to download and install the latest version."
        )
        update_btn = msg.addButton("Update Now", QMessageBox.AcceptRole)
        msg.addButton("Later", QMessageBox.RejectRole)
        msg.exec_()
        if msg.clickedButton() is update_btn:
            self._do_update()

    def _do_update(self) -> None:
        if check_for_updates is None:
            QMessageBox.warning(self, "Update Error", "Auto-updater is not available.")
            return
        check_for_updates(parent=self, silent=True)

    # ── DB / offline status ───────────────────────────────────────────────────

    def _check_connection(self) -> None:
        if not _DB_AVAILABLE:
            return

        store = self._service._store
        if not db_manager.test_connection():
            if _OFFLINE_PENDING:
                _pending_store.is_offline = True
            if store.has_credentials():
                self._set_status("Offline Mode — using cached credentials", "#e67e22")
                QTimer.singleShot(100, lambda: QMessageBox.information(
                    self, "Offline Mode",
                    "No database connection.\n\n"
                    "You can log in with cached credentials.\n"
                    "Entries will be queued and synced when connection is restored.",
                ))
            else:
                self._set_status("Offline — no cached credentials", "#e74c3c")
                QTimer.singleShot(100, lambda: QMessageBox.warning(
                    self, "Connection Required",
                    "Cannot connect to database and no cached credentials exist.\n\n"
                    "Please connect to the network and log in at least once "
                    "to enable offline mode.",
                ))
        else:
            if _OFFLINE_PENDING:
                _pending_store.is_offline = False
            self._set_status("Connected to database", "#27ae60")
            QTimer.singleShot(3000, lambda: self.connection_status.setVisible(False))

    # ── Login ─────────────────────────────────────────────────────────────────

    def _attempt_login(self) -> None:
        if self._version_blocked:
            self._show("Update Required",
                       "Login is disabled — please update the app first.",
                       QMessageBox.Warning)
            return

        username = self.username_input.text().strip()
        password = self.password_input.text().strip()
        if not username or not password:
            self._show("Input Error",
                       "Please enter both username and password.",
                       QMessageBox.Warning)
            return

        self.login_btn.setEnabled(False)
        self.login_btn.setText("Logging in…")

        try:
            is_offline_forced = _DB_AVAILABLE and not db_manager.test_connection()

            if is_offline_forced:
                result = self._service.authenticate_offline(username, password)
            else:
                if _OFFLINE_PENDING:
                    _pending_store.is_offline = False
                result = self._service.authenticate(username, password)

            self._handle_result(result, username, password, is_offline_forced)
        except Exception as exc:
            log.error("Unexpected login error: %s", exc, exc_info=True)
            self._show("Error",
                       "An unexpected error occurred during login. Please try again.",
                       QMessageBox.Critical)
        finally:
            self.login_btn.setEnabled(True)
            self.login_btn.setText("Login")

    def _handle_result(
        self, result: AuthResult, username: str, password: str,
        was_offline: bool
    ) -> None:
        if not result.success:
            self._handle_failure(result)
            return

        if result.is_offline and result.role in ("admin", "super_admin"):
            self._show("Offline Mode Restricted",
                       "Admin users cannot use offline mode.\n\n"
                       "Please connect to the database to access admin features.",
                       QMessageBox.Warning)
            return

        # Inform user if they're in offline mode before opening dashboard
        if result.is_offline:
            pending_msg = ""
            if _OFFLINE_PENDING and hasattr(_pending_store, "get_pending_count"):
                n = _pending_store.get_pending_count(result.username)
                if n:
                    pending_msg = f"\n\nYou have {n} pending entries waiting to sync."
            self._show(
                "Offline Mode",
                f"Welcome, {result.username}! (Offline Mode)\n\n"
                f"Branch: {result.branch}\n"
                f"Corporation: {result.corporation}\n\n"
                f"Entries will be queued and synced when connection is restored.{pending_msg}",
                QMessageBox.Information,
            )

        self._save_credentials(result.username)

        splash = make_splash(result)
        splash.show()
        QApplication.processEvents()

        try:
            self.dashboard = open_dashboard(result)

            if self.dashboard is None:
                splash.close()
                self._show("Error",
                           "Failed to load dashboard. Check the logs for details.",
                           QMessageBox.Critical)
                return

            if hasattr(self.dashboard, "logout_requested"):
                self.dashboard.logout_requested.connect(self._handle_logout)

            self.dashboard.showMaximized()
            splash.close()
            self.hide()
        except Exception as exc:
            splash.close()
            log.error("Dashboard load error: %s", exc, exc_info=True)
            self._show("Error", f"Failed to load dashboard.\n{exc}", QMessageBox.Critical)

    def _handle_failure(self, result: AuthResult) -> None:
        if result.error_code == "locked":
            self._show(
                "Account Locked",
                f"Too many failed attempts.\n\n"
                f"Please wait {format_lockout_time(result.lockout_remaining)} before trying again.",
                QMessageBox.Warning,
            )
        elif result.error_code == "invalid_credentials" and result.attempts_remaining:
            self._show(
                "Login Failed",
                f"Incorrect username or password.\n{result.attempts_remaining} attempt(s) remaining.",
                QMessageBox.Warning,
            )
        elif result.error_code == "network":
            self._show("Connection Error", result.error_message, QMessageBox.Critical)
        else:
            self._show("Login Failed", result.error_message or "Login failed.", QMessageBox.Warning)

    # ── Logout / return ────────────────────────────────────────────────────────

    def _handle_logout(self) -> None:
        log.info("Logout — returning to login screen")
        if self.dashboard:
            self.dashboard.close()
            self.dashboard.deleteLater()
            self.dashboard = None
        self.password_input.clear()
        self.show_pw_checkbox.setChecked(False)
        self.show()
        self._center_window()
        self.raise_()
        self.activateWindow()

    # ── Credentials (remember me) ─────────────────────────────────────────────

    def _load_saved_credentials(self) -> None:
        saved = self.settings.value("username")
        if saved:
            self.username_input.setText(saved)
            self.remember_checkbox.setChecked(True)
            pw = self.settings.value("password")
            if pw:
                try:
                    self.password_input.setText(
                        base64.b64decode(pw.encode()).decode()
                    )
                except Exception:
                    pass

    def _save_credentials(self, username: str) -> None:
        if self.remember_checkbox.isChecked():
            self.settings.setValue("username", username)
            enc = base64.b64encode(self.password_input.text().encode()).decode()
            self.settings.setValue("password", enc)
        else:
            self.settings.remove("username")
            self.settings.remove("password")

    # ── UI helpers ────────────────────────────────────────────────────────────

    def _set_status(self, text: str, color: str = "#a0aec0") -> None:
        self.connection_status.setText(text)
        self.connection_status.setStyleSheet(f"color: {color}; font-weight: bold;")
        self.connection_status.setVisible(True)

    def _show(self, title: str, message: str, icon) -> None:
        QMessageBox(icon, title, message, QMessageBox.Ok, self).exec_()

    def _center_window(self) -> None:
        screen = self.app.desktop().screenGeometry()
        self.move(
            (screen.width()  - self.width())  // 2,
            (screen.height() - self.height()) // 2,
        )

    # ── Qt UI build ───────────────────────────────────────────────────────────

    def _setup_ui(self) -> None:
        main = QHBoxLayout()
        main.setContentsMargins(0, 0, 0, 0)
        main.setSpacing(0)

        # ── Left branding panel ───────────────────────────────────────────────
        left = QFrame()
        left.setObjectName("leftPanel")
        left.setFixedWidth(400)
        lv = QVBoxLayout(left)
        lv.setSpacing(20)
        lv.setContentsMargins(20, 20, 20, 20)
        lv.addStretch()

        logo = QLabel()
        logo_path = os.path.join(os.path.dirname(os.path.dirname(__file__)),
                                  "assets", "logo.ico")
        if os.path.exists(logo_path):
            px = QPixmap(logo_path)
            logo.setPixmap(
                px.scaled(80, 80, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            )
        else:
            logo.setText("📊")
            logo.setFont(QFont("Poppins", 48))
        logo.setAlignment(Qt.AlignCenter)
        lv.addWidget(logo)

        title = QLabel("OPERATION REPORT SYSTEM")
        title.setObjectName("brandTitle")
        title.setAlignment(Qt.AlignCenter)
        title.setFont(QFont("Poppins", 14, QFont.Bold))
        title.setWordWrap(True)
        lv.addWidget(title)

        lv.addStretch()
        credit = QLabel(
            '© 2026 <a href="#" '
            'style="color:rgba(255,255,255,0.75);text-decoration:none;">'
            'Paolo Somido</a>'
        )
        credit.setTextFormat(Qt.RichText)
        credit.setAlignment(Qt.AlignCenter)
        credit.setStyleSheet("font-size: 11px;")
        credit.setTextInteractionFlags(Qt.TextBrowserInteraction)
        credit.setOpenExternalLinks(True)
        lv.addWidget(credit)

        main.addWidget(left)

        # ── Right form panel ──────────────────────────────────────────────────
        right = QFrame()
        right.setObjectName("rightPanel")
        rv = QVBoxLayout(right)
        rv.setContentsMargins(60, 60, 60, 60)
        rv.setSpacing(15)

        welcome = QLabel("WELCOME")
        welcome.setObjectName("welcomeTitle")
        welcome.setAlignment(Qt.AlignCenter)
        welcome.setFont(QFont("Poppins", 24, QFont.Bold))
        rv.addWidget(welcome)
        rv.addSpacing(30)

        def _row(label_text: str, widget) -> QHBoxLayout:
            row = QHBoxLayout()
            lbl = QLabel(label_text)
            lbl.setObjectName("formLabel")
            lbl.setFixedWidth(100)
            lbl.setFont(QFont("Poppins", 11))
            row.addWidget(lbl)
            row.addWidget(widget)
            return row

        self.username_input = QLineEdit()
        self.username_input.setObjectName("formInput")
        self.username_input.setFixedHeight(40)
        rv.addLayout(_row("Username:", self.username_input))
        rv.addSpacing(10)

        self.password_input = QLineEdit()
        self.password_input.setObjectName("formInput")
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.setFixedHeight(40)
        rv.addLayout(_row("Password:", self.password_input))
        rv.addSpacing(10)

        chk_row = QHBoxLayout()
        chk_row.setSpacing(20)
        self.show_pw_checkbox = QCheckBox("Show Password")
        self.show_pw_checkbox.setObjectName("formCheckbox")
        self.show_pw_checkbox.toggled.connect(
            lambda c: self.password_input.setEchoMode(
                QLineEdit.Normal if c else QLineEdit.Password
            )
        )
        chk_row.addWidget(self.show_pw_checkbox)
        self.remember_checkbox = QCheckBox("Remember Me")
        self.remember_checkbox.setObjectName("formCheckbox")
        chk_row.addWidget(self.remember_checkbox)
        chk_row.addStretch()
        rv.addLayout(chk_row)
        rv.addSpacing(20)

        btn_row = QHBoxLayout()
        btn_row.addStretch()
        self.login_btn = QPushButton("Login")
        self.login_btn.setObjectName("loginButton")
        self.login_btn.setFixedSize(180, 45)
        self.login_btn.setCursor(Qt.PointingHandCursor)
        self.login_btn.clicked.connect(self._attempt_login)
        btn_row.addWidget(self.login_btn)
        btn_row.addStretch()
        rv.addLayout(btn_row)

        self.connection_status = QLabel("")
        self.connection_status.setObjectName("statusLabel")
        self.connection_status.setAlignment(Qt.AlignCenter)
        self.connection_status.setFont(QFont("Poppins", 9))
        self.connection_status.setVisible(False)
        rv.addWidget(self.connection_status)

        rv.addStretch()
        main.addWidget(right)
        self.setLayout(main)

    def _apply_styles(self) -> None:
        self.setStyleSheet("""
            QWidget { font-family: 'Poppins', 'Segoe UI', Arial, sans-serif; }

            #leftPanel  { background-color: #1E293B; border: none; }
            #brandTitle {
                color: #94A3B8;
                letter-spacing: 1.5px;
                padding: 0 20px;
                font-weight: 600;
                font-size: 11px;
            }

            #rightPanel   { background-color: #0F172A; border: none; }
            #welcomeTitle {
                color: #F1F5F9;
                letter-spacing: 3px;
                font-weight: 700;
                font-size: 24px;
            }
            #formLabel {
                color: #CBD5E1;
                font-weight: 500;
                font-size: 12px;
            }

            #formInput {
                padding: 11px 16px;
                border: 2px solid #334155;
                border-radius: 9px;
                font-family: 'Poppins', 'Segoe UI', Arial, sans-serif;
                font-size: 13px;
                font-weight: 500;
                background-color: #1E293B;
                color: #F1F5F9;
            }
            #formInput:focus {
                border-color: #38BDF8;
                background-color: #1E3A5F;
                color: #FFFFFF;
            }

            #formCheckbox {
                color: #94A3B8;
                font-size: 11px;
                spacing: 6px;
                font-weight: 500;
            }
            #formCheckbox::indicator {
                width: 14px; height: 14px; border-radius: 4px;
            }
            #formCheckbox::indicator:unchecked {
                border: 2px solid #475569; background-color: #1E293B;
            }
            #formCheckbox::indicator:checked {
                border: 2px solid #38BDF8; background-color: #0284C7;
            }

            #loginButton {
                background-color: #0284C7;
                color: #FFFFFF;
                border: none;
                border-radius: 24px;
                font-family: 'Poppins', 'Segoe UI', Arial, sans-serif;
                font-size: 14px;
                font-weight: 700;
                letter-spacing: 0.8px;
            }
            #loginButton:hover   { background-color: #0369A1; }
            #loginButton:pressed { background-color: #075985; }

            #statusLabel {
                color: #94A3B8;
                font-size: 11px;
                font-weight: 500;
            }
        """)

    # ── Qt overrides ──────────────────────────────────────────────────────────

    def keyPressEvent(self, event) -> None:
        if event.key() in (Qt.Key_Return, Qt.Key_Enter):
            self._attempt_login()
        super().keyPressEvent(event)

    def closeEvent(self, event) -> None:
        event.accept()
