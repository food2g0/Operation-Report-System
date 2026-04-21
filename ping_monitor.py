"""
Ping Monitor — logs user login sessions and periodic DB ping latency.

Table: user_ping_logs (one row per login session)
  id           INT AUTO_INCREMENT PK
  username     VARCHAR(255)
  role         VARCHAR(50)
  hostname     VARCHAR(255)
  login_time   DATETIME  -- when they logged in
  last_seen    DATETIME  -- updated every 5 minutes while active
  last_ping_ms INT       -- latest ping latency (-1 = failed)
  logout_time  DATETIME  -- set on logout (NULL = still active)
"""

import socket
import time
from datetime import datetime

from PyQt5.QtCore import Qt, QTimer, QObject
from PyQt5.QtGui import QColor, QFont
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QComboBox, QFrame,
)


_PING_INTERVAL_MS  = 300_000    # update every 5 minutes (safe for 600+ users)
_PURGE_INTERVAL_MS = 3_600_000  # purge every 1 hour, no login needed


class PingMonitor(QObject):
    """
    Module-level singleton monitor.  Call start() on login, stop() on logout.
    All DB writes are fire-and-forget; failures are silently printed so
    they never break normal app flow.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._do_ping)
        self._purge_timer = QTimer(self)
        self._purge_timer.timeout.connect(self._auto_purge)
        self._purge_timer.start(_PURGE_INTERVAL_MS)  # runs every hour, no login needed
        self._username = None
        self._role = None
        self._hostname = self._get_hostname()
        self._db = None
        self._session_id = None  # PK of the current session row
        self._ip_address = self._get_ip_address()

    # ── Public API ────────────────────────────────────────────────────────

    def start(self, db_manager, username: str, role: str = 'user'):
        """Call immediately after a successful login."""
        self._db = db_manager
        self._username = username
        self._role = role
        self._session_id = None

        self._ensure_table()
        self._session_id = self._create_session()

        self._timer.start(_PING_INTERVAL_MS)
        print(f"[PingMonitor] Started for {username} ({role})")

    def stop(self):
        """Call on logout or window close."""
        if self._timer.isActive():
            self._timer.stop()

        if self._session_id:
            self._close_session()
            print(f"[PingMonitor] Stopped for {self._username}")

        self._username = None
        self._role = None
        self._db = None
        self._session_id = None

    # ── Internal ──────────────────────────────────────────────────────────

    def _create_session(self):
        """Close any stale open sessions, then INSERT a new session row and return its id."""
        if not self._db:
            return None
        try:
            now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            # Mark any previous open sessions for this user+hostname as closed
            # (handles crash / closed-without-logout scenarios)
            self._db.execute_query(
                "UPDATE user_ping_logs SET logout_time=%s "
                "WHERE username=%s AND hostname=%s AND logout_time IS NULL",
                (now, self._username, self._hostname)
            )
            self._db.execute_query(
                """INSERT INTO user_ping_logs
                       (username, role, hostname, ip_address, login_time, last_seen)
                   VALUES (%s, %s, %s, %s, %s, %s)""",
                (self._username, self._role, self._hostname, self._ip_address, now, now)
            )
            result = self._db.execute_query("SELECT LAST_INSERT_ID() AS id")
            if result:
                return result[0]['id']
        except Exception as e:
            print(f"[PingMonitor] Session create failed: {e}")
        return None

    def _do_ping(self):
        if not self._db or not self._session_id:
            return
        try:
            t0 = time.perf_counter()
            self._db.execute_query("SELECT 1")
            ping_ms = int((time.perf_counter() - t0) * 1000)
        except Exception as e:
            print(f"[PingMonitor] DB ping failed: {e}")
            ping_ms = -1

        try:
            now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            self._db.execute_query(
                "UPDATE user_ping_logs SET last_seen=%s, last_ping_ms=%s WHERE id=%s",
                (now, ping_ms, self._session_id)
            )
        except Exception as e:
            print(f"[PingMonitor] Ping update failed: {e}")

    def _close_session(self):
        if not self._db or not self._session_id:
            return
        try:
            now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            self._db.execute_query(
                "UPDATE user_ping_logs SET logout_time=%s WHERE id=%s",
                (now, self._session_id)
            )
        except Exception as e:
            print(f"[PingMonitor] Session close failed: {e}")

    def _auto_purge(self):
        """Delete previous-day rows every hour, no login required."""
        if not self._db:
            return
        try:
            self._db.execute_query(
                "DELETE FROM user_ping_logs WHERE login_time < CURDATE()"
            )
        except Exception as e:
            print(f"[PingMonitor] Auto-purge failed: {e}")

    def _ensure_table(self):
        if not self._db:
            return
        try:
            self._db.execute_query("""
                CREATE TABLE IF NOT EXISTS user_ping_logs (
                    id           INT AUTO_INCREMENT PRIMARY KEY,
                    username     VARCHAR(255) NOT NULL,
                    role         VARCHAR(50)  NOT NULL DEFAULT 'user',
                    hostname     VARCHAR(255) DEFAULT NULL,
                    ip_address   VARCHAR(45)  DEFAULT NULL,
                    login_time   DATETIME     NOT NULL,
                    last_seen    DATETIME     NOT NULL,
                    last_ping_ms INT          DEFAULT NULL,
                    logout_time  DATETIME     DEFAULT NULL,
                    INDEX idx_upl_user_login (username, login_time)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
            """)
            # Migrate old schema if table existed with different columns
            self._migrate_table()
            self._auto_purge()
        except Exception as e:
            print(f"[PingMonitor] Table create failed: {e}")

    def _migrate_table(self):
        """Drop and recreate the table if it still has the old schema."""
        if not self._db:
            return
        try:
            # Use INFORMATION_SCHEMA so execute_query returns rows (SELECT path)
            cols = self._db.execute_query(
                "SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS "
                "WHERE TABLE_NAME = 'user_ping_logs' "
                "AND TABLE_SCHEMA = DATABASE()"
            )
            col_names = {row['COLUMN_NAME'] for row in cols} if cols else set()
            if 'login_time' not in col_names or 'ip_address' not in col_names:
                # Old schema detected — safe to drop since data is purged daily
                self._db.execute_query("DROP TABLE user_ping_logs")
                self._db.execute_query("""
                    CREATE TABLE user_ping_logs (
                        id           INT AUTO_INCREMENT PRIMARY KEY,
                        username     VARCHAR(255) NOT NULL,
                        role         VARCHAR(50)  NOT NULL DEFAULT 'user',
                        hostname     VARCHAR(255) DEFAULT NULL,
                        ip_address   VARCHAR(45)  DEFAULT NULL,
                        login_time   DATETIME     NOT NULL,
                        last_seen    DATETIME     NOT NULL,
                        last_ping_ms INT          DEFAULT NULL,
                        logout_time  DATETIME     DEFAULT NULL,
                        INDEX idx_upl_user_login (username, login_time)
                    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
                """)
                print("[PingMonitor] Table migrated to new schema.")
        except Exception as e:
            print(f"[PingMonitor] Migration failed: {e}")

    @staticmethod
    def _get_hostname() -> str:
        try:
            return socket.gethostname()
        except Exception:
            return 'unknown'

    @staticmethod
    def _get_ip_address() -> str:
        # Try to get the public IP from external services (with short timeout)
        for url in (
            'https://api.ipify.org',
            'https://ifconfig.me/ip',
            'https://checkip.amazonaws.com',
        ):
            try:
                import requests as _req
                resp = _req.get(url, timeout=3)
                ip = resp.text.strip()
                if ip:
                    return ip
            except Exception:
                continue
        # Fallback: local outbound IP if all public lookups fail
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
                s.connect(('8.8.8.8', 80))
                return s.getsockname()[0]
        except Exception:
            return 'unknown'


# Module-level singleton instance (safe to import anywhere)
ping_monitor = PingMonitor()


# ── Monitor Window ────────────────────────────────────────────────────────────

class PingMonitorWindow(QDialog):
    """
    Floating window that shows live user_ping_logs.
    Opens from the super admin dashboard header button.
    Auto-refreshes every 15 seconds while open.

    Color coding:
      Green  = session still active (no logout yet)
      Red    = logged out OR failed ping (-1)
      Yellow = slow ping (>500 ms)
    """

    _COLUMNS = ["Username", "Role", "IP Address", "Hostname", "Login Time", "Last Seen", "Last Ping (ms)", "Logout Time"]
    _AUTO_REFRESH_MS = 15_000

    def __init__(self, db_manager, parent=None):
        super().__init__(parent)
        self._db = db_manager
        self.setWindowTitle("Ping / Connection Monitor")
        self.resize(1000, 550)
        self.setWindowFlags(self.windowFlags() | Qt.Window)
        self._build_ui()

        self._refresh_timer = QTimer(self)
        self._refresh_timer.timeout.connect(self.load_logs)
        self._refresh_timer.start(self._AUTO_REFRESH_MS)

        self.load_logs()

    # ── UI ──────────────────────────────────────────────────────────────

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(12, 12, 12, 12)
        root.setSpacing(8)

        # ── toolbar ──
        toolbar = QHBoxLayout()

        lbl = QLabel("User Connection Log")
        lbl.setFont(QFont("Arial", 12, QFont.Bold))
        toolbar.addWidget(lbl)

        toolbar.addStretch()

        # limit rows
        toolbar.addWidget(QLabel("Show last:"))
        self._limit_cb = QComboBox()
        self._limit_cb.addItems(["50", "100", "200", "500"])
        self._limit_cb.currentTextChanged.connect(self.load_logs)
        toolbar.addWidget(self._limit_cb)

        refresh_btn = QPushButton("Refresh Now")
        refresh_btn.setStyleSheet(
            "QPushButton{background:#2980b9;color:white;border:none;"
            "padding:6px 14px;border-radius:4px;font-weight:bold;}"
            "QPushButton:hover{background:#3498db;}"
        )
        refresh_btn.clicked.connect(self.load_logs)
        toolbar.addWidget(refresh_btn)

        root.addLayout(toolbar)

        # ── legend ──
        legend = QHBoxLayout()
        for color, text in [
            ("#d5f5e3", "Active session"),
            ("#fde8e8", "Logged out / ping failed"),
            ("#fef9e7", "Slow ping (>500ms)"),
        ]:
            dot = QLabel("  ")
            dot.setStyleSheet(f"background:{color};border:1px solid #ccc;border-radius:3px;")
            dot.setFixedSize(18, 18)
            legend.addWidget(dot)
            legend.addWidget(QLabel(text))
            legend.addSpacing(12)
        legend.addStretch()
        root.addLayout(legend)

        # ── status bar ──
        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setFrameShadow(QFrame.Sunken)
        root.addWidget(sep)

        self._status_lbl = QLabel("Loading…")
        self._status_lbl.setStyleSheet("color: #555; font-size: 11px;")
        root.addWidget(self._status_lbl)

        # ── table ──
        self._table = QTableWidget()
        self._table.setColumnCount(len(self._COLUMNS))
        self._table.setHorizontalHeaderLabels(self._COLUMNS)
        self._table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self._table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self._table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeToContents)
        self._table.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeToContents)
        self._table.horizontalHeader().setSectionResizeMode(6, QHeaderView.ResizeToContents)
        self._table.verticalHeader().setVisible(False)
        self._table.setEditTriggers(QTableWidget.NoEditTriggers)
        self._table.setSelectionBehavior(QTableWidget.SelectRows)
        self._table.setAlternatingRowColors(True)
        self._table.setStyleSheet(
            "QTableWidget{font-size:12px;}"
            "QHeaderView::section{background:#2c3e50;color:white;"
            "padding:6px;font-weight:bold;}"
        )
        root.addWidget(self._table)

    # ── Data ────────────────────────────────────────────────────────────

    def load_logs(self):
        limit = int(self._limit_cb.currentText())
        sql = (
            "SELECT username, role, ip_address, hostname, login_time, last_seen, "
            "last_ping_ms, logout_time "
            "FROM user_ping_logs ORDER BY login_time DESC LIMIT %s"
        )
        try:
            rows = self._db.execute_query(sql, (limit,)) or []
        except Exception as e:
            self._status_lbl.setText(f"Error loading logs: {e}")
            return

        self._table.setRowCount(len(rows))
        for r, row in enumerate(rows):
            ping_ms = row.get('last_ping_ms')
            logout  = row.get('logout_time')
            values = [
                row.get('username', ''),
                row.get('role', ''),
                row.get('ip_address', '') or '—',
                row.get('hostname', ''),
                str(row.get('login_time', '')),
                str(row.get('last_seen', '')),
                str(ping_ms) if ping_ms is not None else '—',
                str(logout)  if logout  is not None else 'Active',
            ]
            for c, val in enumerate(values):
                item = QTableWidgetItem(val)
                item.setTextAlignment(Qt.AlignCenter)

                if logout is None:
                    item.setBackground(QColor("#d5f5e3"))   # green = still active
                elif ping_ms is not None and ping_ms < 0:
                    item.setBackground(QColor("#fde8e8"))   # red = failed ping
                elif ping_ms is not None and ping_ms > 500:
                    item.setBackground(QColor("#fef9e7"))   # yellow = slow

                self._table.setItem(r, c, item)

        now = datetime.now().strftime('%H:%M:%S')
        active = sum(1 for row in rows if row.get('logout_time') is None)
        self._status_lbl.setText(
            f"{len(rows)} session(s) — {active} currently active — "
            f"last refreshed {now} (auto-refresh every {self._AUTO_REFRESH_MS // 1000}s)"
        )

    def closeEvent(self, event):
        self._refresh_timer.stop()
        super().closeEvent(event)
