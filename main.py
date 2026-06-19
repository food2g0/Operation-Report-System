import sys
import traceback
import ctypes
import time

# Measure startup time
_startup_start = time.time()

def _log_startup_time(step_name):
    """Log elapsed time since startup"""
    elapsed = time.time() - _startup_start
    print(f"⏱️  [{elapsed:.2f}s] {step_name}")

_log_startup_time("Script start")

try:
    from version import __version__ as APP_VERSION
except ImportError:
    APP_VERSION = "1.0.2"

_log_startup_time("Version imported")


_log_startup_time("Dotenv import")

try:
    from dotenv import load_dotenv as _load_dotenv
    _load_dotenv(override=False)
except ImportError:
    pass

_log_startup_time("PyQt5 imports starting")

from PyQt5.QtWidgets import QApplication, QMessageBox
from PyQt5.QtCore import Qt

_log_startup_time("Logging setup")

from app_logging import setup_logging, get_logger
setup_logging()

_log_startup_time("Client/Login imports")

from Client.client_dashboard import ClientDashboard
from login import LoginWindow

logger = get_logger(__name__)
_log_startup_time("All imports complete")


# ─────────────────────────────────────────────────────────────────────────────
# Single Instance Lock (Windows)
# ─────────────────────────────────────────────────────────────────────────────
_mutex_handle = None

def acquire_single_instance_lock():
    """Prevent multiple instances of the application from running."""
    global _mutex_handle
    
    # Create a named mutex
    mutex_name = "OperationReportSystem_SingleInstance_Mutex"
    
    # Windows API constants
    ERROR_ALREADY_EXISTS = 183
    
    # Create mutex
    _mutex_handle = ctypes.windll.kernel32.CreateMutexW(None, False, mutex_name)
    
    if ctypes.windll.kernel32.GetLastError() == ERROR_ALREADY_EXISTS:
        # Another instance is already running
        return False
    
    return True


def release_single_instance_lock():
    """Release the single instance lock."""
    global _mutex_handle
    if _mutex_handle:
        ctypes.windll.kernel32.CloseHandle(_mutex_handle)
        _mutex_handle = None


def exception_hook(exctype, value, tb):
    """Global exception handler to prevent silent crashes"""
    error_msg = ''.join(traceback.format_exception(exctype, value, tb))
    logger.critical("Uncaught exception:\n%s", error_msg)
    
    # Log to file
    try:
        with open("crash.log", "a") as f:
            f.write(f"\n{'='*50}\n{error_msg}")
    except:
        pass
    
    # Show error dialog if QApplication exists
    app = QApplication.instance()
    if app:
        QMessageBox.critical(None, "Application Error", 
            f"An unexpected error occurred:\n\n{value}\n\nSee crash.log for details.")
    
    sys.exit(1)


