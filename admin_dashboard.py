from PyQt5.QtWidgets import (
    QWidget, QLabel, QVBoxLayout, QHBoxLayout, QGroupBox, QFormLayout,
    QLineEdit, QComboBox, QPushButton, QMessageBox, QDateEdit, QStackedWidget,
    QScrollArea, QFrame
)
from PyQt5.QtGui import QDoubleValidator, QFont
from PyQt5.QtCore import Qt, QDate
from db_connect import db_manager


# Uncomment these imports when you have these page files
from palawan_page import PalawanPage
from mc_page import MCPage
from fund_transfer import FundTransferPage
from payable_page import PayablesPage
from report_page import ReportPage



class AdminDashboard(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Admin Dashboard - Cash Management System")
        self.setGeometry(100, 100, 1000, 700)
        self.setMinimumSize(900, 600)

        # Use the global database manager from db_connect
        self.db = db_manager

        self.debit_inputs = {}
        self.credit_inputs = {}

        # Map UI field names to database column names
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
            "Cash Shortage/Overage": "cash_shortage_overage"
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
            "OTHERS": "others"
        }

        self.setup_styles()
        self.build_ui()
        self.load_corporations()

    def setup_styles(self):
        """Apply comprehensive styling for better UI"""
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

        # --- NAVIGATION BAR ---
        nav_frame = QFrame()
        nav_frame.setObjectName("navBar")
        nav_layout = QHBoxLayout(nav_frame)
        nav_layout.setContentsMargins(10, 8, 10, 8)
        nav_layout.setSpacing(5)

        self.daily_btn = QPushButton("📊 Daily Cash Count")
        self.palawan_btn = QPushButton("🏦 Palawan")
        self.mc_btn = QPushButton("💳 MC")
        self.fund_btn = QPushButton("💰 Fund Transfer")
        self.payable_btn = QPushButton("💰 Payable")
        self.report_btn = QPushButton("Reports")

        # Make buttons checkable for active state
        self.daily_btn.setCheckable(True)
        self.palawan_btn.setCheckable(True)
        self.mc_btn.setCheckable(True)
        self.fund_btn.setCheckable(True)
        self.daily_btn.setChecked(True)  # Default selection
        self.payable_btn.setChecked(True)
        self.report_btn.setChecked(True)

        nav_layout.addWidget(self.daily_btn)
        nav_layout.addWidget(self.palawan_btn)
        nav_layout.addWidget(self.mc_btn)
        nav_layout.addWidget(self.fund_btn)
        nav_layout.addWidget(self.payable_btn)
        nav_layout.addWidget(self.report_btn)
        nav_layout.addStretch()

        main_layout.addWidget(nav_frame)

        # --- STACKED VIEWS ---
        self.stack = QStackedWidget()
        self.daily_cash_widget = self.build_daily_cash_widget()

        # Temporary placeholder widgets for other pages
        # Replace these with actual imports when you have the page files
        self.palawan_widget = QWidget()
        palawan_label = QLabel("Palawan Page - Coming Soon")
        palawan_label.setAlignment(Qt.AlignCenter)
        palawan_layout = QVBoxLayout(self.palawan_widget)
        palawan_layout.addWidget(palawan_label)

        self.mc_widget = QWidget()
        mc_label = QLabel("MC Page - Coming Soon")
        mc_label.setAlignment(Qt.AlignCenter)
        mc_layout = QVBoxLayout(self.mc_widget)
        mc_layout.addWidget(mc_label)

        self.fund_widget = QWidget()
        fund_label = QLabel("Fund Transfer Page - Coming Soon")
        fund_label.setAlignment(Qt.AlignCenter)
        fund_layout = QVBoxLayout(self.fund_widget)
        fund_layout.addWidget(fund_label)

        self.payable_widget = QWidget()
        payable_label = QLabel("Fund Transfer Page - Coming Soon")
        payable_label.setAlignment(Qt.AlignCenter)
        payable_layout = QVBoxLayout(self.payable_widget)
        payable_layout.addWidget(payable_label)

        # Uncomment these when you have the actual page files:
        self.palawan_widget = PalawanPage()
        self.mc_widget = MCPage()
        self.fund_widget = FundTransferPage()
        self.payable_widget = PayablesPage()
        self.report_widget = ReportPage()

        self.stack.addWidget(self.daily_cash_widget)  # index 0
        self.stack.addWidget(self.palawan_widget)  # index 1
        self.stack.addWidget(self.mc_widget)  # index 2
        self.stack.addWidget(self.fund_widget)  # index 3
        self.stack.addWidget(self.payable_widget)
        self.stack.addWidget(self.report_widget)
        main_layout.addWidget(self.stack)

        # Connect nav buttons to switch views
        self.daily_btn.clicked.connect(lambda: self.switch_view(0, self.daily_btn))
        self.palawan_btn.clicked.connect(lambda: self.switch_view(1, self.palawan_btn))
        self.mc_btn.clicked.connect(lambda: self.switch_view(2, self.mc_btn))
        self.fund_btn.clicked.connect(lambda: self.switch_view(3, self.fund_btn))
        self.payable_btn.clicked.connect(lambda: self.switch_view(4, self.payable_btn))
        self.report_btn.clicked.connect(lambda: self.switch_view(5, self.report_btn))

        self.setLayout(main_layout)

    def switch_view(self, index, active_button):
        """Switch view and update button states"""
        self.stack.setCurrentIndex(index)
        # Uncheck all buttons
        for btn in [self.daily_btn, self.palawan_btn, self.mc_btn, self.fund_btn]:
            btn.setChecked(False)
        # Check active button
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

        # Corporation and Branch Selection
        selection_layout = QHBoxLayout()
        selection_layout.setSpacing(15)

        corp_label = QLabel("Corporation:")
        corp_label.setProperty("class", "header")
        self.corp_selector = QComboBox()
        self.corp_selector.currentTextChanged.connect(self.load_branches)

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

        selection_layout.addWidget(corp_label)
        selection_layout.addWidget(self.corp_selector, 1)
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
        balance_layout.addWidget(balance_label)
        balance_layout.addWidget(self.beginning_balance_input)
        balance_layout.addStretch()

        header_layout.addLayout(balance_layout)
        layout.addWidget(header_frame)

        # --- TRANSACTION SECTIONS ---
        columns_layout = QHBoxLayout()
        columns_layout.setSpacing(15)

        # Debit Section
        debit_box = QGroupBox("💸 DEBIT (Money In)")
        debit_form = QFormLayout()
        debit_form.setSpacing(8)
        debit_form.setLabelAlignment(Qt.AlignLeft)

        for label in self.debit_fields.keys():
            field_input = self.create_money_input()
            self.debit_inputs[label] = field_input
            field_label = QLabel(label)
            if any(keyword in label.lower() for keyword in ['interest', 'penalty', 'rescate']):
                field_label.setProperty("class", "important")
            debit_form.addRow(field_label, field_input)

        debit_box.setLayout(debit_form)

        # Credit Section
        credit_box = QGroupBox("💳 CREDIT (Money Out)")
        credit_form = QFormLayout()
        credit_form.setSpacing(8)
        credit_form.setLabelAlignment(Qt.AlignLeft)

        for label in self.credit_fields.keys():
            field_input = self.create_money_input()
            self.credit_inputs[label] = field_input
            field_label = QLabel(label)
            if any(keyword in label.lower() for keyword in ['empeno', 'fund transfer', 'salary']):
                field_label.setProperty("class", "important")
            credit_form.addRow(field_label, field_input)

        credit_box.setLayout(credit_form)

        columns_layout.addWidget(debit_box)
        columns_layout.addWidget(credit_box)
        layout.addLayout(columns_layout)

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

        layout.addWidget(results_frame)

        # --- SAVE BUTTON ---
        save_layout = QHBoxLayout()
        save_layout.addStretch()
        save_button = QPushButton("💾 Save Changes")
        save_button.setObjectName("saveButton")
        save_button.clicked.connect(self.save_changes)
        save_layout.addWidget(save_button)
        layout.addLayout(save_layout)

        # Connect change signals
        self.beginning_balance_input.textChanged.connect(self.update_calculations)
        self.cash_count_input.textChanged.connect(self.update_calculations)

        for field in self.debit_inputs.values():
            field.textChanged.connect(self.update_calculations)

        for field in self.credit_inputs.values():
            field.textChanged.connect(self.update_calculations)

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

    def load_corporations(self):
        """Load corporations from MySQL database"""
        try:
            self.corp_selector.clear()
            result = self.db.execute_query("SELECT DISTINCT corporation FROM daily_reports ORDER BY corporation")
            if result:
                for row in result:
                    if row['corporation']:  # Only add non-null corporations
                        self.corp_selector.addItem(row['corporation'])
        except Exception as e:
            print(f"Error loading corporations: {e}")
            QMessageBox.critical(self, "Database Error", f"Failed to load corporations: {e}")

    def load_branches(self):
        """Load branches for selected corporation from MySQL database"""
        try:
            self.branch_selector.clear()
            corp_name = self.corp_selector.currentText()
            if corp_name:
                query = """
                        SELECT DISTINCT branch
                        FROM daily_reports
                        WHERE corporation = %s
                        ORDER BY branch \
                        """
                result = self.db.execute_query(query, [corp_name])
                if result:
                    for row in result:
                        if row['branch']:  # Only add non-null branches
                            self.branch_selector.addItem(row['branch'])
        except Exception as e:
            print(f"Error loading branches: {e}")
            QMessageBox.critical(self, "Database Error", f"Failed to load branches: {e}")

    def load_entry_by_date(self):
        """Load cash entry from MySQL database by date"""
        corp_name = self.corp_selector.currentText()
        branch_name = self.branch_selector.currentText()
        selected_date = self.date_picker.date().toString("yyyy-MM-dd")

        if not corp_name or not branch_name:
            QMessageBox.warning(self, "Missing Selection", "Please select corporation and branch.")
            return

        try:
            # Query cash entry from daily_reports table
            query = """
                    SELECT * \
                    FROM daily_reports
                    WHERE corporation = %s \
                      AND branch = %s \
                      AND date = %s \
                    """
            result = self.db.execute_query(query, [corp_name, branch_name, selected_date])

            if not result:
                QMessageBox.information(self, "No Entry", f"No entry found for {selected_date}.")
                # Clear all fields
                self.clear_all_fields()
                return

            data = result[0]

            # Load basic entry data
            self.beginning_balance_input.setText(str(data.get('beginning_balance', 0)))
            self.ending_balance_display.setText(str(data.get('ending_balance', 0)))
            self.cash_count_input.setText(str(data.get('cash_count', 0)))
            self.cash_result_display.setText(str(data.get('cash_result', 0)))

            # Load debit fields
            for ui_label, db_column in self.debit_fields.items():
                if db_column in data and data[db_column] is not None:
                    self.debit_inputs[ui_label].setText(str(data[db_column]))
                else:
                    self.debit_inputs[ui_label].setText("0.00")

            # Load credit fields
            for ui_label, db_column in self.credit_fields.items():
                if db_column in data and data[db_column] is not None:
                    self.credit_inputs[ui_label].setText(str(data[db_column]))
                else:
                    self.credit_inputs[ui_label].setText("0.00")

            # Store current record info for updating
            self.current_record_id = data.get('id')

            QMessageBox.information(self, "✅ Loaded", f"Entry for {selected_date} loaded successfully!")

        except Exception as e:
            print(f"Error loading entry: {e}")
            QMessageBox.critical(self, "Error", f"Failed to load entry: {e}")

    def clear_all_fields(self):
        """Clear all input fields"""
        self.beginning_balance_input.setText("0.00")
        self.cash_count_input.setText("0.00")
        self.ending_balance_display.setText("0.00")
        self.cash_result_display.setText("0.00")

        for input_field in self.debit_inputs.values():
            input_field.setText("0.00")
        for input_field in self.credit_inputs.values():
            input_field.setText("0.00")

    def save_changes(self):
        """Save changes to MySQL database"""
        corp_name = self.corp_selector.currentText()
        branch_name = self.branch_selector.currentText()
        selected_date = self.date_picker.date().toString("yyyy-MM-dd")

        if not corp_name or not branch_name:
            QMessageBox.warning(self, "Missing Selection", "Please select corporation and branch.")
            return

        try:
            # Prepare data for saving
            data = {
                'corporation': corp_name,
                'branch': branch_name,
                'date': selected_date,
                'beginning_balance': float(self.beginning_balance_input.text() or 0),
                'ending_balance': float(self.ending_balance_display.text() or 0),
                'cash_count': float(self.cash_count_input.text() or 0),
                'cash_result': float(self.cash_result_display.text() or 0)
            }

            # Add debit fields to data
            for ui_label, db_column in self.debit_fields.items():
                data[db_column] = float(self.debit_inputs[ui_label].text() or 0)

            # Add credit fields to data
            for ui_label, db_column in self.credit_fields.items():
                data[db_column] = float(self.credit_inputs[ui_label].text() or 0)

            # Check if record already exists
            check_query = """
                          SELECT id \
                          FROM daily_reports
                          WHERE corporation = %s \
                            AND branch = %s \
                            AND date = %s \
                          """
            existing_record = self.db.execute_query(check_query, [corp_name, branch_name, selected_date])

            if existing_record:
                # Update existing record
                record_id = existing_record[0]['id']

                # Build update query dynamically
                set_clauses = []
                values = []

                for key, value in data.items():
                    if key not in ['corporation', 'branch', 'date']:  # Don't update these keys
                        set_clauses.append(f"{key} = %s")
                        values.append(value)

                values.append(record_id)  # Add ID for WHERE clause

                update_query = f"""
                UPDATE daily_reports 
                SET {', '.join(set_clauses)}
                WHERE id = %s
                """

                self.db.execute_query(update_query, values)
                message = "Entry updated successfully!"

            else:
                # Insert new record
                columns = list(data.keys())
                placeholders = ', '.join(['%s'] * len(columns))
                values = list(data.values())

                insert_query = f"""
                INSERT INTO daily_reports ({', '.join(columns)})
                VALUES ({placeholders})
                """

                self.db.execute_query(insert_query, values)
                message = "New entry created successfully!"

            QMessageBox.information(self, "✅ Saved", message)

        except Exception as e:
            print(f"Error saving changes: {e}")
            QMessageBox.critical(self, "❌ Error", f"Failed to save entry: {e}")

    def update_calculations(self):
        """Update ending balance and cash result calculations"""
        try:
            beginning_balance = float(self.beginning_balance_input.text() or 0)
            debit_total = sum(float(v.text() or 0) for v in self.debit_inputs.values())
            credit_total = sum(float(v.text() or 0) for v in self.credit_inputs.values())
            ending_balance = beginning_balance + debit_total - credit_total
            self.ending_balance_display.setText(f"{ending_balance:.2f}")
            cash_count = float(self.cash_count_input.text() or 0)
            cash_result = cash_count - ending_balance
            self.cash_result_display.setText(f"{cash_result:.2f}")
        except ValueError:
            pass  # ignore input error

    def closeEvent(self, event):
        """Clean up database connection when closing"""
        # Don't close the global db_manager connection since it might be used elsewhere
        event.accept()


# Optional: to run the widget directly for testing
if __name__ == "__main__":
    import sys
    from PyQt5.QtWidgets import QApplication

    app = QApplication(sys.argv)
    window = AdminDashboard()
    window.show()
    sys.exit(app.exec_())