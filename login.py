from PyQt5.QtWidgets import (
    QWidget, QLineEdit, QPushButton, QVBoxLayout, QHBoxLayout,
    QMessageBox, QLabel, QCheckBox, QFrame, QGraphicsDropShadowEffect
)
from PyQt5.QtCore import QSettings, Qt
from PyQt5.QtGui import QFont, QPixmap, QIcon
import os

from Client.client_dashboard import ClientDashboard
from db_connect_pooled import db_manager
from security import (
    verify_password, hash_password, is_password_hashed,
    login_rate_limiter, format_lockout_time
)
from offline_manager import offline_manager
from ping_monitor import ping_monitor


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
        self._update_checker_threads = [] 
        self.setWindowTitle("Operation Report System")
        self.setFixedSize(820, 500)
        self.settings = QSettings("MyCompany", "MyApp")


        self.setup_ui()
        self.apply_styles()
        self.load_saved_credentials()
        self.center_window()
        
      
        self.init_database()

        if AUTO_UPDATE_ENABLED and CHECK_ON_STARTUP:
            self.check_updates_on_startup()

    def init_database(self):

  
        if not db_manager.test_connection():
            offline_manager.is_offline = True
            
  
            self.connection_status_label.setText("Offline Mode - No database connection")
            self.connection_status_label.setStyleSheet("color: #e67e22; font-weight: bold;")
            self.connection_status_label.setVisible(True)
            
            if offline_manager.has_cached_credentials():

                from PyQt5.QtCore import QTimer
                info_msg = "No Database Connection\n\n"
                info_msg += "You can still log in using cached credentials.\n"
                info_msg += "Entries saved will be queued for posting when connection is restored.\n\n"
                info_msg += "Note: Some features may be limited in offline mode."
                
                QTimer.singleShot(100, lambda: QMessageBox.information(
                    self,
                    "Offline Mode",
                    info_msg
                ))
            else:

                self.connection_status_label.setText("Offline - No cached credentials available")
                self.connection_status_label.setStyleSheet("color: #e74c3c; font-weight: bold;")
                
                from PyQt5.QtCore import QTimer
                error_msg = "Cannot Connect to Database\n\n"
                error_msg += "No cached credentials available for offline login.\n\n"
                error_msg += "Please connect to the internet and log in at least once\n"
                error_msg += "to enable offline mode for future use."
                
                QTimer.singleShot(100, lambda: QMessageBox.warning(
                    self,
                    "Connection Required",
                    error_msg
                ))
        else:
            offline_manager.is_offline = False
            self.connection_status_label.setText("Connected to database")
            self.connection_status_label.setStyleSheet("color: #27ae60;")
            self.connection_status_label.setVisible(True)
            from PyQt5.QtCore import QTimer
            QTimer.singleShot(3000, lambda: self.connection_status_label.setVisible(False))
    
    def check_updates_on_startup(self):

        try:

            check_for_updates_silent(parent=self, auto_install=True)
        except Exception as e:

            print(f"Update check failed: {e}")

    def center_window(self):
        screen = self.app.desktop().screenGeometry()
        size = self.geometry()
        self.move(
            (screen.width() - size.width()) // 2,
            (screen.height() - size.height()) // 2
        )

    def setup_ui(self):

        main_layout = QHBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        left_panel = QFrame()
        left_panel.setObjectName("leftPanel")
        left_panel.setFixedWidth(400)
        left_layout = QVBoxLayout(left_panel)
        left_layout.setSpacing(20)
        left_layout.setContentsMargins(20, 20, 20, 20)

        left_layout.addStretch()


        logo_label = QLabel()
        logo_path = os.path.join(os.path.dirname(__file__), "assets", "logo.ico")
        if os.path.exists(logo_path):
            pixmap = QPixmap(logo_path)
            scaled_pixmap = pixmap.scaled(80, 80, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            logo_label.setPixmap(scaled_pixmap)
        else:
            logo_label.setText("📊")
            logo_label.setFont(QFont("Segoe UI Emoji", 48))
        logo_label.setAlignment(Qt.AlignCenter)
        left_layout.addWidget(logo_label)


        brand_title = QLabel("OPERATION REPORT SYSTEM")
        brand_title.setObjectName("brandTitle")
        brand_title.setAlignment(Qt.AlignCenter)
        brand_title.setFont(QFont("Segoe UI", 14, QFont.Bold))
        brand_title.setWordWrap(True)
        left_layout.addWidget(brand_title)

        left_layout.addStretch()
        credit_label = QLabel("© 2026 Paolo Somido")
        credit_label.setAlignment(Qt.AlignCenter)
        credit_label.setStyleSheet("color: rgba(255,255,255,0.5); font-size: 11px;")
        left_layout.addWidget(credit_label)

        main_layout.addWidget(left_panel)


        right_panel = QFrame()
        right_panel.setObjectName("rightPanel")
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(60, 60, 60, 60)
        right_layout.setSpacing(15)


        welcome_title = QLabel("WELCOME")
        welcome_title.setObjectName("welcomeTitle")
        welcome_title.setAlignment(Qt.AlignCenter)
        welcome_title.setFont(QFont("Segoe UI", 24, QFont.Bold))
        right_layout.addWidget(welcome_title)

        right_layout.addSpacing(30)


        username_row = QHBoxLayout()
        username_label = QLabel("Username:")
        username_label.setObjectName("formLabel")
        username_label.setFixedWidth(100)
        username_label.setFont(QFont("Segoe UI", 11))
        username_row.addWidget(username_label)

        self.username_input = QLineEdit()
        self.username_input.setObjectName("formInput")
        self.username_input.setPlaceholderText("")
        self.username_input.setFixedHeight(40)
        username_row.addWidget(self.username_input)
        right_layout.addLayout(username_row)

        right_layout.addSpacing(10)


        password_row = QHBoxLayout()
        password_label = QLabel("Password:")
        password_label.setObjectName("formLabel")
        password_label.setFixedWidth(100)
        password_label.setFont(QFont("Segoe UI", 11))
        password_row.addWidget(password_label)

        self.password_input = QLineEdit()
        self.password_input.setObjectName("formInput")
        self.password_input.setPlaceholderText("")
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.setFixedHeight(40)
        password_row.addWidget(self.password_input)
        right_layout.addLayout(password_row)

        right_layout.addSpacing(10)


        checkbox_layout = QHBoxLayout()
        checkbox_layout.setSpacing(20)
        
        self.show_password_checkbox = QCheckBox("Show Password")
        self.show_password_checkbox.setObjectName("formCheckbox")
        self.show_password_checkbox.toggled.connect(self.toggle_password_visibility)
        checkbox_layout.addWidget(self.show_password_checkbox)

        self.remember_me_checkbox = QCheckBox("Remember Me")
        self.remember_me_checkbox.setObjectName("formCheckbox")
        checkbox_layout.addWidget(self.remember_me_checkbox)
        
        checkbox_layout.addStretch()
        right_layout.addLayout(checkbox_layout)

        right_layout.addSpacing(20)


        button_layout = QHBoxLayout()
        button_layout.addStretch()

        self.login_button = QPushButton("Login")
        self.login_button.setObjectName("loginButton")
        self.login_button.setFixedSize(180, 45)
        self.login_button.setCursor(Qt.PointingHandCursor)
        self.login_button.clicked.connect(self.manual_login)
        button_layout.addWidget(self.login_button)

        button_layout.addStretch()
        right_layout.addLayout(button_layout)


        self.connection_status_label = QLabel("")
        self.connection_status_label.setObjectName("statusLabel")
        self.connection_status_label.setAlignment(Qt.AlignCenter)
        self.connection_status_label.setFont(QFont("Segoe UI", 9))
        self.connection_status_label.setVisible(False)
        right_layout.addWidget(self.connection_status_label)

        right_layout.addStretch()

        main_layout.addWidget(right_panel)
        self.setLayout(main_layout)

    def apply_styles(self):
     
        self.setStyleSheet("""
            QWidget {
                font-family: 'Segoe UI', Arial, sans-serif;
            }

            /* Left Panel - Branding */
            #leftPanel {
                background-color: #2C3E50;
                border: none;
            }

            #brandTitle {
                color: #A0AEC0;
                letter-spacing: 1px;
                padding: 0 20px;
            }

            /* Right Panel - Login Form */
            #rightPanel {
                background-color: #1A2332;
                border: none;
            }

            #welcomeTitle {
                color: #FFFFFF;
                letter-spacing: 2px;
            }

            #formLabel {
                color: #A0AEC0;
            }

            #formInput {
                padding: 10px 15px;
                border: 2px solid #3D4F5F;
                border-radius: 8px;
                font-size: 13px;
                background-color: #E8ECEF;
                color: #2C3E50;
            }

            #formInput:focus {
                border-color: #20B2AA;
                background-color: #FFFFFF;
            }

            #formCheckbox {
                color: #A0AEC0;
                font-size: 9px;
                spacing: 6px;
            }

            #formCheckbox::indicator {
                width: 12px;
                height: 12px;
                border-radius: 3px;
            }

            #formCheckbox::indicator:unchecked {
                border: 2px solid #3D4F5F;
                background-color: #2C3E50;
            }

            #formCheckbox::indicator:checked {
                border: 2px solid #20B2AA;
                background-color: #20B2AA;
            }

            #loginButton {
                background-color: #20B2AA;
                color: white;
                border: none;
                border-radius: 22px;
                font-size: 14px;
                font-weight: bold;
                letter-spacing: 1px;
            }

            #loginButton:hover {
                background-color: #1A9690;
            }

            #loginButton:pressed {
                background-color: #158580;
            }

            #statusLabel {
                color: #A0AEC0;
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

        self.password_input.clear()
        self.show_password_checkbox.setChecked(False)

    def handle_logout(self):
        """Handle logout from dashboard"""
        print("Logout requested - returning to login screen")
        ping_monitor.stop()

        if self.dashboard:
            self.dashboard.close()
            self.dashboard.deleteLater()
            self.dashboard = None
        

        self.clear_password_field()
        

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


        if not db_manager.test_connection():
      
            offline_manager.is_offline = True
            success, user_data = offline_manager.verify_offline_credentials(username, password)
            
            if success and user_data:
                self._handle_offline_login(username, password, user_data)
            else:
                if offline_manager.has_cached_credentials(username):
                    error_msg = "Offline Login Failed\n\n"
                    error_msg += "Incorrect password for cached credentials."
                else:
                    error_msg = "Cannot connect to database\n\n"
                    error_msg += "No cached credentials found for this user.\n\n"
                    error_msg += "Please connect to the internet and log in at least once\n"
                    error_msg += "to enable offline mode."
                self.show_message("Offline Login Failed", error_msg, QMessageBox.Critical)
            return


        offline_manager.is_offline = False


        self.login_button.setEnabled(False)
        self.login_button.setText("Logging in...")

        try:

            if not self.test_database_connection():
                error_msg = "Database connection lost\n\n"
                error_msg += "Your internet connection may be unstable.\n"
                error_msg += "Please check your connection and try again."
                self.show_message("Connection Error", error_msg, QMessageBox.Critical)
                return


            is_locked, lockout_remaining = login_rate_limiter.is_locked(username)
            if is_locked:
                self.show_message(
                    "Account Locked",
                    f"Too many failed attempts.\n\nPlease wait {format_lockout_time(lockout_remaining)} before trying again.",
                    QMessageBox.Warning
                )
                return


            if self.check_admin_login(username, password):
                return

            self.authenticate_user(username, password)
        except Exception as e:
            print(f"Login Error: {e}")
            self.show_message("Error", "An error occurred during login. Please try again.", QMessageBox.Critical)
        finally:

            self.login_button.setEnabled(True)
            self.login_button.setText("Login")

    def _handle_offline_login(self, username: str, password: str, user_data: dict):
        """Handle successful offline login with cached credentials"""
        role = user_data.get("role", "user")
        branch = user_data.get("branch", "Unknown")
        corporation = user_data.get("corporation", "Unknown")
        
   
        if role in ('admin', 'super_admin'):
            self.show_message(
                "Offline Mode Restricted",
                "Admin users cannot use offline mode.\n\n"
                "Please connect to the database to access admin features.",
                QMessageBox.Warning
            )
            return
        

        pending_count = offline_manager.get_pending_count(username)
        pending_msg = ""
        if pending_count > 0:
            pending_msg = f"\n\nYou have {pending_count} pending entries waiting to sync."
        
        self.show_message(
            "Offline Mode",
            f"Welcome, {username}! (Offline Mode)\n\n"
            f"Branch: {branch}\n"
            f"Corporation: {corporation}\n\n"
            f"Entries saved now will be queued for posting\n"
            f"when connection is restored.{pending_msg}",
            QMessageBox.Information
        )
        
        self.save_credentials(username)
        

        try:
            self.dashboard = ClientDashboard(
                username, branch, corporation, db_manager,
                offline_mode=True
            )
            self.dashboard.logout_requested.connect(self.handle_logout)
            self.dashboard.showMaximized()
            self.hide()
        except Exception as e:
            import traceback
            print(f"Error loading ClientDashboard in offline mode: {e}")
            traceback.print_exc()
            self.show_message("Error", "Failed to load client dashboard.", QMessageBox.Critical)
            return

    def test_database_connection(self):
        try:

            return db_manager.test_connection()
        except Exception as e:
            print(f"Database connection test failed: {e}")
            return False

    def execute_database_query(self, query, params=None):

        return db_manager.execute_query(query, params)

    def _migrate_password_if_needed(self, user_id: int, password: str, stored_password: str):

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

        try:
            query = """
                    SELECT id, username, password, branch, corporation, role, account_type
                    FROM users
                    WHERE username = %s
                      AND role IN ('admin', 'super_admin') LIMIT 1
                    """

            result = self.execute_database_query(query, [username])

            if result:
                user_data = result[0]
                stored_password = user_data['password']
                user_id = user_data['id']

                if verify_password(password, stored_password):

                    self._migrate_password_if_needed(user_id, password, stored_password)
                    login_rate_limiter.reset(username) 
                    role = user_data.get('role', 'admin')
                    try:
                        if role == 'super_admin':
                            from super_admin_dashboard import SuperAdminDashboard
                            self.show_message("Super Admin Login", f"Welcome, {username}! (Super Admin)", QMessageBox.Information)
                            self.save_credentials(username)
                            self.dashboard = SuperAdminDashboard()
                        else:
                            from admin_dashboard import AdminDashboard
                            account_type = user_data.get('account_type', 2)  
                            brand_label = "Brand A" if account_type == 1 else "Brand B"
                            self.show_message("Admin Login", f"Welcome, {username}! ({brand_label} Admin)", QMessageBox.Information)
                            self.save_credentials(username)
                            self.dashboard = AdminDashboard(account_type=account_type)

                        role = user_data.get('role', 'admin')
                        ping_monitor.start(db_manager, username, role)
                        if hasattr(self.dashboard, 'logout_requested'):
                            self.dashboard.logout_requested.connect(self.handle_logout)
                        self.dashboard.showMaximized()
                        self.hide()  
                        return True
                    except Exception as e:
                        print(f"Error loading dashboard: {e}")
                        self.show_message("Error", "Failed to load dashboard.", QMessageBox.Critical)
                        return False
        except Exception as e:

            print(f"Database Error during admin check (users table may be missing): {e}")

        return False

    def authenticate_user(self, username, password):

        try:

            query_users = """
                    SELECT id, username, password, branch, corporation, role, account_type
                    FROM users
                    WHERE username = %s LIMIT 1
                    """

            result = None
            try:
                result = self.execute_database_query(query_users, [username])
            except Exception as e:

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
  
                    self._migrate_password_if_needed(user_id, password, stored_password)
                    login_rate_limiter.reset(username) 
                    
             
                    if role not in ('admin', 'super_admin'):
                        offline_manager.cache_credentials(db_username, password, {
                            "branch": branch,
                            "corporation": corporation,
                            "role": role
                        })
                    
                    ping_monitor.start(db_manager, db_username, role)
                    self.show_message("Login Success", f"Welcome, {db_username}!", QMessageBox.Information)
                    self.save_credentials(db_username)
                    if role == 'super_admin':
                        try:
                            from super_admin_dashboard import SuperAdminDashboard
                            self.dashboard = SuperAdminDashboard()
                            if hasattr(self.dashboard, 'logout_requested'):
                                self.dashboard.logout_requested.connect(self.handle_logout)
                        except Exception as e:
                            print(f"Error loading SuperAdminDashboard: {e}")
                            self.show_message("Error", "Failed to load super admin dashboard.", QMessageBox.Critical)
                            return
                    elif role == 'admin':
                        try:
                            from admin_dashboard import AdminDashboard
                            acct_type = user_data.get('account_type', 2)
                            self.dashboard = AdminDashboard(account_type=acct_type)
                            if hasattr(self.dashboard, 'logout_requested'):
                                self.dashboard.logout_requested.connect(self.handle_logout)
                        except Exception as e:
                            print(f"Error loading AdminDashboard: {e}")
                            self.show_message("Error", "Failed to load admin dashboard.", QMessageBox.Critical)
                            return
                    else:
                        try:
                            self.dashboard = ClientDashboard(db_username, branch, corporation, db_manager)
                            self.dashboard.logout_requested.connect(self.handle_logout)
                        except Exception as e:
                            import traceback
                            print(f"Error loading ClientDashboard: {e}")
                            traceback.print_exc()
                            self.show_message("Error", "Failed to load client dashboard.", QMessageBox.Critical)
                            return
                    
                    self.dashboard.showMaximized()
                    self.hide() 
                else:
        
                    is_locked, remaining, lockout_time = login_rate_limiter.record_failed_attempt(username)
                    if is_locked:
                        self.show_message(
                            "Account Locked",
                            f"Too many failed attempts.\n\nPlease wait {format_lockout_time(lockout_time)} before trying again.",
                            QMessageBox.Warning
                        )
                    elif remaining > 0:
                        self.show_message("Login Failed", f"Incorrect password.\n{remaining} attempts remaining.", QMessageBox.Warning)
                    else:
                        self.show_message("Login Failed", "Incorrect password.", QMessageBox.Warning)
                return
            
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
        ping_monitor.stop()
        if hasattr(self, '_update_checker_threads'):
            for thread in self._update_checker_threads[:]:
                if thread.isRunning():
                    thread.quit()
                    thread.wait(2000) 
        event.accept()