def main():
    _log_startup_time("main() function started")

    # Check for single instance BEFORE creating QApplication
    if not acquire_single_instance_lock():
        # Enable High-DPI scaling
        QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
        QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
        import os
        os.environ['QT_AUTO_SCREEN_SCALE_FACTOR'] = '1'

        temp_app = QApplication(sys.argv)
        QMessageBox.warning(None, "Already Running",
            "Operation Report System is already running.\n\nCheck the taskbar for the existing window.")
        sys.exit(0)

    sys.excepthook = exception_hook

    # Enable High-DPI scaling for better readability on small monitors
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
    import os
    os.environ['QT_AUTO_SCREEN_SCALE_FACTOR'] = '1'

    _log_startup_time("Creating QApplication")
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(True)
    _log_startup_time("QApplication created")

    # Set application name and version for proper taskbar display
    app.setApplicationName("Operation Report System")
    app.setApplicationVersion(APP_VERSION)

    # ── Show splash screen immediately ────────────────────────────────────────
    _log_startup_time("Showing splash screen")
    from PyQt5.QtWidgets import QSplashScreen
    from PyQt5.QtGui import QPixmap

    # Create a simple splash screen (can be improved with a custom pixmap)
    splash = QSplashScreen(QPixmap(400, 300))
    splash.showMessage("Operation Report System\nLoading...", alignment=0x0004)
    splash.show()
    app.processEvents()
    _log_startup_time("Splash screen shown")

    # ── Game-style update launcher (background) ────────────────────────────────────────
    _log_startup_time("Importing UpdateLauncherWindow")
    from update_launcher import UpdateLauncherWindow

    _log_startup_time("Creating UpdateLauncherWindow")
    launcher = UpdateLauncherWindow(app_version=APP_VERSION)
    _log_startup_time("UpdateLauncherWindow created")
    login_window_holder = [None]

    def _on_launch_ready():
        try:
            splash.close()  # Close splash when app is ready

            # ── Machine access check (before login window) ────────────────────
            machine_status = _check_machine_startup()
            if machine_status == "revoked":
                QMessageBox.critical(
                    None,
                    "Access Revoked",
                    "This computer's access has been revoked by the administrator.\n\n"
                    "Please contact your system administrator.",
                )
                release_single_instance_lock()
                sys.exit(0)
                return
            if machine_status == "pending":
                QMessageBox.information(
                    None,
                    "Pending Approval",
                    "This computer is not yet authorized to use this application.\n\n"
                    "Your request has been sent to the administrator.\n"
                    "Please wait for approval before trying again.",
                )
                release_single_instance_lock()
                sys.exit(0)
                return
            # 'approved' or 'bypass' (server unreachable) → show login normally

            lw = LoginWindow(app)
            login_window_holder[0] = lw
            lw.show()

            # Show "Updated successfully" popup if this is a post-update first run
            # Skip in client-only builds without auto_updater
            try:
                from auto_updater import check_update_success
                check_update_success(parent=lw)
            except ImportError:
                pass  # auto_updater not available in client-only build
        except Exception as exc:
            release_single_instance_lock()
            exception_hook(type(exc), exc, exc.__traceback__)

    launcher.launch_ready.connect(_on_launch_ready)
    _log_startup_time("Starting background update check")
    launcher.start()  # runs in background while splash is visible

    result = app.exec_()
    release_single_instance_lock()
    sys.exit(result)


def _check_machine_startup() -> str:
    """
    Called once at app startup (before the login window).
    Registers this machine if unknown, then returns its status:
      'approved' → proceed to login
      'pending'  → show waiting screen and exit
      'revoked'  → show error and exit
      'bypass'   → server unreachable, allow through silently
    """
    try:
        import requests
        from machine_id import get_machine_info
        from api_config import API_URL, API_KEY

        info = get_machine_info()

        # Single call — no separate /api/token step needed
        resp = requests.post(
            f"{API_URL}/api/machine/status",
            json={
                "api_key":    API_KEY,
                "machine_id": info["machine_id"],
                "hostname":   info.get("hostname"),
                "mac_address": info.get("mac_address"),
                "cpu_info":   info.get("cpu_info"),
            },
            timeout=5,
        )
        if resp.status_code == 200:
            return resp.json().get("status", "bypass")

        return "bypass"
    except Exception as exc:
        # Never block startup due to network errors
        logger.warning("Machine startup check failed (bypass): %s", exc)
        return "bypass"


# In your main.py or login manager file
class LoginManager:
    def __init__(self):
        self.login_window = LoginWindow()
        self.dashboard = None
        
        # Connect login button to show dashboard
        self.login_window.login_successful.connect(self.show_dashboard)
    
    def show_dashboard(self, username, branch, corporation, db_manager):
        # Hide login window
        self.login_window.hide()

        # Route through API when API_MODE is enabled
        try:
            from api_config import API_MODE as _API_MODE
            if _API_MODE:
                from Client.api_db_manager import APIDbManager
                _client_db = APIDbManager()
                _client_db.connect()
            else:
                _client_db = db_manager
        except ImportError:
            _client_db = db_manager

        # Create and show dashboard
        self.dashboard = ClientDashboard(username, branch, corporation, _client_db)
        self.dashboard.logout_requested.connect(self.handle_logout)
        self.dashboard.show()
    
    def handle_logout(self):
        # Close dashboard
        if self.dashboard:
            self.dashboard.close()
            self.dashboard = None
        
        # Show login window again
        self.login_window.show()
        self.login_window.clear_fields()  # Clear previous login info

if __name__ == '__main__':
    main()
