import sys
import traceback
import ctypes

try:
    from version import __version__ as APP_VERSION
except ImportError:
    APP_VERSION = "1.0.2"


try:
    from dotenv import load_dotenv as _load_dotenv
    _load_dotenv(override=False)
except ImportError:
    pass

from PyQt5.QtWidgets import QApplication, QMessageBox
from app_logging import setup_logging, get_logger
setup_logging()
from Client.client_dashboard import ClientDashboard
from login import LoginWindow

logger = get_logger(__name__)


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
    # Check for single instance BEFORE creating QApplication
    if not acquire_single_instance_lock():
        temp_app = QApplication(sys.argv)
        QMessageBox.warning(None, "Already Running",
            "Operation Report System is already running.\n\nCheck the taskbar for the existing window.")
        sys.exit(0)

    sys.excepthook = exception_hook

    app = QApplication(sys.argv)

    # ── Game-style update launcher ────────────────────────────────────────────
    from update_launcher import UpdateLauncherWindow

    launcher = UpdateLauncherWindow(app_version=APP_VERSION)
    login_window_holder = [None]

    def _on_launch_ready():
        try:
            lw = LoginWindow(app)
            login_window_holder[0] = lw
            lw.show()

            # Show "Updated successfully" popup if this is a post-update first run
            from auto_updater import check_update_success
            check_update_success(parent=lw)
        except Exception as exc:
            release_single_instance_lock()
            exception_hook(type(exc), exc, exc.__traceback__)

    launcher.launch_ready.connect(_on_launch_ready)
    launcher.start()

    result = app.exec_()
    release_single_instance_lock()
    sys.exit(result)

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
