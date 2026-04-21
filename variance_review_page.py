"""
Variance Review Page for Admin Dashboard
Displays entries with short/over variance and allows viewing cashflow details
"""

from PyQt5.QtWidgets import (
    QWidget, QLabel, QVBoxLayout, QHBoxLayout, QGroupBox, QFormLayout,
    QComboBox, QPushButton, QMessageBox, QDateEdit, QScrollArea, QFrame,
    QTableWidget, QTableWidgetItem, QHeaderView, QSplitter, QSizePolicy
)
from PyQt5.QtCore import Qt, QDate
from db_connect_pooled import db_manager
from date_range_widget import DateRangeWidget


class VarianceReviewPage(QWidget):
    """Page for reviewing entries with cash variance (short/over)"""
    
    # Field mappings for Brand B (daily_reports)
    debit_fields_brand_b = {
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
    
    credit_fields_brand_b = {
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
    
    def __init__(self, account_type=2):
        super().__init__()
        self.db = db_manager
        self.account_type = account_type
        # Set correct table based on brand: Brand A -> daily_reports_brand_a, Brand B -> daily_reports
        self.current_table = "daily_reports_brand_a" if account_type == 1 else "daily_reports"
        self.setup_ui()
        # Set brand filter to match account_type
        if account_type == 1:
            self.brand_filter.setCurrentText("Brand A")
        else:
            self.brand_filter.setCurrentText("Brand B")
        self._load_corporations()

    @staticmethod
    def _filter_label(text, style=""):
        lbl = QLabel(text)
        lbl.setStyleSheet(style or "font-size: 11px; font-weight: 600; padding: 0; background: transparent;")
        return lbl

    def setup_ui(self):
        """Setup the variance review UI"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(8)

        # --- COMPACT FILTER SECTION ---
        filter_frame = QFrame()
        filter_frame.setObjectName("varianceFilterFrame")
        filter_frame.setStyleSheet("""
            QFrame#varianceFilterFrame {
                background-color: #fff3cd;
                border: 1px solid #ffc107;
                border-radius: 6px;
                padding: 4px;
            }
        """)
        filter_frame.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        
        filter_layout = QHBoxLayout(filter_frame)
        filter_layout.setContentsMargins(8, 4, 8, 4)
        filter_layout.setSpacing(8)

        # Title
        title_label = QLabel("⚠️ Variance Review")
        title_label.setStyleSheet("font-size: 13px; font-weight: bold; color: #856404;")
        filter_layout.addWidget(title_label)

        # Brand filter
        self.brand_filter = QComboBox()
        self.brand_filter.addItems(["Brand B", "Brand A"])
        self.brand_filter.setFixedWidth(90)
        self.brand_filter.setStyleSheet("font-size: 11px;")
        self.brand_filter.currentTextChanged.connect(self._on_brand_changed)
        lbl_style = "font-size: 11px; font-weight: 600; color: #856404; padding: 0; background: transparent;"
        filter_layout.addWidget(self._filter_label("Brand:", lbl_style))
        filter_layout.addWidget(self.brand_filter)

        # Corporation filter
        self.corp_filter = QComboBox()
        self.corp_filter.setFixedWidth(140)
        self.corp_filter.setStyleSheet("font-size: 11px;")
        filter_layout.addWidget(self._filter_label("Corp:", lbl_style))
        filter_layout.addWidget(self.corp_filter)

        # Date Range Widget (replaces single date + All Dates toggle)
        self.date_range_widget = DateRangeWidget()
        self.date_filter = self.date_range_widget  # backward-compat
        filter_layout.addWidget(self.date_range_widget)

        # Variance type filter
        self.var_type_filter = QComboBox()
        self.var_type_filter.addItems(["All", "Short", "Over"])
        self.var_type_filter.setFixedWidth(70)
        self.var_type_filter.setStyleSheet("font-size: 11px;")
        filter_layout.addWidget(self._filter_label("Type:", lbl_style))
        filter_layout.addWidget(self.var_type_filter)

        # Search button
        search_btn = QPushButton("🔍 Search")
        search_btn.setFixedWidth(80)
        search_btn.setStyleSheet("""
            QPushButton {
                background-color: #007bff; color: white; border: none;
                padding: 5px 10px; border-radius: 3px; font-weight: bold; font-size: 11px;
            }
            QPushButton:hover { background-color: #0056b3; }
        """)
        search_btn.clicked.connect(self.search_entries)
        filter_layout.addWidget(search_btn)
        
        filter_layout.addStretch()

        main_layout.addWidget(filter_frame)

        # --- SPLITTER FOR BRANCH LIST AND CASHFLOW DETAILS ---
        splitter = QSplitter(Qt.Horizontal)
        
        # Left panel - Branch list
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 5, 0, 0)
        left_layout.setSpacing(5)
        
        branch_label = QLabel("📋 Entries with Variance")
        branch_label.setStyleSheet("font-size: 12px; font-weight: bold; color: #2c3e50;")
        left_layout.addWidget(branch_label)

        self.variance_table = QTableWidget()
        self.variance_table.setColumnCount(7)
        self.variance_table.setHorizontalHeaderLabels(["Date", "Corporation", "Branch", "Variance", "Status", "ID", "Table"])
        self.variance_table.setColumnHidden(5, True)  # Hide ID column
        self.variance_table.setColumnHidden(6, True)  # Hide Table column
        self.variance_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.variance_table.setSelectionMode(QTableWidget.SingleSelection)
        self.variance_table.setAlternatingRowColors(True)
        self.variance_table.setStyleSheet("""
            QTableWidget {
                background-color: white; gridline-color: #dee2e6;
                border: 1px solid #dee2e6; border-radius: 4px; font-size: 11px;
            }
            QTableWidget::item { padding: 5px; }
            QTableWidget::item:selected { background-color: #007bff; color: white; }
            QHeaderView::section {
                background-color: #f8f9fa; padding: 6px; border: none;
                border-bottom: 2px solid #dee2e6; font-weight: bold; font-size: 11px;
            }
        """)
        header = self.variance_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        header.setSectionResizeMode(2, QHeaderView.Stretch)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        
        self.variance_table.cellClicked.connect(self._on_entry_clicked)
        left_layout.addWidget(self.variance_table)
        
        splitter.addWidget(left_panel)

        # Right panel - Cashflow details
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(0, 5, 0, 0)
        right_layout.setSpacing(5)

        details_label = QLabel("💰 Cashflow Details")
        details_label.setStyleSheet("font-size: 12px; font-weight: bold; color: #2c3e50;")
        right_layout.addWidget(details_label)

        details_scroll = QScrollArea()
        details_scroll.setWidgetResizable(True)
        details_scroll.setStyleSheet("""
            QScrollArea { background-color: white; border: 1px solid #dee2e6; border-radius: 4px; }
        """)
        
        self.details_widget = QWidget()
        self.details_layout = QVBoxLayout(self.details_widget)
        self.details_layout.setContentsMargins(10, 10, 10, 10)
        
        # Placeholder
        placeholder = QLabel("Select an entry to view details")
        placeholder.setStyleSheet("color: #6c757d; font-style: italic; padding: 20px;")
        placeholder.setAlignment(Qt.AlignCenter)
        self.details_layout.addWidget(placeholder)
        
        details_scroll.setWidget(self.details_widget)
        right_layout.addWidget(details_scroll)
        
        splitter.addWidget(right_panel)
        splitter.setSizes([400, 600])

        main_layout.addWidget(splitter)

    def _on_brand_changed(self, brand):
        """Handle brand filter change"""
        if brand == "Brand A":
            self.current_table = "daily_reports_brand_a"
        else:
            self.current_table = "daily_reports"
        self._load_corporations()

    def _load_corporations(self):
        """Load corporations for filter"""
        try:
            query = f"SELECT DISTINCT corporation FROM {self.current_table} ORDER BY corporation"
            rows = self.db.execute_query(query)
            self.corp_filter.clear()
            self.corp_filter.addItem("All", "")
            if rows:
                for r in rows:
                    if r.get('corporation'):
                        self.corp_filter.addItem(r['corporation'], r['corporation'])
        except Exception as e:
            print(f"Error loading corporations: {e}")

    def search_entries(self):
        """Search for variance entries"""
        try:
            corp = self.corp_filter.currentData()
            date_start, date_end = self.date_range_widget.get_date_range()
            is_range = self.date_range_widget.is_range_mode()
            var_type = self.var_type_filter.currentText()

            query = f"""
                SELECT id, date, corporation, branch, cash_result, variance_status
                FROM {self.current_table}
                WHERE variance_status IN ('short', 'over')
            """
            params = []

            if corp:
                query += " AND corporation = %s"
                params.append(corp)

            if is_range:
                query += " AND date >= %s AND date <= %s"
                params.extend([date_start, date_end])
            else:
                query += " AND date = %s"
                params.append(date_start)

            if var_type == "Short":
                query += " AND variance_status = 'short'"
            elif var_type == "Over":
                query += " AND variance_status = 'over'"

            query += " ORDER BY date DESC, corporation, branch LIMIT 100"

            result = self.db.execute_query(query, params if params else None)

            self.variance_table.setRowCount(0)
            if not result:
                return

            for row_data in result:
                row_idx = self.variance_table.rowCount()
                self.variance_table.insertRow(row_idx)
                
                date_item = QTableWidgetItem(str(row_data.get('date', ''))[:10])
                corp_item = QTableWidgetItem(str(row_data.get('corporation', '')))
                branch_item = QTableWidgetItem(str(row_data.get('branch', '')))
                
                variance = row_data.get('cash_result', 0) or 0
                variance_item = QTableWidgetItem(f"{variance:,.2f}")
                variance_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                
                status = str(row_data.get('variance_status', '')).upper()
                status_item = QTableWidgetItem(status)
                if status == 'SHORT':
                    status_item.setBackground(Qt.red)
                    status_item.setForeground(Qt.white)
                elif status == 'OVER':
                    status_item.setBackground(Qt.darkYellow)
                
                id_item = QTableWidgetItem(str(row_data.get('id', '')))
                table_item = QTableWidgetItem(self.current_table)

                self.variance_table.setItem(row_idx, 0, date_item)
                self.variance_table.setItem(row_idx, 1, corp_item)
                self.variance_table.setItem(row_idx, 2, branch_item)
                self.variance_table.setItem(row_idx, 3, variance_item)
                self.variance_table.setItem(row_idx, 4, status_item)
                self.variance_table.setItem(row_idx, 5, id_item)
                self.variance_table.setItem(row_idx, 6, table_item)

        except Exception as e:
            print(f"Error searching entries: {e}")
            QMessageBox.critical(self, "Error", f"Failed to search: {e}")

    def _on_entry_clicked(self, row, column):
        """Handle click on entry to show cashflow details"""
        try:
            entry_id = self.variance_table.item(row, 5).text()
            table_name = self.variance_table.item(row, 6).text()
            date_val = self.variance_table.item(row, 0).text()
            corp_val = self.variance_table.item(row, 1).text()
            branch_val = self.variance_table.item(row, 2).text()

            query = (f"SELECT beginning_balance, debit_total, credit_total, "
                     f"ending_balance, cash_count, cash_result, variance_status "
                     f"FROM {table_name} WHERE id = %s")
            result = self.db.execute_query(query, [entry_id])

            if not result:
                return

            data = result[0]

            # Clear existing widgets
            while self.details_layout.count():
                item = self.details_layout.takeAt(0)
                if item.widget():
                    item.widget().deleteLater()

            # Header
            brand_name = "Brand A" if table_name == "daily_reports_brand_a" else "Brand B"
            header = QLabel(f"📅 {date_val} | 🏢 {corp_val} | 📍 {branch_val} | 🏷️ {brand_name}")
            header.setStyleSheet("font-size: 12px; font-weight: bold; color: #2c3e50; padding-bottom: 8px;")
            self.details_layout.addWidget(header)

            # Summary section
            summary_frame = QFrame()
            summary_frame.setStyleSheet("""
                QFrame { background-color: #e8f5e9; border: 1px solid #81c784; border-radius: 5px; padding: 8px; }
            """)
            summary_layout = QFormLayout(summary_frame)
            summary_layout.setSpacing(3)

            beginning = data.get('beginning_balance', 0) or 0
            debit_total = data.get('debit_total', 0) or 0
            credit_total = data.get('credit_total', 0) or 0
            ending = data.get('ending_balance', 0) or 0
            cash_count = data.get('cash_count', 0) or 0
            cash_result = data.get('cash_result', 0) or 0
            variance_status = data.get('variance_status', 'balanced')

            summary_layout.addRow(QLabel("Beginning:"), QLabel(f"₱ {beginning:,.2f}"))
            summary_layout.addRow(QLabel("Debit Total:"), QLabel(f"₱ {debit_total:,.2f}"))
            summary_layout.addRow(QLabel("Credit Total:"), QLabel(f"₱ {credit_total:,.2f}"))
            summary_layout.addRow(QLabel("Ending:"), QLabel(f"₱ {ending:,.2f}"))
            summary_layout.addRow(QLabel("Cash Count:"), QLabel(f"₱ {cash_count:,.2f}"))
            
            var_label = QLabel(f"₱ {cash_result:,.2f}")
            if variance_status == 'short':
                var_label.setStyleSheet("color: #c62828; font-weight: bold;")
            elif variance_status == 'over':
                var_label.setStyleSheet("color: #f57c00; font-weight: bold;")
            summary_layout.addRow(QLabel("Variance:"), var_label)

            status_text = f"⚠️ {variance_status.upper()}" if variance_status != 'balanced' else "✓ BALANCED"
            status_lbl = QLabel(status_text)
            if variance_status == 'short':
                status_lbl.setStyleSheet("background: #ffcdd2; color: #c62828; font-weight: bold; padding: 3px 6px; border-radius: 3px;")
            elif variance_status == 'over':
                status_lbl.setStyleSheet("background: #fff3cd; color: #856404; font-weight: bold; padding: 3px 6px; border-radius: 3px;")
            else:
                status_lbl.setStyleSheet("background: #c8e6c9; color: #2e7d32; font-weight: bold; padding: 3px 6px; border-radius: 3px;")
            summary_layout.addRow(QLabel("Status:"), status_lbl)

            self.details_layout.addWidget(summary_frame)

            # Debit section
            debit_group = QGroupBox("💸 DEBIT (Cash In)")
            debit_group.setStyleSheet("""
                QGroupBox { font-weight: bold; border: 1px solid #81c784; border-radius: 5px; margin-top: 8px; padding-top: 12px; font-size: 11px; }
                QGroupBox::title { color: #2e7d32; }
            """)
            debit_form = QFormLayout(debit_group)
            debit_form.setSpacing(2)
            
            for ui_label, db_column in self.debit_fields_brand_b.items():
                value = data.get(db_column, 0) or 0
                lotes = data.get(db_column + "_lotes", 0) or 0
                if value > 0 or lotes > 0:
                    val_lbl = QLabel(f"₱ {value:,.2f}" + (f" (Lotes: {lotes})" if lotes > 0 else ""))
                    val_lbl.setStyleSheet("color: #2e7d32; font-size: 10px;")
                    lbl = QLabel(ui_label + ":")
                    lbl.setStyleSheet("font-size: 10px;")
                    debit_form.addRow(lbl, val_lbl)

            self.details_layout.addWidget(debit_group)

            # Credit section
            credit_group = QGroupBox("💳 CREDIT (Cash Out)")
            credit_group.setStyleSheet("""
                QGroupBox { font-weight: bold; border: 1px solid #e57373; border-radius: 5px; margin-top: 8px; padding-top: 12px; font-size: 11px; }
                QGroupBox::title { color: #c62828; }
            """)
            credit_form = QFormLayout(credit_group)
            credit_form.setSpacing(2)
            
            for ui_label, db_column in self.credit_fields_brand_b.items():
                value = data.get(db_column, 0) or 0
                lotes = data.get(db_column + "_lotes", 0) or 0
                if value > 0 or lotes > 0:
                    val_lbl = QLabel(f"₱ {value:,.2f}" + (f" (Lotes: {lotes})" if lotes > 0 else ""))
                    val_lbl.setStyleSheet("color: #c62828; font-size: 10px;")
                    lbl = QLabel(ui_label + ":")
                    lbl.setStyleSheet("font-size: 10px;")
                    credit_form.addRow(lbl, val_lbl)

            self.details_layout.addWidget(credit_group)
            self.details_layout.addStretch()

        except Exception as e:
            print(f"Error loading entry details: {e}")
            QMessageBox.critical(self, "Error", f"Failed to load details: {e}")
