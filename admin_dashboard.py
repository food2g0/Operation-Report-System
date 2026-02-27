from PyQt5.QtWidgets import (
    QWidget, QLabel, QVBoxLayout, QHBoxLayout, QGroupBox, QFormLayout,
    QLineEdit, QComboBox, QPushButton, QMessageBox, QDateEdit, QStackedWidget,
    QScrollArea, QFrame, QFileDialog
)
from PyQt5.QtGui import QDoubleValidator, QFont, QIntValidator
from PyQt5.QtCore import Qt, QDate, pyqtSignal, QTimer
from db_connect_pooled import db_manager
from security import SessionManager
import json
import os
import sys

from palawan_page import PalawanPage
from mc_page import MCPage
from fund_transfer import FundTransferPage
from payable_page import PayablesPage
from report_page import ReportPage
from admin_manage import create_corporation, create_branch, create_client
from variance_review_page import VarianceReviewPage
from user_management_page import UserManagementPage
from daily_transaction_page import DailyTransactionPage
from new_sanla_page import NewSanlaPage
from new_renew_page import NewRenewPage

# Auto-updater (optional)
try:
    from auto_updater import check_for_updates, check_update_success
    from version import __version__
    AUTO_UPDATE_ENABLED = True
except ImportError:
    AUTO_UPDATE_ENABLED = False
    __version__ = "1.0.0"
    check_update_success = None


