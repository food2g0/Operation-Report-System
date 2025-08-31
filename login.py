from PyQt5.QtWidgets import (
    QWidget, QLineEdit, QPushButton, QVBoxLayout, QHBoxLayout,
    QMessageBox, QLabel, QCheckBox
)
from PyQt5.QtCore import QSettings, Qt
from PyQt5.QtGui import QFont

from Client.client_dashboard import ClientDashboard
from db_connect import db_manager
from dotenv import load_dotenv

# Load environment variables
load_dotenv()




class LoginWindow(QWidget):
    def __init__(self, app):
        super().__init__()
        self.app = app
        self.db_connection = None
        self.dashboard = None
        self.setWindowTitle("Secure Login")
        self.setFixedSize(400, 500)
        self.settings = QSettings("MyCompany", "MyApp")

        # Initialize database connection
        self.init_database()

        self.setup_ui()
        self.apply_styles()
        self.load_saved_credentials()
        self.center_window()

    def init_database(self):
        """Initialize MySQL database connection"""
        # Use the global database manager
        self.db_connection = db_manager.connection

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

    def manual_login(self):
        username = self.username_input.text().strip()
        password = self.password_input.text().strip()

        if not username or not password:
            self.show_message("Input Error", "Please enter both username and password.", QMessageBox.Warning)
            return

        # Check if database connection exists
        if not self.db_connection:
            self.show_message("Connection Error", "No database connection available.", QMessageBox.Critical)
            return

        # Disable button during login attempt
        self.login_button.setEnabled(False)
        self.login_button.setText("Logging in...")

        try:
            # Check database connection first
            if not self.test_database_connection():
                self.show_message("Connection Error", "Failed to connect to the database.", QMessageBox.Critical)
                return

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
            if not self.db_connection:
                return False

            with self.db_connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                result = cursor.fetchone()
                return result is not None
        except Exception as e:
            print(f"Database connection test failed: {e}")
            return False

    def execute_database_query(self, query, params=None):
        """Execute database query with MySQL"""
        return db_manager.execute_query(query, params)

    def check_admin_login(self, username, password):
        """Check for hardcoded admin login first, then check database"""
        # Check hardcoded admin (backward compatibility)
        if username.lower() == "admin" and password == "Admin1234":
            try:
                from admin_dashboard import AdminDashboard
                self.show_message("Admin Login", "Welcome, Admin!", QMessageBox.Information)
                self.save_credentials(username)
                self.dashboard = AdminDashboard()
                self.dashboard.show()
                self.close()
                return True
            except Exception as e:
                print(f"Error loading AdminDashboard: {e}")
                self.show_message("Error", "Failed to load admin dashboard.", QMessageBox.Critical)
                return False

        # Check database for admin users
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
                stored_password = user_data['password']  # Use dict key for MySQL DictCursor

                if stored_password == password:
                    try:
                        from admin_dashboard import AdminDashboard
                        self.show_message("Admin Login", f"Welcome, {username}!", QMessageBox.Information)
                        self.save_credentials(username)
                        self.dashboard = AdminDashboard()
                        self.dashboard.show()
                        self.close()
                        return True
                    except Exception as e:
                        print(f"Error loading AdminDashboard: {e}")
                        self.show_message("Error", "Failed to load admin dashboard.", QMessageBox.Critical)
                        return False
        except Exception as e:
            print(f"Database Error during admin check: {e}")
            # Don't show error message here, let it fall through to regular user authentication

        return False

    def authenticate_user(self, username, password):
        """Authenticate regular users from the database"""
        try:
            # Query to get user by username
            query = """
                    SELECT id, username, password, branch, corporation, role
                    FROM users
                    WHERE username = %s LIMIT 1
                    """

            result = self.execute_database_query(query, [username])

            if result:
                user_data = result[0]
                # Extract data from result dictionary (using DictCursor)
                user_id = user_data['id']
                db_username = user_data['username']
                stored_password = user_data['password']
                branch = user_data.get('branch') or "Unknown"
                corporation = user_data.get('corporation') or "Unknown"
                role = user_data['role']

                if stored_password == password:
                    # Successful login
                    self.show_message("Login Success", f"Welcome, {db_username}!", QMessageBox.Information)
                    self.save_credentials(db_username)

                    # Create appropriate dashboard based on role
                    if role == 'admin':
                        try:
                            from admin_dashboard import AdminDashboard
                            self.dashboard = AdminDashboard()
                        except Exception as e:
                            print(f"Error loading AdminDashboard: {e}")
                            self.show_message("Error", "Failed to load admin dashboard.", QMessageBox.Critical)
                            return
                    else:
                        # Regular user dashboard - pass database manager
                        self.dashboard = ClientDashboard(db_username, branch, corporation, db_manager)

                    self.dashboard.show()
                    self.close()
                else:
                    self.show_message("Login Failed", "Incorrect password.", QMessageBox.Warning)
            else:
                self.show_message("Login Failed", "User not found.", QMessageBox.Warning)

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