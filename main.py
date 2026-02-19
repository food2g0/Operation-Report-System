import sys
import traceback
from PyQt5.QtWidgets import QApplication, QMessageBox
from Client.client_dashboard import ClientDashboard
from login import LoginWindow


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
    # Set exception hook before creating QApplication
    sys.excepthook = exception_hook
    
    app = QApplication(sys.argv)
    
    try:
        login_window = LoginWindow(app)
        login_window.show()
        sys.exit(app.exec_())
    except Exception as e:
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
