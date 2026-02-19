from PyQt5.QtWidgets import (
    QWidget, QLineEdit, QPushButton, QVBoxLayout, QHBoxLayout,
    QMessageBox, QLabel, QCheckBox
)
from PyQt5.QtCore import QSettings, Qt
from PyQt5.QtGui import QFont

from Client.client_dashboard import ClientDashboard
from db_connect_pooled import db_manager
from security import (
    verify_password, hash_password, is_password_hashed,
    login_rate_limiter, format_lockout_time
)

# Auto-updater (optional - comment out if not using)
try:
    from auto_updater import check_for_updates_silent
    from version import __version__, CHECK_ON_STARTUP
    AUTO_UPDATE_ENABLED = True
except ImportError:
    AUTO_UPDATE_ENABLED = False
    print("Auto-updater not available (missing dependencies)")


class LoginWindow(QWidget):
    def __init__(self, app):
        super().__init__()
        self.app = app
        self.dashboard = None
        self._update_checker_threads = []  # Store update checker threads
        self.setWindowTitle("Secure Login")
        self.setFixedSize(400, 500)
        self.settings = QSettings("MyCompany", "MyApp")

        # Initialize database connection
        self.init_database()

        self.setup_ui()
        self.apply_styles()
        self.load_saved_credentials()
        self.center_window()
        
        # Check for updates on startup (if enabled)
        if AUTO_UPDATE_ENABLED and CHECK_ON_STARTUP:
            self.check_updates_on_startup()

    def init_database(self):
        """Initialize MySQL database connection"""
        # Test connection on startup and show error if it fails
        if not db_manager.test_connection():
            error_msg = "⚠️ Cannot Connect to Database\n\n"
            error_msg += "Possible causes:\n"
            error_msg += "• No internet connection\n"
            error_msg += "• Database server is down\n"
            error_msg += "• Incorrect database configuration\n\n"
            error_msg += "Please check your connection and try again."
            
            QMessageBox.critical(
                self,
                "Database Connection Error",
                error_msg
            )
    
    def check_updates_on_startup(self):
        """Check for application updates silently when the app starts"""
        try:
            # Silent update: downloads and installs automatically without user interaction
            check_for_updates_silent(parent=self, auto_install=True)
        except Exception as e:
            # Don't show errors for update check failures on startup
            print(f"Update check failed: {e}")

    def center_window(self):
        screen = self.app.desktop().screenGeometry()
        size = self.geometry()
        self.move(
            (screen.width() - size.width()) // 2,
            (screen.height() - size.height()) // 2
        )

    def setup_ui(self):
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(30, 30, 30, 30)
        main_layout.setSpacing(20)

        # Title
        title = QLabel("🔒 Secure Login")
        title.setAlignment(Qt.AlignCenter)
        title.setFont(QFont("Arial", 18, QFont.Bold))
        main_layout.addWidget(title)

        subtitle = QLabel("Please enter your credentials to continue")
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setFont(QFont("Arial", 10))
        subtitle.setStyleSheet("color: #666;")
        main_layout.addWidget(subtitle)

        # Add spacing
        main_layout.addSpacing(20)

        # Username
        username_label = QLabel("Username:")
        username_label.setFont(QFont("Arial", 10, QFont.Bold))
        main_layout.addWidget(username_label)

        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Enter your username")
        self.username_input.setFixedHeight(35)
        self.username_input.setMaximumWidth(300)
        main_layout.addWidget(self.username_input)

        # Password
        password_label = QLabel("Password:")
        password_label.setFont(QFont("Arial", 10, QFont.Bold))
        main_layout.addWidget(password_label)

        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Enter your password")
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.setFixedHeight(35)
        self.password_input.setMaximumWidth(300)
        main_layout.addWidget(self.password_input)

        # Checkboxes
        checkbox_layout = QVBoxLayout()
        checkbox_layout.setSpacing(8)

        self.show_password_checkbox = QCheckBox("Show Password")
        self.show_password_checkbox.toggled.connect(self.toggle_password_visibility)
        checkbox_layout.addWidget(self.show_password_checkbox)

        self.remember_me_checkbox = QCheckBox("Remember Me")
        checkbox_layout.addWidget(self.remember_me_checkbox)

        main_layout.addLayout(checkbox_layout)

        # Login button
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        self.login_button = QPushButton("Login")
        self.login_button.setFixedSize(100, 35)
        self.login_button.clicked.connect(self.manual_login)
        button_layout.addWidget(self.login_button)

        main_layout.addLayout(button_layout)

        # Add stretch to push everything up
        main_layout.addStretch()

        self.setLayout(main_layout)

    def apply_styles(self):
        """Apply clean, simple styling"""
        self.setStyleSheet("""
            QWidget {
                background-color: #f0f0f0;
                font-family: Arial, sans-serif;
            }

            QLineEdit {
                padding: 8px;
                border: 2px solid #ddd;
                border-radius: 5px;
                font-size: 12px;
                background-color: white;
            }

            QLineEdit:focus {
                border-color: #4CAF50;
            }

            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                border-radius: 5px;
                font-size: 12px;
                font-weight: bold;
            }

            QPushButton:hover {
                background-color: #45a049;
            }

            QPushButton:pressed {
                background-color: #3d8b40;
            }

            QCheckBox {
                font-size: 11px;
                spacing: 5px;
            }

            QCheckBox::indicator {
                width: 15px;
                height: 15px;
            }

            QCheckBox::indicator:unchecked {
                border: 2px solid #ddd;
                background-color: white;
            }

            QCheckBox::indicator:checked {
                border: 2px solid #4CAF50;
                background-color: #4CAF50;
            }
        """)

    def toggle_password_visibility(self, checked):
        self.password_input.setEchoMode(QLineEdit.Normal if checked else QLineEdit.Password)

    def load_saved_credentials(self):
        saved_username = self.settings.value("username")
        if saved_username:
            self.username_input.setText(saved_username)
            self.remember_me_checkbox.setChecked(True)

    def save_credentials(self, username):
        if self.remember_me_checkbox.isChecked():
            self.settings.setValue("username", username)
        else:
            self.settings.remove("username")

    def clear_password_field(self):
        """Clear password field when returning to login"""
        self.password_input.clear()
        self.show_password_checkbox.setChecked(False)

    def handle_logout(self):
        """Handle logout from dashboard"""
        print("🔓 Logout requested - returning to login screen")
        
        # Close and cleanup dashboard
        if self.dashboard:
            self.dashboard.close()
            self.dashboard.deleteLater()
            self.dashboard = None
        
        # Clear password for security
        self.clear_password_field()
        
        # Show login window again
        self.show()
        self.center_window()
        self.raise_()
        self.activateWindow()

    def manual_login(self):
        username = self.username_input.text().strip()
        password = self.password_input.text().strip()

        if not username or not password:
            self.show_message("Input Error", "Please enter both username and password.", QMessageBox.Warning)
            return

        # Check if database connection exists
        if not db_manager.test_connection():
            error_msg = "⚠️ Cannot connect to database\n\n"
            error_msg += "Please check:\n"
            error_msg += "• Your internet connection\n"
            error_msg += "• VPN if required\n"
            error_msg += "• Database server status\n\n"
            error_msg += "Contact IT support if the problem persists."
            self.show_message("Connection Error", error_msg, QMessageBox.Critical)
            return

        # Disable button during login attempt
        self.login_button.setEnabled(False)
        self.login_button.setText("Logging in...")

        try:
            # Check database connection first
            if not self.test_database_connection():
                error_msg = "⚠️ Database connection lost\n\n"
                error_msg += "Your internet connection may be unstable.\n"
                error_msg += "Please check your connection and try again."
                self.show_message("Connection Error", error_msg, QMessageBox.Critical)
                return

            # Check rate limiting before attempting login
            is_locked, lockout_remaining = login_rate_limiter.is_locked(username)
            if is_locked:
                self.show_message(
                    "Account Locked",
                    f"⚠️ Too many failed attempts.\n\nPlease wait {format_lockout_time(lockout_remaining)} before trying again.",
                    QMessageBox.Warning
                )
                return

            # Check admin login first, then regular user
            if self.check_admin_login(username, password):
                return

            self.authenticate_user(username, password)
        except Exception as e:
            print(f"Login Error: {e}")
            self.show_message("Error", "An error occurred during login. Please try again.", QMessageBox.Critical)
        finally:
            # Re-enable button
            self.login_button.setEnabled(True)
            self.login_button.setText("Login")

    def test_database_connection(self):
        """Test database connection"""
        try:
            # Use db_manager's built-in connection test
            return db_manager.test_connection()
        except Exception as e:
            print(f"Database connection test failed: {e}")
            return False

    def execute_database_query(self, query, params=None):
        """Execute database query with MySQL"""
        return db_manager.execute_query(query, params)

    def _migrate_password_if_needed(self, user_id: int, password: str, stored_password: str):
        """Migrate plaintext password to bcrypt hash after successful login"""
        if not is_password_hashed(stored_password):
            try:
                hashed = hash_password(password)
                db_manager.execute_query(
                    "UPDATE users SET password = %s WHERE id = %s",
                    (hashed, user_id)
                )
                print(f"Password migrated to bcrypt for user ID {user_id}")
            except Exception as e:
                print(f"Failed to migrate password: {e}")

    def check_admin_login(self, username, password):
        """Check database for admin users - no hardcoded credentials"""
        try:
            query = """
                    SELECT id, username, password, branch, corporation, role
                    FROM users
                    WHERE username = %s \
                      AND role = 'admin' LIMIT 1
                    """

            result = self.execute_database_query(query, [username])

            if result:
                user_data = result[0]
                stored_password = user_data['password']
                user_id = user_data['id']

                if verify_password(password, stored_password):
                    # Migrate password to bcrypt if still plaintext
                    self._migrate_password_if_needed(user_id, password, stored_password)
                    login_rate_limiter.reset(username)  # Clear failed attempts
                    try:
                        from admin_dashboard import AdminDashboard
                        self.show_message("Admin Login", f"Welcome, {username}!", QMessageBox.Information)
                        self.save_credentials(username)
                        self.dashboard = AdminDashboard()
                        # Connect logout signal if admin dashboard has one
                        if hasattr(self.dashboard, 'logout_requested'):
                            self.dashboard.logout_requested.connect(self.handle_logout)
                        self.dashboard.show()
                        self.hide()  # Hide instead of close
                        return True
                    except Exception as e:
                        print(f"Error loading AdminDashboard: {e}")
                        self.show_message("Error", "Failed to load admin dashboard.", QMessageBox.Critical)
                        return False
        except Exception as e:
            # If `users` table doesn't exist, skip DB admin check and continue
            print(f"Database Error during admin check (users table may be missing): {e}")

        return False

    def authenticate_user(self, username, password):
        """Authenticate regular users from the database"""
        try:
            # Query to get user by username
            # Prefer `users` table if available
            query_users = """
                    SELECT id, username, password, branch, corporation, role
                    FROM users
                    WHERE username = %s LIMIT 1
                    """

            result = None
            try:
                result = self.execute_database_query(query_users, [username])
            except Exception as e:
                # Likely `users` table missing; fall back to `clients` table
                print(f"users table query failed, falling back to clients: {e}")

            if result:
                user_data = result[0]
                user_id = user_data['id']
                db_username = user_data['username']
                stored_password = user_data['password']
                branch = user_data.get('branch') or "Unknown"
                corporation = user_data.get('corporation') or "Unknown"
                role = user_data.get('role', 'user')

                if verify_password(password, stored_password):
                    # Migrate password to bcrypt if still plaintext
                    self._migrate_password_if_needed(user_id, password, stored_password)
                    login_rate_limiter.reset(username)  # Clear failed attempts
                    
                    self.show_message("Login Success", f"Welcome, {db_username}!", QMessageBox.Information)
                    self.save_credentials(db_username)
                    if role == 'admin':
                        try:
                            from admin_dashboard import AdminDashboard
                            self.dashboard = AdminDashboard()
                            # Connect logout signal if admin dashboard has one
                            if hasattr(self.dashboard, 'logout_requested'):
                                self.dashboard.logout_requested.connect(self.handle_logout)
                        except Exception as e:
                            print(f"Error loading AdminDashboard: {e}")
                            self.show_message("Error", "Failed to load admin dashboard.", QMessageBox.Critical)
                            return
                    else:
                        self.dashboard = ClientDashboard(db_username, branch, corporation, db_manager)
                        # Connect logout signal from client dashboard
                        self.dashboard.logout_requested.connect(self.handle_logout)
                    
                    self.dashboard.show()
                    self.hide()  # Hide instead of close
                else:
                    # Record failed attempt
                    is_locked, remaining, lockout_time = login_rate_limiter.record_failed_attempt(username)
                    if is_locked:
                        self.show_message(
                            "Account Locked",
                            f"⚠️ Too many failed attempts.\n\nPlease wait {format_lockout_time(lockout_time)} before trying again.",
                            QMessageBox.Warning
                        )
                    elif remaining > 0:
                        self.show_message("Login Failed", f"Incorrect password.\n{remaining} attempts remaining.", QMessageBox.Warning)
                    else:
                        self.show_message("Login Failed", "Incorrect password.", QMessageBox.Warning)
                return
            
            # If no user found in users table
            # Still record as failed attempt to prevent username enumeration
            login_rate_limiter.record_failed_attempt(username)
            self.show_message("Login Failed", "Invalid username or password.", QMessageBox.Warning)

        except Exception as e:
            print(f"Database Error during authentication: {e}")
            self.show_message("Connection Error", "Failed to connect to the database.", QMessageBox.Critical)

    def show_message(self, title, message, icon):
        msg = QMessageBox(icon, title, message, QMessageBox.Ok, self)
        msg.exec_()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Return or event.key() == Qt.Key_Enter:
            self.manual_login()
        super().keyPressEvent(event)
    
    def closeEvent(self, event):
        """Clean up threads before closing"""
        # Wait for update checker threads to finish (max 2 seconds)
        if hasattr(self, '_update_checker_threads'):
            for thread in self._update_checker_threads[:]:
                if thread.isRunning():
                    thread.quit()
                    thread.wait(2000)  # Wait up to 2 seconds
        event.accept()