class AdminDashboard(QWidget):
    logout_requested = pyqtSignal()
    
    def __init__(self, account_type=2):
        super().__init__()
        # account_type: 1 = Brand A Admin, 2 = Brand B Admin
        self.account_type = account_type
        brand_label = "Brand A" if account_type == 1 else "Brand B"
        self.setWindowTitle(f"Admin Dashboard ({brand_label}) - Cash Management System")
        self.db = db_manager
        self._update_checker_threads = []  # Store update checker threads
        
        # Session management - 30 minute timeout (1800 seconds)
        self.session = SessionManager(inactivity_timeout=1800)
        self._session_timer = QTimer(self)
        self._session_timer.timeout.connect(self._check_session_timeout)
        self._session_timer.start(60000)  # Check every minute

        self.debit_inputs = {}
        self.credit_inputs = {}
        self.debit_lotes_inputs = {}
        self.credit_lotes_inputs = {}

        # Load field mappings from field_config.json based on account_type
        brand_key = "Brand A" if account_type == 1 else "Brand B"
        field_config = self._load_field_config()
        
        if field_config and brand_key in field_config:
            brand_config = field_config[brand_key]
            # Convert list format to dict format: [["Label", "placeholder", "db_column"], ...] -> {"Label": "db_column"}
            self.debit_fields = {item[0]: item[2] for item in brand_config.get("debit", [])}
            self.credit_fields = {item[0]: item[2] for item in brand_config.get("credit", [])}
        else:
            # Fallback to Brand B hardcoded fields if config not found
            self.debit_fields = {
                "Rescate Jewelry": "rescate_jewelry",
                "Interest": "interest",
                "Penalty": "penalty",
                "Stamp": "stamp",
                "Resguardo/Affidavit": "resguardo_affidavit",
                "HABOL Renew/Tubos": "habol_renew_tubos",
                "Habol R/T Interest&Stamp": "habol_rt_interest_stamp",
                "Jew. A.I": "jew_ai",
                "S.C": "sc",
                "Fund Transfer from BRANCH": "fund_transfer_from_branch",
                "Sendah Load + SC": "sendah_load_sc",
                "PPAY CO SC": "ppay_co_sc",
                "Palawan Send Out": "palawan_send_out",
                "Palawan S.C": "palawan_sc",
                "Palawan Suki Card": "palawan_suki_card",
                "Palawan Pay Cash-In + SC": "palawan_pay_cash_in_sc",
                "Palawan Pay Bills + SC": "palawan_pay_bills_sc",
                "Palawan Load": "palawan_load",
                "Palawan Change Receiver": "palawan_change_receiver",
                "MC In": "mc_in",
                "Handling fee": "handling_fee",
                "Other Penalty": "other_penalty",
                "Cash Overage": "cash_overage"
            }
            self.credit_fields = {
                "Empeno JEW. (NEW)": "empeno_jew_new",
                "Empeno JEW (RENEW)": "empeno_jew_renew",
                "Fund Transfer to HEAD OFFICE": "fund_transfer_to_head_office",
                "Fund Transfer to BRANCH": "fund_transfer_to_branch",
                "Palawan Pay Out": "palawan_pay_out",
                "Palawan Pay Out (incentives)": "palawan_pay_out_incentives",
                "Palawan Pay Cash Out": "palawan_pay_cash_out",
                "MC Out": "mc_out",
                "PC-Salary": "pc_salary",
                "PC-Rental": "pc_rental",
                "PC-Electric": "pc_electric",
                "PC-Water": "pc_water",
                "PC-Internet": "pc_internet",
                "PC-Lbc/Jrs/Jnt": "pc_lbc_jrs_jnt",
                "PC-Permits/BIR Payments": "pc_permits_bir_payments",
                "PC-Supplies/Xerox/Maintenance": "pc_supplies_xerox_maintenance",
                "PC-Transpo": "pc_transpo",
                "Palawan Cancel": "palawan_cancel",
                "Palawan Suki Discounts": "palawan_suki_discounts",
                "Palawan Suki Rebates": "palawan_suki_rebates",
                "OTHERS": "others",
                "Cash Shortage": "cash_shortage"
            }

        # Set correct table based on brand: Brand A -> daily_reports_brand_a, Brand B -> daily_reports
        self.daily_table = "daily_reports_brand_a" if account_type == 1 else "daily_reports"
        
        self.setup_styles()
        self.build_ui()
        self.load_corporations()
        
        # Check if the app was just updated and show success message
        if AUTO_UPDATE_ENABLED and check_update_success:
            check_update_success(parent=self)

    def _load_field_config(self):
        """Load field configuration from field_config.json"""
        try:
            # Determine config directory based on whether we're frozen (PyInstaller)
            if getattr(sys, 'frozen', False):
                config_dir = os.path.dirname(sys.executable)
            else:
                config_dir = os.path.dirname(os.path.abspath(__file__))
            
            config_path = os.path.join(config_dir, 'field_config.json')
            
            if os.path.exists(config_path):
                with open(config_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            else:
                print(f"field_config.json not found at {config_path}")
                return None
        except Exception as e:
            print(f"Error loading field_config.json: {e}")
            return None

    def setup_styles(self):

        self.setStyleSheet("""
            /* Main Window */
            QWidget {
                background-color: #f5f6fa;
                font-family: 'Segoe UI', Arial, sans-serif;
                font-size: 12px;
            }

            /* Navigation Buttons */
            QPushButton {
                background-color: #3498db;
                color: black;
                border: none;
                padding: 8px 16px;
                border-radius: 6px;
                font-weight: bold;
                font-size: 12px;
                min-height: 30px;
            }

            QPushButton:hover {
                background-color: #2980b9;
            }

            QPushButton:pressed {
                background-color: #21618c;
            }

            QPushButton#saveButton {
                background-color: #27ae60;
                font-size: 13px;
                padding: 10px 20px;
                min-width: 120px;
            }

            QPushButton#saveButton:hover {
                background-color: #219a52;
            }

            QPushButton#loadButton {
                background-color: #f39c12;
                font-size: 11px;
                padding: 6px 12px;
            }

            QPushButton#loadButton:hover {
                background-color: #e67e22;
            }

            /* Group Boxes */
            QGroupBox {
                font-weight: bold;
                font-size: 13px;
                color: #2c3e50;
                border: 2px solid #bdc3c7;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 15px;
                background-color: white;
            }

            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 8px 0 8px;
                color: #2c3e50;
                font-weight: bold;
                font-size: 14px;
                background-color: white;
            }

            /* Labels */
            QLabel {
                color: #2c3e50;
                font-size: 11px;
                font-weight: bold;
            }

            QLabel[class="header"] {
                font-weight: bold;
                font-size: 13px;
                color: #2c3e50;
            }

            QLabel[class="section"] {
                font-weight: bold;
                font-size: 14px;
                color: #34495e;
                background-color: #ecf0f1;
                padding: 5px;
                border-radius: 4px;
            }

            /* Input Fields */
            QLineEdit {
                border: 1px solid #bdc3c7;
                border-radius: 4px;
                padding: 5px 8px;
                font-size: 11px;
                background-color: white;
                min-height: 20px;
            }

            QLineEdit:focus {
                border: 2px solid #3498db;
            }

            QLineEdit[readOnly="true"] {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                font-weight: bold;
                color: #495057;
            }

            QLineEdit[class="money"] {
                font-weight: bold;
                text-align: right;
                color: #27ae60;
                font-size: 12px;
            }

            QLineEdit[class="result"] {
                background-color: #fff3cd;
                border: 2px solid #ffeaa7;
                font-weight: bold;
                font-size: 12px;
                color: #856404;
            }

            /* Dropdowns */
            QComboBox {
                border: 1px solid #bdc3c7;
                border-radius: 4px;
                padding: 5px 8px;
                background-color: white;
                font-size: 11px;
                min-width: 120px;
                min-height: 25px;
            }

            QComboBox:focus {
                border: 2px solid #3498db;
            }

            QComboBox::drop-down {
                border: none;
                width: 20px;
            }

            QComboBox::down-arrow {
                width: 12px;
                height: 12px;
            }

            /* Date Edit */
            QDateEdit {
                border: 1px solid #bdc3c7;
                border-radius: 4px;
                padding: 5px 8px;
                background-color: white;
                font-size: 11px;
                min-height: 25px;
                min-width: 120px;
            }

            QDateEdit:focus {
                border: 2px solid #3498db;
            }

            /* Scroll Area */
            QScrollArea {
                border: none;
                background-color: transparent;
            }

            /* Navigation Bar */
            QFrame#navBar {
                background-color: #34495e;
                border-radius: 8px;
                margin-bottom: 10px;
                padding: 5px;
            }

            QFrame#navBar QPushButton {
                background-color: #34495e;
                border: 2px solid transparent;
                color: #ecf0f1;
                font-size: 12px;
                font-weight: bold;
                padding: 10px 15px;
                border-radius: 6px;
            }

            QFrame#navBar QPushButton:hover {
                background-color: #3498db;
                border-color: #3498db;
            }

            QFrame#navBar QPushButton:checked {
                background-color: #3498db;
                border-color: #2980b9;
            }
        """)

    def build_ui(self):
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(10)

        # --- HEADER WITH LOGOUT ---
        header_frame = QFrame()
        header_frame.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #3498db, stop:1 #2980b9);
                border-radius: 8px;
                padding: 15px;
                margin-bottom: 10px;
            }
        """)
        header_layout = QHBoxLayout(header_frame)
        
        # Left side - Title
        title_label = QLabel("🔧 Admin Dashboard")
        title_label.setStyleSheet("font-size: 20px; font-weight: bold; color: white;")
        
        # Right side - Update and Logout buttons
        if AUTO_UPDATE_ENABLED:
            update_button = QPushButton(f"ℹ️ v{__version__}")
            update_button.setStyleSheet("""
                QPushButton {
                    background-color: #16a085;
                    color: white;
                    border: none;
                    padding: 10px 20px;
                    border-radius: 6px;
                    font-weight: bold;
                    font-size: 11px;
                    min-width: 80px;
                    max-height: 40px;
                }
                QPushButton:hover {
                    background-color: #1abc9c;
                }
                QPushButton:pressed {
                    background-color: #138d75;
                }
            """)
            update_button.clicked.connect(self.check_for_updates)
            update_button.setToolTip("Check for updates")
        
        logout_button = QPushButton("🚪 Logout")
        logout_button.setStyleSheet("""
            QPushButton {
                background-color: #e74c3c;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 6px;
                font-weight: bold;
                font-size: 12px;
                min-width: 100px;
                max-height: 40px;
            }
            QPushButton:hover {
                background-color: #c0392b;
            }
            QPushButton:pressed {
                background-color: #a93226;
            }
        """)
        logout_button.clicked.connect(self.handle_logout)
        
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        if AUTO_UPDATE_ENABLED:
            header_layout.addWidget(update_button)
        header_layout.addWidget(logout_button)
        
        main_layout.addWidget(header_frame)

        # --- NAVIGATION BAR ---
        nav_frame = QFrame()
        nav_frame.setObjectName("navBar")
        nav_layout = QHBoxLayout(nav_frame)
        nav_layout.setContentsMargins(10, 8, 10, 8)
        nav_layout.setSpacing(5)

        # Create all buttons
        self.daily_btn = QPushButton("📊 Daily Cash Count")
        self.variance_btn = QPushButton("⚠️ Variance Review")
        self.palawan_btn = QPushButton("🏦 Palawan")
        self.mc_btn = QPushButton("💳 MC")
        self.fund_btn = QPushButton("💰 Fund Transfer")
        self.payable_btn = QPushButton("💰 Payable")
        self.report_btn = QPushButton("📈 Payable Reports")
        self.daily_txn_btn = QPushButton("📋 Daily Transaction")
        self.new_sanla_btn = QPushButton("🆕 New Sanla")
        self.new_renew_btn = QPushButton("🔄 New & Renew")
        self.admin_btn = QPushButton("⚙️ User Management")

        # Make buttons checkable for active state
        for btn in [self.daily_btn, self.variance_btn, self.palawan_btn, self.mc_btn,
                    self.fund_btn, self.payable_btn, self.report_btn, self.daily_txn_btn,
                    self.new_sanla_btn, self.new_renew_btn, self.admin_btn]:
            btn.setCheckable(True)
        self.daily_btn.setChecked(True)  # Default selection

        # Brand A Admin (account_type=1): Daily Cash, Variance, Palawan, MC, Fund Transfer,
        #                                 Payable, Daily Txn, New Sanla, New & Renew, User Mgmt
        # Brand B Admin (account_type=2): Daily Cash, Variance, Palawan, MC, Fund Transfer,
        #                                 Payable, Payable Reports, User Mgmt
        if self.account_type == 1:
            # Brand A Admin tabs
            self.nav_buttons = [
                self.daily_btn, self.variance_btn, self.palawan_btn, self.mc_btn,
                self.fund_btn, self.payable_btn, self.daily_txn_btn, self.new_sanla_btn,
                self.new_renew_btn, self.admin_btn
            ]
        else:
            # Brand B Admin tabs
            self.nav_buttons = [
                self.daily_btn, self.variance_btn, self.palawan_btn, self.mc_btn,
                self.fund_btn, self.payable_btn, self.report_btn, self.admin_btn
            ]

        for btn in self.nav_buttons:
            nav_layout.addWidget(btn)
        nav_layout.addStretch()

        main_layout.addWidget(nav_frame)

        # --- STACKED VIEWS ---
        self.stack = QStackedWidget()
        
        # Create all widgets - pass account_type where needed for brand-specific data
        self.daily_cash_widget = self.build_daily_cash_widget()
        self.variance_widget = VarianceReviewPage(account_type=self.account_type)
        self.palawan_widget = PalawanPage(account_type=self.account_type)
        self.mc_widget = MCPage(account_type=self.account_type)
        self.fund_widget = FundTransferPage(account_type=self.account_type)
        self.payable_widget = PayablesPage(account_type=self.account_type)
        self.report_widget = ReportPage()
        self.daily_txn_widget = DailyTransactionPage()
        self.new_sanla_widget = NewSanlaPage()
        self.new_renew_widget = NewRenewPage()
        self.admin_widget = UserManagementPage()

        # Add widgets to stack based on account type
        # Brand A: Daily Cash, Variance, Palawan, MC, Fund, Payable, Daily Txn, New Sanla, New Renew, User Mgmt
        # Brand B: Daily Cash, Variance, Palawan, MC, Fund, Payable, Report, User Mgmt
        if self.account_type == 1:
            # Brand A Admin stack
            self.stack.addWidget(self.daily_cash_widget)  # index 0
            self.stack.addWidget(self.variance_widget)    # index 1
            self.stack.addWidget(self.palawan_widget)     # index 2
            self.stack.addWidget(self.mc_widget)          # index 3
            self.stack.addWidget(self.fund_widget)        # index 4
            self.stack.addWidget(self.payable_widget)     # index 5
            self.stack.addWidget(self.daily_txn_widget)   # index 6
            self.stack.addWidget(self.new_sanla_widget)   # index 7
            self.stack.addWidget(self.new_renew_widget)   # index 8
            self.stack.addWidget(self.admin_widget)       # index 9
        else:
            # Brand B Admin stack
            self.stack.addWidget(self.daily_cash_widget)  # index 0
            self.stack.addWidget(self.variance_widget)    # index 1
            self.stack.addWidget(self.palawan_widget)     # index 2
            self.stack.addWidget(self.mc_widget)          # index 3
            self.stack.addWidget(self.fund_widget)        # index 4
            self.stack.addWidget(self.payable_widget)     # index 5
            self.stack.addWidget(self.report_widget)      # index 6
            self.stack.addWidget(self.admin_widget)       # index 7
        
        main_layout.addWidget(self.stack)

        # Connect nav buttons to switch views
        if self.account_type == 1:
            # Brand A connections
            self.daily_btn.clicked.connect(lambda: self.switch_view(0, self.daily_btn))
            self.variance_btn.clicked.connect(lambda: self.switch_view(1, self.variance_btn))
            self.palawan_btn.clicked.connect(lambda: self.switch_view(2, self.palawan_btn))
            self.mc_btn.clicked.connect(lambda: self.switch_view(3, self.mc_btn))
            self.fund_btn.clicked.connect(lambda: self.switch_view(4, self.fund_btn))
            self.payable_btn.clicked.connect(lambda: self.switch_view(5, self.payable_btn))
            self.daily_txn_btn.clicked.connect(lambda: self.switch_view(6, self.daily_txn_btn))
            self.new_sanla_btn.clicked.connect(lambda: self.switch_view(7, self.new_sanla_btn))
            self.new_renew_btn.clicked.connect(lambda: self.switch_view(8, self.new_renew_btn))
            self.admin_btn.clicked.connect(lambda: self.switch_view(9, self.admin_btn))
        else:
            # Brand B connections
            self.daily_btn.clicked.connect(lambda: self.switch_view(0, self.daily_btn))
            self.variance_btn.clicked.connect(lambda: self.switch_view(1, self.variance_btn))
            self.palawan_btn.clicked.connect(lambda: self.switch_view(2, self.palawan_btn))
            self.mc_btn.clicked.connect(lambda: self.switch_view(3, self.mc_btn))
            self.fund_btn.clicked.connect(lambda: self.switch_view(4, self.fund_btn))
            self.payable_btn.clicked.connect(lambda: self.switch_view(5, self.payable_btn))
            self.report_btn.clicked.connect(lambda: self.switch_view(6, self.report_btn))
            self.admin_btn.clicked.connect(lambda: self.switch_view(7, self.admin_btn))

        self.setLayout(main_layout)

    def handle_logout(self):
        """Handle logout button click"""
        reply = QMessageBox.question(
            self,
            "Confirm Logout",
            "Are you sure you want to logout?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.session.logout()
            self.logout_requested.emit()
            self.close()
    
    def _check_session_timeout(self):
        """Check if session has timed out due to inactivity"""
        if self.session.check_timeout():
            self._session_timer.stop()
            QMessageBox.warning(
                self,
                "Session Expired",
                "Your session has expired due to inactivity.\nPlease log in again.",
                QMessageBox.Ok
            )
            self.logout_requested.emit()
            self.close()
    
    def mousePressEvent(self, event):
        """Reset session timer on mouse activity"""
        self.session.update_activity()
        super().mousePressEvent(event)
    
    def keyPressEvent(self, event):
        """Reset session timer on keyboard activity"""
        self.session.update_activity()
        super().keyPressEvent(event)
    
    def check_for_updates(self):
        """Manually check for application updates"""
        if AUTO_UPDATE_ENABLED:
            check_for_updates(parent=self, silent=False)
        else:
            QMessageBox.information(
                self,
                "Auto-Updater",
                "Auto-updater is not enabled.\n\n"
                "To enable it, install required dependencies:\n"
                "pip install requests packaging"
            )
    
    def closeEvent(self, event):
        """Clean up threads before closing"""
        # Wait for update checker threads to finish (max 2 seconds)
        if hasattr(self, '_update_checker_threads'):
            for thread in self._update_checker_threads[:]:
                if thread.isRunning():
                    thread.quit()
                    thread.wait(2000)  # Wait up to 2 seconds
        event.accept()

    def switch_view(self, index, active_button):
        """Switch view and update button states"""
        self.stack.setCurrentIndex(index)
        # Uncheck all buttons
        for btn in self.nav_buttons:
            if btn:
                btn.setChecked(False)
        # Check active button
        if active_button:
            active_button.setChecked(True)

    def build_daily_cash_widget(self):
        # Create main widget with scroll area for small screens
        main_widget = QWidget()
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setWidget(main_widget)

        layout = QVBoxLayout(main_widget)
        layout.setSpacing(15)

        # --- HEADER SECTION ---
        header_frame = QFrame()
        header_frame.setStyleSheet("background-color: white; border-radius: 8px; padding: 10px;")
        header_layout = QVBoxLayout(header_frame)

        # Filter Type Selection (Corporation or OS)
        filter_type_layout = QHBoxLayout()
        filter_type_label = QLabel("Filter By:")
        filter_type_label.setProperty("class", "header")
        self.filter_type_selector = QComboBox()
        self.filter_type_selector.addItem("Corporation", "corporation")
        self.filter_type_selector.addItem("OS", "os")
        self.filter_type_selector.currentIndexChanged.connect(self.on_filter_type_changed)
        filter_type_layout.addWidget(filter_type_label)
        filter_type_layout.addWidget(self.filter_type_selector)
        filter_type_layout.addStretch()
        header_layout.addLayout(filter_type_layout)

        # Corporation and Branch Selection
        selection_layout = QHBoxLayout()
        selection_layout.setSpacing(15)

        # Corporation selector
        self.corp_label = QLabel("Corporation:")
        self.corp_label.setProperty("class", "header")
        self.corp_selector = QComboBox()
        self.corp_selector.currentTextChanged.connect(self.load_branches)

        # OS selector (hidden by default)
        self.os_label = QLabel("OS:")
        self.os_label.setProperty("class", "header")
        self.os_selector = QComboBox()
        self.os_selector.currentTextChanged.connect(self.load_branches_by_os)
        self.os_label.setVisible(False)
        self.os_selector.setVisible(False)

        branch_label = QLabel("Branch:")
        branch_label.setProperty("class", "header")
        self.branch_selector = QComboBox()

        date_label = QLabel("Date:")
        date_label.setProperty("class", "header")
        self.date_picker = QDateEdit()
        self.date_picker.setDisplayFormat("yyyy-MM-dd")
        self.date_picker.setCalendarPopup(True)
        self.date_picker.setDate(QDate.currentDate())

        self.load_button = QPushButton("Load Entry")
        self.load_button.setObjectName("loadButton")
        self.load_button.clicked.connect(self.load_entry_by_date)

        selection_layout.addWidget(self.corp_label)
        selection_layout.addWidget(self.corp_selector, 1)
        selection_layout.addWidget(self.os_label)
        selection_layout.addWidget(self.os_selector, 1)
        selection_layout.addWidget(branch_label)
        selection_layout.addWidget(self.branch_selector, 1)
        selection_layout.addWidget(date_label)
        selection_layout.addWidget(self.date_picker)
        selection_layout.addWidget(self.load_button)

        header_layout.addLayout(selection_layout)

        # Beginning Balance Section
        balance_layout = QHBoxLayout()
        balance_label = QLabel("💰 Beginning Balance:")
        balance_label.setProperty("class", "important")
        self.beginning_balance_input = self.create_money_input()
        self.beginning_balance_input.setReadOnly(True)
        balance_layout.addWidget(balance_label)
        balance_layout.addWidget(self.beginning_balance_input)
        balance_layout.addStretch()

        header_layout.addLayout(balance_layout)
        layout.addWidget(header_frame)

        # --- TRANSACTION SECTIONS ---
        columns_layout = QHBoxLayout()
        columns_layout.setSpacing(15)

        # Debit Section
        debit_box = QGroupBox("💸 DEBIT")
        debit_form = QFormLayout()
        debit_form.setSpacing(8)
        debit_form.setLabelAlignment(Qt.AlignLeft)

        for label in self.debit_fields.keys():
            field_input = self.create_money_input()
            field_input.setReadOnly(False)  # Editable for admin
            self.debit_inputs[label] = field_input

            lotes_input = self.create_lotes_input(read_only=False)  # Editable for admin
            self.debit_lotes_inputs[label] = lotes_input

            row = QHBoxLayout()
            row.setContentsMargins(0, 0, 0, 0)
            row.setSpacing(6)
            row.addWidget(field_input, 2)
            lotes_label = QLabel("Lotes:")
            row.addWidget(lotes_label)
            row.addWidget(lotes_input)

            field_label = QLabel(label)
            if any(keyword in label.lower() for keyword in ['interest', 'penalty', 'rescate']):
                field_label.setProperty("class", "important")
            debit_form.addRow(field_label, row)

        debit_box.setLayout(debit_form)

        # Credit Section
        credit_box = QGroupBox("💳 CREDIT")
        credit_form = QFormLayout()
        credit_form.setSpacing(8)
        credit_form.setLabelAlignment(Qt.AlignLeft)

        for label in self.credit_fields.keys():
            field_input = self.create_money_input()
            field_input.setReadOnly(False)  # Editable for admin
            self.credit_inputs[label] = field_input

            lotes_input = self.create_lotes_input(read_only=False)  # Editable for admin
            self.credit_lotes_inputs[label] = lotes_input

            row = QHBoxLayout()
            row.setContentsMargins(0, 0, 0, 0)
            row.setSpacing(6)
            row.addWidget(field_input, 2)
            lotes_label = QLabel("Lotes:")
            row.addWidget(lotes_label)
            row.addWidget(lotes_input)

            field_label = QLabel(label)
            if any(keyword in label.lower() for keyword in ['empeno', 'fund transfer', 'salary']):
                field_label.setProperty("class", "important")
            credit_form.addRow(field_label, row)

        credit_box.setLayout(credit_form)

        columns_layout.addWidget(debit_box)
        columns_layout.addWidget(credit_box)
        layout.addLayout(columns_layout)

        # --- TOTALS SECTION ---
        totals_frame = QFrame()
        totals_frame.setStyleSheet(
            "background-color: #e8f5e9; border: 2px solid #81c784; border-radius: 8px; padding: 15px;")
        totals_layout = QHBoxLayout(totals_frame)

        # Total Debit
        debit_total_label = QLabel("💸 Total Debit:")
        debit_total_label.setProperty("class", "important")
        debit_total_label.setStyleSheet("font-weight: bold; font-size: 12px; color: #2e7d32;")
        self.debit_total_display = self.create_display_field()
        self.debit_total_display.setStyleSheet(
            "background-color: #c8e6c9; border: 2px solid #66bb6a; font-weight: bold; font-size: 12px; color: #1b5e20;")

        # Total Credit
        credit_total_label = QLabel("💳 Total Credit:")
        credit_total_label.setProperty("class", "important")
        credit_total_label.setStyleSheet("font-weight: bold; font-size: 12px; color: #c62828;")
        self.credit_total_display = self.create_display_field()
        self.credit_total_display.setStyleSheet(
            "background-color: #ffcdd2; border: 2px solid #e57373; font-weight: bold; font-size: 12px; color: #b71c1c;")

        totals_layout.addWidget(debit_total_label)
        totals_layout.addWidget(self.debit_total_display, 1)
        totals_layout.addWidget(credit_total_label)
        totals_layout.addWidget(self.credit_total_display, 1)

        layout.addWidget(totals_frame)

        # --- RESULTS SECTION ---
        results_frame = QFrame()
        results_frame.setStyleSheet(
            "background-color: #fff3cd; border: 2px solid #ffeaa7; border-radius: 8px; padding: 15px;")
        results_layout = QHBoxLayout(results_frame)

        # Ending Balance
        ending_label = QLabel("📊 Ending Balance:")
        ending_label.setProperty("class", "important")
        self.ending_balance_display = self.create_display_field()
        self.ending_balance_display.setProperty("class", "result")

        # Cash Count
        cash_label = QLabel("💵 Cash Count:")
        cash_label.setProperty("class", "important")
        self.cash_count_input = self.create_money_input()
        self.cash_count_input.setReadOnly(True)

        # Cash Result
        result_label = QLabel("⚖️ Short/Over:")
        result_label.setProperty("class", "important")
        self.cash_result_display = self.create_display_field()
        self.cash_result_display.setProperty("class", "result")

        results_layout.addWidget(ending_label)
        results_layout.addWidget(self.ending_balance_display, 1)
        results_layout.addWidget(cash_label)
        results_layout.addWidget(self.cash_count_input, 1)
        results_layout.addWidget(result_label)
        results_layout.addWidget(self.cash_result_display, 1)
        
        # Variance Status Display
        status_label = QLabel("🏷️ Status:")
        status_label.setProperty("class", "important")
        self.variance_status_display = QLabel("—")
        self.variance_status_display.setStyleSheet(
            "font-weight: bold; font-size: 12px; padding: 5px 10px; border-radius: 4px;"
        )
        results_layout.addWidget(status_label)
        results_layout.addWidget(self.variance_status_display)

        layout.addWidget(results_frame)
        
        # --- ACTION BUTTONS ---
        action_layout = QHBoxLayout()
        action_layout.addStretch()
        
        # Save button
        save_button = QPushButton("💾 Save Changes")
        save_button.setObjectName("saveButton")
        save_button.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                color: white;
            }
            QPushButton:hover {
                background-color: #219a52;
            }
        """)
        save_button.clicked.connect(self.save_entry)
        
        delete_button = QPushButton("🗑️ Delete Entry (Reset)")
        delete_button.setObjectName("deleteButton")
        delete_button.setStyleSheet("""
            QPushButton {
                background-color: #e74c3c;
                color: white;
            }
            QPushButton:hover {
                background-color: #c0392b;
            }
        """)
        delete_button.clicked.connect(self.delete_entry)
        
        export_button = QPushButton("📊 Export to Excel")
        export_button.setObjectName("exportButton")
        export_button.setStyleSheet("""
            QPushButton {
                background-color: #217346;
                color: white;
            }
            QPushButton:hover {
                background-color: #1a5c38;
            }
        """)
        export_button.clicked.connect(self.export_daily_cash_to_excel)
        
        generate_report_button = QPushButton("📋 Generate Report")
        generate_report_button.setObjectName("generateReportButton")
        generate_report_button.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
        """)
        generate_report_button.clicked.connect(self.show_generate_report_dialog)
        
        action_layout.addWidget(save_button)
        action_layout.addWidget(delete_button)
        action_layout.addWidget(export_button)
        action_layout.addWidget(generate_report_button)
        layout.addLayout(action_layout)

        # Return scroll area instead of main widget
        container = QWidget()
        container_layout = QVBoxLayout(container)
        container_layout.addWidget(scroll_area)
        return container

    def create_money_input(self):
        field = QLineEdit()
        field.setValidator(QDoubleValidator(0.0, 1e12, 2))
        field.setProperty("class", "money")
        field.setPlaceholderText("0.00")
        return field

    def create_display_field(self):
        field = QLineEdit()
        field.setReadOnly(True)
        field.setProperty("class", "result")
        return field

    def create_lotes_input(self, read_only=False):
        field = QLineEdit()
        field.setValidator(QIntValidator(0, 999999))
        field.setPlaceholderText("0")
        field.setMaximumWidth(70)
        field.setReadOnly(bool(read_only))
        return field

    def build_admin_widget(self):
        """Build Admin Manage UI for corporations, branches, and clients"""
        widget = QWidget()
        
        # Create scroll area
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_content = QWidget()
        layout = QVBoxLayout(scroll_content)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)

        # --- Corporations Section ---
        corp_box = QGroupBox("📊 Manage Corporations")
        corp_box.setStyleSheet("""
            QGroupBox {
                font-size: 14px;
                font-weight: bold;
                padding-top: 20px;
            }
        """)
        corp_layout = QVBoxLayout()
        
        # Input form
        corp_form = QFormLayout()
        corp_form.setSpacing(10)
        self.corp_name_input = QLineEdit()
        self.corp_name_input.setPlaceholderText("Enter corporation name")
        
        corp_add_btn = QPushButton("➕ Add Corporation")
        corp_add_btn.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                padding: 8px 16px;
            }
            QPushButton:hover {
                background-color: #229954;
            }
        """)
        corp_add_btn.clicked.connect(self._on_add_corporation)
        
        corp_form.addRow(QLabel("Corporation Name:"), self.corp_name_input)
        corp_form.addRow(corp_add_btn)
        
        # List display
        self.corp_list_display = QLabel("No corporations loaded")
        self.corp_list_display.setStyleSheet("""
            QLabel {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 4px;
                padding: 10px;
                font-family: 'Courier New', monospace;
                font-size: 10px;
                min-height: 100px;
            }
        """)
        self.corp_list_display.setWordWrap(True)
        self.corp_list_display.setTextInteractionFlags(Qt.TextSelectableByMouse)
        
        corp_refresh_btn = QPushButton("🔄 Refresh List")
        corp_refresh_btn.clicked.connect(self._refresh_corporation_display)
        
        corp_layout.addLayout(corp_form)
        corp_layout.addWidget(QLabel("Existing Corporations:"))
        corp_layout.addWidget(self.corp_list_display)
        corp_layout.addWidget(corp_refresh_btn)
        corp_box.setLayout(corp_layout)

        # --- Branches Section ---
        branch_box = QGroupBox("🏢 Manage Branches")
        branch_box.setStyleSheet("""
            QGroupBox {
                font-size: 14px;
                font-weight: bold;
                padding-top: 20px;
            }
        """)
        branch_layout = QVBoxLayout()
        
        # Input form
        branch_form = QFormLayout()
        branch_form.setSpacing(10)
        self.branch_corp_selector = QComboBox()
        self.branch_corp_selector.setMinimumWidth(200)
        self.branch_name_input = QLineEdit()
        self.branch_name_input.setPlaceholderText("Enter branch name")
        
        branch_add_btn = QPushButton("➕ Add Branch")
        branch_add_btn.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                padding: 8px 16px;
            }
            QPushButton:hover {
                background-color: #229954;
            }
        """)
        branch_add_btn.clicked.connect(self._on_add_branch)
        
        branch_form.addRow(QLabel("Select Corporation:"), self.branch_corp_selector)
        branch_form.addRow(QLabel("Branch Name:"), self.branch_name_input)
        branch_form.addRow(branch_add_btn)
        
        # List display
        self.branch_list_display = QLabel("No branches loaded")
        self.branch_list_display.setStyleSheet("""
            QLabel {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 4px;
                padding: 10px;
                font-family: 'Courier New', monospace;
                font-size: 10px;
                min-height: 100px;
            }
        """)
        self.branch_list_display.setWordWrap(True)
        self.branch_list_display.setTextInteractionFlags(Qt.TextSelectableByMouse)
        
        branch_refresh_btn = QPushButton("🔄 Refresh List")
        branch_refresh_btn.clicked.connect(self._refresh_branch_display)
        
        branch_layout.addLayout(branch_form)
        branch_layout.addWidget(QLabel("Existing Branches:"))
        branch_layout.addWidget(self.branch_list_display)
        branch_layout.addWidget(branch_refresh_btn)
        branch_box.setLayout(branch_layout)

        # --- Clients Section ---
        client_box = QGroupBox("👥 Manage Clients")
        client_box.setStyleSheet("""
            QGroupBox {
                font-size: 14px;
                font-weight: bold;
                padding-top: 20px;
            }
        """)
        client_layout = QVBoxLayout()
        
        # Input form
        client_form = QFormLayout()
        client_form.setSpacing(10)
        
        # Username display (read-only, auto-generated)
        self.client_username_display = QLineEdit()
        self.client_username_display.setReadOnly(True)
        self.client_username_display.setPlaceholderText("Auto-generated (e.g., CL-0001)")
        self.client_username_display.setStyleSheet("""
            QLineEdit {
                background-color: #e9ecef;
                font-weight: bold;
                color: #495057;
                border: 2px solid #ced4da;
            }
        """)
        
        self.client_first_input = QLineEdit()
        self.client_first_input.setPlaceholderText("Enter first name")
        self.client_last_input = QLineEdit()
        self.client_last_input.setPlaceholderText("Enter last name")
        self.client_corp_selector = QComboBox()
        self.client_corp_selector.setMinimumWidth(200)
        self.client_branch_selector = QComboBox()
        self.client_branch_selector.setMinimumWidth(200)
        self.client_password_input = QLineEdit()
        self.client_password_input.setPlaceholderText("Enter password")
        self.client_password_input.setEchoMode(QLineEdit.Password)
        
        # Preview button to generate username
        preview_btn = QPushButton("👁️ Preview Username")
        preview_btn.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                padding: 6px 12px;
                font-size: 10px;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
        """)
        preview_btn.clicked.connect(self._preview_username)
        
        client_add_btn = QPushButton("➕ Add Client")
        client_add_btn.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                padding: 8px 16px;
            }
            QPushButton:hover {
                background-color: #229954;
            }
        """)
        client_add_btn.clicked.connect(self._on_add_client)
        
        client_form.addRow(QLabel("Username (Auto):"), self.client_username_display)
        client_form.addRow(preview_btn)
        client_form.addRow(QLabel("First Name:"), self.client_first_input)
        client_form.addRow(QLabel("Last Name:"), self.client_last_input)
        client_form.addRow(QLabel("Corporation:"), self.client_corp_selector)
        client_form.addRow(QLabel("Branch:"), self.client_branch_selector)
        client_form.addRow(QLabel("Password:"), self.client_password_input)
        client_form.addRow(client_add_btn)
        
        # List display
        self.client_list_display = QLabel("No clients loaded")
        self.client_list_display.setStyleSheet("""
            QLabel {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 4px;
                padding: 10px;
                font-family: 'Courier New', monospace;
                font-size: 10px;
                min-height: 150px;
            }
        """)
        self.client_list_display.setWordWrap(True)
        self.client_list_display.setTextInteractionFlags(Qt.TextSelectableByMouse)
        
        client_refresh_btn = QPushButton("🔄 Refresh List")
        client_refresh_btn.clicked.connect(self._refresh_client_display)
        
        client_layout.addLayout(client_form)
        client_layout.addWidget(QLabel("Existing Clients:"))
        client_layout.addWidget(self.client_list_display)
        client_layout.addWidget(client_refresh_btn)
        client_box.setLayout(client_layout)

        # Add all sections to main layout
        layout.addWidget(corp_box)
        layout.addWidget(branch_box)
        layout.addWidget(client_box)
        layout.addStretch()

        # Set scroll content
        scroll_area.setWidget(scroll_content)
        
        # Main widget layout
        main_layout = QVBoxLayout(widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(scroll_area)

        # Initial population
        self._refresh_admin_corporations()
        self._refresh_corporation_display()
        self._refresh_branch_display()
        self._refresh_client_display()

        # Update branches when corp selectors change
        self.branch_corp_selector.currentIndexChanged.connect(
            lambda: self._refresh_admin_branches(self.branch_corp_selector.currentData())
        )
        self.client_corp_selector.currentIndexChanged.connect(
            lambda: self._refresh_admin_branches(self.client_corp_selector.currentData(), target='client')
        )

        return widget

    def _preview_username(self):
       
        try:
            row = self.db.execute_query(
                "SELECT MAX(CAST(SUBSTRING(username,4) AS UNSIGNED)) AS maxnum FROM users WHERE username LIKE 'CL-%'"
            )
            maxnum = 0
            if row and row[0] and row[0].get('maxnum') is not None:
                try:
                    maxnum = int(row[0]['maxnum'])
                except Exception:
                    maxnum = 0
            
            next_num = maxnum + 1
            username = f"CL-{str(next_num).zfill(4)}"
            self.client_username_display.setText(username)
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to preview username: {e}")

    def _refresh_corporation_display(self):
      
        try:
            rows = self.db.execute_query("SELECT id, name, created_at FROM corporations ORDER BY name")
            if not rows:
                self.corp_list_display.setText("No corporations found")
                return
            
            # Create professional table-like display
            display_text = "┌─────┬────────────────────────────────┬─────────────────────┐\n"
            display_text += "│ ID  │ Corporation Name               │ Created At          │\n"
            display_text += "├─────┼────────────────────────────────┼─────────────────────┤\n"
            
            for r in rows:
                corp_id = str(r['id']).ljust(3)
                name = str(r['name'])[:30].ljust(30)
                created = str(r.get('created_at', 'N/A'))[:19].ljust(19)
                display_text += f"│ {corp_id} │ {name} │ {created} │\n"
            
            display_text += "└─────┴────────────────────────────────┴─────────────────────┘"
            self.corp_list_display.setText(display_text)
            
        except Exception as e:
            self.corp_list_display.setText(f"Error loading corporations: {e}")

    def _refresh_branch_display(self):
 
        try:
            query = """
                SELECT b.id, b.name, b.corporation_id, c.name as corp_name, b.created_at
                FROM branches b
                LEFT JOIN corporations c ON b.corporation_id = c.id
                ORDER BY c.name, b.name
            """
            rows = self.db.execute_query(query)
            if not rows:
                self.branch_list_display.setText("No branches found")
                return
            
            # Create professional table-like display
            display_text = "┌─────┬──────────────────────┬──────────────────────┬─────────────────────┐\n"
            display_text += "│ ID  │ Branch Name          │ Corporation          │ Created At          │\n"
            display_text += "├─────┼──────────────────────┼──────────────────────┼─────────────────────┤\n"
            
            for r in rows:
                branch_id = str(r['id']).ljust(3)
                name = str(r['name'])[:20].ljust(20)
                corp = str(r.get('corp_name', 'N/A'))[:20].ljust(20)
                created = str(r.get('created_at', 'N/A'))[:19].ljust(19)
                display_text += f"│ {branch_id} │ {name} │ {corp} │ {created} │\n"
            
            display_text += "└─────┴──────────────────────┴──────────────────────┴─────────────────────┘"
            self.branch_list_display.setText(display_text)
            
        except Exception as e:
            self.branch_list_display.setText(f"Error loading branches: {e}")

    def _refresh_client_display(self):
        """Refresh the client list display"""
        try:
            query = """
                SELECT u.id, u.username, u.first_name, u.last_name, 
                       u.corporation as corp_name, u.branch as branch_name, u.created_at
                FROM users u
                WHERE u.role = 'user'
                ORDER BY u.id DESC
                LIMIT 50
            """
            rows = self.db.execute_query(query)
            if not rows:
                self.client_list_display.setText("No clients found")
                return
            
            # Create professional table-like display
            display_text = "┌─────┬──────────┬──────────────────────┬──────────────────┬──────────────────┬─────────────────────┐\n"
            display_text += "│ ID  │ Username │ Name                 │ Corporation      │ Branch           │ Created At          │\n"
            display_text += "├─────┼──────────┼──────────────────────┼──────────────────┼──────────────────┼─────────────────────┤\n"
            
            for r in rows:
                client_id = str(r['id']).ljust(3)
                username = str(r['username']).ljust(8)
                full_name = f"{r.get('first_name', '')} {r.get('last_name', '')}"[:20].ljust(20)
                corp = str(r.get('corp_name', 'N/A'))[:16].ljust(16)
                branch = str(r.get('branch_name', 'N/A'))[:16].ljust(16)
                created = str(r.get('created_at', 'N/A'))[:19].ljust(19)
                display_text += f"│ {client_id} │ {username} │ {full_name} │ {corp} │ {branch} │ {created} │\n"
            
            display_text += "└─────┴──────────┴──────────────────────┴──────────────────┴──────────────────┴─────────────────────┘"
            display_text += f"\n\nShowing last 50 clients (Total in database may be more)"
            self.client_list_display.setText(display_text)
            
        except Exception as e:
            self.client_list_display.setText(f"Error loading clients: {e}")

    def load_corporations(self):
     
        try:
            self.corp_selector.clear()
            # Query all corporations from corporations table
            result = self.db.execute_query("SELECT name as corporation FROM corporations ORDER BY name")
            if result:
                for row in result:
                    if row['corporation']:
                        self.corp_selector.addItem(row['corporation'])
            # Also load OS options
            self.load_os_options()
        except Exception as e:
            print(f"Error loading corporations: {e}")
            QMessageBox.critical(self, "Database Error", f"Failed to load corporations: {e}")

    def load_os_options(self):
        """Load OS names for the OS selector"""
        try:
            self.os_selector.clear()
            result = self.db.execute_query("""
                SELECT DISTINCT os_name FROM branches 
                WHERE os_name IS NOT NULL AND os_name != '' 
                ORDER BY os_name
            """)
            if result:
                for row in result:
                    os_name = row['os_name'] if isinstance(row, dict) else row[0]
                    if os_name:
                        self.os_selector.addItem(os_name)
        except Exception as e:
            print(f"Error loading OS options: {e}")

    def on_filter_type_changed(self):
        """Toggle between Corporation and OS filtering"""
        filter_type = self.filter_type_selector.currentData()
        if filter_type == "corporation":
            self.corp_label.setVisible(True)
            self.corp_selector.setVisible(True)
            self.os_label.setVisible(False)
            self.os_selector.setVisible(False)
            # Reload branches for current corporation
            self.load_branches()
        else:
            self.corp_label.setVisible(False)
            self.corp_selector.setVisible(False)
            self.os_label.setVisible(True)
            self.os_selector.setVisible(True)
            # Load branches for current OS
            self.load_branches_by_os()

    def load_branches(self):
    
        try:
            self.branch_selector.clear()
            corp_name = self.corp_selector.currentText()
            if corp_name:
                # Query all branches belonging to this corporation
                query = """
                    SELECT b.name as branch
                    FROM branches b
                    INNER JOIN corporations c ON b.corporation_id = c.id
                    WHERE c.name = %s
                    ORDER BY b.name
                """
                result = self.db.execute_query(query, [corp_name])
                if result:
                    for row in result:
                        if row['branch']:
                            self.branch_selector.addItem(row['branch'])
        except Exception as e:
            print(f"Error loading branches: {e}")
            QMessageBox.critical(self, "Database Error", f"Failed to load branches: {e}")

    def load_branches_by_os(self):
        """Load branches filtered by OS name"""
        try:
            self.branch_selector.clear()
            os_name = self.os_selector.currentText()
            if os_name:
                # Query all branches belonging to this OS
                query = """
                    SELECT name as branch
                    FROM branches
                    WHERE os_name = %s
                    ORDER BY name
                """
                result = self.db.execute_query(query, [os_name])
                if result:
                    for row in result:
                        if row['branch']:
                            self.branch_selector.addItem(row['branch'])
        except Exception as e:
            print(f"Error loading branches by OS: {e}")
            QMessageBox.critical(self, "Database Error", f"Failed to load branches: {e}")

    def _refresh_admin_corporations(self):
        try:
            rows = self.db.execute_query("SELECT id, name FROM corporations ORDER BY name")
            self.branch_corp_selector.clear()
            self.client_corp_selector.clear()
            if rows:
                for r in rows:
                    self.branch_corp_selector.addItem(r['name'], r['id'])
                    self.client_corp_selector.addItem(r['name'], r['id'])
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load corporations: {e}")

    def _refresh_admin_branches(self, corp_id=None, target='both'):
        try:
            if corp_id is None:
                corp_id = self.branch_corp_selector.currentData()
            if not corp_id:
                self.client_branch_selector.clear()
                return

            rows = self.db.execute_query("SELECT id, name FROM branches WHERE corporation_id=%s ORDER BY name", (corp_id,))
            self.client_branch_selector.clear()
            if rows:
                for r in rows:
                    self.client_branch_selector.addItem(r['name'], r['id'])
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load branches: {e}")

    def _on_add_corporation(self):
        name = self.corp_name_input.text().strip()
        if not name:
            QMessageBox.warning(self, "Input Required", "Please enter a corporation name.")
            return
        try:
            cid = create_corporation(name)
            if cid:
                QMessageBox.information(self, "✅ Created", f"Corporation '{name}' created successfully (ID: {cid}).")
                self.corp_name_input.clear()
                self._refresh_admin_corporations()
                self._refresh_corporation_display()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to create corporation: {e}")

    def _on_add_branch(self):
        name = self.branch_name_input.text().strip()
        corp_id = self.branch_corp_selector.currentData()
        if not corp_id:
            QMessageBox.warning(self, "Selection Required", "Please select a corporation for this branch.")
            return
        if not name:
            QMessageBox.warning(self, "Input Required", "Please enter a branch name.")
            return
        try:
            bid = create_branch(name, corp_id)
            if bid:
                QMessageBox.information(self, "✅ Created", f"Branch '{name}' created successfully (ID: {bid}).")
                self.branch_name_input.clear()
                self._refresh_admin_branches(corp_id)
                self._refresh_branch_display()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to create branch: {e}")

    def _on_add_client(self):
        first = self.client_first_input.text().strip()
        last = self.client_last_input.text().strip()
        corp_id = self.client_corp_selector.currentData()
        branch_id = self.client_branch_selector.currentData()
        password = self.client_password_input.text() or None

        if not (first and last):
            QMessageBox.warning(self, "Input Required", "Please enter client's first and last names.")
            return
        if not corp_id or not branch_id:
            QMessageBox.warning(self, "Selection Required", "Please select corporation and branch for the client.")
            return

        try:
            row = create_client(first, last, corp_id, branch_id, password)
            if row:
                QMessageBox.information(
                    self, 
                    "✅ Created", 
                    f"Client created successfully!\n\n"
                    f"Username: {row['username']}\n"
                    f"ID: {row['id']}\n"
                    f"Name: {first} {last}"
                )
                # Clear inputs
                self.client_first_input.clear()
                self.client_last_input.clear()
                self.client_password_input.clear()
                self.client_username_display.clear()
                self._refresh_client_display()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to create client: {e}")

    def delete_entry(self):
       
        try:
            branch_name = self.branch_selector.currentText()
            selected_date = self.date_picker.date().toString("yyyy-MM-dd")

            if not branch_name:
                QMessageBox.warning(self, "Selection Required", "Please select a branch.")
                return

            reply = QMessageBox.question(
                self,
                "Confirm Delete",
                f"Are you sure you want to delete the entry for:\n\n"
                f"Branch: {branch_name}\n"
                f"Date: {selected_date}\n\n"
                f"This will allow clients to re-enter data for that day.",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )

            if reply == QMessageBox.No:
                return

            delete_query = f"""
                DELETE FROM {self.daily_table}
                WHERE branch = %s AND date = %s
            """
            rows_affected = self.db.execute_query(delete_query, [branch_name, selected_date])

            if rows_affected > 0:
                QMessageBox.information(
                    self,
                    "Success",
                    f"Entry for {branch_name} on {selected_date} has been deleted.\n\n"
                    f"Clients can now re-enter data for that day."
                )
                self.clear_all_fields()
            else:
                QMessageBox.information(
                    self,
                    "No Entry Found",
                    f"No entry found for {branch_name} on {selected_date}."
                )

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to delete entry: {e}")

    def export_daily_cash_to_excel(self):
        """Export Daily Cash Count to Excel with file dialog for save location"""
        try:
            from openpyxl import Workbook
            from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
        except ImportError:
            QMessageBox.critical(
                self,
                "Missing Dependency",
                "The openpyxl package is required to export to Excel.\nInstall with: pip install openpyxl"
            )
            return
        
        filter_type = self.filter_type_selector.currentData()
        if filter_type == "corporation":
            filter_label = "Corporation"
            filter_value = self.corp_selector.currentText()
        else:
            filter_label = "OS"
            filter_value = self.os_selector.currentText()
        
        branch_name = self.branch_selector.currentText()
        selected_date = self.date_picker.date().toString("yyyy-MM-dd")
        
        if not branch_name:
            QMessageBox.warning(self, "Selection Required", "Please select a branch.")
            return
        
        # File dialog for save location
        default_filename = f"DailyCashCount_{filter_value}_{branch_name}_{selected_date}.xlsx"
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Excel File",
            default_filename,
            "Excel Files (*.xlsx);;All Files (*)"
        )
        
        if not file_path:
            return  # User cancelled
        
        try:
            wb = Workbook()
            ws = wb.active
            ws.title = "Daily Cash Count"
            
            # Styles
            title_font = Font(bold=True, size=16)
            header_font = Font(bold=True, size=11)
            header_fill = PatternFill(start_color="4472C4", end_color="4472C4", fill_type="solid")
            header_font_white = Font(bold=True, size=11, color="FFFFFF")
            money_font = Font(size=10)
            total_fill = PatternFill(start_color="E2EFDA", end_color="E2EFDA", fill_type="solid")
            border = Border(
                left=Side(style='thin'),
                right=Side(style='thin'),
                top=Side(style='thin'),
                bottom=Side(style='thin')
            )
            
            # Title
            ws.merge_cells('A1:D1')
            ws['A1'] = "Daily Cash Count Report"
            ws['A1'].font = title_font
            ws['A1'].alignment = Alignment(horizontal='center')
            
            # Info section
            ws['A3'] = f"{filter_label}:"
            ws['B3'] = filter_value
            ws['A4'] = "Branch:"
            ws['B4'] = branch_name
            ws['A5'] = "Date:"
            ws['B5'] = selected_date
            ws['A6'] = "Beginning Balance:"
            ws['B6'] = float(self.beginning_balance_input.text() or 0)
            ws['B6'].number_format = '#,##0.00'
            
            for row in range(3, 7):
                ws[f'A{row}'].font = header_font
            
            # Debit Section
            row = 8
            ws.merge_cells(f'A{row}:D{row}')
            ws[f'A{row}'] = "💸 DEBIT TRANSACTIONS"
            ws[f'A{row}'].font = header_font_white
            ws[f'A{row}'].fill = PatternFill(start_color="27AE60", end_color="27AE60", fill_type="solid")
            ws[f'A{row}'].alignment = Alignment(horizontal='center')
            
            row += 1
            ws[f'A{row}'] = "Description"
            ws[f'B{row}'] = "Amount"
            ws[f'C{row}'] = "Lotes"
            for col in ['A', 'B', 'C']:
                ws[f'{col}{row}'].font = header_font
                ws[f'{col}{row}'].border = border
            
            row += 1
            for label, db_col in self.debit_fields.items():
                ws[f'A{row}'] = label
                amount = float(self.debit_inputs[label].text() or 0) if label in self.debit_inputs else 0
                lotes = int(self.debit_lotes_inputs[label].text() or 0) if label in self.debit_lotes_inputs else 0
                ws[f'B{row}'] = amount
                ws[f'B{row}'].number_format = '#,##0.00'
                ws[f'C{row}'] = lotes
                for col in ['A', 'B', 'C']:
                    ws[f'{col}{row}'].border = border
                row += 1
            
            # Debit Total
            ws[f'A{row}'] = "Total Debit"
            ws[f'A{row}'].font = header_font
            ws[f'B{row}'] = float(self.debit_total_display.text() or 0)
            ws[f'B{row}'].number_format = '#,##0.00'
            ws[f'B{row}'].font = header_font
            for col in ['A', 'B', 'C']:
                ws[f'{col}{row}'].fill = total_fill
                ws[f'{col}{row}'].border = border
            
            row += 2
            
            # Credit Section
            ws.merge_cells(f'A{row}:D{row}')
            ws[f'A{row}'] = "💳 CREDIT TRANSACTIONS"
            ws[f'A{row}'].font = header_font_white
            ws[f'A{row}'].fill = PatternFill(start_color="E74C3C", end_color="E74C3C", fill_type="solid")
            ws[f'A{row}'].alignment = Alignment(horizontal='center')
            
            row += 1
            ws[f'A{row}'] = "Description"
            ws[f'B{row}'] = "Amount"
            ws[f'C{row}'] = "Lotes"
            for col in ['A', 'B', 'C']:
                ws[f'{col}{row}'].font = header_font
                ws[f'{col}{row}'].border = border
            
            row += 1
            for label, db_col in self.credit_fields.items():
                ws[f'A{row}'] = label
                amount = float(self.credit_inputs[label].text() or 0) if label in self.credit_inputs else 0
                lotes = int(self.credit_lotes_inputs[label].text() or 0) if label in self.credit_lotes_inputs else 0
                ws[f'B{row}'] = amount
                ws[f'B{row}'].number_format = '#,##0.00'
                ws[f'C{row}'] = lotes
                for col in ['A', 'B', 'C']:
                    ws[f'{col}{row}'].border = border
                row += 1
            
            # Credit Total
            ws[f'A{row}'] = "Total Credit"
            ws[f'A{row}'].font = header_font
            ws[f'B{row}'] = float(self.credit_total_display.text() or 0)
            ws[f'B{row}'].number_format = '#,##0.00'
            ws[f'B{row}'].font = header_font
            for col in ['A', 'B', 'C']:
                ws[f'{col}{row}'].fill = total_fill
                ws[f'{col}{row}'].border = border
            
            row += 2
            
            # Results Section
            ws.merge_cells(f'A{row}:D{row}')
            ws[f'A{row}'] = "📊 SUMMARY"
            ws[f'A{row}'].font = header_font_white
            ws[f'A{row}'].fill = PatternFill(start_color="F39C12", end_color="F39C12", fill_type="solid")
            ws[f'A{row}'].alignment = Alignment(horizontal='center')
            
            row += 1
            ws[f'A{row}'] = "Ending Balance:"
            ws[f'B{row}'] = float(self.ending_balance_display.text() or 0)
            ws[f'B{row}'].number_format = '#,##0.00'
            ws[f'A{row}'].font = header_font
            
            row += 1
            ws[f'A{row}'] = "Cash Count:"
            ws[f'B{row}'] = float(self.cash_count_input.text() or 0)
            ws[f'B{row}'].number_format = '#,##0.00'
            ws[f'A{row}'].font = header_font
            
            row += 1
            ws[f'A{row}'] = "Short/Over:"
            ws[f'B{row}'] = float(self.cash_result_display.text() or 0)
            ws[f'B{row}'].number_format = '#,##0.00'
            ws[f'A{row}'].font = header_font
            
            # Auto-adjust column widths
            ws.column_dimensions['A'].width = 30
            ws.column_dimensions['B'].width = 18
            ws.column_dimensions['C'].width = 10
            ws.column_dimensions['D'].width = 10
            
            wb.save(file_path)
            QMessageBox.information(self, "Export Successful", f"Daily Cash Count exported to:\n{file_path}")
            
        except Exception as e:
            QMessageBox.critical(self, "Export Error", f"Error exporting to Excel: {str(e)}")

    def show_generate_report_dialog(self):
        """Show dialog to choose between generating report by OS or by Corporation"""
        from PyQt5.QtWidgets import QDialog, QRadioButton, QButtonGroup
        
        dialog = QDialog(self)
        dialog.setWindowTitle("Generate Daily Cash Count Report")
        dialog.setMinimumWidth(400)
        
        layout = QVBoxLayout(dialog)
        
        # Report Type Selection
        type_group = QGroupBox("Report Type")
        type_layout = QVBoxLayout(type_group)
        
        self.report_by_corp_radio = QRadioButton("By Corporation")
        self.report_by_os_radio = QRadioButton("By OS")
        self.report_by_corp_radio.setChecked(True)
        
        type_layout.addWidget(self.report_by_corp_radio)
        type_layout.addWidget(self.report_by_os_radio)
        layout.addWidget(type_group)
        
        # Selection Group
        selection_group = QGroupBox("Select")
        selection_layout = QVBoxLayout(selection_group)
        
        # Corporation selector
        self.report_corp_label = QLabel("Corporation:")
        self.report_corp_combo = QComboBox()
        self.load_report_corporations()
        
        # OS selector
        self.report_os_label = QLabel("OS:")
        self.report_os_combo = QComboBox()
        self.load_report_os_list()
        self.report_os_label.setVisible(False)
        self.report_os_combo.setVisible(False)
        
        selection_layout.addWidget(self.report_corp_label)
        selection_layout.addWidget(self.report_corp_combo)
        selection_layout.addWidget(self.report_os_label)
        selection_layout.addWidget(self.report_os_combo)
        
        # Date selector
        date_label = QLabel("Date:")
        self.report_date_picker = QDateEdit()
        self.report_date_picker.setDisplayFormat("yyyy-MM-dd")
        self.report_date_picker.setCalendarPopup(True)
        self.report_date_picker.setDate(QDate.currentDate())
        selection_layout.addWidget(date_label)
        selection_layout.addWidget(self.report_date_picker)
        
        layout.addWidget(selection_group)
        
        # Connect radio buttons to toggle visibility
        self.report_by_corp_radio.toggled.connect(self.toggle_report_selection)
        
        # Buttons
        button_layout = QHBoxLayout()
        generate_btn = QPushButton("Generate Report")
        generate_btn.setStyleSheet("background-color: #217346; color: white; padding: 8px 16px;")
        cancel_btn = QPushButton("Cancel")
        
        generate_btn.clicked.connect(lambda: self.generate_daily_cash_report(dialog))
        cancel_btn.clicked.connect(dialog.reject)
        
        button_layout.addStretch()
        button_layout.addWidget(cancel_btn)
        button_layout.addWidget(generate_btn)
        layout.addLayout(button_layout)
        
        dialog.exec_()

    def toggle_report_selection(self):
        """Toggle between Corporation and OS selection"""
        by_corp = self.report_by_corp_radio.isChecked()
        self.report_corp_label.setVisible(by_corp)
        self.report_corp_combo.setVisible(by_corp)
        self.report_os_label.setVisible(not by_corp)
        self.report_os_combo.setVisible(not by_corp)

    def load_report_corporations(self):
        """Load corporations for report dialog"""
        try:
            # Query all corporations from corporations table
            query = "SELECT name as corporation FROM corporations ORDER BY name"
            result = db_manager.execute_query(query)
            if result:
                for row in result:
                    self.report_corp_combo.addItem(row['corporation'])
        except Exception as e:
            print(f"Error loading corporations: {e}")

    def load_report_os_list(self):
        """Load OS list for report dialog"""
        try:
            query = """
                SELECT DISTINCT os_name FROM branches 
                WHERE os_name IS NOT NULL AND os_name != '' 
                ORDER BY os_name
            """
            result = db_manager.execute_query(query)
            if result:
                for row in result:
                    os_name = row['os_name'] if isinstance(row, dict) else row[0]
                    self.report_os_combo.addItem(os_name)
        except Exception as e:
            print(f"Error loading OS list: {e}")

    def generate_daily_cash_report(self, dialog):
        """Generate Daily Cash Count report by Corporation or OS with all debit/credit fields"""
        try:
            from openpyxl import Workbook
            from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
            from openpyxl.utils import get_column_letter
        except ImportError:
            QMessageBox.critical(self, "Missing Dependency", 
                "The openpyxl package is required.\nInstall with: pip install openpyxl")
            return
        
        by_corp = self.report_by_corp_radio.isChecked()
        selected_date = self.report_date_picker.date().toString("yyyy-MM-dd")
        
        # Build list of all columns to select
        debit_columns = list(self.debit_fields.values())
        credit_columns = list(self.credit_fields.values())
        all_columns = ['branch', 'beginning_balance'] + debit_columns + ['debit_total'] + credit_columns + ['credit_total', 'ending_balance', 'cash_count', 'cash_result']
        
        # Build SELECT clause
        select_parts = []
        for col in all_columns:
            select_parts.append(f"COALESCE(dr.{col}, 0) as {col}" if col != 'branch' else "dr.branch")
        select_clause = ", ".join(select_parts)
        
        if by_corp:
            filter_value = self.report_corp_combo.currentText()
            filter_label = "Corporation"
            query = f"""
                SELECT {select_clause}
                FROM {self.daily_table} dr
                WHERE dr.corporation = %s AND dr.date = %s
                ORDER BY dr.branch
            """
            params = (filter_value, selected_date)
        else:
            filter_value = self.report_os_combo.currentText()
            filter_label = "OS"
            query = f"""
                SELECT {select_clause}
                FROM {self.daily_table} dr
                INNER JOIN branches b ON dr.branch = b.name
                WHERE b.os_name = %s AND dr.date = %s
                ORDER BY dr.branch
            """
            params = (filter_value, selected_date)
        
        if not filter_value:
            QMessageBox.warning(self, "Selection Required", f"Please select a {filter_label}.")
            return
        
        results = db_manager.execute_query(query, params)
        
        if not results:
            QMessageBox.warning(self, "No Data", f"No data found for {filter_value} on {selected_date}.")
            return
        
        # File dialog
        default_filename = f"DailyCashCount_{filter_label}_{filter_value}_{selected_date}.xlsx"
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Save Excel File", default_filename, "Excel Files (*.xlsx);;All Files (*)"
        )
        
        if not file_path:
            return
        
        try:
            wb = Workbook()
            ws = wb.active
            ws.title = "Daily Cash Count"
            
            # Styles
            title_font = Font(bold=True, size=14)
            header_font = Font(bold=True, size=9, color="FFFFFF")
            debit_fill = PatternFill(start_color="27AE60", end_color="27AE60", fill_type="solid")
            credit_fill = PatternFill(start_color="E74C3C", end_color="E74C3C", fill_type="solid")
            summary_fill = PatternFill(start_color="F39C12", end_color="F39C12", fill_type="solid")
            total_fill = PatternFill(start_color="E2EFDA", end_color="E2EFDA", fill_type="solid")
            thin = Side(style='thin')
            border = Border(left=thin, right=thin, top=thin, bottom=thin)
            
            # Title
            ws['A1'] = "Daily Cash Count Report"
            ws['A1'].font = title_font
            
            # Info
            ws['A3'] = f"{filter_label}:"
            ws['B3'] = filter_value
            ws['A4'] = "Date:"
            ws['B4'] = selected_date
            ws['A3'].font = Font(bold=True)
            ws['A4'].font = Font(bold=True)
            
            # Build headers
            header_row = 6
            headers = ["Branch", "Beg. Balance"]
            
            # Debit headers
            for label in self.debit_fields.keys():
                headers.append(label)
            headers.append("Debit Total")
            
            # Credit headers
            for label in self.credit_fields.keys():
                headers.append(label)
            headers.append("Credit Total")
            
            # Summary headers
            headers.extend(["Ending Balance", "Cash Count", "Short/Over"])
            
            # Calculate column positions for coloring
            debit_start = 3  # Column C
            debit_end = debit_start + len(self.debit_fields)  # Includes Debit Total
            credit_start = debit_end + 1
            credit_end = credit_start + len(self.credit_fields)  # Includes Credit Total
            summary_start = credit_end + 1
            
            # Write headers with appropriate colors
            for col_idx, header in enumerate(headers, 1):
                cell = ws.cell(row=header_row, column=col_idx, value=header)
                cell.font = header_font
                cell.border = border
                cell.alignment = Alignment(horizontal='center', wrap_text=True)
                
                if col_idx >= debit_start and col_idx <= debit_end:
                    cell.fill = debit_fill
                elif col_idx >= credit_start and col_idx <= credit_end:
                    cell.fill = credit_fill
                elif col_idx >= summary_start:
                    cell.fill = summary_fill
                else:
                    cell.fill = PatternFill(start_color="4472C4", end_color="4472C4", fill_type="solid")
            
            # Initialize totals
            totals = {col: 0.0 for col in all_columns if col != 'branch'}
            
            # Write data rows
            for row_idx, row_data in enumerate(results, header_row + 1):
                col_idx = 1
                
                # Branch
                ws.cell(row=row_idx, column=col_idx, value=row_data['branch']).border = border
                col_idx += 1
                
                # Beginning Balance
                val = float(row_data.get('beginning_balance', 0) or 0)
                cell = ws.cell(row=row_idx, column=col_idx, value=val)
                cell.number_format = '#,##0.00'
                cell.border = border
                totals['beginning_balance'] = totals.get('beginning_balance', 0) + val
                col_idx += 1
                
                # Debit fields
                for db_col in debit_columns:
                    val = float(row_data.get(db_col, 0) or 0)
                    cell = ws.cell(row=row_idx, column=col_idx, value=val)
                    cell.number_format = '#,##0.00'
                    cell.border = border
                    totals[db_col] = totals.get(db_col, 0) + val
                    col_idx += 1
                
                # Debit Total
                val = float(row_data.get('debit_total', 0) or 0)
                cell = ws.cell(row=row_idx, column=col_idx, value=val)
                cell.number_format = '#,##0.00'
                cell.border = border
                cell.font = Font(bold=True)
                totals['debit_total'] = totals.get('debit_total', 0) + val
                col_idx += 1
                
                # Credit fields
                for db_col in credit_columns:
                    val = float(row_data.get(db_col, 0) or 0)
                    cell = ws.cell(row=row_idx, column=col_idx, value=val)
                    cell.number_format = '#,##0.00'
                    cell.border = border
                    totals[db_col] = totals.get(db_col, 0) + val
                    col_idx += 1
                
                # Credit Total
                val = float(row_data.get('credit_total', 0) or 0)
                cell = ws.cell(row=row_idx, column=col_idx, value=val)
                cell.number_format = '#,##0.00'
                cell.border = border
                cell.font = Font(bold=True)
                totals['credit_total'] = totals.get('credit_total', 0) + val
                col_idx += 1
                
                # Summary fields
                for summary_col in ['ending_balance', 'cash_count', 'cash_result']:
                    val = float(row_data.get(summary_col, 0) or 0)
                    cell = ws.cell(row=row_idx, column=col_idx, value=val)
                    cell.number_format = '#,##0.00'
                    cell.border = border
                    totals[summary_col] = totals.get(summary_col, 0) + val
                    col_idx += 1
            
            # Total row
            total_row = header_row + len(results) + 1
            col_idx = 1
            
            cell = ws.cell(row=total_row, column=col_idx, value="TOTAL")
            cell.font = Font(bold=True)
            cell.fill = total_fill
            cell.border = border
            col_idx += 1
            
            # Write totals for all numeric columns
            for col_key in ['beginning_balance'] + debit_columns + ['debit_total'] + credit_columns + ['credit_total', 'ending_balance', 'cash_count', 'cash_result']:
                cell = ws.cell(row=total_row, column=col_idx, value=totals.get(col_key, 0))
                cell.number_format = '#,##0.00'
                cell.font = Font(bold=True)
                cell.fill = total_fill
                cell.border = border
                col_idx += 1
            
            # Auto-adjust column widths
            for col_idx in range(1, len(headers) + 1):
                col_letter = get_column_letter(col_idx)
                if col_idx == 1:
                    ws.column_dimensions[col_letter].width = 20
                else:
                    ws.column_dimensions[col_letter].width = 12
            
            wb.save(file_path)
            dialog.accept()
            QMessageBox.information(self, "Export Successful", f"Report exported to:\n{file_path}")
            
        except Exception as e:
            QMessageBox.critical(self, "Export Error", f"Error exporting: {str(e)}")

    def load_entry_by_date(self):
        filter_type = self.filter_type_selector.currentData()
        branch_name = self.branch_selector.currentText()
        selected_date = self.date_picker.date().toString("yyyy-MM-dd")

        if not branch_name:
            QMessageBox.warning(self, "Missing Selection", "Please select a branch.")
            return

        try:
            # Query by branch and date (works for both Corporation and OS filtering)
            query = f"""
                SELECT *
                FROM {self.daily_table}
                WHERE branch = %s
                  AND date = %s
            """
            result = self.db.execute_query(query, [branch_name, selected_date])

            if not result:
                QMessageBox.information(self, "No Entry", f"No entry found for {selected_date}.")
                self.clear_all_fields()
                return

            data = result[0]

            # Load basic entry data
            self.beginning_balance_input.setText(str(data.get('beginning_balance', 0)))
            self.ending_balance_display.setText(str(data.get('ending_balance', 0)))
            self.cash_count_input.setText(str(data.get('cash_count', 0)))
            self.cash_result_display.setText(str(data.get('cash_result', 0)))
            
            # Load and display totals
            debit_total = data.get('debit_total', 0)
            credit_total = data.get('credit_total', 0)
            self.debit_total_display.setText(f"{debit_total:.2f}")
            self.credit_total_display.setText(f"{credit_total:.2f}")

            # Load debit fields
            for ui_label, db_column in self.debit_fields.items():
                if db_column in data and data[db_column] is not None:
                    self.debit_inputs[ui_label].setText(str(data[db_column]))
                else:
                    self.debit_inputs[ui_label].setText("0.00")

                lotes_col = db_column + "_lotes"
                if lotes_col in data and data[lotes_col] is not None:
                    self.debit_lotes_inputs[ui_label].setText(str(data[lotes_col]))
                else:
                    self.debit_lotes_inputs[ui_label].setText("0")

            # Load credit fields
            for ui_label, db_column in self.credit_fields.items():
                if db_column in data and data[db_column] is not None:
                    self.credit_inputs[ui_label].setText(str(data[db_column]))
                else:
                    self.credit_inputs[ui_label].setText("0.00")

                lotes_col = db_column + "_lotes"
                if lotes_col in data and data[lotes_col] is not None:
                    self.credit_lotes_inputs[ui_label].setText(str(data[lotes_col]))
                else:
                    self.credit_lotes_inputs[ui_label].setText("0")

            self.current_record_id = data.get('id')
            
            # Display variance status
            variance_status = data.get('variance_status', 'balanced')
            if variance_status == 'short':
                self.variance_status_display.setText("⚠️ SHORT")
                self.variance_status_display.setStyleSheet(
                    "font-weight: bold; font-size: 12px; padding: 5px 10px; border-radius: 4px; background-color: #ffcdd2; color: #c62828;"
                )
            elif variance_status == 'over':
                self.variance_status_display.setText("⚠️ OVER")
                self.variance_status_display.setStyleSheet(
                    "font-weight: bold; font-size: 12px; padding: 5px 10px; border-radius: 4px; background-color: #fff3cd; color: #856404;"
                )
            else:
                self.variance_status_display.setText("✓ Balanced")
                self.variance_status_display.setStyleSheet(
                    "font-weight: bold; font-size: 12px; padding: 5px 10px; border-radius: 4px; background-color: #c8e6c9; color: #2e7d32;"
                )

            QMessageBox.information(self, "✅ Loaded", f"Entry for {selected_date} loaded successfully!")

        except Exception as e:
            print(f"Error loading entry: {e}")
            QMessageBox.critical(self, "Error", f"Failed to load entry: {e}")

    def clear_all_fields(self):
        
        self.beginning_balance_input.setText("0.00")
        self.cash_count_input.setText("0.00")
        self.ending_balance_display.setText("0.00")
        self.cash_result_display.setText("0.00")
        self.debit_total_display.setText("0.00")
        self.credit_total_display.setText("0.00")

        for input_field in self.debit_inputs.values():
            input_field.setText("0.00")
        for input_field in self.credit_inputs.values():
            input_field.setText("0.00")
        for input_field in self.debit_lotes_inputs.values():
            input_field.setText("0")
        for input_field in self.credit_lotes_inputs.values():
            input_field.setText("0")
        
        # Reset variance status display
        self.variance_status_display.setText("—")
        self.variance_status_display.setStyleSheet(
            "font-weight: bold; font-size: 12px; padding: 5px 10px; border-radius: 4px;"
        )

    def save_entry(self):
        """Save edited entry to the database"""
        if not hasattr(self, 'current_record_id') or not self.current_record_id:
            QMessageBox.warning(self, "No Entry Loaded", "Please load an entry first before saving.")
            return

        branch_name = self.branch_selector.currentText()
        selected_date = self.date_picker.date().toString("yyyy-MM-dd")

        if not branch_name:
            QMessageBox.warning(self, "Selection Required", "Please select a branch.")
            return

        reply = QMessageBox.question(
            self,
            "Confirm Save",
            f"Are you sure you want to save changes for:\n\n"
            f"Branch: {branch_name}\n"
            f"Date: {selected_date}\n\n"
            f"This will update the existing entry.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply == QMessageBox.No:
            return

        try:
            # Collect all debit values
            update_data = {}
            debit_sum = 0
            for ui_label, db_column in self.debit_fields.items():
                try:
                    val = float(self.debit_inputs[ui_label].text().strip() or 0)
                except ValueError:
                    val = 0
                update_data[db_column] = val
                debit_sum += val
                
                # Lotes
                lotes_col = db_column + "_lotes"
                try:
                    lotes_val = int(self.debit_lotes_inputs[ui_label].text().strip() or 0)
                except ValueError:
                    lotes_val = 0
                update_data[lotes_col] = lotes_val

            # Collect all credit values
            credit_sum = 0
            for ui_label, db_column in self.credit_fields.items():
                try:
                    val = float(self.credit_inputs[ui_label].text().strip() or 0)
                except ValueError:
                    val = 0
                update_data[db_column] = val
                credit_sum += val
                
                # Lotes
                lotes_col = db_column + "_lotes"
                try:
                    lotes_val = int(self.credit_lotes_inputs[ui_label].text().strip() or 0)
                except ValueError:
                    lotes_val = 0
                update_data[lotes_col] = lotes_val

            # Calculate totals
            try:
                beginning = float(self.beginning_balance_input.text().strip() or 0)
            except ValueError:
                beginning = 0
            
            try:
                cash_count = float(self.cash_count_input.text().strip() or 0)
            except ValueError:
                cash_count = 0

            debit_total = beginning + debit_sum
            credit_total = credit_sum
            ending_balance = beginning + debit_sum - credit_sum
            cash_result = cash_count - ending_balance

            # Determine variance status
            if abs(cash_result) < 0.01:
                variance_status = "balanced"
            elif cash_result > 0:
                variance_status = "over"
            else:
                variance_status = "short"

            update_data['debit_total'] = debit_total
            update_data['credit_total'] = credit_total
            update_data['ending_balance'] = ending_balance
            update_data['cash_result'] = cash_result
            update_data['variance_status'] = variance_status

            # Build UPDATE query
            set_clauses = []
            values = []
            for col, val in update_data.items():
                set_clauses.append(f"`{col}` = %s")
                values.append(val)
            
            values.extend([branch_name, selected_date])
            
            update_query = f"""
                UPDATE {self.daily_table}
                SET {', '.join(set_clauses)}
                WHERE branch = %s AND date = %s
            """
            
            rows_affected = self.db.execute_query(update_query, values)

            if rows_affected is not None and rows_affected > 0:
                # Update display fields
                self.debit_total_display.setText(f"{debit_total:.2f}")
                self.credit_total_display.setText(f"{credit_total:.2f}")
                self.ending_balance_display.setText(f"{ending_balance:.2f}")
                self.cash_result_display.setText(f"{cash_result:.2f}")
                
                # Update variance status display
                if variance_status == 'short':
                    self.variance_status_display.setText("⚠️ SHORT")
                    self.variance_status_display.setStyleSheet(
                        "font-weight: bold; font-size: 12px; padding: 5px 10px; border-radius: 4px; background-color: #ffcdd2; color: #c62828;"
                    )
                elif variance_status == 'over':
                    self.variance_status_display.setText("⚠️ OVER")
                    self.variance_status_display.setStyleSheet(
                        "font-weight: bold; font-size: 12px; padding: 5px 10px; border-radius: 4px; background-color: #fff3cd; color: #856404;"
                    )
                else:
                    self.variance_status_display.setText("✓ Balanced")
                    self.variance_status_display.setStyleSheet(
                        "font-weight: bold; font-size: 12px; padding: 5px 10px; border-radius: 4px; background-color: #c8e6c9; color: #2e7d32;"
                    )
                
                QMessageBox.information(
                    self,
                    "✅ Saved",
                    f"Entry for {selected_date} has been updated successfully!"
                )
            else:
                QMessageBox.warning(
                    self,
                    "No Changes",
                    f"No entry was updated. The entry may not exist."
                )

        except Exception as e:
            print(f"Error saving entry: {e}")
            QMessageBox.critical(self, "Error", f"Failed to save entry: {e}")

    def closeEvent(self, event):
       
        event.accept()


# Optional: to run the widget directly for testing
if __name__ == "__main__":
    import sys
    from PyQt5.QtWidgets import QApplication

    app = QApplication(sys.argv)
    window = AdminDashboard()
    window.show()
    sys.exit(app.exec_())