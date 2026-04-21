from PyQt5.QtWidgets import (
    QWidget, QLabel, QVBoxLayout, QHBoxLayout, QGroupBox, QFormLayout,
    QLineEdit, QComboBox, QPushButton, QMessageBox, QDateEdit, QStackedWidget,
    QScrollArea, QFrame, QFileDialog, QDialog, QTableWidget, QTableWidgetItem, QHeaderView,
    QApplication, QSizePolicy, QCheckBox
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
from global_payable_page import GlobalPayablePage
from report_page import ReportPage
from admin_manage import create_corporation, create_branch, create_client, get_all_supervisors
from variance_review_page import VarianceReviewPage
from user_management_page import UserManagementPage
from daily_transaction_page import DailyTransactionPage
from new_sanla_page import NewSanlaPage
from new_renew_page import NewRenewPage
from global_other_services_page import GlobalOtherServicesPage
from ft_ho_page import FTHOPage
from review_summary_page import ReviewSummaryPage


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
 
        self.account_type = account_type
        brand_label = "Brand A" if account_type == 1 else "Brand B"
        self.setWindowTitle(f"Admin Dashboard ({brand_label}) - Cash Management System")
        self.db = db_manager
        self._update_checker_threads = []  
        

        self.session = SessionManager(inactivity_timeout=1800)
        self._session_timer = QTimer(self)
        self._session_timer.timeout.connect(self._check_session_timeout)
        self._session_timer.start(60000)  

        self.debit_inputs = {}
        self.credit_inputs = {}
        self.debit_lotes_inputs = {}
        self.credit_lotes_inputs = {}
        self.selected_bank_account = None  
        self.bank_account_btn = None 
        self.selected_branch_dest = None
        self.branch_dest_btn = None
        self.selected_from_branch_dest = None 
        self.from_branch_dest_btn = None

      
        brand_key = "Brand A" if account_type == 1 else "Brand B"
        field_config = self._load_field_config()
        
        if field_config and brand_key in field_config:
            brand_config = field_config[brand_key]

            self.debit_fields = {item[0]: item[2] for item in brand_config.get("debit", [])}
            self.credit_fields = {item[0]: item[2] for item in brand_config.get("credit", [])}
        else:
  
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
                "Fund Transfer": "fund_transfer_from_branch",
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
                "Empeno Motor/Car": "empeno_motor_car",
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


        self.daily_table = "daily_reports_brand_a" if account_type == 1 else "daily_reports"
        
        self._ensure_review_table()
        self.setup_styles()
        self.build_ui()
        self.load_corporations()
        

        if AUTO_UPDATE_ENABLED and check_update_success:
            check_update_success(parent=self)

    def _ensure_review_table(self):

        try:
            self.db.execute_query("""
                CREATE TABLE IF NOT EXISTS admin_review_marks (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    brand VARCHAR(10) NOT NULL,
                    branch VARCHAR(255) NOT NULL,
                    report_date DATE NOT NULL,
                    reviewed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE KEY uq_review (brand, branch, report_date)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
            """)
        except Exception as e:
            print(f"[AdminDashboard] review table create: {e}")

    def _load_field_config(self):

        try:
            result = self.db.execute_query(
                "SELECT config_value FROM field_config WHERE config_key = 'field_definitions'"
            )
            if result and result[0].get('config_value'):
                cfg = json.loads(result[0]['config_value'])
                for brand in ("Brand A", "Brand B"):
                    cfg.setdefault(brand, {})
                    cfg[brand].setdefault("debit", [])
                    cfg[brand].setdefault("credit", [])
                return cfg
        except Exception as e:
            print(f"[AdminDashboard] Failed to load config from DB: {e}")

        try:
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

            /* Calendar Popup */
            QCalendarWidget {
                background-color: white;
            }

            QCalendarWidget QWidget#qt_calendar_navigationbar {
                background-color: #3498db;
                min-height: 36px;
            }

            QCalendarWidget QToolButton {
                color: white;
                font-size: 13px;
                font-weight: bold;
                background-color: transparent;
                padding: 4px 8px;
                border-radius: 4px;
            }

            QCalendarWidget QToolButton:hover {
                background-color: #2980b9;
            }

            QCalendarWidget QToolButton::menu-indicator {
                image: none;
                width: 0px;
            }

            QCalendarWidget QSpinBox {
                color: white;
                background-color: #3498db;
                font-size: 13px;
                font-weight: bold;
                border: none;
                selection-background-color: #2980b9;
                selection-color: white;
            }

            QCalendarWidget QSpinBox::up-button,
            QCalendarWidget QSpinBox::down-button {
                subcontrol-origin: border;
                width: 16px;
                height: 12px;
            }

            QCalendarWidget QMenu {
                background-color: white;
                color: #2c3e50;
                font-size: 12px;
            }

            QCalendarWidget QMenu::item:selected {
                background-color: #3498db;
                color: white;
            }

            QCalendarWidget QAbstractItemView {
                background-color: white;
                color: #2c3e50;
                selection-background-color: #3498db;
                selection-color: white;
                font-size: 11px;
            }

            QCalendarWidget QAbstractItemView:enabled {
                color: #2c3e50;
            }

            QCalendarWidget QAbstractItemView:disabled {
                color: #bdc3c7;
            }

            /* Scroll Area */
            QScrollArea {
                border: none;
                background-color: transparent;
            }

            /* Navigation Bar */
            QFrame#navBar {
                background-color: #2c3e50;
                border-radius: 0px;
                margin-bottom: 0px;
                padding: 0px;
            }

            QFrame#navBar QPushButton {
                background-color: transparent;
                border: none;
                border-bottom: 3px solid transparent;
                color: #bdc3c7;
                font-size: 11px;
                font-weight: bold;
                padding: 10px 6px;
                border-radius: 0px;
            }

            QFrame#navBar QPushButton:hover {
                background-color: rgba(52, 152, 219, 0.15);
                color: #ecf0f1;
                border-bottom: 3px solid #3498db;
            }

            QFrame#navBar QPushButton:checked {
                background-color: rgba(52, 152, 219, 0.25);
                color: #ffffff;
                border-bottom: 3px solid #3498db;
            }
        """)

    def build_ui(self):
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(10, 8, 10, 8)
        main_layout.setSpacing(6)


        header_frame = QFrame()
        header_frame.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #3498db, stop:1 #2980b9);
                border-radius: 8px;
                padding: 8px;
                margin-bottom: 4px;
            }
        """)
        header_layout = QHBoxLayout(header_frame)
        header_layout.setContentsMargins(10, 4, 10, 4)

        title_label = QLabel("Admin Dashboard")
        title_label.setStyleSheet("font-size: 20px; font-weight: bold; color: white;")
        
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
        
        logout_button = QPushButton("Logout")
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

        nav_frame = QFrame()
        nav_frame.setObjectName("navBar")
        nav_layout = QHBoxLayout(nav_frame)
        nav_layout.setContentsMargins(0, 0, 0, 0)
        nav_layout.setSpacing(0)

        self.daily_btn = QPushButton("Daily Cash Count")
        self.variance_btn = QPushButton("Variance Review")
        self.palawan_btn = QPushButton("Palawan")
        self.mc_btn = QPushButton("MC")
        self.fund_btn = QPushButton("Fund Transfer")
        self.payable_btn = QPushButton("Payable")
        self.global_payable_btn = QPushButton("Global Payable")
        self.report_btn = QPushButton("Payable Reports")
        self.daily_txn_btn = QPushButton("Daily Transaction")
        self.new_sanla_btn = QPushButton("New Sanla")
        self.new_renew_btn = QPushButton("New & Renew")
        self.global_os_btn = QPushButton("Global Other Services")
        self.ft_ho_btn = QPushButton("FT HO")
        self.admin_btn = QPushButton("User Management")
        self.review_summary_btn = QPushButton("Review Summary")


        for btn in [self.daily_btn, self.variance_btn, self.palawan_btn, self.mc_btn,
                    self.fund_btn, self.payable_btn, self.global_payable_btn, self.report_btn, self.daily_txn_btn,
                    self.new_sanla_btn, self.new_renew_btn, self.global_os_btn, self.ft_ho_btn, self.admin_btn,
                    self.review_summary_btn]:
            btn.setCheckable(True)
        self.daily_btn.setChecked(True) 

        if self.account_type == 1:
  
            self.nav_buttons = [
                self.daily_btn, self.variance_btn, self.palawan_btn, self.mc_btn,
                self.fund_btn, self.payable_btn, self.daily_txn_btn, self.new_sanla_btn,
                self.new_renew_btn, self.global_os_btn, self.ft_ho_btn, self.review_summary_btn, self.admin_btn
            ]
        else:
     
            self.nav_buttons = [
                self.daily_btn, self.variance_btn, self.palawan_btn, self.mc_btn,
                self.fund_btn, self.payable_btn, self.global_payable_btn, self.report_btn, self.review_summary_btn, self.admin_btn
            ]

        for btn in self.nav_buttons:
            btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
            nav_layout.addWidget(btn)

        main_layout.addWidget(nav_frame)


        self.stack = QStackedWidget()

        self._lazy_factories = {} 
        self.daily_cash_widget = self.build_daily_cash_widget()

        if self.account_type == 1:

            self.stack.addWidget(self.daily_cash_widget)    
            self._add_lazy(1, lambda: VarianceReviewPage(account_type=self.account_type), 'variance_widget')
            self._add_lazy(2, lambda: PalawanPage(account_type=self.account_type), 'palawan_widget')
            self._add_lazy(3, lambda: MCPage(account_type=self.account_type), 'mc_widget')
            self._add_lazy(4, lambda: FundTransferPage(account_type=self.account_type), 'fund_widget')
            self._add_lazy(5, lambda: PayablesPage(account_type=self.account_type), 'payable_widget')
            self._add_lazy(6, lambda: DailyTransactionPage(), 'daily_txn_widget')
            self._add_lazy(7, lambda: NewSanlaPage(), 'new_sanla_widget')
            self._add_lazy(8, lambda: NewRenewPage(), 'new_renew_widget')
            self._add_lazy(9, lambda: GlobalOtherServicesPage(), 'global_os_widget')
            self._add_lazy(10, lambda: FTHOPage(account_type=self.account_type), 'ft_ho_widget')
            self._add_lazy(11, lambda: ReviewSummaryPage(account_type=self.account_type), 'review_summary_widget')
            self._add_lazy(12, lambda: UserManagementPage(), 'admin_widget')
        else:
      
            self.stack.addWidget(self.daily_cash_widget)         
            self._add_lazy(1, lambda: VarianceReviewPage(account_type=self.account_type), 'variance_widget')
            self._add_lazy(2, lambda: PalawanPage(account_type=self.account_type), 'palawan_widget')
            self._add_lazy(3, lambda: MCPage(account_type=self.account_type), 'mc_widget')
            self._add_lazy(4, lambda: FundTransferPage(account_type=self.account_type), 'fund_widget')
            self._add_lazy(5, lambda: PayablesPage(account_type=self.account_type), 'payable_widget')
            self._add_lazy(6, lambda: GlobalPayablePage(account_type=self.account_type), 'global_payable_widget')
            self._add_lazy(7, lambda: ReportPage(), 'report_widget')
            self._add_lazy(8, lambda: ReviewSummaryPage(account_type=self.account_type), 'review_summary_widget')
            self._add_lazy(9, lambda: UserManagementPage(), 'admin_widget')
        
        main_layout.addWidget(self.stack)


        if self.account_type == 1:
         
            self.daily_btn.clicked.connect(lambda: self.switch_view(0, self.daily_btn))
            self.variance_btn.clicked.connect(lambda: self.switch_view(1, self.variance_btn))
            self.palawan_btn.clicked.connect(lambda: self.switch_view(2, self.palawan_btn))
            self.mc_btn.clicked.connect(lambda: self.switch_view(3, self.mc_btn))
            self.fund_btn.clicked.connect(lambda: self.switch_view(4, self.fund_btn))
            self.payable_btn.clicked.connect(lambda: self.switch_view(5, self.payable_btn))
            self.daily_txn_btn.clicked.connect(lambda: self.switch_view(6, self.daily_txn_btn))
            self.new_sanla_btn.clicked.connect(lambda: self.switch_view(7, self.new_sanla_btn))
            self.new_renew_btn.clicked.connect(lambda: self.switch_view(8, self.new_renew_btn))
            self.global_os_btn.clicked.connect(lambda: self.switch_view(9, self.global_os_btn))
            self.ft_ho_btn.clicked.connect(lambda: self.switch_view(10, self.ft_ho_btn))
            self.review_summary_btn.clicked.connect(lambda: self.switch_view(11, self.review_summary_btn))
            self.admin_btn.clicked.connect(lambda: self.switch_view(12, self.admin_btn))
        else:

            self.daily_btn.clicked.connect(lambda: self.switch_view(0, self.daily_btn))
            self.variance_btn.clicked.connect(lambda: self.switch_view(1, self.variance_btn))
            self.palawan_btn.clicked.connect(lambda: self.switch_view(2, self.palawan_btn))
            self.mc_btn.clicked.connect(lambda: self.switch_view(3, self.mc_btn))
            self.fund_btn.clicked.connect(lambda: self.switch_view(4, self.fund_btn))
            self.payable_btn.clicked.connect(lambda: self.switch_view(5, self.payable_btn))
            self.global_payable_btn.clicked.connect(lambda: self.switch_view(6, self.global_payable_btn))
            self.report_btn.clicked.connect(lambda: self.switch_view(7, self.report_btn))
            self.review_summary_btn.clicked.connect(lambda: self.switch_view(8, self.review_summary_btn))
            self.admin_btn.clicked.connect(lambda: self.switch_view(9, self.admin_btn))

        self.setLayout(main_layout)

    def handle_logout(self):
    
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
  
        self.session.update_activity()
        super().mousePressEvent(event)
    
    def keyPressEvent(self, event):
   
        self.session.update_activity()
        super().keyPressEvent(event)
    
    def check_for_updates(self):
       
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

        if hasattr(self, '_update_checker_threads'):
            for thread in self._update_checker_threads[:]:
                if thread.isRunning():
                    thread.quit()
                    thread.wait(2000) 
        event.accept()

    def _add_lazy(self, index, factory, attr_name):

        self._lazy_factories[index] = (factory, attr_name)
        self.stack.addWidget(QWidget())

    def switch_view(self, index, active_button):

        if index in self._lazy_factories:
            factory, attr_name = self._lazy_factories.pop(index)
            QApplication.setOverrideCursor(Qt.WaitCursor)
            try:
                widget = factory()
                setattr(self, attr_name, widget)
                old = self.stack.widget(index)
                self.stack.removeWidget(old)
                old.deleteLater()
                self.stack.insertWidget(index, widget)
            finally:
                QApplication.restoreOverrideCursor()

        self.stack.setCurrentIndex(index)

        for btn in self.nav_buttons:
            if btn:
                btn.setChecked(False)

        if active_button:
            active_button.setChecked(True)

    def build_daily_cash_widget(self):

        main_widget = QWidget()
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setWidget(main_widget)

        layout = QVBoxLayout(main_widget)
        layout.setSpacing(15)


        header_frame = QFrame()
        header_frame.setStyleSheet("background-color: white; border-radius: 8px; padding: 10px;")
        header_layout = QVBoxLayout(header_frame)


        filter_type_layout = QHBoxLayout()
        filter_type_label = QLabel("Filter By:")
        filter_type_label.setProperty("class", "header")
        self.filter_type_selector = QComboBox()
        self.filter_type_selector.addItem("Corporation", "corporation")
        self.filter_type_selector.addItem("Group", "group")
        self.filter_type_selector.currentIndexChanged.connect(self.on_filter_type_changed)
        filter_type_layout.addWidget(filter_type_label)
        filter_type_layout.addWidget(self.filter_type_selector)
        filter_type_layout.addStretch()
        header_layout.addLayout(filter_type_layout)

        selection_layout = QHBoxLayout()
        selection_layout.setSpacing(15)

        self.corp_label = QLabel("Corporation:")
        self.corp_label.setProperty("class", "header")
        self.corp_selector = QComboBox()
        self.corp_selector.currentTextChanged.connect(self.load_branches)

        self.os_label = QLabel("Group:")
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


        self.reviewed_checkbox = QCheckBox("Pending review")
        self.reviewed_checkbox.setStyleSheet("""
            QCheckBox {
                font-weight: bold; font-size: 12px; padding: 5px 10px;
                color: #c0392b;
            }
            QCheckBox::indicator { width: 18px; height: 18px; }
            QCheckBox::indicator:checked {
                background-color: #27ae60; border: 2px solid #1e8449; border-radius: 3px;
            }
            QCheckBox::indicator:unchecked {
                background-color: white; border: 2px solid #bdc3c7; border-radius: 3px;
            }
        """)
        self.reviewed_checkbox.setEnabled(False)
        self.reviewed_checkbox.toggled.connect(self._on_review_toggled)
        selection_layout.addWidget(self.reviewed_checkbox)

        header_layout.addLayout(selection_layout)


        balance_layout = QHBoxLayout()
        balance_label = QLabel("Beginning Balance:")
        balance_label.setProperty("class", "important")
        self.beginning_balance_input = self.create_money_input()
        self.beginning_balance_input.setReadOnly(True)
        balance_layout.addWidget(balance_label)
        balance_layout.addWidget(self.beginning_balance_input)
        balance_layout.addStretch()

        header_layout.addLayout(balance_layout)
        layout.addWidget(header_frame)


        columns_layout = QHBoxLayout()
        columns_layout.setSpacing(15)

    
        debit_box = QGroupBox("CREDIT")
        debit_form = QFormLayout()
        debit_form.setSpacing(8)
        debit_form.setLabelAlignment(Qt.AlignLeft)

        for label in self.debit_fields.keys():
            field_input = self.create_money_input()
            field_input.setReadOnly(False)
            self.debit_inputs[label] = field_input

            lotes_input = self.create_lotes_input(read_only=False) 
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
            
            if label == "MC In":
                mc_in_btn = QPushButton("View")
                mc_in_btn.setStyleSheet("""
                    QPushButton {
                        background-color: #3B82F6; color: white;
                        border: none; border-radius: 5px;
                        font-size: 11px; font-weight: 700;
                        padding: 4px 8px;
                    }
                    QPushButton:hover { background-color: #2563EB; }
                """)
                mc_in_btn.setToolTip("Show MC In currency breakdown")
                mc_in_btn.clicked.connect(lambda checked, ft="MC In": self.show_mc_breakdown(ft))
                row.addWidget(mc_in_btn)
     
            elif label in ("Fund Transfer", "Fund Transfer from BRANCH"):
                from_branch_btn = QPushButton("View")
                from_branch_btn.setStyleSheet("""
                    QPushButton {
                        background-color: #059669; color: white;
                        border: none; border-radius: 5px;
                        font-size: 11px; font-weight: 700;
                        padding: 4px 10px;
                    }
                    QPushButton:hover { background-color: #047857; }
                """)
                from_branch_btn.setToolTip("View source branch for this fund transfer")
                from_branch_btn.clicked.connect(self.show_from_branch_dest_info)
                self.from_branch_dest_btn = from_branch_btn
                row.addWidget(from_branch_btn)
            
            debit_form.addRow(field_label, row)

        debit_box.setLayout(debit_form)


        credit_box = QGroupBox("DEBIT")
        credit_form = QFormLayout()
        credit_form.setSpacing(8)
        credit_form.setLabelAlignment(Qt.AlignLeft)

        from Client.salary_detail_dialog import SalaryDetailDialog
        for label in self.credit_fields.keys():
            field_input = self.create_money_input()
            field_input.setReadOnly(False) 
            self.credit_inputs[label] = field_input

            lotes_input = self.create_lotes_input(read_only=False) 
            self.credit_lotes_inputs[label] = lotes_input

            row = QHBoxLayout()
            row.setContentsMargins(0, 0, 0, 0)
            row.setSpacing(6)
            row.addWidget(field_input, 2)

     
            if label == "Fund Transfer to HEAD OFFICE":
                bank_btn = QPushButton("View")
                bank_btn.setStyleSheet("""
                    QPushButton {
                        background-color: #8B5CF6; color: white;
                        border: none; border-radius: 5px;
                        font-size: 11px; font-weight: 700;
                        padding: 4px 10px;
                    }
                    QPushButton:hover { background-color: #7C3AED; }
                """)
                bank_btn.setToolTip("View fund transfer breakdown")
                def show_ft_ho_breakdown():
                    from Client.client_dashboard import FundTransferHODialog
                    entry = self.get_current_entry_data()
                    if not entry:
                        QMessageBox.information(self, "No Entry Loaded",
                            "Please load an entry first by selecting a branch and date, then clicking Load.")
                        return
                    breakdown = []
                    raw = entry.get('ft_ho_breakdown')
                    if raw:
                        try:
                            breakdown = json.loads(raw)
                        except Exception:
                            breakdown = []
                    if not breakdown:
                  
                        if self.selected_bank_account:
                            self.show_bank_account_info()
                        else:
                            QMessageBox.information(self, "No Breakdown",
                                "No Fund Transfer to HEAD OFFICE breakdown data found.\n\n"
                                "The client needs to submit using the new breakdown format.")
                        return
                    dlg = FundTransferHODialog("Fund Transfer to HEAD OFFICE", parent=self)
                    dlg.setWindowTitle("Fund Transfer to HEAD OFFICE Breakdown (View Only)")
                    dlg.setMinimumSize(750, 460)
            
                    while dlg.table.rowCount() > 0:
                        dlg.table.removeRow(0)
                    dlg._rows_data = []
                    for bank_display, bank_id, amt in breakdown:
                        row_idx = dlg.table.rowCount()
                        dlg.table.insertRow(row_idx)
                  
                        bank_label = QLabel(f"  {bank_display}")
                        bank_label.setStyleSheet(
                            "font-size: 12px; font-weight: 600; color: #1E293B; padding: 4px 6px;"
                        )
                        bank_label.setToolTip(bank_display)
                        dlg.table.setCellWidget(row_idx, 0, bank_label)
                        amt_label = QLabel(f"  {amt:,.2f}")
                        amt_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
                        amt_label.setStyleSheet(
                            "font-size: 13px; font-weight: 700; color: #0F766E; padding: 4px 8px;"
                        )
                        dlg.table.setCellWidget(row_idx, 1, amt_label)
             
                        empty = QLabel("")
                        dlg.table.setCellWidget(row_idx, 2, empty)
                    dlg._recalc()
            
                    for child in dlg.findChildren(QPushButton):
                        if "Add" in child.text():
                            child.setVisible(False)
                        if child.text() == "Post":
                            child.setText("Close")
                    dlg.exec_()
                bank_btn.clicked.connect(show_ft_ho_breakdown)
                self.bank_account_btn = bank_btn
                row.addWidget(bank_btn)
   
            elif label == "Fund Transfer to BRANCH":
                branch_btn = QPushButton("View")
                branch_btn.setStyleSheet("""
                    QPushButton {
                        background-color: #059669; color: white;
                        border: none; border-radius: 5px;
                        font-size: 11px; font-weight: 700;
                        padding: 4px 10px;
                    }
                    QPushButton:hover { background-color: #047857; }
                """)
                branch_btn.setToolTip("View destination branch for this fund transfer")
                branch_btn.clicked.connect(self.show_branch_dest_info)
                self.branch_dest_btn = branch_btn
                row.addWidget(branch_btn)
            else:
                lotes_label = QLabel("Lotes:")
                row.addWidget(lotes_label)
                row.addWidget(lotes_input)

            field_label = QLabel(label)
            if any(keyword in label.lower() for keyword in ['empeno', 'fund transfer', 'salary']):
                field_label.setProperty("class", "important")

     
            if label == "PC-Salary" and self.account_type == 1:
                breakdown_btn = QPushButton("View")
                breakdown_btn.setStyleSheet("""
                    QPushButton {
                        background-color: #2563EB; color: white;
                        border: none; border-radius: 5px;
                        font-size: 12px; font-weight: 700;
                        padding: 4px 12px;
                    }
                    QPushButton:hover { background-color: #1D4ED8; }
                """)
                breakdown_btn.setToolTip("Show salary breakdown for P.C. Salary")
                def show_salary_breakdown():
                    from Client.salary_detail_dialog import SalaryDetailDialog
         
                    entry = self.get_current_entry_data()
                    breakdown = []
                    if entry and entry.get('pc_salary_breakdown'):
                        try:
                            breakdown = json.loads(entry['pc_salary_breakdown'])
                        except Exception:
                            breakdown = []
                    if not breakdown:
                        QMessageBox.information(self, "No Breakdown", 
                            "No salary breakdown available for this entry.\n\n"
                            "Please load an entry with salary breakdown data first.")
                        return
                    dlg = SalaryDetailDialog(parent=self)
                    dlg.setWindowTitle("P.C. Salary Breakdown (View Only)")
                
                    while dlg.table.rowCount() > 0:
                        dlg.table.removeRow(0)
                    dlg._rows_data = []
                
                    for name, salary in breakdown:
                        dlg._add_row()
                        row_idx = dlg.table.rowCount() - 1
                        dlg.table.cellWidget(row_idx, 0).setText(str(name))
                        dlg.table.cellWidget(row_idx, 1).setText(str(salary))
               
                        dlg.table.cellWidget(row_idx, 0).setReadOnly(True)
                        dlg.table.cellWidget(row_idx, 1).setReadOnly(True)
                    dlg._recalc()
                    dlg.exec_()
                breakdown_btn.clicked.connect(show_salary_breakdown)
                row.addWidget(breakdown_btn)

        
            if label == "Empeno Motor/Car":
                motor_btn = QPushButton("View")
                motor_btn.setStyleSheet("""
                    QPushButton {
                        background-color: #D97706; color: white;
                        border: none; border-radius: 5px;
                        font-size: 11px; font-weight: 700;
                        padding: 4px 8px;
                    }
                    QPushButton:hover { background-color: #B45309; }
                """)
                motor_btn.setToolTip("Show Motor/Car breakdown")
                def show_motor_breakdown():
                    from Client.client_dashboard import MotorCarDetailDialog
                    entry = self.get_current_entry_data()
                    breakdown = []
                    if entry and entry.get('empeno_motor_car_breakdown'):
                        try:
                            breakdown = json.loads(entry['empeno_motor_car_breakdown'])
                        except Exception:
                            breakdown = []
                    if not breakdown:
                        QMessageBox.information(self, "No Breakdown",
                            "No Motor/Car breakdown available for this entry.\n\n"
                            "Please load an entry with Motor/Car breakdown data first.")
                        return
                    dlg = MotorCarDetailDialog("Empeno Motor/Car", parent=self)
                    dlg.setWindowTitle("Empeno Motor/Car Breakdown (View Only)")
     
                    while dlg.table.rowCount() > 0:
                        dlg.table.removeRow(0)
                    dlg._rows_data = []
                    for pct_str, amt in breakdown:
                        dlg._add_row()
                        row_idx = dlg.table.rowCount() - 1
                        combo = dlg.table.cellWidget(row_idx, 0)
                        idx = combo.findText(pct_str)
                        if idx >= 0:
                            combo.setCurrentIndex(idx)
                        combo.setEnabled(False)
                        amt_edit = dlg.table.cellWidget(row_idx, 1)
                        amt_edit.setText(f"{amt:.2f}")
                        amt_edit.setReadOnly(True)
                        rem_btn = dlg.table.cellWidget(row_idx, 3)
                        if rem_btn:
                            rem_btn.setVisible(False)
                    dlg._recalc()
                    dlg.exec_()
                motor_btn.clicked.connect(show_motor_breakdown)
                row.addWidget(motor_btn)

    
            if label == "MC Out":
                mc_out_btn = QPushButton("View")
                mc_out_btn.setStyleSheet("""
                    QPushButton {
                        background-color: #DC2626; color: white;
                        border: none; border-radius: 5px;
                        font-size: 11px; font-weight: 700;
                        padding: 4px 8px;
                    }
                    QPushButton:hover { background-color: #B91C1C; }
                """)
                mc_out_btn.setToolTip("Show MC Out currency breakdown")
                mc_out_btn.clicked.connect(lambda checked, ft="MC Out": self.show_mc_breakdown(ft))
                row.addWidget(mc_out_btn)

            credit_form.addRow(field_label, row)

        credit_box.setLayout(credit_form)

        columns_layout.addWidget(debit_box)
        columns_layout.addWidget(credit_box)
        layout.addLayout(columns_layout)


        totals_frame = QFrame()
        totals_frame.setStyleSheet(
            "background-color: #e8f5e9; border: 2px solid #81c784; border-radius: 8px; padding: 15px;")
        totals_layout = QHBoxLayout(totals_frame)

 
        debit_total_label = QLabel("Total Cash Receipt:")
        debit_total_label.setProperty("class", "important")
        debit_total_label.setStyleSheet("font-weight: bold; font-size: 12px; color: #2e7d32;")
        self.debit_total_display = self.create_display_field()
        self.debit_total_display.setStyleSheet(
            "background-color: #c8e6c9; border: 2px solid #66bb6a; font-weight: bold; font-size: 12px; color: #1b5e20;")


        credit_total_label = QLabel("Total Cash out:")
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


        results_frame = QFrame()
        results_frame.setStyleSheet(
            "background-color: #fff3cd; border: 2px solid #ffeaa7; border-radius: 8px; padding: 15px;")
        results_layout = QHBoxLayout(results_frame)


        ending_label = QLabel("Ending Balance:")
        ending_label.setProperty("class", "important")
        self.ending_balance_display = self.create_display_field()
        self.ending_balance_display.setProperty("class", "result")


        cash_label = QLabel("Cash Count:")
        cash_label.setProperty("class", "important")
        self.cash_count_input = self.create_money_input()
        self.cash_count_input.setReadOnly(True)


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
        

        status_label = QLabel("Status:")
        status_label.setProperty("class", "important")
        self.variance_status_display = QLabel("—")
        self.variance_status_display.setStyleSheet(
            "font-weight: bold; font-size: 12px; padding: 5px 10px; border-radius: 4px;"
        )
        results_layout.addWidget(status_label)
        results_layout.addWidget(self.variance_status_display)

        layout.addWidget(results_frame)
        

        action_layout = QHBoxLayout()
        action_layout.addStretch()
        

        save_button = QPushButton("Save Changes")
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
        
        reset_button = QPushButton("Reset Entry")
        reset_button.setObjectName("resetButton")
        reset_button.setStyleSheet("""
            QPushButton {
                background-color: #E67E22;
                color: white;
            }
            QPushButton:hover {
                background-color: #D35400;
            }
        """)
        reset_button.clicked.connect(self.reset_entry)
        
        export_button = QPushButton("Export to Excel")
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
        

        date_range_button = QPushButton("Date Range Report")
        date_range_button.setObjectName("dateRangeReportButton")
        date_range_button.setStyleSheet("""
            QPushButton {
                background-color: #8E44AD;
                color: white;
            }
            QPushButton:hover {
                background-color: #7D3C98;
            }
        """)
        date_range_button.clicked.connect(self.show_date_range_report_dialog)
        
        action_layout.addWidget(save_button)
        action_layout.addWidget(reset_button)
        action_layout.addWidget(export_button)
        action_layout.addWidget(date_range_button)
        layout.addLayout(action_layout)


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


    BANK_ACCOUNTS = [
                {"id": 1, "bank_name": "CIB-BDO", "account_name": "Global Reliance", "account_number": "0077-9002-3923"},
        {"id": 2, "bank_name": "CIB-BPI", "account_name": "Kristal Clear Diamond and Gold Pawnshop", "account_number": "0091-0692-29"},
        {"id": 3, "bank_name": "CIB-BDO", "account_name": "Kristal Clear", "account_number": "0077-9001-8784"},
        {"id": 4, "bank_name": "CIB-Union Bank", "account_name": "Golbal Reliance Mgmt and Holdings Corp", "account_number": "0015-6000-5790"},
        {"id": 5, "bank_name": "CIB-BDO", "account_name": "Europacific Management & Holdings Corp", "account_number": "0038-1801-5838"},
        {"id": 6, "bank_name": "CIB-BPI", "account_name": "Europacific Management & Holdings Corp", "account_number": "3541-0035-67"},
        {"id": 7, "bank_name": "CIB-UB", "account_name": "Europacific Management & Holdings Corp", "account_number": "0021-7001-7921"},
    ]
    def show_bank_account_info(self):

        dialog = QDialog(self)
        dialog.setWindowTitle("Bank Account")
        dialog.setMinimumWidth(400)
        
        layout = QVBoxLayout(dialog)
        

        if self.selected_bank_account:

            selected_bank = None
            for bank in self.BANK_ACCOUNTS:
                if bank['id'] == self.selected_bank_account:
                    selected_bank = bank
                    break
            
            if selected_bank:

                header = QLabel("Client Selected Bank Account")
                header.setStyleSheet("font-size: 14px; font-weight: bold; color: #10B981; padding: 10px;")
                layout.addWidget(header)
                

                info_frame = QFrame()
                info_frame.setStyleSheet("""
                    QFrame {
                        background-color: #ECFDF5;
                        border: 2px solid #10B981;
                        border-radius: 8px;
                        padding: 15px;
                    }
                """)
                info_layout = QVBoxLayout(info_frame)
                info_layout.setSpacing(8)
                
                bank_label = QLabel(f"<b>Bank:</b> {selected_bank['bank_name']}")
                bank_label.setStyleSheet("font-size: 14px; color: #065F46;")
                info_layout.addWidget(bank_label)
                
                account_label = QLabel(f"<b>Account Name:</b> {selected_bank['account_name']}")
                account_label.setStyleSheet("font-size: 13px; color: #065F46;")
                info_layout.addWidget(account_label)
                
                if selected_bank.get('account_number'):
                    number_label = QLabel(f"<b>Account #:</b> {selected_bank['account_number']}")
                    number_label.setStyleSheet("font-size: 13px; color: #065F46;")
                    info_layout.addWidget(number_label)
                
                layout.addWidget(info_frame)
            else:
         
                header = QLabel("Bank Account Not Found")
                header.setStyleSheet("font-size: 14px; font-weight: bold; color: #F59E0B; padding: 10px;")
                layout.addWidget(header)
                note = QLabel(f"Bank account ID {self.selected_bank_account} not found in system.")
                note.setStyleSheet("font-size: 11px; color: #64748B; padding: 5px 10px;")
                layout.addWidget(note)
        else:
     
            header = QLabel("No Bank Account Selected")
            header.setStyleSheet("font-size: 14px; font-weight: bold; color: #64748B; padding: 10px;")
            layout.addWidget(header)
            
            note = QLabel("The client has not selected a bank account for this fund transfer.")
            note.setStyleSheet("font-size: 11px; color: #64748B; padding: 5px 10px;")
            layout.addWidget(note)
        
        layout.addStretch()
        
        close_btn = QPushButton("Close")
        close_btn.setStyleSheet("""
            QPushButton {
                background-color: #8B5CF6; color: white;
                border: none; border-radius: 5px;
                font-size: 12px; font-weight: 700;
                padding: 8px 20px;
            }
            QPushButton:hover { background-color: #7C3AED; }
        """)
        close_btn.clicked.connect(dialog.accept)
        layout.addWidget(close_btn)
        
        dialog.exec_()

    def show_branch_dest_info(self):
        """Show destination branch info for Fund Transfer to BRANCH (view only for admin)"""

        dialog = QDialog(self)
        dialog.setWindowTitle("Destination Branch")
        dialog.setMinimumWidth(400)
        
        layout = QVBoxLayout(dialog)
        

        if self.selected_branch_dest:

            header = QLabel("Fund Transfer Destination Branch")
            header.setStyleSheet("font-size: 14px; font-weight: bold; color: #059669; padding: 10px;")
            layout.addWidget(header)
            

            info_frame = QFrame()
            info_frame.setStyleSheet("""
                QFrame {
                    background-color: #ECFDF5;
                    border: 2px solid #059669;
                    border-radius: 8px;
                    padding: 15px;
                }
            """)
            info_layout = QVBoxLayout(info_frame)
            info_layout.setSpacing(8)
            
            branch_label = QLabel(f"<b>Destination Branch:</b> {self.selected_branch_dest}")
            branch_label.setStyleSheet("font-size: 14px; color: #065F46;")
            info_layout.addWidget(branch_label)
            
            layout.addWidget(info_frame)
        else:

            header = QLabel("No Destination Branch")
            header.setStyleSheet("font-size: 14px; font-weight: bold; color: #64748B; padding: 10px;")
            layout.addWidget(header)
            
            note = QLabel("The client has not specified a destination branch for this fund transfer.")
            note.setStyleSheet("font-size: 11px; color: #64748B; padding: 5px 10px;")
            layout.addWidget(note)
        
        layout.addStretch()
        

        close_btn = QPushButton("Close")
        close_btn.setStyleSheet("""
            QPushButton {
                background-color: #059669; color: white;
                border: none; border-radius: 5px;
                font-size: 12px; font-weight: 700;
                padding: 8px 20px;
            }
            QPushButton:hover { background-color: #047857; }
        """)
        close_btn.clicked.connect(dialog.accept)
        layout.addWidget(close_btn)
        
        dialog.exec_()

    def show_from_branch_dest_info(self):

        dialog = QDialog(self)
        dialog.setWindowTitle("Source Branch")
        dialog.setMinimumWidth(400)
        
        layout = QVBoxLayout(dialog)
        
        if self.selected_from_branch_dest:
            header = QLabel("Fund Transfer Source Branch")
            header.setStyleSheet("font-size: 14px; font-weight: bold; color: #059669; padding: 10px;")
            layout.addWidget(header)
            
            info_frame = QFrame()
            info_frame.setStyleSheet("""
                QFrame {
                    background-color: #ECFDF5;
                    border: 2px solid #059669;
                    border-radius: 8px;
                    padding: 15px;
                }
            """)
            info_layout = QVBoxLayout(info_frame)
            info_layout.setSpacing(8)
            
            branch_label = QLabel(f"<b>Source Branch:</b> {self.selected_from_branch_dest}")
            branch_label.setStyleSheet("font-size: 14px; color: #065F46;")
            info_layout.addWidget(branch_label)
            
            layout.addWidget(info_frame)
        else:
            header = QLabel("No Source Branch")
            header.setStyleSheet("font-size: 14px; font-weight: bold; color: #64748B; padding: 10px;")
            layout.addWidget(header)
            
            note = QLabel("The client has not specified a source branch for this fund transfer.")
            note.setStyleSheet("font-size: 11px; color: #64748B; padding: 5px 10px;")
            layout.addWidget(note)
        
        layout.addStretch()
        
        close_btn = QPushButton("Close")
        close_btn.setStyleSheet("""
            QPushButton {
                background-color: #059669; color: white;
                border: none; border-radius: 5px;
                font-size: 12px; font-weight: 700;
                padding: 8px 20px;
            }
            QPushButton:hover { background-color: #047857; }
        """)
        close_btn.clicked.connect(dialog.accept)
        layout.addWidget(close_btn)
        
        dialog.exec_()

    def build_admin_widget(self):
        """Build Admin Manage UI for corporations, branches, and clients"""
        widget = QWidget()
        
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_content = QWidget()
        layout = QVBoxLayout(scroll_content)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)

        corp_box = QGroupBox("Manage Corporations")
        corp_box.setStyleSheet("""
            QGroupBox {
                font-size: 14px;
                font-weight: bold;
                padding-top: 20px;
            }
        """)
        corp_layout = QVBoxLayout()
        
        corp_form = QFormLayout()
        corp_form.setSpacing(10)
        self.corp_name_input = QLineEdit()
        self.corp_name_input.setPlaceholderText("Enter corporation name")
        
        corp_add_btn = QPushButton("Add Corporation")
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
        
        corp_refresh_btn = QPushButton("Refresh List")
        corp_refresh_btn.clicked.connect(self._refresh_corporation_display)
        
        corp_layout.addLayout(corp_form)
        corp_layout.addWidget(QLabel("Existing Corporations:"))
        corp_layout.addWidget(self.corp_list_display)
        corp_layout.addWidget(corp_refresh_btn)
        corp_box.setLayout(corp_layout)


        branch_box = QGroupBox("Manage Branches")
        branch_box.setStyleSheet("""
            QGroupBox {
                font-size: 14px;
                font-weight: bold;
                padding-top: 20px;
            }
        """)
        branch_layout = QVBoxLayout()

        branch_form = QFormLayout()
        branch_form.setSpacing(10)
        self.branch_corp_selector = QComboBox()
        self.branch_corp_selector.setMinimumWidth(200)
        self.branch_name_input = QLineEdit()
        self.branch_name_input.setPlaceholderText("Enter branch name")

        self.branch_os_selector = QComboBox()
        self.branch_os_selector.setMinimumWidth(200)
        self.branch_os_selector.addItem("-- Select OS (optional) --", None)
        self._load_os_options_for_branch()
        
        branch_add_btn = QPushButton("Add Branch")
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
        branch_form.addRow(QLabel("Operation Supervisor:"), self.branch_os_selector)
        branch_form.addRow(branch_add_btn)
        
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
        
        branch_refresh_btn = QPushButton("Refresh List")
        branch_refresh_btn.clicked.connect(self._refresh_branch_display)
        
        branch_layout.addLayout(branch_form)
        branch_layout.addWidget(QLabel("Existing Branches:"))
        branch_layout.addWidget(self.branch_list_display)
        branch_layout.addWidget(branch_refresh_btn)
        branch_box.setLayout(branch_layout)


        client_box = QGroupBox("Manage Clients")
        client_box.setStyleSheet("""
            QGroupBox {
                font-size: 14px;
                font-weight: bold;
                padding-top: 20px;
            }
        """)
        client_layout = QVBoxLayout()
        

        client_form = QFormLayout()
        client_form.setSpacing(10)
        

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
        
        preview_btn = QPushButton("Preview Username")
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
        
        client_add_btn = QPushButton("Add Client")
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
        
        client_refresh_btn = QPushButton("Refresh List")
        client_refresh_btn.clicked.connect(self._refresh_client_display)
        
        client_layout.addLayout(client_form)
        client_layout.addWidget(QLabel("Existing Clients:"))
        client_layout.addWidget(self.client_list_display)
        client_layout.addWidget(client_refresh_btn)
        client_box.setLayout(client_layout)

        layout.addWidget(corp_box)
        layout.addWidget(branch_box)
        layout.addWidget(client_box)
        layout.addStretch()


        scroll_area.setWidget(scroll_content)
        
        main_layout = QVBoxLayout(widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(scroll_area)

        self._refresh_admin_corporations()
        self._refresh_corporation_display()
        self._refresh_branch_display()
        self._refresh_client_display()

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
                SELECT b.id, b.name, b.corporation_id, c.name as corp_name, b.created_at,
                       b.sub_corporation_id, sc.name as sub_corp_name
                FROM branches b
                LEFT JOIN corporations c ON b.corporation_id = c.id
                LEFT JOIN corporations sc ON b.sub_corporation_id = sc.id
                ORDER BY c.name, b.name
            """
            rows = self.db.execute_query(query)
            if not rows:
                self.branch_list_display.setText("No branches found")
                return
            
            display_text = "┌─────┬──────────────────────┬──────────────────────────────────────┬─────────────────────┐\n"
            display_text += "│ ID  │ Branch Name          │ Corporation                          │ Created At          │\n"
            display_text += "├─────┼──────────────────────┼──────────────────────────────────────┼─────────────────────┤\n"
            
            for r in rows:
                branch_id = str(r['id']).ljust(3)
                name = str(r['name'])[:20].ljust(20)
                corp_display = str(r.get('corp_name', 'N/A'))
                if r.get('sub_corp_name'):
                    corp_display += f" + {r.get('sub_corp_name')}"
                corp_display = corp_display[:36].ljust(36)
                created = str(r.get('created_at', 'N/A'))[:19].ljust(19)
                display_text += f"│ {branch_id} │ {name} │ {corp_display} │ {created} │\n"
            
            display_text += "└─────┴──────────────────────┴──────────────────────────────────────┴─────────────────────┘"
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

        filter_type = self.filter_type_selector.currentData()
        if filter_type == "corporation":
            self.corp_label.setVisible(True)
            self.corp_selector.setVisible(True)
            self.os_label.setVisible(False)
            self.os_selector.setVisible(False)
            self.load_branches()
        else:
            self.corp_label.setVisible(False)
            self.corp_selector.setVisible(False)
            self.os_label.setVisible(True)
            self.os_selector.setVisible(True)
            self.load_branches_by_os()

    def load_branches(self):
    
        try:
            self.branch_selector.clear()
            corp_name = self.corp_selector.currentText()
            if corp_name:

                query = """
                    SELECT b.name as branch
                    FROM branches b
                    LEFT JOIN corporations c ON b.corporation_id = c.id
                    LEFT JOIN corporations sc ON b.sub_corporation_id = sc.id
                    WHERE c.name = %s OR sc.name = %s
                    ORDER BY b.name
                """
                result = self.db.execute_query(query, [corp_name, corp_name])
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


            rows = self.db.execute_query("SELECT id, name FROM branches WHERE corporation_id=%s OR sub_corporation_id=%s ORDER BY name", (corp_id, corp_id))
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
                QMessageBox.information(self, "Created", f"Corporation '{name}' created successfully (ID: {cid}).")
                self.corp_name_input.clear()
                self._refresh_admin_corporations()
                self._refresh_corporation_display()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to create corporation: {e}")

    def _load_os_options_for_branch(self):

        try:
            supervisors = get_all_supervisors()
            for sup in supervisors:
                self.branch_os_selector.addItem(sup['name'], sup['name'])
        except Exception as e:
            print(f"Error loading OS options: {e}")

    def _on_add_branch(self):
        name = self.branch_name_input.text().strip()
        corp_id = self.branch_corp_selector.currentData()
        os_name = self.branch_os_selector.currentData()
        if not corp_id:
            QMessageBox.warning(self, "Selection Required", "Please select a corporation for this branch.")
            return
        if not name:
            QMessageBox.warning(self, "Input Required", "Please enter a branch name.")
            return
        try:
            bid = create_branch(name, corp_id, os_name)
            if bid:
                QMessageBox.information(self, "Created", f"Branch '{name}' created successfully (ID: {bid}).")
                self.branch_name_input.clear()
                self.branch_os_selector.setCurrentIndex(0)
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

    def reset_entry(self):
  
        try:
            branch_name = self.branch_selector.currentText()
            selected_date = self.date_picker.date().toString("yyyy-MM-dd")

            if not branch_name:
                QMessageBox.warning(self, "Selection Required", "Please select a branch.")
                return

            reply = QMessageBox.question(
                self,
                "Confirm Reset",
                f"Are you sure you want to reset the entry for:\n\n"
                f"Branch: {branch_name}\n"
                f"Date: {selected_date}\n\n"
                f"This will reset BOTH Brand A and Brand B,\n"
                f"allowing the branch to edit and resubmit their report.",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )

            if reply == QMessageBox.No:
                return

   
            both_tables = ["daily_reports_brand_a", "daily_reports"]
            total_rows = 0

            for table in both_tables:

                try:
                    col_check = self.db.execute_query(
                        f"SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS "
                        f"WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = %s AND COLUMN_NAME = 'is_locked'",
                        [table]
                    )
                    if not col_check:
                        self.db.execute_query(
                            f"ALTER TABLE {table} ADD COLUMN is_locked TINYINT(1) NOT NULL DEFAULT 1",
                            []
                        )
                except Exception:
                    pass

                reset_query = f"""
                    UPDATE {table}
                    SET is_locked = 0
                    WHERE branch = %s AND date = %s
                """
                rows = self.db.execute_query(reset_query, [branch_name, selected_date])
                if rows is not None and rows > 0:
                    total_rows += rows

            if total_rows > 0:
                QMessageBox.information(
                    self,
                    "Entry Reset",
                    f"Entry for {branch_name} on {selected_date} has been reset.\n\n"
                    f"Both Brand A and Brand B are now unlocked.\n"
                    f"The branch can edit and resubmit their report."
                )
            else:
                QMessageBox.information(
                    self,
                    "No Entry Found",
                    f"No entry found for {branch_name} on {selected_date}."
                )

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to reset entry: {e}")

    def export_daily_cash_to_excel(self):
   
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
            filter_label = "Group"
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
        self.report_by_os_radio = QRadioButton("By Group")
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
        self.report_os_label = QLabel("Group:")
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
        
        # Get actual columns in the table to avoid querying non-existent fields
        try:
            col_rows = db_manager.execute_query(
                "SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS "
                "WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = %s",
                (self.daily_table,)
            )
            existing_cols = {r['COLUMN_NAME'] for r in col_rows} if col_rows else set()
        except Exception:
            existing_cols = set()
        
        if existing_cols:
            debit_columns = [c for c in debit_columns if c in existing_cols]
            credit_columns = [c for c in credit_columns if c in existing_cols]
        
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
            filter_label = "Group"
            query = f"""
                SELECT {select_clause}
                FROM {self.daily_table} dr
                INNER JOIN branches b ON dr.branch COLLATE utf8mb4_general_ci = b.name COLLATE utf8mb4_general_ci
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

    def show_date_range_report_dialog(self):
        """Show dialog to generate a date range report for Daily Cash Count"""
        from PyQt5.QtWidgets import QDialog, QRadioButton, QButtonGroup
        
        brand_label = "Brand A" if self.account_type == 1 else "Brand B"
        dialog = QDialog(self)
        dialog.setWindowTitle(f"Generate Date Range Report - {brand_label}")
        dialog.setMinimumWidth(450)
        
        layout = QVBoxLayout(dialog)
        
        # Report Type Selection
        type_group = QGroupBox("Report Type")
        type_layout = QVBoxLayout(type_group)
        
        self.range_by_corp_radio = QRadioButton("By Corporation")
        self.range_by_os_radio = QRadioButton("By Group")
        self.range_by_corp_radio.setChecked(True)
        
        type_layout.addWidget(self.range_by_corp_radio)
        type_layout.addWidget(self.range_by_os_radio)
        layout.addWidget(type_group)
        
        # Selection Group
        selection_group = QGroupBox("Filter Selection")
        selection_layout = QVBoxLayout(selection_group)
        
        # Corporation selector
        self.range_corp_label = QLabel("Corporation:")
        self.range_corp_combo = QComboBox()
        self._load_range_corporations()
        
        # OS selector
        self.range_os_label = QLabel("Group:")
        self.range_os_combo = QComboBox()
        self._load_range_os_list()
        self.range_os_label.setVisible(False)
        self.range_os_combo.setVisible(False)
        
        selection_layout.addWidget(self.range_corp_label)
        selection_layout.addWidget(self.range_corp_combo)
        selection_layout.addWidget(self.range_os_label)
        selection_layout.addWidget(self.range_os_combo)
        layout.addWidget(selection_group)
        
        # Date Range Group
        date_group = QGroupBox("Date Range")
        date_layout = QHBoxLayout(date_group)
        
        date_layout.addWidget(QLabel("From:"))
        self.range_start_date = QDateEdit()
        self.range_start_date.setDisplayFormat("yyyy-MM-dd")
        self.range_start_date.setCalendarPopup(True)
        self.range_start_date.setDate(QDate.currentDate().addDays(-7))
        date_layout.addWidget(self.range_start_date)
        
        date_layout.addWidget(QLabel("To:"))
        self.range_end_date = QDateEdit()
        self.range_end_date.setDisplayFormat("yyyy-MM-dd")
        self.range_end_date.setCalendarPopup(True)
        self.range_end_date.setDate(QDate.currentDate())
        date_layout.addWidget(self.range_end_date)
        
        layout.addWidget(date_group)
        
        # Connect radio buttons to toggle visibility
        self.range_by_corp_radio.toggled.connect(self._toggle_range_selection)
        self.range_by_os_radio.toggled.connect(self._toggle_range_selection)
        
        # Buttons
        button_layout = QHBoxLayout()
        generate_btn = QPushButton("Generate Report")
        generate_btn.setStyleSheet("background-color: #8E44AD; color: white; padding: 8px 16px;")
        cancel_btn = QPushButton("Cancel")
        
        generate_btn.clicked.connect(lambda: self._generate_date_range_report(dialog))
        cancel_btn.clicked.connect(dialog.reject)
        
        button_layout.addStretch()
        button_layout.addWidget(cancel_btn)
        button_layout.addWidget(generate_btn)
        layout.addLayout(button_layout)
        
        dialog.exec_()

    def _toggle_range_selection(self):
        """Toggle between Corporation and OS selection for date range report"""
        by_corp = self.range_by_corp_radio.isChecked()
        by_os = self.range_by_os_radio.isChecked()
        
        self.range_corp_label.setVisible(by_corp)
        self.range_corp_combo.setVisible(by_corp)
        self.range_os_label.setVisible(by_os)
        self.range_os_combo.setVisible(by_os)

    def _load_range_corporations(self):
        """Load corporations for date range report dialog"""
        try:
            query = "SELECT name as corporation FROM corporations ORDER BY name"
            result = db_manager.execute_query(query)
            if result:
                for row in result:
                    self.range_corp_combo.addItem(row['corporation'])
        except Exception as e:
            print(f"Error loading corporations: {e}")

    def _load_range_os_list(self):
        """Load OS list for date range report dialog"""
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
                    self.range_os_combo.addItem(os_name)
        except Exception as e:
            print(f"Error loading OS list: {e}")

    def _generate_date_range_report(self, dialog):
        """Generate Date Range Report for Brand A with daily breakdown and grand totals"""
        try:
            from openpyxl import Workbook
            from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
            from openpyxl.utils import get_column_letter
        except ImportError:
            QMessageBox.critical(self, "Missing Dependency", 
                "The openpyxl package is required.\nInstall with: pip install openpyxl")
            return
        
        # Determine filter type and value
        if self.range_by_corp_radio.isChecked():
            filter_type = "corporation"
            filter_value = self.range_corp_combo.currentText()
            filter_label = "Corporation"
        else:
            filter_type = "os"
            filter_value = self.range_os_combo.currentText()
            filter_label = "Group"
        
        start_date = self.range_start_date.date().toString("yyyy-MM-dd")
        end_date = self.range_end_date.date().toString("yyyy-MM-dd")
        
        if not filter_value:
            QMessageBox.warning(self, "Selection Required", f"Please select a {filter_label}.")
            return
        
        if start_date > end_date:
            QMessageBox.warning(self, "Invalid Date Range", "Start date must be before or equal to end date.")
            return
        
        # Build list of all columns to select
        debit_columns = list(self.debit_fields.values())
        credit_columns = list(self.credit_fields.values())
        
        # Get actual columns in the table to avoid querying non-existent fields
        try:
            col_rows = db_manager.execute_query(
                "SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS "
                "WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = %s",
                (self.daily_table,)
            )
            existing_cols = {r['COLUMN_NAME'] for r in col_rows} if col_rows else set()
        except Exception:
            existing_cols = set()
        
        if existing_cols:
            debit_columns = [c for c in debit_columns if c in existing_cols]
            credit_columns = [c for c in credit_columns if c in existing_cols]
        
        # Build SELECT clause - include both amount and lotes columns
        select_parts = ["dr.date", "dr.branch", "COALESCE(dr.beginning_balance, 0) as beginning_balance"]
        for col in debit_columns:
            select_parts.append(f"COALESCE(dr.{col}, 0) as {col}")
            select_parts.append(f"COALESCE(dr.{col}_lotes, 0) as {col}_lotes")
        select_parts.append("COALESCE(dr.debit_total, 0) as debit_total")
        for col in credit_columns:
            select_parts.append(f"COALESCE(dr.{col}, 0) as {col}")
            select_parts.append(f"COALESCE(dr.{col}_lotes, 0) as {col}_lotes")
        select_parts.extend([
            "COALESCE(dr.credit_total, 0) as credit_total",
            "COALESCE(dr.ending_balance, 0) as ending_balance",
            "COALESCE(dr.cash_count, 0) as cash_count",
            "COALESCE(dr.cash_result, 0) as cash_result"
        ])
        select_clause = ", ".join(select_parts)
        
        # Build query based on filter type - order by branch first for grouping
        if filter_type == "corporation":
            query = f"""
                SELECT {select_clause}
                FROM {self.daily_table} dr
                WHERE dr.corporation = %s AND dr.date BETWEEN %s AND %s
                ORDER BY dr.branch, dr.date
            """
            params = (filter_value, start_date, end_date)
        else:  # os/group
            query = f"""
                SELECT {select_clause}
                FROM {self.daily_table} dr
                INNER JOIN branches b ON dr.branch COLLATE utf8mb4_general_ci = b.name COLLATE utf8mb4_general_ci
                WHERE b.os_name = %s AND dr.date BETWEEN %s AND %s
                ORDER BY dr.branch, dr.date
            """
            params = (filter_value, start_date, end_date)
        
        results = db_manager.execute_query(query, params)
        
        if not results:
            QMessageBox.warning(self, "No Data", f"No data found for {filter_value} between {start_date} and {end_date}.")
            return
        
        # File dialog
        default_filename = f"DateRangeReport_{filter_label}_{filter_value}_{start_date}_to_{end_date}.xlsx"
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Save Excel File", default_filename, "Excel Files (*.xlsx);;All Files (*)"
        )
        
        if not file_path:
            return
        
        try:
            wb = Workbook()
            ws = wb.active
            ws.title = "Date Range Report"
            
            # Styles
            title_font = Font(bold=True, size=14)
            header_font = Font(bold=True, size=9, color="FFFFFF")
            date_fill = PatternFill(start_color="9B59B6", end_color="9B59B6", fill_type="solid")
            debit_fill = PatternFill(start_color="27AE60", end_color="27AE60", fill_type="solid")
            credit_fill = PatternFill(start_color="E74C3C", end_color="E74C3C", fill_type="solid")
            summary_fill = PatternFill(start_color="F39C12", end_color="F39C12", fill_type="solid")
            total_fill = PatternFill(start_color="E2EFDA", end_color="E2EFDA", fill_type="solid")
            grand_total_fill = PatternFill(start_color="D5A6BD", end_color="D5A6BD", fill_type="solid")
            thin = Side(style='thin')
            border = Border(left=thin, right=thin, top=thin, bottom=thin)
            
            # Title
            brand_title = "Brand A" if self.account_type == 1 else "Brand B"
            ws['A1'] = f"{brand_title} - Date Range Report"
            ws['A1'].font = title_font
            
            # Info
            ws['A3'] = f"{filter_label}:"
            ws['B3'] = filter_value
            ws['A4'] = "Date Range:"
            ws['B4'] = f"{start_date} to {end_date}"
            ws['A3'].font = Font(bold=True)
            ws['A4'].font = Font(bold=True)
            
            # Define PC fields for calculating totals
            salary_fields = ['pc_salary']
            pc_fields_no_salary = [
                'pc_inc_emp', 'pc_inc_motor', 'pc_inc_suki_card', 'pc_inc_insurance', 'pc_inc_mc',
                'pc_rental', 'pc_electric', 'pc_water', 'pc_internet',
                'pc_lbc_jrs_jnt', 'pc_permits_bir_payments', 'pc_supplies_xerox_maintenance', 'pc_transpo'
            ]
            
            # Aggregate data by branch
            branch_totals = {}
            branches_list = []
            for row_data in results:
                branch_name = row_data.get('branch', 'Unknown')
                if branch_name not in branch_totals:
                    branch_totals[branch_name] = {}
                    branches_list.append(branch_name)
                
                # Aggregate amounts and lotes
                for col in ['beginning_balance'] + debit_columns + ['debit_total'] + credit_columns + ['credit_total', 'ending_balance', 'cash_count', 'cash_result']:
                    val = float(row_data.get(col, 0) or 0)
                    branch_totals[branch_name][col] = branch_totals[branch_name].get(col, 0) + val
                
                # Aggregate lotes
                for col in debit_columns + credit_columns:
                    lotes_col = f"{col}_lotes"
                    val = int(row_data.get(lotes_col, 0) or 0)
                    branch_totals[branch_name][lotes_col] = branch_totals[branch_name].get(lotes_col, 0) + val
                
                for pc_col in salary_fields:
                    val = float(row_data.get(pc_col, 0) or 0)
                    branch_totals[branch_name]['salary'] = branch_totals[branch_name].get('salary', 0) + val
                
                for pc_col in pc_fields_no_salary:
                    val = float(row_data.get(pc_col, 0) or 0)
                    branch_totals[branch_name]['total_pc'] = branch_totals[branch_name].get('total_pc', 0) + val
            
            # Build vertical layout headers: Field | Branch1(Amount/Lotes) | Branch2(Amount/Lotes) | ... | Total(Amount/Lotes)
            header_row = 6
            branches_sorted = sorted(branches_list)
            
            # Build header structure
            # Row 1: Field names
            ws.cell(row=header_row, column=1, value="Field")
            cell = ws.cell(row=header_row, column=1)
            cell.font = header_font
            cell.fill = date_fill
            cell.border = border
            cell.alignment = Alignment(horizontal='center', wrap_text=True)
            
            col_idx = 2
            for branch_name in branches_sorted:
                # Merge cells for branch name
                ws.merge_cells(start_row=header_row, start_column=col_idx, end_row=header_row, end_column=col_idx+1)
                cell = ws.cell(row=header_row, column=col_idx, value=branch_name)
                cell.font = header_font
                cell.fill = PatternFill(start_color="4472C4", end_color="4472C4", fill_type="solid")
                cell.border = border
                cell.alignment = Alignment(horizontal='center', wrap_text=True)
                col_idx += 2
            
            # Merge cells for Total
            ws.merge_cells(start_row=header_row, start_column=col_idx, end_row=header_row, end_column=col_idx+1)
            cell = ws.cell(row=header_row, column=col_idx, value="TOTAL")
            cell.font = header_font
            cell.fill = grand_total_fill
            cell.border = border
            cell.alignment = Alignment(horizontal='center', wrap_text=True)
            
            # Row 2: Amount / Lotes sub-headers
            sub_header_row = header_row + 1
            ws.cell(row=sub_header_row, column=1, value="")
            cell = ws.cell(row=sub_header_row, column=1)
            cell.font = header_font
            cell.fill = date_fill
            cell.border = border
            
            col_idx = 2
            for branch_name in branches_sorted:
                # Amount header
                cell = ws.cell(row=sub_header_row, column=col_idx, value="Amount")
                cell.font = Font(bold=True, size=8, color="FFFFFF")
                cell.fill = PatternFill(start_color="4472C4", end_color="4472C4", fill_type="solid")
                cell.border = border
                cell.alignment = Alignment(horizontal='center', wrap_text=True)
                col_idx += 1
                
                # Lotes header
                cell = ws.cell(row=sub_header_row, column=col_idx, value="Lotes")
                cell.font = Font(bold=True, size=8, color="FFFFFF")
                cell.fill = PatternFill(start_color="4472C4", end_color="4472C4", fill_type="solid")
                cell.border = border
                cell.alignment = Alignment(horizontal='center', wrap_text=True)
                col_idx += 1
            
            # Total Amount header
            cell = ws.cell(row=sub_header_row, column=col_idx, value="Amount")
            cell.font = Font(bold=True, size=8, color="FFFFFF")
            cell.fill = grand_total_fill
            cell.border = border
            cell.alignment = Alignment(horizontal='center', wrap_text=True)
            col_idx += 1
            
            # Total Lotes header
            cell = ws.cell(row=sub_header_row, column=col_idx, value="Lotes")
            cell.font = Font(bold=True, size=8, color="FFFFFF")
            cell.fill = grand_total_fill
            cell.border = border
            cell.alignment = Alignment(horizontal='center', wrap_text=True)
            
            # Write data rows by field
            current_row = sub_header_row + 1
            total_col_start = 2 + len(branches_sorted) * 2
            
            # Beginning Balance
            ws.cell(row=current_row, column=1, value="Beginning Balance")
            ws.cell(row=current_row, column=1).font = Font(bold=True)
            ws.cell(row=current_row, column=1).fill = PatternFill(start_color="E8F4F8", end_color="E8F4F8", fill_type="solid")
            ws.cell(row=current_row, column=1).border = border
            
            total_amount = 0.0
            col_idx = 2
            for branch_name in branches_sorted:
                val = float(branch_totals[branch_name].get('beginning_balance', 0))
                cell = ws.cell(row=current_row, column=col_idx, value=val)
                cell.number_format = '#,##0.00'
                cell.border = border
                cell.alignment = Alignment(horizontal='right')
                total_amount += val
                col_idx += 1
                
                # Lotes column (leave blank for beginning balance)
                cell = ws.cell(row=current_row, column=col_idx, value="")
                cell.border = border
                cell.alignment = Alignment(horizontal='center')
                col_idx += 1
            
            cell = ws.cell(row=current_row, column=total_col_start, value=total_amount)
            cell.number_format = '#,##0.00'
            cell.border = border
            cell.font = Font(bold=True)
            cell.alignment = Alignment(horizontal='right')
            cell.fill = total_fill
            
            cell = ws.cell(row=current_row, column=total_col_start + 1, value="")
            cell.border = border
            cell.alignment = Alignment(horizontal='center')
            current_row += 1
            
            # Debit fields
            ws.cell(row=current_row, column=1, value="CASH RECEIPT (DEBIT)")
            ws.cell(row=current_row, column=1).font = Font(bold=True, color="FFFFFF")
            ws.cell(row=current_row, column=1).fill = debit_fill
            ws.cell(row=current_row, column=1).border = border
            current_row += 1
            
            for label in self.debit_fields.keys():
                db_col = self.debit_fields[label]
                if db_col in debit_columns:
                    ws.cell(row=current_row, column=1, value=label)
                    ws.cell(row=current_row, column=1).border = border
                    
                    total_amount = 0.0
                    total_lotes = 0
                    col_idx = 2
                    for branch_name in branches_sorted:
                        # Amount
                        val = float(branch_totals[branch_name].get(db_col, 0))
                        cell = ws.cell(row=current_row, column=col_idx, value=val)
                        cell.number_format = '#,##0.00'
                        cell.border = border
                        cell.alignment = Alignment(horizontal='right')
                        total_amount += val
                        col_idx += 1
                        
                        # Lotes
                        lotes_val = int(branch_totals[branch_name].get(f"{db_col}_lotes", 0))
                        cell = ws.cell(row=current_row, column=col_idx, value=lotes_val)
                        cell.border = border
                        cell.alignment = Alignment(horizontal='center')
                        total_lotes += lotes_val
                        col_idx += 1
                    
                    # Total amount
                    cell = ws.cell(row=current_row, column=total_col_start, value=total_amount)
                    cell.number_format = '#,##0.00'
                    cell.border = border
                    cell.alignment = Alignment(horizontal='right')
                    cell.fill = total_fill
                    
                    # Total lotes
                    cell = ws.cell(row=current_row, column=total_col_start + 1, value=total_lotes)
                    cell.border = border
                    cell.alignment = Alignment(horizontal='center')
                    cell.fill = total_fill
                    current_row += 1
            
            # Total Cash Receipt
            ws.cell(row=current_row, column=1, value="Total Cash Receipt")
            ws.cell(row=current_row, column=1).font = Font(bold=True)
            ws.cell(row=current_row, column=1).border = border
            ws.cell(row=current_row, column=1).fill = PatternFill(start_color="E8F4F8", end_color="E8F4F8", fill_type="solid")
            
            total_amount = 0.0
            col_idx = 2
            for branch_name in branches_sorted:
                val = float(branch_totals[branch_name].get('debit_total', 0))
                cell = ws.cell(row=current_row, column=col_idx, value=val)
                cell.number_format = '#,##0.00'
                cell.border = border
                cell.font = Font(bold=True)
                cell.alignment = Alignment(horizontal='right')
                total_amount += val
                col_idx += 1
                
                # Lotes column (leave blank for totals)
                cell = ws.cell(row=current_row, column=col_idx, value="")
                cell.border = border
                cell.alignment = Alignment(horizontal='center')
                col_idx += 1
            
            cell = ws.cell(row=current_row, column=total_col_start, value=total_amount)
            cell.number_format = '#,##0.00'
            cell.border = border
            cell.font = Font(bold=True)
            cell.alignment = Alignment(horizontal='right')
            cell.fill = total_fill
            
            cell = ws.cell(row=current_row, column=total_col_start + 1, value="")
            cell.border = border
            cell.alignment = Alignment(horizontal='center')
            current_row += 2
            
            # Credit fields
            ws.cell(row=current_row, column=1, value="CASH OUT (CREDIT)")
            ws.cell(row=current_row, column=1).font = Font(bold=True, color="FFFFFF")
            ws.cell(row=current_row, column=1).fill = credit_fill
            ws.cell(row=current_row, column=1).border = border
            current_row += 1
            
            for label in self.credit_fields.keys():
                db_col = self.credit_fields[label]
                if db_col in credit_columns:
                    ws.cell(row=current_row, column=1, value=label)
                    ws.cell(row=current_row, column=1).border = border
                    
                    total_amount = 0.0
                    total_lotes = 0
                    col_idx = 2
                    for branch_name in branches_sorted:
                        # Amount
                        val = float(branch_totals[branch_name].get(db_col, 0))
                        cell = ws.cell(row=current_row, column=col_idx, value=val)
                        cell.number_format = '#,##0.00'
                        cell.border = border
                        cell.alignment = Alignment(horizontal='right')
                        total_amount += val
                        col_idx += 1
                        
                        # Lotes
                        lotes_val = int(branch_totals[branch_name].get(f"{db_col}_lotes", 0))
                        cell = ws.cell(row=current_row, column=col_idx, value=lotes_val)
                        cell.border = border
                        cell.alignment = Alignment(horizontal='center')
                        total_lotes += lotes_val
                        col_idx += 1
                    
                    # Total amount
                    cell = ws.cell(row=current_row, column=total_col_start, value=total_amount)
                    cell.number_format = '#,##0.00'
                    cell.border = border
                    cell.alignment = Alignment(horizontal='right')
                    cell.fill = total_fill
                    
                    # Total lotes
                    cell = ws.cell(row=current_row, column=total_col_start + 1, value=total_lotes)
                    cell.border = border
                    cell.alignment = Alignment(horizontal='center')
                    cell.fill = total_fill
                    current_row += 1
            
            # Total Cash Out
            ws.cell(row=current_row, column=1, value="Total Cash Out")
            ws.cell(row=current_row, column=1).font = Font(bold=True)
            ws.cell(row=current_row, column=1).border = border
            ws.cell(row=current_row, column=1).fill = PatternFill(start_color="E8F4F8", end_color="E8F4F8", fill_type="solid")
            
            total_amount = 0.0
            col_idx = 2
            for branch_name in branches_sorted:
                val = float(branch_totals[branch_name].get('credit_total', 0))
                cell = ws.cell(row=current_row, column=col_idx, value=val)
                cell.number_format = '#,##0.00'
                cell.border = border
                cell.font = Font(bold=True)
                cell.alignment = Alignment(horizontal='right')
                total_amount += val
                col_idx += 1
                
                # Lotes column (leave blank for totals)
                cell = ws.cell(row=current_row, column=col_idx, value="")
                cell.border = border
                cell.alignment = Alignment(horizontal='center')
                col_idx += 1
            
            cell = ws.cell(row=current_row, column=total_col_start, value=total_amount)
            cell.number_format = '#,##0.00'
            cell.border = border
            cell.font = Font(bold=True)
            cell.alignment = Alignment(horizontal='right')
            cell.fill = total_fill
            
            cell = ws.cell(row=current_row, column=total_col_start + 1, value="")
            cell.border = border
            cell.alignment = Alignment(horizontal='center')
            current_row += 2
            
            # Summary fields
            summary_fields = [
                ("Ending Balance", "ending_balance"),
                ("Cash Count", "cash_count"),
                ("Variance", "cash_result")
            ]
            
            ws.cell(row=current_row, column=1, value="SUMMARY")
            ws.cell(row=current_row, column=1).font = Font(bold=True, color="FFFFFF")
            ws.cell(row=current_row, column=1).fill = summary_fill
            ws.cell(row=current_row, column=1).border = border
            current_row += 1
            
            for label, db_col in summary_fields:
                ws.cell(row=current_row, column=1, value=label)
                ws.cell(row=current_row, column=1).border = border
                
                total_amount = 0.0
                col_idx = 2
                for branch_name in branches_sorted:
                    val = float(branch_totals[branch_name].get(db_col, 0))
                    cell = ws.cell(row=current_row, column=col_idx, value=val)
                    cell.number_format = '#,##0.00'
                    cell.border = border
                    cell.alignment = Alignment(horizontal='right')
                    total_amount += val
                    col_idx += 1
                    
                    # Lotes column (leave blank)
                    cell = ws.cell(row=current_row, column=col_idx, value="")
                    cell.border = border
                    cell.alignment = Alignment(horizontal='center')
                    col_idx += 1
                
                cell = ws.cell(row=current_row, column=total_col_start, value=total_amount)
                cell.number_format = '#,##0.00'
                cell.border = border
                cell.alignment = Alignment(horizontal='right')
                cell.fill = total_fill
                
                cell = ws.cell(row=current_row, column=total_col_start + 1, value="")
                cell.border = border
                cell.alignment = Alignment(horizontal='center')
                current_row += 1
            
            # PC fields
            ws.cell(row=current_row, column=1, value="SALARY")
            ws.cell(row=current_row, column=1).font = Font(bold=True)
            ws.cell(row=current_row, column=1).border = border
            ws.cell(row=current_row, column=1).fill = PatternFill(start_color="E8F4F8", end_color="E8F4F8", fill_type="solid")
            
            total_amount = 0.0
            col_idx = 2
            for branch_name in branches_sorted:
                val = float(branch_totals[branch_name].get('salary', 0))
                cell = ws.cell(row=current_row, column=col_idx, value=val)
                cell.number_format = '#,##0.00'
                cell.border = border
                cell.font = Font(bold=True, color="9B59B6")
                cell.alignment = Alignment(horizontal='right')
                total_amount += val
                col_idx += 1
                
                # Lotes column
                cell = ws.cell(row=current_row, column=col_idx, value="")
                cell.border = border
                cell.alignment = Alignment(horizontal='center')
                col_idx += 1
            
            cell = ws.cell(row=current_row, column=total_col_start, value=total_amount)
            cell.number_format = '#,##0.00'
            cell.border = border
            cell.font = Font(bold=True, color="9B59B6")
            cell.alignment = Alignment(horizontal='right')
            cell.fill = total_fill
            
            cell = ws.cell(row=current_row, column=total_col_start + 1, value="")
            cell.border = border
            cell.alignment = Alignment(horizontal='center')
            current_row += 1
            
            ws.cell(row=current_row, column=1, value="Total PC")
            ws.cell(row=current_row, column=1).font = Font(bold=True)
            ws.cell(row=current_row, column=1).border = border
            ws.cell(row=current_row, column=1).fill = PatternFill(start_color="E8F4F8", end_color="E8F4F8", fill_type="solid")
            
            total_amount = 0.0
            col_idx = 2
            for branch_name in branches_sorted:
                val = float(branch_totals[branch_name].get('total_pc', 0))
                cell = ws.cell(row=current_row, column=col_idx, value=val)
                cell.number_format = '#,##0.00'
                cell.border = border
                cell.font = Font(bold=True, color="9B59B6")
                cell.alignment = Alignment(horizontal='right')
                total_amount += val
                col_idx += 1
                
                # Lotes column
                cell = ws.cell(row=current_row, column=col_idx, value="")
                cell.border = border
                cell.alignment = Alignment(horizontal='center')
                col_idx += 1
            
            cell = ws.cell(row=current_row, column=total_col_start, value=total_amount)
            cell.number_format = '#,##0.00'
            cell.border = border
            cell.font = Font(bold=True, color="9B59B6")
            cell.alignment = Alignment(horizontal='right')
            cell.fill = total_fill
            
            cell = ws.cell(row=current_row, column=total_col_start + 1, value="")
            cell.border = border
            cell.alignment = Alignment(horizontal='center')
            
            # Auto-adjust column widths
            ws.column_dimensions['A'].width = 25
            col_idx = 2
            for branch_name in branches_sorted:
                col_letter = get_column_letter(col_idx)
                ws.column_dimensions[col_letter].width = 12  # Amount column
                col_idx += 1
                col_letter = get_column_letter(col_idx)
                ws.column_dimensions[col_letter].width = 10  # Lotes column
                col_idx += 1
            
            # Total columns
            col_letter = get_column_letter(total_col_start)
            ws.column_dimensions[col_letter].width = 12
            col_letter = get_column_letter(total_col_start + 1)
            ws.column_dimensions[col_letter].width = 10
            
            ws.freeze_panes = 'B8'
            
            wb.save(file_path)
            dialog.accept()
            QMessageBox.information(self, "Export Successful", f"Date Range Report exported to:\n{file_path}")
            
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
            self._current_entry_data = data  

            self.beginning_balance_input.setText(str(data.get('beginning_balance', 0)))
            self.ending_balance_display.setText(str(data.get('ending_balance', 0)))
            self.cash_count_input.setText(str(data.get('cash_count', 0)))
            self.cash_result_display.setText(str(data.get('cash_result', 0)))
            
            debit_total = data.get('debit_total', 0)
            credit_total = data.get('credit_total', 0)
            self.debit_total_display.setText(f"{debit_total:.2f}")
            self.credit_total_display.setText(f"{credit_total:.2f}")

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

            self.selected_bank_account = data.get('fund_transfer_bank_account')
            if self.bank_account_btn:

                ft_ho_bd = data.get('ft_ho_breakdown')
                if ft_ho_bd:
                    try:
                        bd_list = json.loads(ft_ho_bd)
                        self.bank_account_btn.setText(f"🏦 View ({len(bd_list)})")
                        self.bank_account_btn.setToolTip(f"View {len(bd_list)} fund transfer(s) breakdown")
                    except Exception:
                        self.bank_account_btn.setText("View")
                        self.bank_account_btn.setToolTip("View fund transfer breakdown")
                elif self.selected_bank_account:

                    bank_name = "View"
                    for bank in self.BANK_ACCOUNTS:
                        if bank['id'] == self.selected_bank_account:
                            bank_name = bank['bank_name']
                            break
                    self.bank_account_btn.setText(f"🏦 {bank_name}")
                    self.bank_account_btn.setToolTip("View selected bank account")
                else:
                    self.bank_account_btn.setText("View")
                    self.bank_account_btn.setToolTip("No bank account selected")


            self.selected_branch_dest = data.get('fund_transfer_to_branch_dest')
            if self.branch_dest_btn:
                self.branch_dest_btn.setText("View")
                if self.selected_branch_dest:
                    self.branch_dest_btn.setToolTip(f"Destination: {self.selected_branch_dest}")
                else:
                    self.branch_dest_btn.setToolTip("No destination branch specified")

       
            self.selected_from_branch_dest = data.get('fund_transfer_from_branch_dest')
            if self.from_branch_dest_btn:
                self.from_branch_dest_btn.setText("View")
                if self.selected_from_branch_dest:
                    self.from_branch_dest_btn.setToolTip(f"Source: {self.selected_from_branch_dest}")
                else:
                    self.from_branch_dest_btn.setToolTip("No source branch specified")

            self.current_record_id = data.get('id')
            

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

            # Check review status
            brand_key = "A" if self.account_type == 1 else "B"
            try:
                review_row = self.db.execute_query(
                    "SELECT id FROM admin_review_marks WHERE brand = %s AND branch = %s AND report_date = %s",
                    [brand_key, branch_name, selected_date]
                )
                is_reviewed = bool(review_row)
                self.reviewed_checkbox.blockSignals(True)
                self.reviewed_checkbox.setChecked(is_reviewed)
                self.reviewed_checkbox.setText("✅ Reviewed" if is_reviewed else "Pending review")
                self.reviewed_checkbox.setStyleSheet(self.reviewed_checkbox.styleSheet().replace(
                    "color: #c0392b;" if is_reviewed else "color: #2e7d32;",
                    "color: #2e7d32;" if is_reviewed else "color: #c0392b;"
                ))
                self.reviewed_checkbox.blockSignals(False)
                self.reviewed_checkbox.setEnabled(True)
            except Exception:
                self.reviewed_checkbox.setEnabled(False)

            QMessageBox.information(self, "✅ Loaded", f"Entry for {selected_date} loaded successfully!")

        except Exception as e:
            print(f"Error loading entry: {e}")
            QMessageBox.critical(self, "Error", f"Failed to load entry: {e}")

    def _on_review_toggled(self, checked):
        """Save or remove the review mark for the current entry."""
        branch_name = self.branch_selector.currentText()
        selected_date = self.date_picker.date().toString("yyyy-MM-dd")
        brand_key = "A" if self.account_type == 1 else "B"
        if not branch_name or not selected_date:
            return
        try:
            if checked:
                self.db.execute_query(
                    "INSERT IGNORE INTO admin_review_marks (brand, branch, report_date) VALUES (%s, %s, %s)",
                    [brand_key, branch_name, selected_date]
                )
                self.reviewed_checkbox.setText("Reviewed")
                self.reviewed_checkbox.setStyleSheet(self.reviewed_checkbox.styleSheet().replace(
                    "color: #c0392b;", "color: #2e7d32;"
                ))
            else:
                self.db.execute_query(
                    "DELETE FROM admin_review_marks WHERE brand = %s AND branch = %s AND report_date = %s",
                    [brand_key, branch_name, selected_date]
                )
                self.reviewed_checkbox.setText("Pending review")
                self.reviewed_checkbox.setStyleSheet(self.reviewed_checkbox.styleSheet().replace(
                    "color: #2e7d32;", "color: #c0392b;"
                ))
        except Exception as e:
            print(f"Error toggling review mark: {e}")

    def get_current_entry_data(self):
        """Return the current loaded entry data for breakdown views"""
        return getattr(self, '_current_entry_data', None)

    def show_mc_breakdown(self, field_type):
        """Show MC currency breakdown in a dialog"""
        entry = self.get_current_entry_data()
        if not entry:
            QMessageBox.information(self, "No Entry Loaded", 
                "Please load an entry first to view MC breakdown.")
            return
        
        # Determine which details field to use
        details_key = "mc_in_details" if field_type == "MC In" else "mc_out_details"
        breakdown = []
        
        if entry.get(details_key):
            try:
                breakdown = json.loads(entry[details_key])
            except Exception:
                breakdown = []
        
        if not breakdown:
            QMessageBox.information(self, "No Breakdown", 
                f"No {field_type} currency breakdown available for this entry.")
            return
        
        # Create breakdown dialog
        dialog = QDialog(self)
        dialog.setWindowTitle(f"{field_type} Currency Breakdown (View Only)")
        dialog.setMinimumWidth(600)
        dialog.setMinimumHeight(300)
        
        layout = QVBoxLayout(dialog)
        
        # Header
        header_text = "SELLING Currency (Money In)" if field_type == "MC In" else "BUYING Currency (Money Out)"
        header_color = "#22C55E" if field_type == "MC In" else "#DC2626"
        
        header = QLabel(f"💱 {header_text}")
        header.setStyleSheet(f"font-size: 14px; font-weight: 800; color: {header_color}; padding: 10px;")
        layout.addWidget(header)
        
        # Table for breakdown
        table = QTableWidget()
        table.setColumnCount(5)
        table.setHorizontalHeaderLabels(["Currency", "Pcs", "Denomination", "Rate", "Total"])
        table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        table.setEditTriggers(QTableWidget.NoEditTriggers)
        
        total = 0.0
        for entry_data in breakdown:
            row = table.rowCount()
            table.insertRow(row)
            
            currency = entry_data.get('currency', 'Unknown')
            qty = entry_data.get('quantity', 0)
            denom = entry_data.get('denomination', 0.0)
            rate = entry_data.get('rate', 0.0)
            total_php = entry_data.get('total_php', 0)
            if total_php == 0 and qty > 0 and rate > 0:
                if denom > 0:
                    total_php = qty * denom * rate
                else:
                    total_php = qty * rate
            total += total_php
            
            table.setItem(row, 0, QTableWidgetItem(str(currency)))
            table.setItem(row, 1, QTableWidgetItem(str(qty)))
            table.setItem(row, 2, QTableWidgetItem(f"{denom:,.2f}" if denom else "-"))
            table.setItem(row, 3, QTableWidgetItem(f"{rate:,.2f}"))
            table.setItem(row, 4, QTableWidgetItem(f"₱{total_php:,.2f}"))
        
        layout.addWidget(table)
        

        total_label = QLabel(f"TOTAL: ₱{total:,.2f}")
        total_label.setStyleSheet(f"font-size: 16px; font-weight: 800; color: {header_color}; padding: 10px;")
        total_label.setAlignment(Qt.AlignRight)
        layout.addWidget(total_label)
        

        close_btn = QPushButton("Close")
        close_btn.setStyleSheet("""
            QPushButton {
                background-color: #6B7280; color: white;
                padding: 10px 24px; border-radius: 6px;
                font-weight: 600;
            }
            QPushButton:hover { background-color: #4B5563; }
        """)
        close_btn.clicked.connect(dialog.accept)
        layout.addWidget(close_btn)
        
        dialog.exec_()

    def clear_all_fields(self):
        self._current_entry_data = None
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
        
        # Reset bank account selection
        self.selected_bank_account = None
        if self.bank_account_btn:
            self.bank_account_btn.setText("View")
            self.bank_account_btn.setToolTip("No bank account selected")
        
        # Reset branch destination selection
        self.selected_branch_dest = None
        if self.branch_dest_btn:
            self.branch_dest_btn.setText("View")
            self.branch_dest_btn.setToolTip("No destination branch specified")
        
        # Reset from branch source selection
        self.selected_from_branch_dest = None
        if self.from_branch_dest_btn:
            self.from_branch_dest_btn.setText("View")
            self.from_branch_dest_btn.setToolTip("No source branch specified")
        
        # Reset variance status display
        self.variance_status_display.setText("—")
        self.variance_status_display.setStyleSheet(
            "font-weight: bold; font-size: 12px; padding: 5px 10px; border-radius: 4px;"
        )

        # Reset reviewed checkbox
        self.reviewed_checkbox.blockSignals(True)
        self.reviewed_checkbox.setChecked(False)
        self.reviewed_checkbox.setText("Pending review")
        self.reviewed_checkbox.setStyleSheet(self.reviewed_checkbox.styleSheet().replace(
            "color: #2e7d32;", "color: #c0392b;"
        ))
        self.reviewed_checkbox.blockSignals(False)
        self.reviewed_checkbox.setEnabled(False)

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

            update_data = {}
            debit_sum = 0
            for ui_label, db_column in self.debit_fields.items():
                try:
                    val = float(self.debit_inputs[ui_label].text().strip() or 0)
                except ValueError:
                    val = 0
                update_data[db_column] = val
                debit_sum += val
                

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

                self.debit_total_display.setText(f"{debit_total:.2f}")
                self.credit_total_display.setText(f"{credit_total:.2f}")
                self.ending_balance_display.setText(f"{ending_balance:.2f}")
                self.cash_result_display.setText(f"{cash_result:.2f}")
                
                if variance_status == 'short':
                    self.variance_status_display.setText("SHORT")
                    self.variance_status_display.setStyleSheet(
                        "font-weight: bold; font-size: 12px; padding: 5px 10px; border-radius: 4px; background-color: #ffcdd2; color: #c62828;"
                    )
                elif variance_status == 'over':
                    self.variance_status_display.setText("OVER")
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