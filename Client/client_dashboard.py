import datetime
from PyQt5.QtWidgets import (
    QWidget, QLabel, QLineEdit, QVBoxLayout, QHBoxLayout,
    QGroupBox, QFormLayout, QPushButton, QSpacerItem, QSizePolicy,
    QDateEdit, QMessageBox, QScrollArea, QFrame, QGridLayout, QTabWidget
)
from PyQt5.QtGui import QDoubleValidator, QFont, QPalette
from PyQt5.QtCore import Qt, QDate

from Client.cash_flow_tab import CashFlowTab
from Client.palawan_details_tab import PalawanDetailsTab
from Client.mc_currency_tab import MCCurrencyTab


class ClientDashboard(QWidget):
    def __init__(self, username, branch, corporation, db_manager):
        super().__init__()
        self.user_email = username
        self.corporation = corporation
        self.branch = branch
        self.db_manager = db_manager
        self.setWindowTitle("Client Dashboard - Daily Cash Report")
        self.setMinimumSize(1200, 800)

        # Track if beginning balance was auto-filled (for strict validation)
        self.beginning_balance_auto_filled = False
        self.previous_day_balance = None
        self.previous_day_date = None

        # Set professional styling
        self.setStyleSheet("""
            QWidget {
                background-color: #f5f5f5;
                font-family: 'Segoe UI', Arial, sans-serif;
            }
            QGroupBox {
                font-weight: bold;
                font-size: 12px;
                border: 2px solid #cccccc;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
                background-color: white;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 8px 0 8px;
                color: #2c3e50;
                background-color: white;
            }
            QLineEdit {
                border: 1px solid #bdc3c7;
                border-radius: 4px;
                padding: 8px;
                font-size: 11px;
                min-width: 120px;
                background-color: white;
            }
            QLineEdit:focus {
                border: 2px solid #3498db;
            }
            QLineEdit:read-only {
                background-color: #ecf0f1;
                color: #2c3e50;
                font-weight: bold;
            }
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                padding: 12px 24px;
                border-radius: 6px;
                font-weight: bold;
                font-size: 12px;
                min-width: 100px;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
            QPushButton:pressed {
                background-color: #21618c;
            }
            QPushButton:disabled {
                background-color: #bdc3c7;
                color: #7f8c8d;
            }
            QLabel {
                color: #2c3e50;
                font-size: 11px;
                min-width: 140px;
            }
            QTabWidget::pane {
                border: 1px solid #bdc3c7;
                background-color: white;
                border-radius: 4px;
            }
            QTabBar::tab {
                background-color: #ecf0f1;
                color: #2c3e50;
                border: 1px solid #bdc3c7;
                padding: 10px 16px;
                margin-right: 2px;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
            }
            QTabBar::tab:selected {
                background-color: white;
                border-bottom: 1px solid white;
            }
            QScrollArea {
                border: none;
                background-color: transparent;
            }
        """)

        # Create main scroll area
        main_scroll = QScrollArea()
        main_scroll.setWidgetResizable(True)
        main_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        main_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)

        # Create the main content widget
        content_widget = QWidget()
        main_scroll.setWidget(content_widget)

        # === Header Section ===
        header_frame = self.create_header_frame(username, branch, corporation)

        # === Date and Balance Section ===
        top_controls_frame = self.create_top_controls_frame()

        # === Create Tab Widget for better organization ===
        tab_widget = QTabWidget()

        # Initialize tabs
        self.cash_flow_tab = CashFlowTab(self)
        self.palawan_tab = PalawanDetailsTab(self)
        self.mc_currency_tab = MCCurrencyTab(self)

        # Add tabs
        tab_widget.addTab(self.cash_flow_tab, "Cash Flow")
        tab_widget.addTab(self.palawan_tab, "Palawan Details")
        tab_widget.addTab(self.mc_currency_tab, "MC Currency")

        # === Summary Section ===
        summary_frame = self.create_summary_frame()

        # === Post Button ===
        button_frame = self.create_button_frame()

        # === Main Layout Assembly ===
        main_layout = QVBoxLayout(content_widget)
        main_layout.setSpacing(15)
        main_layout.setContentsMargins(20, 20, 20, 20)

        main_layout.addWidget(header_frame)
        main_layout.addWidget(top_controls_frame)
        main_layout.addWidget(tab_widget)
        main_layout.addWidget(summary_frame)
        main_layout.addWidget(button_frame)
        main_layout.addStretch()

        # Set main layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(main_scroll)

        # Initialize validation on startup
        self.on_date_changed()

        self.showMaximized()

    def create_header_frame(self, username, branch, corporation):
        """Create header section"""
        header_frame = QFrame()
        header_frame.setFrameStyle(QFrame.StyledPanel)
        header_frame.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #3498db, stop:1 #2980b9);
                border-radius: 8px;
                margin: 5px;
            }
            QLabel {
                color: white;
                font-weight: bold;
            }
        """)

        header_layout = QVBoxLayout(header_frame)
        welcome_label = QLabel(f"Welcome, {username}!")
        welcome_label.setStyleSheet("font-size: 18px; font-weight: bold; color: white;")
        branch_label = QLabel(f"Branch: {branch}")
        branch_label.setStyleSheet("font-size: 14px; color: white;")
        corp_label = QLabel(f"Corporation: {corporation}")
        corp_label.setStyleSheet("font-size: 14px; color: white;")

        header_layout.addWidget(welcome_label)
        header_layout.addWidget(branch_label)
        header_layout.addWidget(corp_label)

        return header_frame

    def create_top_controls_frame(self):
        """Create date and balance controls"""
        top_controls_frame = QFrame()
        top_controls_frame.setStyleSheet("QFrame { background-color: white; border-radius: 8px; padding: 10px; }")
        top_controls_layout = QGridLayout(top_controls_frame)

        # Date Picker
        date_label = QLabel("Report Date:")
        date_label.setStyleSheet("font-weight: bold; font-size: 12px;")
        self.date_picker = QDateEdit()
        self.date_picker.setCalendarPopup(True)
        self.date_picker.setDate(QDate.currentDate())
        self.date_picker.setStyleSheet("QDateEdit { min-width: 150px; }")
        # Connect date change to comprehensive validation
        self.date_picker.dateChanged.connect(self.on_date_changed)

        # Beginning Balance - now read-only by default
        balance_label = QLabel("Beginning Balance:")
        balance_label.setStyleSheet("font-weight: bold; font-size: 12px;")
        self.beginning_balance_input = self.create_money_input("Will auto-fill from previous day")
        self.beginning_balance_input.setReadOnly(True)  # Make it read-only initially
        self.beginning_balance_input.setStyleSheet(self.beginning_balance_input.styleSheet() +
                                                   "background-color: #ecf0f1; color: #7f8c8d;")

        # Status label for beginning balance
        self.balance_status_label = QLabel("")
        self.balance_status_label.setStyleSheet("font-size: 10px; font-weight: bold;")

        # Auto-fill button for beginning balance (now the primary way to set it)
        self.auto_fill_button = QPushButton("Load from Previous Day")
        self.auto_fill_button.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                font-size: 10px;
                padding: 6px 12px;
                min-width: 140px;
            }
            QPushButton:hover {
                background-color: #229954;
            }
        """)
        self.auto_fill_button.clicked.connect(self.auto_fill_beginning_balance)

        top_controls_layout.addWidget(date_label, 0, 0)
        top_controls_layout.addWidget(self.date_picker, 0, 1)
        top_controls_layout.addWidget(balance_label, 0, 2)
        top_controls_layout.addWidget(self.beginning_balance_input, 0, 3)
        top_controls_layout.addWidget(self.auto_fill_button, 0, 4)
        top_controls_layout.addWidget(self.balance_status_label, 1, 2, 1, 3)

        return top_controls_frame

    def create_summary_frame(self):
        """Create summary section"""
        summary_frame = QFrame()
        summary_frame.setStyleSheet("QFrame { background-color: white; border-radius: 8px; padding: 15px; }")
        summary_layout = QGridLayout(summary_frame)

        # Summary title
        summary_title = QLabel("Cash Summary")
        summary_title.setStyleSheet("font-size: 16px; font-weight: bold; color: #2c3e50; margin-bottom: 10px;")
        summary_layout.addWidget(summary_title, 0, 0, 1, 4)

        # Ending Balance
        ending_label = QLabel("Ending Balance:")
        ending_label.setStyleSheet("font-weight: bold; font-size: 12px;")
        self.ending_balance_display = self.create_display_field("0.00")
        self.ending_balance_display.setStyleSheet(
            self.ending_balance_display.styleSheet() + "font-size: 14px; font-weight: bold;")

        # Cash Count
        cash_count_label = QLabel("Actual Cash Count:")
        cash_count_label.setStyleSheet("font-weight: bold; font-size: 12px;")
        self.cash_count_input = self.create_money_input("Enter actual cash counted")
        self.cash_count_input.textChanged.connect(self.update_cash_result)

        # Cash Result
        cash_result_label = QLabel("Variance:")
        cash_result_label.setStyleSheet("font-weight: bold; font-size: 12px;")
        self.cash_result_display = self.create_display_field("0.00")
        self.cash_result_display.setStyleSheet(
            self.cash_result_display.styleSheet() + "font-size: 14px; font-weight: bold;")

        # Variance status indicator
        self.variance_status_label = QLabel("")
        self.variance_status_label.setStyleSheet("font-weight: bold; font-size: 11px;")

        # Layout summary items
        summary_layout.addWidget(ending_label, 1, 0)
        summary_layout.addWidget(self.ending_balance_display, 1, 1)
        summary_layout.addWidget(cash_count_label, 2, 0)
        summary_layout.addWidget(self.cash_count_input, 2, 1)
        summary_layout.addWidget(cash_result_label, 3, 0)
        summary_layout.addWidget(self.cash_result_display, 3, 1)
        summary_layout.addWidget(self.variance_status_label, 3, 2, 1, 2)

        return summary_frame

    def create_button_frame(self):
        """Create post button section"""
        button_frame = QFrame()
        button_layout = QHBoxLayout(button_frame)
        button_layout.addStretch()

        self.post_button = QPushButton("📊 Post Report")
        self.post_button.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                color: white;
                font-size: 14px;
                font-weight: bold;
                padding: 15px 30px;
                border-radius: 8px;
                min-width: 150px;
            }
            QPushButton:hover {
                background-color: #229954;
            }
            QPushButton:disabled {
                background-color: #bdc3c7;
                color: #7f8c8d;
            }
        """)
        self.post_button.clicked.connect(self.handle_post)
        self.post_button.setEnabled(False)  # Disabled by default

        button_layout.addWidget(self.post_button)

        return button_frame

    def create_money_input(self, placeholder=""):
        """Create a money input field"""
        field = QLineEdit()
        field.setValidator(QDoubleValidator(0.0, 1e12, 2))
        field.setPlaceholderText(placeholder)
        field.textChanged.connect(self.recalculate_all)
        return field

    def create_display_field(self, placeholder=""):
        """Create a read-only display field"""
        field = QLineEdit()
        field.setReadOnly(True)
        field.setPlaceholderText(placeholder)
        return field

    def create_separator(self):
        """Create a visual separator line"""
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Sunken)
        separator.setStyleSheet("QFrame { color: #bdc3c7; margin: 5px 0; }")
        return separator

    def get_total_amount(self, inputs_dict):
        """Calculate total from input dictionary"""
        total = 0.0
        for field in inputs_dict.values():
            try:
                val = float(field.text().strip()) if field.text().strip() else 0.0
                total += val
            except ValueError:
                continue
        return total

    def get_previous_day_ending_balance(self, selected_date):
        """Get the ending balance from the previous working day"""
        try:
            print(f"🔍 Looking for previous day balance for date: {selected_date}")
            print(f"🏢 Branch: {self.branch}, Corporation: {self.corporation}")

            # Convert selected date to datetime object
            current_date = datetime.datetime.strptime(selected_date, "%Y-%m-%d")

            # Look for previous day's record (up to 10 days back to account for weekends/holidays)
            for days_back in range(1, 11):
                previous_date = current_date - datetime.timedelta(days=days_back)
                previous_date_str = previous_date.strftime("%Y-%m-%d")

                print(f"📅 Checking date: {previous_date_str} ({days_back} days back)")

                # Try to access the raw connection if available
                if hasattr(self.db_manager, 'connection') or hasattr(self.db_manager, 'conn'):
                    conn = getattr(self.db_manager, 'connection', None) or getattr(self.db_manager, 'conn', None)
                    if conn:
                        try:
                            cursor = conn.cursor()
                            query = """
                                    SELECT ending_balance
                                    FROM daily_reports
                                    WHERE date = %s
                                      AND branch = %s
                                      AND corporation = %s
                                    ORDER BY id DESC
                                        LIMIT 1 \
                                    """
                            cursor.execute(query, (previous_date_str, self.branch, self.corporation))
                            result = cursor.fetchone()
                            cursor.close()

                            print(f"📋 Direct cursor result: {result}")

                            if result:
                                # Handle different result formats
                                if isinstance(result, dict):
                                    ending_balance = result.get('ending_balance')
                                    if ending_balance is not None:
                                        print(
                                            f"✅ Found ending balance (dict): {ending_balance} for {previous_date_str}")
                                        return float(ending_balance), previous_date_str
                                elif isinstance(result, (list, tuple)) and len(result) > 0:
                                    ending_balance = result[0]
                                    print(
                                        f"✅ Found ending balance (tuple/list): {ending_balance} for {previous_date_str}")
                                    return float(ending_balance), previous_date_str
                                else:
                                    print(f"✅ Found ending balance (single): {result} for {previous_date_str}")
                                    return float(result), previous_date_str

                        except Exception as e:
                            print(f"❌ Direct cursor error: {e}")
                            continue

            print("❌ No previous day balance found in the last 10 days")
            return None, None

        except Exception as e:
            print(f"❌ Error getting previous day balance: {str(e)}")
            return None, None

    def check_existing_entry(self, selected_date):
        """Check if an entry already exists for the selected date"""
        try:
            print(f"🔍 Checking for existing entry on: {selected_date}")

            if hasattr(self.db_manager, 'connection') or hasattr(self.db_manager, 'conn'):
                conn = getattr(self.db_manager, 'connection', None) or getattr(self.db_manager, 'conn', None)
                if conn:
                    cursor = conn.cursor()
                    query = """
                            SELECT COUNT(*) as count
                            FROM daily_reports
                            WHERE date = %s
                              AND branch = %s
                              AND corporation = %s
                            """
                    cursor.execute(query, (selected_date, self.branch, self.corporation))
                    result = cursor.fetchone()
                    cursor.close()

                    if result:
                        if isinstance(result, dict):
                            count = result.get('count', 0)
                        else:
                            count = result[0] if isinstance(result, (list, tuple)) else result

                        print(f"📋 Existing entries found: {count}")
                        return count > 0

            return False

        except Exception as e:
            print(f"❌ Error checking existing entry: {str(e)}")
            return False

    def on_date_changed(self):
        """Handle date picker changes with comprehensive validation"""
        selected_date = self.date_picker.date().toString("yyyy-MM-dd")
        print(f"📅 Date changed to: {selected_date}")

        # Reset states
        self.beginning_balance_auto_filled = False
        self.previous_day_balance = None
        self.previous_day_date = None

        # Clear beginning balance
        self.beginning_balance_input.clear()
        self.beginning_balance_input.setReadOnly(True)

        # Check if entry already exists
        if self.check_existing_entry(selected_date):
            self.balance_status_label.setText("⚠️ Entry already exists for this date!")
            self.balance_status_label.setStyleSheet("color: #e74c3c; font-weight: bold; font-size: 10px;")
            self.auto_fill_button.setEnabled(False)
            self.post_button.setEnabled(False)
            self.disable_all_inputs()
            return
        else:
            self.enable_all_inputs()
            self.auto_fill_button.setEnabled(True)

        # Get previous day's balance
        previous_balance, previous_date = self.get_previous_day_ending_balance(selected_date)

        if previous_balance is not None:
            self.previous_day_balance = previous_balance
            self.previous_day_date = previous_date
            self.balance_status_label.setText(f"Previous day ({previous_date}): {previous_balance:.2f}")
            self.balance_status_label.setStyleSheet("color: #3498db; font-weight: bold; font-size: 10px;")
        else:
            self.balance_status_label.setText("No previous day record found - First entry allowed")
            self.balance_status_label.setStyleSheet("color: #f39c12; font-weight: bold; font-size: 10px;")
            # For first entry, allow manual input
            self.beginning_balance_input.setReadOnly(False)
            self.beginning_balance_input.setPlaceholderText("Enter beginning balance (first entry)")
            self.beginning_balance_input.setStyleSheet("background-color: white; color: #2c3e50;")

        self.recalculate_all()

    def auto_fill_beginning_balance(self):
        """Auto-fill beginning balance from previous day's ending balance"""
        selected_date = self.date_picker.date().toString("yyyy-MM-dd")

        # Check for existing entry first
        if self.check_existing_entry(selected_date):
            self.show_message("Entry Exists",
                              f"An entry already exists for {selected_date}. Cannot create duplicate entries.",
                              QMessageBox.Warning)
            return

        if self.previous_day_balance is not None:
            self.beginning_balance_input.setText(f"{self.previous_day_balance:.2f}")
            self.beginning_balance_auto_filled = True

            # Update styling to show it's correctly set
            self.beginning_balance_input.setStyleSheet("""
                QLineEdit {
                    border: 2px solid #27ae60;
                    background-color: #f2fdf2;
                    color: #2c3e50;
                    font-weight: bold;
                }
            """)

            self.balance_status_label.setText(
                f"✅ Loaded from {self.previous_day_date}: {self.previous_day_balance:.2f}")
            self.balance_status_label.setStyleSheet("color: #27ae60; font-weight: bold; font-size: 10px;")

            self.auto_fill_button.setText("✅ Balance Loaded")
            self.auto_fill_button.setEnabled(False)

            self.show_message("Success",
                              f"Beginning balance set to {self.previous_day_balance:.2f} from {self.previous_day_date}",
                              QMessageBox.Information)
        else:
            self.show_message("No Previous Record",
                              "No previous day's record found. This appears to be the first entry.",
                              QMessageBox.Information)
            # Allow manual input for first entry
            self.beginning_balance_input.setReadOnly(False)
            self.beginning_balance_input.setPlaceholderText("Enter beginning balance (first entry)")
            self.beginning_balance_input.setStyleSheet("background-color: white; color: #2c3e50;")
            self.beginning_balance_auto_filled = True  # Mark as valid for first entry

    def disable_all_inputs(self):
        """Disable all input fields when entry exists"""
        self.beginning_balance_input.setEnabled(False)
        self.cash_count_input.setEnabled(False)
        # Disable tab inputs
        if hasattr(self.cash_flow_tab, 'set_enabled'):
            self.cash_flow_tab.set_enabled(False)
        if hasattr(self.palawan_tab, 'set_enabled'):
            self.palawan_tab.set_enabled(False)
        if hasattr(self.mc_currency_tab, 'set_enabled'):
            self.mc_currency_tab.set_enabled(False)

    def enable_all_inputs(self):
        """Enable all input fields when no entry exists"""
        self.beginning_balance_input.setEnabled(True)
        self.cash_count_input.setEnabled(True)
        # Enable tab inputs
        if hasattr(self.cash_flow_tab, 'set_enabled'):
            self.cash_flow_tab.set_enabled(True)
        if hasattr(self.palawan_tab, 'set_enabled'):
            self.palawan_tab.set_enabled(True)
        if hasattr(self.mc_currency_tab, 'set_enabled'):
            self.mc_currency_tab.set_enabled(True)

    def recalculate_all(self):
        """Recalculate all totals and balances"""
        try:
            beginning = float(
                self.beginning_balance_input.text().strip()) if self.beginning_balance_input.text().strip() else 0.0
        except ValueError:
            beginning = 0.0

        debit_total = self.cash_flow_tab.get_debit_total()
        credit_total = self.cash_flow_tab.get_credit_total()

        self.cash_flow_tab.update_totals(beginning, debit_total, credit_total)

        ending = beginning + debit_total - credit_total
        self.ending_balance_display.setText(f"{ending:.2f}")

        # Color code the ending balance
        if ending > 0:
            self.ending_balance_display.setStyleSheet(self.ending_balance_display.styleSheet() + "color: #27ae60;")
        elif ending < 0:
            self.ending_balance_display.setStyleSheet(self.ending_balance_display.styleSheet() + "color: #e74c3c;")
        else:
            self.ending_balance_display.setStyleSheet(self.ending_balance_display.styleSheet() + "color: #2c3e50;")

        self.update_cash_result()
        self.palawan_tab.calculate_palawan_totals()
        self.mc_currency_tab.calculate_mc_totals()

    def update_cash_result(self):
        """Update cash variance calculation and post button status"""
        try:
            cash_count = float(self.cash_count_input.text().strip()) if self.cash_count_input.text().strip() else 0.0
            ending_balance = float(
                self.ending_balance_display.text().strip()) if self.ending_balance_display.text().strip() else 0.0
            diff = cash_count - ending_balance
            self.cash_result_display.setText(f"{diff:.2f}")

            # Check all validation conditions
            can_post = (
                    self.beginning_balance_auto_filled and  # Beginning balance must be properly set
                    abs(diff) < 0.01 and  # No variance allowed
                    self.beginning_balance_input.text().strip() and  # Beginning balance must be entered
                    self.cash_count_input.text().strip()  # Cash count must be entered
            )

            # Update variance status and post button
            if abs(diff) < 0.01:  # Exact (within 1 cent)
                self.cash_result_display.setStyleSheet(self.cash_result_display.styleSheet() + "color: #27ae60;")
                if can_post:
                    self.variance_status_label.setText("✅ No Variance - Ready to Post")
                    self.variance_status_label.setStyleSheet("color: #27ae60; font-weight: bold;")
                    self.post_button.setEnabled(True)
                else:
                    self.variance_status_label.setText("⚠️ Load beginning balance first")
                    self.variance_status_label.setStyleSheet("color: #f39c12; font-weight: bold;")
                    self.post_button.setEnabled(False)
            else:
                if diff > 0:  # Over
                    self.cash_result_display.setStyleSheet(self.cash_result_display.styleSheet() + "color: #f39c12;")
                    self.variance_status_label.setText(f"⚠️ OVER by {diff:.2f} - Cannot Post")
                else:  # Short
                    self.cash_result_display.setStyleSheet(self.cash_result_display.styleSheet() + "color: #e74c3c;")
                    self.variance_status_label.setText(f"❌ SHORT by {abs(diff):.2f} - Cannot Post")

                self.variance_status_label.setStyleSheet("color: #e74c3c; font-weight: bold;")
                self.post_button.setEnabled(False)

        except ValueError:
            self.cash_result_display.setText("0.00")
            self.variance_status_label.setText("⚠️ Invalid Input")
            self.variance_status_label.setStyleSheet("color: #e74c3c; font-weight: bold;")
            self.post_button.setEnabled(False)

    def handle_post(self):
        """Handle the post report action with enhanced validation"""
        try:
            selected_date = self.date_picker.date().toString("yyyy-MM-dd")

            # Final validation check
            if not self.validate_all_requirements():
                return

            # Double-check for duplicate entry
            if self.check_existing_entry(selected_date):
                self.show_message("Duplicate Entry",
                                  f"An entry already exists for {selected_date}. Cannot create duplicate entries.",
                                  QMessageBox.Critical)
                return

            # Gather all data
            beginning = float(self.beginning_balance_input.text().strip())

            # Get data from all tabs
            cash_flow_data = self.cash_flow_tab.get_data()
            palawan_data = self.palawan_tab.get_data()
            mc_currency_data = self.mc_currency_tab.get_data()

            debit_total = sum(cash_flow_data['debit'].values())
            credit_total = sum(cash_flow_data['credit'].values())
            ending = beginning + debit_total - credit_total
            cash_count = float(self.cash_count_input.text().strip())
            cash_result = cash_count - ending

            # Combine all field values
            all_values = {**cash_flow_data['debit'], **cash_flow_data['credit'], **palawan_data, **mc_currency_data}

            # Build the INSERT query
            columns = [
                          'date', 'username', 'branch', 'corporation',
                          'beginning_balance', 'debit_total', 'credit_total',
                          'ending_balance', 'cash_count', 'cash_result'
                      ] + list(all_values.keys())

            values = [
                         selected_date, self.user_email, self.branch, self.corporation,
                         beginning, debit_total, credit_total,
                         ending, cash_count, cash_result
                     ] + list(all_values.values())

            # Create placeholders for the query - NO ON DUPLICATE KEY UPDATE
            placeholders = ', '.join(['%s'] * len(columns))
            columns_str = ', '.join(columns)

            insert_query = f"""
                INSERT INTO daily_reports ({columns_str})
                VALUES ({placeholders})
            """

            # Execute the query
            rows_affected = self.db_manager.execute_query(insert_query, values)

            if rows_affected > 0:
                self.show_success_message(f"Report for {selected_date} posted successfully!")
                print(f"✅ Data saved successfully. Rows affected: {rows_affected}")
                self.clear_all_fields()
            else:
                self.show_message("Warning", "No rows were inserted.", QMessageBox.Warning)

        except Exception as e:
            error_msg = f"Failed to post data: {str(e)}"
            print(f"❌ {error_msg}")
            self.show_message("Error", error_msg, QMessageBox.Critical)

    def validate_all_requirements(self):
        """Enhanced validation for all requirements"""
        selected_date = self.date_picker.date().toString("yyyy-MM-dd")

        # Check if entry already exists (most important check)
        if self.check_existing_entry(selected_date):
            self.show_message("Duplicate Entry Error",
                              f"An entry for {selected_date} already exists. Only one entry per day is allowed.",
                              QMessageBox.Critical)
            return False

        # Check if beginning balance was properly loaded
        if not self.beginning_balance_auto_filled:
            if self.previous_day_balance is not None:
                self.show_message("Beginning Balance Error",
                                  f"You must load the beginning balance from the previous day ({self.previous_day_date}).\n\n" +
                                  f"Click 'Load from Previous Day' to set the correct beginning balance of {self.previous_day_balance:.2f}.",
                                  QMessageBox.Critical)
                return False
            else:
                # First entry - check if beginning balance is manually entered
                if not self.beginning_balance_input.text().strip():
                    self.show_message("Beginning Balance Error",
                                      "This appears to be your first entry. Please enter the beginning balance manually.",
                                      QMessageBox.Critical)
                    self.beginning_balance_input.setFocus()
                    return False

        # Check basic required fields
        if not self.beginning_balance_input.text().strip():
            self.show_message("Validation Error", "Please set the beginning balance.", QMessageBox.Warning)
            return False

        if not self.cash_count_input.text().strip():
            self.show_message("Validation Error", "Please enter the actual cash count.", QMessageBox.Warning)
            self.cash_count_input.setFocus()
            return False

        # Validate beginning balance matches previous day (if not first entry)
        if self.previous_day_balance is not None:
            try:
                current_beginning = float(self.beginning_balance_input.text().strip())
                if abs(current_beginning - self.previous_day_balance) > 0.01:
                    self.show_message("Beginning Balance Mismatch",
                                      f"Beginning balance MUST match the previous day's ending balance.\n\n" +
                                      f"Expected: {self.previous_day_balance:.2f} (from {self.previous_day_date})\n" +
                                      f"Current: {current_beginning:.2f}\n\n" +
                                      f"Please click 'Load from Previous Day' to set the correct amount.",
                                      QMessageBox.Critical)
                    return False
            except ValueError:
                self.show_message("Validation Error", "Invalid beginning balance value.", QMessageBox.Warning)
                return False

        # Check for variance (critical check)
        try:
            cash_count = float(self.cash_count_input.text().strip())
            ending_balance = float(self.ending_balance_display.text().strip())
            variance = abs(cash_count - ending_balance)

            if variance >= 0.01:  # More than 1 cent variance
                self.show_message("Variance Error",
                                  f"Cannot post report with cash variance!\n\n" +
                                  f"Ending Balance: {ending_balance:.2f}\n" +
                                  f"Cash Count: {cash_count:.2f}\n" +
                                  f"Variance: {cash_count - ending_balance:.2f}\n\n" +
                                  f"Please reconcile the difference before posting.",
                                  QMessageBox.Critical)
                self.cash_count_input.setFocus()
                return False

        except ValueError:
            self.show_message("Validation Error", "Invalid cash count value.", QMessageBox.Warning)
            return False

        return True

    def clear_all_fields(self):
        """Clear all input fields after successful post"""
        reply = QMessageBox.question(
            self,
            "Clear Fields",
            "Report posted successfully! Would you like to advance to the next day?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.Yes
        )

        if reply == QMessageBox.Yes:
            # Advance date to next day
            current_date = self.date_picker.date()
            next_date = current_date.addDays(1)
            self.date_picker.setDate(next_date)

            # Clear all fields
            self.beginning_balance_input.clear()
            self.cash_count_input.clear()

            # Reset states
            self.beginning_balance_auto_filled = False
            self.previous_day_balance = None
            self.previous_day_date = None

            # Reset button and styling
            self.auto_fill_button.setText("Load from Previous Day")
            self.auto_fill_button.setEnabled(True)
            self.beginning_balance_input.setStyleSheet("")
            self.balance_status_label.setText("")

            # Clear tab fields
            if hasattr(self.cash_flow_tab, 'clear_fields'):
                self.cash_flow_tab.clear_fields()
            if hasattr(self.palawan_tab, 'clear_fields'):
                self.palawan_tab.clear_fields()
            if hasattr(self.mc_currency_tab, 'clear_fields'):
                self.mc_currency_tab.clear_fields()

            # Trigger date validation for new date
            self.on_date_changed()

    def show_success_message(self, message):
        """Show a styled success message"""
        msg = QMessageBox(self)
        msg.setIcon(QMessageBox.Information)
        msg.setWindowTitle("Success")
        msg.setText(message)
        msg.setStyleSheet("""
            QMessageBox {
                background-color: white;
            }
            QMessageBox QPushButton {
                background-color: #27ae60;
                color: white;
                border-radius: 4px;
                padding: 8px 16px;
                min-width: 80px;
            }
        """)
        msg.exec_()

    def show_message(self, title, message, icon):
        """Show message dialog with improved styling"""
        msg = QMessageBox(icon, title, message, QMessageBox.Ok, self)
        msg.setStyleSheet("""
            QMessageBox {
                background-color: white;
                font-size: 12px;
            }
            QMessageBox QPushButton {
                background-color: #3498db;
                color: white;
                border-radius: 4px;
                padding: 8px 16px;
                min-width: 80px;
            }
        """)
        msg.exec_()

    # Legacy methods kept for compatibility
    def validate_beginning_balance(self):
        """Legacy method - now handled by on_date_changed"""
        return self.beginning_balance_auto_filled

    def validate_required_fields(self):
        """Legacy validation method - kept for compatibility"""
        return self.validate_all_requirements()

    def check_duplicate_entry(self, selected_date):
        """Legacy method - redirects to check_existing_entry"""
        return self.check_existing_entry(selected_date)