"""
Game-style update launcher shown at app startup.
Checks GitHub for a new release → downloads with live progress → installs silently.
If already up to date, shows "Launching…" and emits launch_ready immediately.
"""

import os
import sys
import time
import tempfile
import subprocess

from PyQt5.QtWidgets import QWidget, QLabel, QProgressBar, QApplication, QFrame
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QTimer, QPropertyAnimation, QRect, QEasingCurve
from PyQt5.QtGui import QFont, QColor, QPainter, QLinearGradient, QPen, QBrush

try:
    from version import __version__ as CURRENT_VERSION, GITHUB_REPO
except ImportError:
    CURRENT_VERSION = "1.0.0"
    GITHUB_REPO = "food2g0/Operation-Report-System"

from auto_updater import (
    _create_retry_session,
    _is_trusted_download_url,
    _validate_downloaded_installer,
    _save_pre_update_version,
    REQUIRE_CHECKSUM,
    _find_release_checksum,
    _sha256_file,
)

try:
    from packaging import version as pkg_version
except ImportError:
    pkg_version = None


def _version_gt(a, b):
    if pkg_version:
        return pkg_version.parse(a) > pkg_version.parse(b)
    return tuple(int(x) for x in a.split(".")) > tuple(int(x) for x in b.split("."))


# ── Colour palette (game-launcher dark theme) ─────────────────────────────────
_BG         = "#0d1117"
_CARD       = "#161b22"
_BORDER     = "#30363d"
_ACCENT1    = "#58a6ff"
_ACCENT2    = "#1f6feb"
_TEXT_PRI   = "#e6edf3"
_TEXT_SEC   = "#8b949e"
_SUCCESS    = "#3fb950"
_ERROR      = "#f85149"
_WARNING    = "#d29922"
_BAR_BG     = "#21262d"


class _UpdateWorker(QThread):
    """Checks for an update, downloads it, emits progress signals."""

    status_changed   = pyqtSignal(str)         # human-readable status line
    sub_status       = pyqtSignal(str)          # smaller detail line
    progress_changed = pyqtSignal(int, int)     # (bytes_done, bytes_total)
    no_update        = pyqtSignal()
    ready_to_install = pyqtSignal(str, str)     # (installer_path, new_version)
    failed           = pyqtSignal(str)          # error message — proceed to login anyway

    def run(self):
        try:
            self.status_changed.emit("Checking for updates…")
            self.sub_status.emit(f"Current version: v{CURRENT_VERSION}")

            session = _create_retry_session()
            api_url = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"
            resp = session.get(api_url, timeout=10)

            if resp.status_code != 200:
                self.failed.emit(f"Update check failed (HTTP {resp.status_code})")
                return

            data = resp.json()
            latest = data.get("tag_name", "").lstrip("v").strip()

            if not latest:
                self.failed.emit("Could not read latest version tag.")
                return

            if not _version_gt(latest, CURRENT_VERSION):
                self.no_update.emit()
                return

            # ── Find installer asset ───────────────────────────────────────
            download_url = None
            installer_filename = None
            for asset in data.get("assets", []):
                name = asset.get("name", "").lower()
                if name.endswith(".exe") and any(k in name for k in ("setup", "installer", "ors")):
                    download_url = asset.get("browser_download_url")
                    installer_filename = asset.get("name")
                    break
            if not download_url:
                for asset in data.get("assets", []):
                    if asset.get("name", "").lower().endswith(".exe"):
                        download_url = asset.get("browser_download_url")
                        installer_filename = asset.get("name")
                        break

            if not download_url or not _is_trusted_download_url(download_url):
                self.failed.emit("No trusted installer found in release.")
                return

            # ── Download ───────────────────────────────────────────────────
            self.status_changed.emit(f"Downloading v{latest}…")
            self.sub_status.emit("Please wait while the update is being downloaded.")

            filename = installer_filename or f"ORS_Update_v{latest}.exe"
            dest = os.path.join(tempfile.gettempdir(), filename)
            partial = dest + ".part"

            resp2 = session.get(download_url, stream=True, timeout=120)
            resp2.raise_for_status()
            total = int(resp2.headers.get("content-length", 0))
            done = 0
            t0 = time.time()

            with open(partial, "wb") as f:
                for chunk in resp2.iter_content(chunk_size=65536):
                    if chunk:
                        f.write(chunk)
                        done += len(chunk)
                        self.progress_changed.emit(done, total)

            os.replace(partial, dest)

            # Size check
            if total and os.path.getsize(dest) != total:
                self.failed.emit("Download incomplete — file size mismatch.")
                return

            # Checksum
            expected_cs = _find_release_checksum(session, data, filename)
            if expected_cs:
                actual_cs = _sha256_file(dest)
                if actual_cs.lower() != expected_cs.lower():
                    self.failed.emit("Checksum verification failed.")
                    return
            elif REQUIRE_CHECKSUM:
                self.failed.emit("Checksum required but not found in release.")
                return

            # Basic integrity
            ok, reason = _validate_downloaded_installer(dest)
            if not ok:
                self.failed.emit(reason)
                return

            self.status_changed.emit("Installing update…")
            self.sub_status.emit("The application will restart automatically.")
            self.ready_to_install.emit(dest, latest)

        except Exception as exc:
            self.failed.emit(str(exc))


