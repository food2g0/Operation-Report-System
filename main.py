import sys
import traceback
import ctypes
from PyQt5.QtWidgets import QApplication, QMessageBox, QLabel
from PyQt5.QtCore import Qt
from Client.client_dashboard import ClientDashboard
from login import LoginWindow


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
    print(f"Uncaught exception:\n{error_msg}")
    
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
        # Another instance is running - show message and exit
        # Need temporary app just to show message
        temp_app = QApplication(sys.argv)
        QMessageBox.warning(None, "Already Running", 
            "Operation Report System is already running.\n\nCheck the taskbar for the existing window.")
        sys.exit(0)
    
    # Set exception hook before creating QApplication
    sys.excepthook = exception_hook
    
    app = QApplication(sys.argv)
    
    # ─────────────────────────────────────────────────────────────────────────
    # Professional Splash Screen
    # ─────────────────────────────────────────────────────────────────────────
    from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QFrame, QProgressBar
    from PyQt5.QtGui import QPainter, QColor, QPen
    import os
    
    # Create splash widget
    splash_widget = QWidget()
    splash_widget.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.SplashScreen)
    splash_widget.setAttribute(Qt.WA_TranslucentBackground)
    splash_widget.setFixedSize(480, 280)
    
    # Center on screen
    screen = app.primaryScreen().geometry()
    splash_widget.move(
        (screen.width() - 480) // 2,
        (screen.height() - 280) // 2
    )
    
    # Main container with shadow effect
    container = QFrame(splash_widget)
    container.setGeometry(10, 10, 460, 260)
    container.setStyleSheet("""
        QFrame {
            background-color: #ffffff;
            border-radius: 12px;
            border: 1px solid #e0e0e0;
        }
    """)
    
    # Header bar
    header = QFrame(container)
    header.setGeometry(0, 0, 460, 8)
    header.setStyleSheet("""
        QFrame {
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 #667eea, stop:1 #764ba2);
            border-top-left-radius: 12px;
            border-top-right-radius: 12px;
            border: none;
        }
    """)
    
    # Logo/Icon area
    logo_label = QLabel("ORS", container)
    logo_label.setGeometry(180, 35, 100, 50)
    logo_label.setAlignment(Qt.AlignCenter)
    logo_label.setStyleSheet("""
        QLabel {
            color: #667eea;
            font-size: 36px;
            font-weight: bold;
            font-family: 'Segoe UI', Arial, sans-serif;
            background: transparent;
        }
    """)
    
    # App name
    title_label = QLabel("Operation Report System", container)
    title_label.setGeometry(0, 90, 460, 28)
    title_label.setAlignment(Qt.AlignCenter)
    title_label.setStyleSheet("""
        QLabel {
            color: #333333;
            font-size: 18px;
            font-weight: 600;
            font-family: 'Segoe UI', Arial, sans-serif;
            background: transparent;
        }
    """)
    
    # Version
    version_label = QLabel("v2.0", container)
    version_label.setGeometry(0, 118, 460, 18)
    version_label.setAlignment(Qt.AlignCenter)
    version_label.setStyleSheet("""
        QLabel {
            color: #999999;
            font-size: 11px;
            font-family: 'Segoe UI', Arial, sans-serif;
            background: transparent;
        }
    """)
    
    # Loading status
    status_label = QLabel("Initializing application...", container)
    status_label.setGeometry(0, 155, 460, 20)
    status_label.setAlignment(Qt.AlignCenter)
    status_label.setStyleSheet("""
        QLabel {
            color: #666666;
            font-size: 11px;
            font-family: 'Segoe UI', Arial, sans-serif;
            background: transparent;
        }
    """)
    
    # Progress bar
    progress = QProgressBar(container)
    progress.setGeometry(60, 180, 340, 4)
    progress.setRange(0, 0)  # Indeterminate
    progress.setTextVisible(False)
    progress.setStyleSheet("""
        QProgressBar {
            background-color: #f0f0f0;
            border: none;
            border-radius: 2px;
        }
        QProgressBar::chunk {
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 #667eea, stop:1 #764ba2);
            border-radius: 2px;
        }
    """)
    
    # Footer separator
    footer_line = QFrame(container)
    footer_line.setGeometry(30, 210, 400, 1)
    footer_line.setStyleSheet("QFrame { background-color: #eeeeee; }")
    
    # Developer credit
    credit_label = QLabel("Developed by Paolo Somido", container)
    credit_label.setGeometry(0, 225, 460, 20)
    credit_label.setAlignment(Qt.AlignCenter)
    credit_label.setStyleSheet("""
        QLabel {
            color: #aaaaaa;
            font-size: 10px;
            font-family: 'Segoe UI', Arial, sans-serif;
            background: transparent;
        }
    """)
    
    splash_widget.show()
    app.processEvents()  # Ensure splash shows immediately
    
    try:
        status_label.setText("Checking database connection...")
        app.processEvents()
        
        login_window = LoginWindow(app)
        
        # Check if we're in offline mode and update splash accordingly
        from offline_manager import offline_manager
        if offline_manager.is_offline:
            status_label.setText("Starting in offline mode...")
        else:
            status_label.setText("Ready")
        app.processEvents()
        
        splash_widget.close()
        login_window.show()
        
        # Cleanup on exit
        result = app.exec_()
        release_single_instance_lock()
        sys.exit(result)
    except Exception as e:
        release_single_instance_lock()
        exception_hook(type(e), e, e.__traceback__)

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
        
        # Create and show dashboard
        self.dashboard = ClientDashboard(username, branch, corporation, db_manager)
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
