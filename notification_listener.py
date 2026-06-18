"""
Client-side notification listener.
- Socket.IO WebSocket: instant delivery when connected to the same worker
- HTTP polling fallback: reliable delivery across all workers / after reconnect / when app was offline
"""

import logging
import time
import threading
from PyQt5.QtCore import QThread, pyqtSignal, QObject

logger = logging.getLogger(__name__)

_LONG_POLL_TIMEOUT = 25   # seconds the server holds the request open
_CONNECT_TIMEOUT  = 10   # seconds to establish the TCP connection


class NotificationSignals(QObject):
    """Qt signals for notifications."""
    entry_reset_signal = pyqtSignal(dict)
    connection_changed = pyqtSignal(bool)
    error_signal = pyqtSignal(str)


class NotificationListener(QThread):
    """
    Maintains a Socket.IO connection for instant notifications AND polls
    an HTTP endpoint every POLL_INTERVAL seconds as a reliable fallback.

    The polling fallback handles:
    - Multi-worker Gunicorn (Socket.IO only reaches one worker's clients)
    - Worker auto-restart (brief disconnect window)
    - Client was offline when admin reset happened
    """

    def __init__(self, api_url: str, branch: str, parent=None):
        super().__init__(parent)
        self.api_url = api_url.rstrip("/")
        self.branch = branch
        self.signals = NotificationSignals()
        self._sio = None
        self._running = True
        self._connected = False
        self._token = None
        self._poll_thread = None
        self._http_session = None   # shared requests.Session — closed on stop() to interrupt poll
        self.daemon = True

    # ── Capability check ─────────────────────────────────────────────────────

    def _server_has_socketio(self) -> bool:
        """Ask the server once whether Socket.IO is enabled."""
        try:
            import requests
            resp = requests.get(
                f"{self.api_url}/api/notify/capabilities", timeout=5
            )
            if resp.status_code == 200:
                return resp.json().get("socketio", False)
        except Exception:
            pass
        return False

    # ── Socket.IO connection ──────────────────────────────────────────────────

    def run(self):
        """Main thread: check capabilities, then run Socket.IO loop if available."""
        self._start_poll_thread()

        if not self._server_has_socketio():
            logger.info("[Notify] Server has Socket.IO disabled — using HTTP polling only")
            # Stay alive so the poll thread keeps running
            while self._running:
                time.sleep(1)
            return

        logger.info("[Notify] Socket.IO available — starting WebSocket listener")
        while self._running:
            try:
                import socketio

                self._sio = socketio.Client(
                    reconnection=True,
                    reconnection_delay=2,
                    reconnection_delay_max=30,
                    reconnection_attempts=0,  # 0 = unlimited internal retries
                    ssl_verify=False,
                    logger=False,
                    engineio_logger=False,
                )

                @self._sio.on("connect")
                def on_connect():
                    logger.info("[Notify] Socket.IO connected")
                    self._connected = True
                    self.signals.connection_changed.emit(True)
                    self._sio.emit("register_branch", {"branch": self.branch})

                @self._sio.on("disconnect")
                def on_disconnect():
                    logger.info("[Notify] Socket.IO disconnected (will reconnect)")
                    self._connected = False
                    self.signals.connection_changed.emit(False)

                @self._sio.on("entry_reset")
                def on_entry_reset(data):
                    logger.info(f"[Notify] entry_reset via Socket.IO: {data}")
                    self.signals.entry_reset_signal.emit(data)

                @self._sio.on("register_success")
                def on_register_success(data):
                    logger.debug(f"[Notify] Registered for branch: {data.get('branch')}")

                logger.info(f"[Notify] Connecting to {self.api_url}")
                self._sio.connect(
                    self.api_url,
                    transports=["websocket", "polling"],
                    wait_timeout=10,
                )
                self._sio.wait()

            except Exception as e:
                if not self._running:
                    break
                logger.warning(f"[Notify] Socket.IO error: {e} — retrying in 10s")
                time.sleep(10)

        logger.info("[Notify] Socket.IO listener stopped")

    # ── HTTP polling fallback ─────────────────────────────────────────────────

    def _start_poll_thread(self):
        """Start background thread that polls /api/notify/pending."""
        self._poll_thread = threading.Thread(target=self._poll_loop, daemon=True)
        self._poll_thread.start()

    def _poll_loop(self):
        """Long-poll loop — reconnects immediately after each response.

        The server holds each request open for up to _LONG_POLL_TIMEOUT seconds,
        checking the DB every 500 ms. As soon as a notification is written the
        server returns it, so delivery latency is under 1 second.

        On slow / broken connections the request times out after _CONNECT_TIMEOUT +
        _LONG_POLL_TIMEOUT seconds and the loop retries — the UI is never affected
        because this runs in a background daemon thread.
        """
        # Let the app finish auth before the first request
        time.sleep(5)
        while self._running:
            try:
                self._poll_pending()
            except Exception as e:
                logger.debug(f"[Notify] Poll error: {e}")
                # Brief back-off on repeated failures so we don't hammer the server
                for _ in range(5):
                    if not self._running:
                        break
                    time.sleep(1)

    def _poll_pending(self):
        """Single long-poll request to the server."""
        import requests
        if not self._running:
            return

        token = self._get_token()
        if not token:
            return

        # Reuse a persistent session so we can close it from stop() to interrupt
        # a blocking request without waiting for the full read timeout to expire.
        if self._http_session is None:
            self._http_session = requests.Session()

        # (connect_timeout, read_timeout) — read timeout must exceed the server's
        # long-poll hold time so we don't disconnect before the server responds.
        req_timeout = (_CONNECT_TIMEOUT, _LONG_POLL_TIMEOUT + 5)

        def _get(tok):
            return self._http_session.get(
                f"{self.api_url}/api/notify/pending",
                params={"branch": self.branch, "timeout": _LONG_POLL_TIMEOUT},
                headers={"Authorization": f"Bearer {tok}"},
                timeout=req_timeout,
            )

        resp = _get(token)
        if resp.status_code == 401:
            self._token = None
            token = self._get_token()
            if not token:
                return
            resp = _get(token)

        if resp.status_code == 200:
            notifications = resp.json().get("notifications", [])
            for notif in notifications:
                logger.info(f"[Notify] entry_reset via poll: {notif}")
                self.signals.entry_reset_signal.emit(notif)

    def _get_token(self) -> str:
        """Obtain a JWT for API calls. Returns cached value; clears on 401."""
        if self._token:
            return self._token
        try:
            import requests
            from api_config import API_URL, API_KEY
            resp = requests.post(
                f"{API_URL}/api/token",
                json={"api_key": API_KEY},
                timeout=5,
            )
            if resp.status_code == 200:
                self._token = resp.json().get("token")
                return self._token
        except Exception as e:
            logger.debug(f"[Notify] Token fetch failed: {e}")
        return None

    # ── Lifecycle ─────────────────────────────────────────────────────────────

    def stop(self):
        """Stop both Socket.IO and the poll thread."""
        self._running = False
        self._token = None
        # Close the HTTP session — this immediately aborts any blocking requests.get()
        # call in the poll thread so it exits within milliseconds instead of waiting
        # for the full read timeout (up to 30 s) to expire.
        if self._http_session is not None:
            try:
                self._http_session.close()
            except Exception:
                pass
            self._http_session = None
        try:
            if self._sio and self._sio.connected:
                self._sio.disconnect()
        except Exception:
            pass

    def is_connected(self) -> bool:
        return self._connected and bool(self._sio and self._sio.connected)