class UpdateLauncherWindow(QWidget):
    """
    Full-screen-style launcher shown before login.
    Looks like a game update/patch screen.
    Emits `launch_ready` when the app should proceed to login.
    """

    launch_ready = pyqtSignal()

    _W, _H = 720, 420

    def __init__(self, app_version=CURRENT_VERSION):
        super().__init__()
        self._app_version = app_version
        self._worker = None
        self._anim_dots = 0
        self._anim_timer = QTimer(self)
        self._anim_timer.timeout.connect(self._tick_dots)
        self._speed_bytes = 0
        self._last_done = 0
        self._last_t = time.time()

        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setFixedSize(self._W, self._H)

        screen = QApplication.primaryScreen().geometry()
        self.move(
            (screen.width()  - self._W) // 2,
            (screen.height() - self._H) // 2,
        )

        self._build_ui()

    # ── UI construction ────────────────────────────────────────────────────────

    def _build_ui(self):
        # Card
        card = QFrame(self)
        card.setGeometry(10, 10, self._W - 20, self._H - 20)
        card.setObjectName("card")
        card.setStyleSheet(f"""
            QFrame#card {{
                background-color: {_CARD};
                border-radius: 14px;
                border: 1px solid {_BORDER};
            }}
        """)

        # Top accent bar
        accent_bar = QFrame(card)
        accent_bar.setGeometry(0, 0, self._W - 20, 5)
        accent_bar.setStyleSheet(f"""
            QFrame {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {_ACCENT2}, stop:1 {_ACCENT1});
                border-top-left-radius: 14px;
                border-top-right-radius: 14px;
                border: none;
            }}
        """)

        cx = self._W - 20  # card width

        # App badge / icon text
        badge = QLabel("ORS", card)
        badge.setGeometry(0, 30, cx, 52)
        badge.setAlignment(Qt.AlignCenter)
        badge.setStyleSheet(f"""
            QLabel {{
                color: {_ACCENT1};
                font-size: 44px;
                font-weight: 900;
                font-family: 'Segoe UI', 'Arial Black', sans-serif;
                background: transparent;
                letter-spacing: 6px;
            }}
        """)

        # App title
        title = QLabel("Operation Report System", card)
        title.setGeometry(0, 85, cx, 28)
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet(f"""
            QLabel {{
                color: {_TEXT_PRI};
                font-size: 18px;
                font-weight: 600;
                font-family: 'Segoe UI', Arial, sans-serif;
                background: transparent;
            }}
        """)

        # Version badge
        self._ver_label = QLabel(f"v{self._app_version}", card)
        self._ver_label.setGeometry(0, 114, cx, 18)
        self._ver_label.setAlignment(Qt.AlignCenter)
        self._ver_label.setStyleSheet(f"""
            QLabel {{
                color: {_TEXT_SEC};
                font-size: 11px;
                font-family: 'Segoe UI', Arial, sans-serif;
                background: transparent;
            }}
        """)

        # Separator line
        sep = QFrame(card)
        sep.setGeometry(40, 145, cx - 80, 1)
        sep.setStyleSheet(f"QFrame {{ background-color: {_BORDER}; }}")

        # Status label (big)
        self._status_lbl = QLabel("Initializing…", card)
        self._status_lbl.setGeometry(0, 160, cx, 28)
        self._status_lbl.setAlignment(Qt.AlignCenter)
        self._status_lbl.setStyleSheet(f"""
            QLabel {{
                color: {_TEXT_PRI};
                font-size: 15px;
                font-weight: 600;
                font-family: 'Segoe UI', Arial, sans-serif;
                background: transparent;
            }}
        """)

        # Sub-status label (small detail)
        self._sub_lbl = QLabel("", card)
        self._sub_lbl.setGeometry(0, 190, cx, 18)
        self._sub_lbl.setAlignment(Qt.AlignCenter)
        self._sub_lbl.setStyleSheet(f"""
            QLabel {{
                color: {_TEXT_SEC};
                font-size: 11px;
                font-family: 'Segoe UI', Arial, sans-serif;
                background: transparent;
            }}
        """)

        # Progress bar
        self._bar = QProgressBar(card)
        self._bar.setGeometry(50, 225, cx - 100, 14)
        self._bar.setRange(0, 100)
        self._bar.setValue(0)
        self._bar.setTextVisible(False)
        self._bar.setStyleSheet(f"""
            QProgressBar {{
                background-color: {_BAR_BG};
                border: none;
                border-radius: 7px;
            }}
            QProgressBar::chunk {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {_ACCENT2}, stop:0.5 {_ACCENT1}, stop:1 #79c0ff);
                border-radius: 7px;
            }}
        """)

        # Indeterminate pulse overlay (shown while checking)
        self._pulse_bar = QProgressBar(card)
        self._pulse_bar.setGeometry(50, 225, cx - 100, 14)
        self._pulse_bar.setRange(0, 0)   # indeterminate
        self._pulse_bar.setTextVisible(False)
        self._pulse_bar.setStyleSheet(f"""
            QProgressBar {{
                background-color: {_BAR_BG};
                border: none;
                border-radius: 7px;
            }}
            QProgressBar::chunk {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {_ACCENT2}, stop:1 {_ACCENT1});
                border-radius: 7px;
                width: 80px;
                margin: 0px;
            }}
        """)
        self._bar.hide()   # hide real bar until download starts

        # Progress details row  (e.g. "24.3 MB / 45.6 MB  —  2.1 MB/s")
        self._detail_lbl = QLabel("", card)
        self._detail_lbl.setGeometry(0, 248, cx, 16)
        self._detail_lbl.setAlignment(Qt.AlignCenter)
        self._detail_lbl.setStyleSheet(f"""
            QLabel {{
                color: {_ACCENT1};
                font-size: 11px;
                font-family: 'Segoe UI Mono', Consolas, monospace;
                background: transparent;
            }}
        """)

        # Percent label (right side of bar)
        self._pct_lbl = QLabel("", card)
        self._pct_lbl.setGeometry(cx - 48, 222, 48, 20)
        self._pct_lbl.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self._pct_lbl.setStyleSheet(f"""
            QLabel {{
                color: {_ACCENT1};
                font-size: 11px;
                font-weight: bold;
                font-family: 'Segoe UI', monospace;
                background: transparent;
            }}
        """)

        # Bottom separator
        sep2 = QFrame(card)
        sep2.setGeometry(40, 285, cx - 80, 1)
        sep2.setStyleSheet(f"QFrame {{ background-color: {_BORDER}; }}")

        # Footer: new-version pill
        self._new_ver_lbl = QLabel("", card)
        self._new_ver_lbl.setGeometry(0, 296, cx, 18)
        self._new_ver_lbl.setAlignment(Qt.AlignCenter)
        self._new_ver_lbl.setStyleSheet(f"""
            QLabel {{
                color: {_SUCCESS};
                font-size: 11px;
                font-family: 'Segoe UI', Arial, sans-serif;
                background: transparent;
            }}
        """)

        # Developer credit
        credit = QLabel("Developed by Paolo Somido", card)
        credit.setGeometry(0, 355, cx, 16)
        credit.setAlignment(Qt.AlignCenter)
        credit.setStyleSheet(f"""
            QLabel {{
                color: {_TEXT_SEC};
                font-size: 10px;
                font-family: 'Segoe UI', Arial, sans-serif;
                background: transparent;
                opacity: 0.6;
            }}
        """)

        # GitHub repo label
        repo_lbl = QLabel(f"github.com/{GITHUB_REPO}", card)
        repo_lbl.setGeometry(0, 372, cx, 14)
        repo_lbl.setAlignment(Qt.AlignCenter)
        repo_lbl.setStyleSheet(f"""
            QLabel {{
                color: {_BORDER};
                font-size: 9px;
                font-family: 'Segoe UI', monospace;
                background: transparent;
            }}
        """)

    # ── Start ──────────────────────────────────────────────────────────────────

    def start(self):
        """Show the window and kick off the update check."""
        self.show()
        QApplication.processEvents()
        self._anim_timer.start(500)

        self._worker = _UpdateWorker()
        self._worker.status_changed.connect(self._on_status)
        self._worker.sub_status.connect(self._on_sub_status)
        self._worker.progress_changed.connect(self._on_progress)
        self._worker.no_update.connect(self._on_no_update)
        self._worker.ready_to_install.connect(self._on_ready_to_install)
        self._worker.failed.connect(self._on_failed)
        self._worker.start()

    # ── Slots ──────────────────────────────────────────────────────────────────

    def _on_status(self, text):
        self._status_lbl.setText(text)
        QApplication.processEvents()

    def _on_sub_status(self, text):
        self._sub_lbl.setText(text)
        QApplication.processEvents()

    def _on_progress(self, done, total):
        # Switch to determinate bar on first progress signal
        if self._pulse_bar.isVisible():
            self._pulse_bar.hide()
            self._bar.show()

        if total > 0:
            pct = int(done / total * 100)
            self._bar.setValue(pct)
            self._pct_lbl.setText(f"{pct}%")

        # Speed calculation
        now = time.time()
        elapsed = now - self._last_t
        if elapsed >= 0.5:
            speed = (done - self._last_done) / elapsed
            self._last_done = done
            self._last_t = now
            self._speed_bytes = speed

        done_mb  = done  / 1_048_576
        total_mb = total / 1_048_576
        spd_mb   = self._speed_bytes / 1_048_576
        if total > 0:
            self._detail_lbl.setText(
                f"{done_mb:.1f} MB / {total_mb:.1f} MB   —   {spd_mb:.1f} MB/s"
            )
        else:
            self._detail_lbl.setText(f"{done_mb:.1f} MB downloaded")
        QApplication.processEvents()

    def _on_no_update(self):
        self._anim_timer.stop()
        self._pulse_bar.hide()
        self._bar.setRange(0, 100)
        self._bar.setValue(100)
        self._bar.show()
        self._status_lbl.setStyleSheet(
            self._status_lbl.styleSheet().replace(_TEXT_PRI, _SUCCESS)
        )
        self._status_lbl.setText("✓  Already up to date")
        self._sub_lbl.setText("Launching application…")
        self._detail_lbl.setText("")
        self._pct_lbl.setText("100%")
        QApplication.processEvents()
        QTimer.singleShot(1200, self._finish)

    def _on_ready_to_install(self, installer_path, new_version):
        self._anim_timer.stop()
        self._bar.setValue(100)
        self._pct_lbl.setText("100%")
        self._status_lbl.setText("✓  Update downloaded")
        self._sub_lbl.setText(f"Installing v{new_version}  —  application will restart…")
        self._new_ver_lbl.setText(f"v{CURRENT_VERSION}  →  v{new_version}")
        self._detail_lbl.setText("")
        QApplication.processEvents()

        QTimer.singleShot(800, lambda: self._install(installer_path))

    def _on_failed(self, msg):
        """Update failed (network error, etc.) — log and proceed to login."""
        self._anim_timer.stop()
        self._pulse_bar.hide()
        self._bar.setRange(0, 100)
        self._bar.setValue(0)
        self._bar.show()
        self._status_lbl.setStyleSheet(
            self._status_lbl.styleSheet().replace(_TEXT_PRI, _WARNING)
        )
        self._status_lbl.setText("Update check skipped")
        self._sub_lbl.setText(f"{msg[:80]}…" if len(msg) > 80 else msg)
        self._detail_lbl.setText("Launching with current version…")
        QApplication.processEvents()
        QTimer.singleShot(2000, self._finish)

    # ── Helpers ────────────────────────────────────────────────────────────────

    @staticmethod
    def _unblock_file(path):
        """Remove the Mark-of-the-Web Zone.Identifier tag from a downloaded file.
        Without this, Windows restricts DLL loading when the installer runs,
        causing 'Failed to load python dll' errors in the installed exe."""
        try:
            zone_path = path + ":Zone.Identifier"
            import ctypes
            ctypes.windll.kernel32.DeleteFileW(zone_path)
        except Exception:
            pass  # Non-fatal — best effort only

    @staticmethod
    def _hidden_popen(args):
        """Launch a subprocess completely hidden — no console window at all."""
        si = subprocess.STARTUPINFO()
        si.dwFlags = subprocess.STARTF_USESHOWWINDOW
        si.wShowWindow = subprocess.SW_HIDE
        return subprocess.Popen(
            args,
            startupinfo=si,
            creationflags=subprocess.DETACHED_PROCESS | subprocess.CREATE_NO_WINDOW,
            close_fds=True,
        )

    def _install(self, path):
        """
        Relay-based silent install:
        1. Strip MOTW from installer (fixes DLL error)
        2. Write a fully-hidden batch relay to %TEMP%
        3. Relay waits for us to exit, runs installer, then launches new exe
        4. We show 'Installing…' for 2 s then quit cleanly
        """
        try:
            _save_pre_update_version()

            # Remove Zone.Identifier so installer runs without DLL restrictions
            self._unblock_file(path)

            appdata_local = os.environ.get('LOCALAPPDATA', '')
            new_exe = os.path.join(appdata_local, 'ORS', 'main.exe')
            bat_path = os.path.join(tempfile.gettempdir(), 'ors_update_relay.bat')

            bat = (
                '@echo off\r\n'
                # 3 s delay — gives old process time to fully exit
                'ping -n 4 127.0.0.1 > nul\r\n'
                # Run installer silently; batch WAITS for it to complete
                f'"{path}" /VERYSILENT /SUPPRESSMSGBOXES /NORESTART\r\n'
                # Extra 2 s for file writes to flush
                'ping -n 3 127.0.0.1 > nul\r\n'
                # Launch the new version via explorer to get a clean user context
                f'explorer.exe "{new_exe}"\r\n'
                # Self-delete
                'del "%~f0"\r\n'
            )
            with open(bat_path, 'w') as f:
                f.write(bat)

            # Launch batch fully hidden and detached
            self._hidden_popen(['cmd', '/c', bat_path])

            # Show installing state
            self._anim_timer.stop()
            self._bar.setRange(0, 0)
            self._status_lbl.setText("Installing update…")
            self._sub_lbl.setText("The application will restart automatically.")
            self._detail_lbl.setText("")
            self._pct_lbl.setText("")
            QApplication.processEvents()

            # Quit after 2 s — relay handles everything from here
            QTimer.singleShot(2000, lambda: QApplication.instance().quit())

        except Exception as exc:
            self._on_failed(f"Install failed: {exc}")

    def _finish(self):
        self.hide()
        self.launch_ready.emit()

    def _tick_dots(self):
        self._anim_dots = (self._anim_dots + 1) % 4
        dots = "." * self._anim_dots
        text = self._status_lbl.text().rstrip(".")
        self._status_lbl.setText(text + dots)
