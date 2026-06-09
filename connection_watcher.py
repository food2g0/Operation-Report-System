"""
connection_watcher.py
─────────────────────
Reusable network connectivity monitor for client and admin dashboards.

Usage
-----
    from connection_watcher import ConnectionWatcher, ConnectionBanner

    # 1. Create watcher (pass your db_manager)
    self._conn_watcher = ConnectionWatcher(db_manager)
    self._conn_watcher.connection_lost.connect(self._on_connection_lost)
    self._conn_watcher.connection_restored.connect(self._on_connection_restored)
    self._conn_watcher.start()

    # 2. Add banner to your layout (hidden until connection drops)
    self._conn_banner = ConnectionBanner()
    your_layout.addWidget(self._conn_banner)

    # 3. Wire the signals
    def _on_connection_lost(self):
        self._is_connected = False
        self._conn_banner.show_banner()

    def _on_connection_restored(self):
        self._is_connected = True
        self._conn_banner.hide_banner()
"""

import time
import logging

from PyQt5.QtCore import QObject, QTimer, QRunnable, QThreadPool, pyqtSignal, Qt
from PyQt5.QtWidgets import QLabel, QHBoxLayout, QWidget, QPushButton

logger = logging.getLogger(__name__)


class _PingWorkerSignals(QObject):
    result = pyqtSignal(bool)   # True = online, False = offline


class _PingWorker(QRunnable):
    """Runs a socket check in the global thread pool — zero GIL contention
    with the main thread, no persistent background thread."""

    TIMEOUT = 0.5

    def __init__(self):
        super().__init__()
        self.signals = _PingWorkerSignals()
        self.setAutoDelete(True)

    def run(self):
        from network_safety import safe_socket_check
        # Use safer timeout handling
        ok = safe_socket_check(host="8.8.8.8", port=53, timeout=self.TIMEOUT)
        self.signals.result.emit(ok)


class ConnectionWatcher(QObject):
    """
    Non-blocking connectivity monitor.

    Uses QTimer + QThreadPool instead of a persistent QThread.
    The socket check runs in the thread pool so it NEVER touches the
    main thread or the GIL during I/O — no UI lag at all.

    Emits connection_lost / connection_restored at most once per transition.
    """

    connection_lost     = pyqtSignal()
    connection_restored = pyqtSignal()

    CHECK_INTERVAL_MS = 3000   # ms between checks

    def __init__(self, db_manager, parent=None):
        super().__init__(parent)
        self._db          = db_manager
        self._last_state  = True          # assume connected at start
        self._pending     = False         # prevent overlapping checks
        self._timer       = QTimer(self)
        self._timer.timeout.connect(self._schedule_check)

    def start(self):
        self._timer.start(self.CHECK_INTERVAL_MS)

    def stop(self):
        self._timer.stop()

    def _schedule_check(self):
        if self._pending:
            return   # previous check still running, skip
        self._pending = True
        worker = _PingWorker()
        worker.signals.result.connect(self._on_result)
        QThreadPool.globalInstance().start(worker)

    def _on_result(self, ok: bool):
        self._pending = False
        if ok and not self._last_state:
            self._last_state = True
            self.connection_restored.emit()
            logger.info("ConnectionWatcher: connection restored")
        elif not ok and self._last_state:
            self._last_state = False
            self.connection_lost.emit()
            logger.warning("ConnectionWatcher: connection lost")


class ConnectionBanner(QWidget):
    """
    Red banner shown at the top of the window when the connection is lost.
    Hidden by default — call show_banner() / hide_banner() to toggle.

    Usage:
        self._conn_banner = ConnectionBanner()
        layout.insertWidget(0, self._conn_banner)   # insert at top
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        # Required for QWidget subclasses to paint stylesheet backgrounds
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setVisible(False)
        self.setFixedHeight(40)
        self.setObjectName("ConnectionBanner")
        self.setStyleSheet("""
            QWidget#ConnectionBanner {
                background-color: #c0392b;
            }
        """)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 0, 16, 0)
        layout.setSpacing(12)

        icon = QLabel("⚠")
        icon.setStyleSheet("color: white; font-size: 16px; background: transparent;")
        icon.setFixedWidth(20)

        self._label = QLabel(
            "No internet connection — please check your network."
        )
        self._label.setStyleSheet(
            "color: white; font-weight: bold; font-size: 12px; background: transparent;"
        )
        self._label.setAlignment(Qt.AlignVCenter | Qt.AlignLeft)

        self._retry_btn = QPushButton("↺  Retry")
        self._retry_btn.setFixedSize(80, 26)
        self._retry_btn.setCursor(Qt.PointingHandCursor)
        self._retry_btn.setStyleSheet("""
            QPushButton {
                background: rgba(255,255,255,0.22);
                color: white;
                border: 1px solid rgba(255,255,255,0.55);
                border-radius: 4px;
                font-size: 11px;
                font-weight: bold;
                padding: 0 8px;
            }
            QPushButton:hover  { background: rgba(255,255,255,0.38); }
            QPushButton:pressed{ background: rgba(255,255,255,0.15); }
        """)

        layout.addWidget(icon)
        layout.addWidget(self._label, 1)
        layout.addWidget(self._retry_btn)

    # ── Public API ─────────────────────────────────────────────────────────

    def show_banner(self):
        self.setVisible(True)
        self.update()          # force repaint

    def hide_banner(self):
        self.setVisible(False)

    def set_message(self, text: str):
        self._label.setText(text)

    @property
    def retry_btn(self):
        """Direct access to the Retry button for connecting custom slots."""
        return self._retry_btn