class ToastNotification:
    """Frameless always-on-top toast popup, auto-dismisses after `duration` ms."""

    def __init__(self, title: str, message: str, duration: int = 8000):
        from PyQt5.QtWidgets import QWidget, QLabel, QVBoxLayout
        from PyQt5.QtCore import Qt, QTimer
        from PyQt5.QtGui import QFont

        self.widget = QWidget()
        self.widget.setWindowTitle(title)
        self.widget.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.widget.setStyleSheet("""
            QWidget {
                background-color: #2c3e50;
                border: 2px solid #3498db;
                border-radius: 8px;
                padding: 15px;
            }
            QLabel { color: white; }
        """)

        layout = QVBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)

        title_lbl = QLabel(title)
        f = QFont()
        f.setPointSize(11)
        f.setBold(True)
        title_lbl.setFont(f)
        layout.addWidget(title_lbl)

        msg_lbl = QLabel(message)
        msg_lbl.setWordWrap(True)
        msg_lbl.setMaximumWidth(400)
        layout.addWidget(msg_lbl)

        self.widget.setLayout(layout)

        self._timer = QTimer()
        self._timer.setSingleShot(True)
        self._timer.timeout.connect(self.hide)
        self._timer.start(duration)

    def show(self):
        from PyQt5.QtWidgets import QApplication
        screen = QApplication.primaryScreen().availableGeometry()
        self.widget.move(screen.right() - 460, screen.bottom() - 220)
        self.widget.show()

    def hide(self):
        self.widget.hide()
        self.widget.close()
