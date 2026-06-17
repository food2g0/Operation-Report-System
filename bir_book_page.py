"""BIR Book Tab - Display all Palawan transaction details from database."""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView, QDateEdit, QMessageBox,
    QSpinBox, QFileDialog, QApplication
)
from PyQt5.QtCore import Qt, QDate
from PyQt5.QtGui import QColor, QFont
from api_db_manager import db_manager
import json
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class BIRBookPage(QWidget):
    """Tab for viewing all Palawan transactions (BIR Book compliance)."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_dashboard = parent
        self.db = db_manager
        self.branch_status_map = {}
        self.all_transactions = []  # Store all transactions for pagination
        self.current_page = 1
        self.rows_per_page = 50
        self.expanded_groups = set()  # Track which groups are expanded (date, branch)
        self._setup_ui()
        self._load_corporations()
        self._find_available_dates()  # Auto-detect latest date with data

    def _setup_ui(self):
        """Setup the user interface."""
        root = QVBoxLayout(self)
        root.setContentsMargins(12, 12, 12, 12)
        root.setSpacing(12)

        # Title
        title = QLabel("BIR Book - Palawan Transaction Details")
        title.setStyleSheet("font-size: 16px; font-weight: 800; color: #1E293B;")
        root.addWidget(title)

        # Filter section - Row 1: Corporation, Date, and Transaction Type
        filter_row1 = QHBoxLayout()
        filter_row1.setSpacing(16)

        # Corporation filter (REQUIRED - no "All" option)
        corp_label = QLabel("Corporation:")
        corp_label.setStyleSheet("font-weight: 600; color: #334155;")
        filter_row1.addWidget(corp_label)

        self.corporation_combo = QComboBox()
        self.corporation_combo.setMinimumWidth(250)
        self.corporation_combo.currentTextChanged.connect(self._on_filter_changed)
        filter_row1.addWidget(self.corporation_combo)

        filter_row1.addSpacing(32)

        # Date filter
        date_label = QLabel("Date:")
        date_label.setStyleSheet("font-weight: 600; color: #334155;")
        filter_row1.addWidget(date_label)

        self.date_picker = QDateEdit()
        # Set to today's date (use QDate explicitly)
        today = QDate.currentDate()
        self.date_picker.setDate(today)
        self.date_picker.setCalendarPopup(True)
        # Allow selecting any date (past or future)
        self.date_picker.setDateRange(QDate(2020, 1, 1), QDate(2099, 12, 31))
        self.date_picker.dateChanged.connect(self._on_filter_changed)
        filter_row1.addWidget(self.date_picker)

        filter_row1.addStretch()

        load_btn = QPushButton("Load Report")
        load_btn.setStyleSheet("""
            QPushButton {
                background: #0EA5E9; color: white; border: none;
                border-radius: 5px; padding: 6px 16px;
                font-weight: 700;
            }
            QPushButton:hover { background: #0284C7; }
        """)
        load_btn.clicked.connect(self._load_transactions)
        filter_row1.addWidget(load_btn)

        monthly_report_btn = QPushButton("Generate Monthly Report")
        monthly_report_btn.setStyleSheet("""
            QPushButton {
                background: #F59E0B; color: white; border: none;
                border-radius: 5px; padding: 6px 16px;
                font-weight: 700;
            }
            QPushButton:hover { background: #D97706; }
        """)
        monthly_report_btn.clicked.connect(self._generate_monthly_report)
        filter_row1.addWidget(monthly_report_btn)

        export_btn = QPushButton("Export to Excel")
        export_btn.setStyleSheet("""
            QPushButton {
                background: #10B981; color: white; border: none;
                border-radius: 5px; padding: 6px 16px;
                font-weight: 700;
            }
            QPushButton:hover { background: #059669; }
        """)
        export_btn.clicked.connect(self._export_to_excel)
        filter_row1.addWidget(export_btn)

        filter_row1.addSpacing(20)

        # Transaction Type toggle
        txn_type_label = QLabel("Transaction Type:")
        txn_type_label.setStyleSheet("font-weight: 600; color: #334155;")
        filter_row1.addWidget(txn_type_label)

        self.txn_type_combo = QComboBox()
        self.txn_type_combo.setMinimumWidth(150)
        self.txn_type_combo.addItem("Send-Out (Sendout)", "sendout")
        self.txn_type_combo.addItem("Pay-Out (Payout)", "payout")
        self.txn_type_combo.currentIndexChanged.connect(self._on_filter_changed)
        filter_row1.addWidget(self.txn_type_combo)

        root.addLayout(filter_row1)

        # Info label
        self.info_label = QLabel("")
        self.info_label.setStyleSheet("font-size: 11px; color: #64748B;")
        root.addWidget(self.info_label)

        # Transactions table
        self.table = QTableWidget()
        self.table.setColumnCount(18)
        self.table.setHorizontalHeaderLabels([
            "Date", "Branch", "Code", "Receiver", "Sender", "Principal",
            "Commission", "SC", "Total SC", "Income (43%)", "A/R Palawan",
            "KYC Docs", "Business Name", "Relationship", "Source Funds", "Purpose", "Evaluation", ""
        ])

        hh = self.table.horizontalHeader()
        hh.setSectionResizeMode(QHeaderView.Stretch)
        # Fix last column to have more width for button
        hh.setSectionResizeMode(17, QHeaderView.ResizeToContents)
        self.table.setSelectionMode(QAbstractItemView.NoSelection)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.setStyleSheet("""
            QTableWidget {
                border: 1px solid #E2E8F0;
                border-radius: 6px;
                gridline-color: #E2E8F0;
            }
            QHeaderView::section {
                background: #F1F5F9;
                font-weight: 700;
                font-size: 11px;
                padding: 8px;
                border: 1px solid #CBD5E1;
            }
            QTableWidget::item {
                padding: 6px 8px;
            }
        """)

        root.addWidget(self.table)

        # Pagination controls
        pagination_row = QHBoxLayout()
        pagination_row.setSpacing(12)

        prev_btn = QPushButton("◀ Previous")
        prev_btn.setMaximumWidth(100)
        prev_btn.setStyleSheet("""
            QPushButton {
                background: #94A3B8; color: white; border: none;
                border-radius: 4px; padding: 5px 12px;
                font-weight: 600;
            }
            QPushButton:hover { background: #78909C; }
        """)
        prev_btn.clicked.connect(self._prev_page)
        pagination_row.addWidget(prev_btn)

        self.page_info = QLabel("Page 1")
        self.page_info.setStyleSheet("font-weight: 600; color: #334155;")
        pagination_row.addWidget(self.page_info)

        next_btn = QPushButton("Next ▶")
        next_btn.setMaximumWidth(100)
        next_btn.setStyleSheet("""
            QPushButton {
                background: #94A3B8; color: white; border: none;
                border-radius: 4px; padding: 5px 12px;
                font-weight: 600;
            }
            QPushButton:hover { background: #78909C; }
        """)
        next_btn.clicked.connect(self._next_page)
        pagination_row.addWidget(next_btn)

        pagination_row.addSpacing(20)

        rows_label = QLabel("Rows per page:")
        rows_label.setStyleSheet("font-weight: 600; color: #334155;")
        pagination_row.addWidget(rows_label)

        self.rows_spinner = QSpinBox()
        self.rows_spinner.setValue(50)
        self.rows_spinner.setMinimum(10)
        self.rows_spinner.setMaximum(500)
        self.rows_spinner.setSingleStep(10)
        self.rows_spinner.setMaximumWidth(80)
        self.rows_spinner.valueChanged.connect(self._on_rows_per_page_changed)
        pagination_row.addWidget(self.rows_spinner)

        pagination_row.addStretch()
        root.addLayout(pagination_row)

    def _find_available_dates(self):
        """Find the most recent date with data in the database (not exceeding today)."""
        try:
            result = self.db.execute_query(
                "SELECT DISTINCT DATE(date) as report_date FROM payable_tbl_brand_a ORDER BY DATE(date) DESC LIMIT 1"
            )

            if result:
                date_str = result[0].get("report_date")
                if date_str:
                    logger.info(f"[BIRBookPage] Found latest data date: {date_str}")
                    # Parse the date and set it
                    parts = str(date_str).split('-')
                    if len(parts) == 3:
                        year, month, day = int(parts[0]), int(parts[1]), int(parts[2])
                        latest_date = QDate(year, month, day)

                        # Only use the date if it's not in the future
                        today = QDate.currentDate()
                        if latest_date <= today:
                            self.date_picker.blockSignals(True)
                            self.date_picker.setDate(latest_date)
                            self.date_picker.blockSignals(False)
                            return True
                        else:
                            logger.warning(f"[BIRBookPage] Latest date {date_str} is in future, using today instead")
                            return False
            return False
        except Exception as e:
            logger.error("[BIRBookPage] Find available dates error: %s", e)
            return False

    def _load_corporations(self):
        """Load list of corporations into filter (no 'All' option to prevent app crash)."""
        try:
            self.corporation_combo.blockSignals(True)
            self.corporation_combo.clear()

            result = self.db.execute_query(
                "SELECT DISTINCT corporation FROM payable_tbl_brand_a WHERE corporation IS NOT NULL AND corporation != '' ORDER BY corporation"
            )

            if result:
                for row in result:
                    corp = row.get("corporation", "")
                    if corp:
                        self.corporation_combo.addItem(corp, corp)
                logger.info(f"[BIRBookPage] Loaded {len(result)} corporations")
                if self.corporation_combo.count() > 0:
                    self.corporation_combo.setCurrentIndex(0)
            else:
                logger.warning("[BIRBookPage] No corporations found in database")
                QMessageBox.warning(self, "No Data", "No corporations found in the database.")

            self.corporation_combo.blockSignals(False)
        except Exception as e:
            logger.error("[BIRBookPage] Load corporations error: %s", e)
            QMessageBox.warning(self, "Error", f"Failed to load corporations: {str(e)}")

    def _on_filter_changed(self):
        """Handle filter changes."""
        self.current_page = 1
        self._load_transactions()

    def _load_transactions(self):
        """Load all transactions and display current page."""
        try:
            self.table.setRowCount(0)
            self.info_label.setText("Loading transactions...")

            selected_corp = self.corporation_combo.currentData()
            selected_date = self.date_picker.date().toString("yyyy-MM-dd")

            if not selected_corp:
                self.info_label.setText("❌ Please select a corporation")
                logger.warning("[BIRBookPage] No corporation selected")
                return

            logger.info(f"[BIRBookPage] Loading transactions - Corp: {selected_corp}, Date: {selected_date}")

            # Query all payable records for the selected corporation and date
            query = """
                SELECT date, branch, corporation,
                       sendout_detailed_principal, sendout_detailed_sc, sendout_detailed_commission,
                       payout_detailed_principal, payout_detailed_sc, payout_detailed_commission,
                       international_detailed_principal, international_detailed_sc, international_detailed_commission
                FROM payable_tbl_brand_a
                WHERE corporation = %s AND date = %s
                ORDER BY branch
            """
            result = self.db.execute_query(query, (selected_corp, selected_date))

            if not result:
                self.all_transactions = []
                self.info_label.setText(f"No records found for {selected_date} | Corporation: {selected_corp}")
                logger.info("[BIRBookPage] No records found")
                return

            logger.info(f"[BIRBookPage] Found {len(result)} total records for date {selected_date}")

            # Collect all transactions into a flat list
            self.all_transactions = []

            for record in result:
                date = record.get("date", "")
                branch = record.get("branch", "")

                # Process all three sections (sendout, payout, international)
                sections = [
                    ("sendout", "Sendout"),
                    ("payout", "Payout"),
                    ("international", "International")
                ]

                for section_key, section_name in sections:
                    for field_type in ("principal", "sc", "commission"):
                        col_name = f"{section_key}_detailed_{field_type}"
                        json_str = record.get(col_name)

                        if json_str:
                            try:
                                transactions = json.loads(json_str)
                                logger.debug(f"[BIRBookPage] Parsed {len(transactions)} transactions from {col_name}")
                                for txn in transactions:
                                    txn_with_meta = {
                                        'date': date,
                                        'branch': branch,
                                        '_type': section_key,  # 'sendout', 'payout', 'international'
                                        **txn
                                    }
                                    self.all_transactions.append(txn_with_meta)
                            except (json.JSONDecodeError, TypeError) as e:
                                logger.error(f"[BIRBookPage] JSON parse error for {col_name}: {e}")

            logger.info(f"[BIRBookPage] Total transactions collected: {len(self.all_transactions)}")
            self.current_page = 1
            self._display_page()

        except Exception as e:
            logger.error("[BIRBookPage] Load transactions error: %s", e)
            self.info_label.setText(f"Error loading transactions: {str(e)}")
            QMessageBox.critical(self, "Error", f"Failed to load transactions:\n{str(e)}\n\nMake sure the database is connected and available.")

    def _display_page(self):
        """Display the current page with expandable groups and per-group totals."""
        self.table.setRowCount(0)

        if not self.all_transactions:
            self.info_label.setText("No transactions to display")
            return

        selected_corp = self.corporation_combo.currentData()
        selected_date = self.date_picker.date().toString("yyyy-MM-dd")
        selected_txn_type = self.txn_type_combo.currentData()

        # Filter transactions by type
        filtered_txns = [t for t in self.all_transactions if t.get('_type') == selected_txn_type]

        start_idx = (self.current_page - 1) * self.rows_per_page
        end_idx = start_idx + self.rows_per_page
        page_transactions = filtered_txns[start_idx:end_idx]

        total_pages = (len(filtered_txns) + self.rows_per_page - 1) // self.rows_per_page

        # Group transactions by date and branch
        groups = {}
        for txn in page_transactions:
            key = (txn.get('date'), txn.get('branch'))
            if key not in groups:
                groups[key] = []
            groups[key].append(txn)

        # Store group data for expansion
        self.group_data = {}  # Maps (row_idx) -> (date, branch, all_txns)
        row_idx = 0

        # Display only first transaction per group with expand button
        for (date, branch), txns in groups.items():
            if txns:
                # INSERT NEW ROW FIRST
                self.table.insertRow(row_idx)

                # Add first transaction with date/branch visible
                self._add_table_row(txns[0], show_date_branch=True, row_idx=row_idx)

                # Add expand button in last column if group has multiple transactions
                if len(txns) > 1:
                    expand_btn = QPushButton("▼")
                    expand_btn.setMaximumWidth(35)
                    expand_btn.setMaximumHeight(25)
                    expand_btn.setMinimumWidth(35)
                    expand_btn.setMinimumHeight(25)
                    expand_btn.setCursor(Qt.PointingHandCursor)
                    expand_btn.setStyleSheet("""
                        QPushButton {
                            background: #3B82F6; color: white;
                            border: none; border-radius: 3px;
                            padding: 0px 5px; font-weight: 600;
                            font-size: 12px;
                        }
                        QPushButton:hover { background: #2563EB; }
                    """)
                    expand_btn.clicked.connect(lambda checked, r=row_idx, d=(date, branch), t=txns:
                                               self._toggle_group_expansion(r, d, t))

                    # Create container widget to center the button
                    container = QWidget()
                    layout = QHBoxLayout(container)
                    layout.setContentsMargins(2, 2, 2, 2)
                    layout.setSpacing(0)
                    layout.addStretch()
                    layout.addWidget(expand_btn)
                    layout.addStretch()

                    self.table.setCellWidget(row_idx, 17, container)
                    self.group_data[row_idx] = (date, branch, txns[1:])  # Store hidden transactions

                row_idx += 1

        self.page_info.setText(f"Page {self.current_page} of {total_pages}")
        self.info_label.setText(
            f"✓ Showing {len([g for g in groups])} branches | "
            f"Total: {len(filtered_txns)} transactions | "
            f"Type: {self.txn_type_combo.currentText()} | "
            f"Date: {selected_date} | Corporation: {selected_corp}"
        )

    def _toggle_group_expansion(self, header_row, group_key, hidden_txns):
        """Toggle expansion of a transaction group."""
        date, branch = group_key
        group_id = (header_row, date, branch)

        if group_id in self.expanded_groups:
            # Collapse: remove hidden rows and totals
            self._collapse_group(header_row, group_id)
        else:
            # Expand: add hidden rows and totals
            self._expand_group(header_row, group_key, hidden_txns)

    def _expand_group(self, header_row, group_key, hidden_txns):
        """Expand a group to show hidden transactions and totals."""
        date, branch = group_key
        group_id = (header_row, date, branch)

        # Get all transactions in this group (including the visible one)
        all_txns = [self.table.item(header_row, col).text() if self.table.item(header_row, col) else ''
                    for col in range(18)]
        all_txns_data = hidden_txns

        # Find first transaction to get the visible one
        first_txn_code = self.table.item(header_row, 2).text()
        first_txn = None
        for t in self.all_transactions:
            if t.get('code') == first_txn_code and t.get('date') == date and t.get('branch') == branch:
                first_txn = t
                break

        insert_row = header_row + 1

        # Insert hidden transactions (NOT including first_txn, which is already shown)
        for hidden_txn in hidden_txns:
            self.table.insertRow(insert_row)
            self._add_table_row(hidden_txn, show_date_branch=False, row_idx=insert_row)
            insert_row += 1

        # Insert totals row for this group (includes first_txn + hidden_txns)
        if first_txn:
            all_group_txns = [first_txn] + hidden_txns
        else:
            all_group_txns = hidden_txns

        self.table.insertRow(insert_row)
        self._add_group_totals_row(all_group_txns, insert_row)

        # Update button to collapse
        container = self.table.cellWidget(header_row, 17)
        if container:
            button = container.findChild(QPushButton)
            if button:
                button.setText("▲")

        # Mark as expanded
        self.expanded_groups.add(group_id)

    def _collapse_group(self, header_row, group_id):
        """Collapse a group to hide transactions and totals."""
        date, branch = group_id[:2] if len(group_id) > 2 else (None, None)

        # Count rows to remove (hidden transactions + totals)
        rows_to_remove = 0
        check_row = header_row + 1

        while check_row < self.table.rowCount():
            # Check if this is an empty row (part of the group)
            first_col = self.table.item(check_row, 0)
            if first_col and first_col.text().strip() == "":
                rows_to_remove += 1
                check_row += 1
            else:
                break

        # Remove rows in reverse order
        for _ in range(rows_to_remove):
            self.table.removeRow(header_row + 1)

        # Update button to expand
        container = self.table.cellWidget(header_row, 17)
        if container:
            button = container.findChild(QPushButton)
            if button:
                button.setText("▼")

        # Mark as collapsed
        self.expanded_groups.discard(group_id)


    def _prev_page(self):
        """Go to previous page."""
        if self.current_page > 1:
            self.current_page -= 1
            self._display_page()

    def _next_page(self):
        """Go to next page."""
        total_pages = (len(self.all_transactions) + self.rows_per_page - 1) // self.rows_per_page
        if self.current_page < total_pages:
            self.current_page += 1
            self._display_page()

    def _on_rows_per_page_changed(self):
        """Handle rows per page change."""
        self.rows_per_page = self.rows_spinner.value()
        self.current_page = 1
        self._display_page()

    def _add_table_row(self, txn, show_date_branch=True, row_idx=None):
        """Add a transaction row to the table."""
        if row_idx is None:
            row_idx = self.table.rowCount()

        # Map transaction data to table columns
        data = [
            str(txn.get("date", "")) if show_date_branch else "",
            txn.get("branch", "") if show_date_branch else "",
            txn.get("code", ""),
            txn.get("receiver", ""),
            txn.get("sender", ""),
            f"{txn.get('principal', 0):.2f}",
            f"{txn.get('commission', 0):.2f}",
            f"{txn.get('sc', 0):.2f}",
            f"{txn.get('total_sc', 0):.2f}",
            f"{txn.get('income', 0):.2f}",
            f"{txn.get('ar_palawan', 0):.2f}",
            txn.get("kyc_docs", ""),
            txn.get("business_name", ""),
            txn.get("relationship", ""),
            txn.get("source_funds", ""),
            txn.get("purpose", ""),
            txn.get("evaluation", ""),
            ""
        ]

        for col, value in enumerate(data):
            item = QTableWidgetItem(str(value))
            item.setFlags(item.flags() & ~Qt.ItemIsEditable)
            # Right-align numeric columns
            if col in [5, 6, 7, 8, 9, 10]:
                item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            # Add light indentation for hidden rows (show_date_branch=False)
            if not show_date_branch and col == 2:
                item.setText("  " + item.text())
            self.table.setItem(row_idx, col, item)

    def _add_group_totals_row(self, transactions, row_idx):
        """Add a totals row for a specific branch group."""
        # Calculate totals for this group only
        total_principal = sum(float(t.get("principal", 0)) for t in transactions)
        total_commission = sum(float(t.get("commission", 0)) for t in transactions)
        total_sc = sum(float(t.get("sc", 0)) for t in transactions)
        total_total_sc = sum(float(t.get("total_sc", 0)) for t in transactions)
        total_income = sum(float(t.get("income", 0)) for t in transactions)
        total_ar = sum(float(t.get("ar_palawan", 0)) for t in transactions)

        # Style for totals row
        totals_bg = QColor("#E0E7FF")
        totals_fg = QColor("#3730A3")
        totals_font = QFont()
        totals_font.setBold(True)

        def _create_totals_item(text=""):
            """Helper to create styled totals item."""
            item = QTableWidgetItem(text)
            item.setBackground(totals_bg)
            item.setForeground(totals_fg)
            item.setFont(totals_font)
            item.setTextAlignment(Qt.AlignCenter | Qt.AlignVCenter)
            return item

        # Code column - "Totals" label
        label_item = _create_totals_item("Totals")
        label_item.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.table.setItem(row_idx, 2, label_item)

        # Empty columns before Principal
        for col in range(0, 2):
            self.table.setItem(row_idx, col, _create_totals_item())
        for col in range(3, 5):
            self.table.setItem(row_idx, col, _create_totals_item())

        # Principal (column 5)
        principal_item = _create_totals_item(f"{total_principal:,.2f}")
        principal_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.table.setItem(row_idx, 5, principal_item)

        # Commission (column 6)
        commission_item = _create_totals_item(f"{total_commission:,.2f}")
        commission_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.table.setItem(row_idx, 6, commission_item)

        # SC (column 7)
        sc_item = _create_totals_item(f"{total_sc:,.2f}")
        sc_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.table.setItem(row_idx, 7, sc_item)

        # Total SC (column 8)
        total_sc_item = _create_totals_item(f"{total_total_sc:,.2f}")
        total_sc_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.table.setItem(row_idx, 8, total_sc_item)

        # Income (column 9)
        income_item = _create_totals_item(f"{total_income:,.2f}")
        income_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.table.setItem(row_idx, 9, income_item)

        # A/R Palawan (column 10)
        ar_item = _create_totals_item(f"{total_ar:,.2f}")
        ar_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.table.setItem(row_idx, 10, ar_item)

        # Rest of columns
        for col in range(11, 18):
            self.table.setItem(row_idx, col, _create_totals_item())

    def _export_to_excel(self):
        """Export current transactions to Excel file."""
        if not self.all_transactions:
            QMessageBox.warning(self, "No Data", "No transactions to export. Load a report first.")
            return

        selected_txn_type = self.txn_type_combo.currentData()
        filtered_txns = [t for t in self.all_transactions if t.get('_type') == selected_txn_type]

        if not filtered_txns:
            QMessageBox.warning(self, "No Data", f"No {self.txn_type_combo.currentText()} transactions to export.")
            return

        try:
            import openpyxl
            from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
        except ImportError:
            QMessageBox.warning(self, "Missing Library", "openpyxl is required for Excel export. Please install it.")
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self, "Export Transactions to Excel", "",
            "Excel Files (*.xlsx);;All Files (*)"
        )

        if not file_path:
            return

        try:
            wb = openpyxl.Workbook()
            ws = wb.active
            ws.title = "BIR Book"

            # Header styling
            header_fill = PatternFill(start_color="366092", end_color="366092", fill_type="solid")
            header_font = Font(bold=True, color="FFFFFF", size=11)
            header_alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
            border = Border(
                left=Side(style='thin'),
                right=Side(style='thin'),
                top=Side(style='thin'),
                bottom=Side(style='thin')
            )

            # Columns
            columns = [
                "Date", "Branch", "Code", "Receiver", "Sender", "Principal",
                "Commission", "SC", "Total SC", "Income (43%)", "A/R Palawan",
                "KYC Docs", "Business Name", "Relationship", "Source Funds", "Purpose", "Evaluation"
            ]

            # Write headers
            for col_idx, col_name in enumerate(columns, 1):
                cell = ws.cell(row=1, column=col_idx)
                cell.value = col_name
                cell.fill = header_fill
                cell.font = header_font
                cell.alignment = header_alignment
                cell.border = border

            # Write data
            for row_idx, txn in enumerate(filtered_txns, 2):
                ws.cell(row=row_idx, column=1).value = str(txn.get("date", ""))
                ws.cell(row=row_idx, column=2).value = txn.get("branch", "")
                ws.cell(row=row_idx, column=3).value = txn.get("code", "")
                ws.cell(row=row_idx, column=4).value = txn.get("receiver", "")
                ws.cell(row=row_idx, column=5).value = txn.get("sender", "")
                ws.cell(row=row_idx, column=6).value = float(txn.get("principal", 0))
                ws.cell(row=row_idx, column=7).value = float(txn.get("commission", 0))
                ws.cell(row=row_idx, column=8).value = float(txn.get("sc", 0))
                ws.cell(row=row_idx, column=9).value = float(txn.get("total_sc", 0))
                ws.cell(row=row_idx, column=10).value = float(txn.get("income", 0))
                ws.cell(row=row_idx, column=11).value = float(txn.get("ar_palawan", 0))
                ws.cell(row=row_idx, column=12).value = txn.get("kyc_docs", "")
                ws.cell(row=row_idx, column=13).value = txn.get("business_name", "")
                ws.cell(row=row_idx, column=14).value = txn.get("relationship", "")
                ws.cell(row=row_idx, column=15).value = txn.get("source_funds", "")
                ws.cell(row=row_idx, column=16).value = txn.get("purpose", "")
                ws.cell(row=row_idx, column=17).value = txn.get("evaluation", "")

                # Apply borders and formatting
                for col in range(1, 18):
                    cell = ws.cell(row=row_idx, column=col)
                    cell.border = border
                    cell.alignment = Alignment(horizontal="left", vertical="top", wrap_text=True)
                    if col in [6, 7, 8, 9, 10, 11]:  # Number columns
                        cell.number_format = '#,##0.00'
                        cell.alignment = Alignment(horizontal="right", vertical="top")

            # Adjust column widths
            ws.column_dimensions['A'].width = 12
            ws.column_dimensions['B'].width = 15
            ws.column_dimensions['C'].width = 12
            ws.column_dimensions['D'].width = 15
            ws.column_dimensions['E'].width = 15
            ws.column_dimensions['F'].width = 12
            ws.column_dimensions['G'].width = 12
            ws.column_dimensions['H'].width = 10
            ws.column_dimensions['I'].width = 12
            ws.column_dimensions['J'].width = 12
            ws.column_dimensions['K'].width = 12
            ws.column_dimensions['L'].width = 15
            ws.column_dimensions['M'].width = 18
            ws.column_dimensions['N'].width = 15
            ws.column_dimensions['O'].width = 15
            ws.column_dimensions['P'].width = 15
            ws.column_dimensions['Q'].width = 15

            # Add summary at bottom
            summary_row = len(filtered_txns) + 3
            ws.cell(row=summary_row, column=1).value = "Summary"
            ws.cell(row=summary_row, column=1).font = Font(bold=True, size=11)

            total_principal = sum(float(txn.get("principal", 0)) for txn in filtered_txns)
            total_commission = sum(float(txn.get("commission", 0)) for txn in filtered_txns)
            total_sc = sum(float(txn.get("sc", 0)) for txn in filtered_txns)
            total_total_sc = sum(float(txn.get("total_sc", 0)) for txn in filtered_txns)
            total_income = sum(float(txn.get("income", 0)) for txn in filtered_txns)
            total_ar = sum(float(txn.get("ar_palawan", 0)) for txn in filtered_txns)

            ws.cell(row=summary_row + 1, column=5).value = "Total Principal:"
            ws.cell(row=summary_row + 1, column=6).value = total_principal
            ws.cell(row=summary_row + 1, column=6).number_format = '#,##0.00'
            ws.cell(row=summary_row + 1, column=6).font = Font(bold=True)

            ws.cell(row=summary_row + 2, column=5).value = "Total Commission:"
            ws.cell(row=summary_row + 2, column=7).value = total_commission
            ws.cell(row=summary_row + 2, column=7).number_format = '#,##0.00'
            ws.cell(row=summary_row + 2, column=7).font = Font(bold=True)

            ws.cell(row=summary_row + 3, column=5).value = "Total SC:"
            ws.cell(row=summary_row + 3, column=8).value = total_sc
            ws.cell(row=summary_row + 3, column=8).number_format = '#,##0.00'
            ws.cell(row=summary_row + 3, column=8).font = Font(bold=True)

            ws.cell(row=summary_row + 4, column=5).value = "Total A/R Palawan:"
            ws.cell(row=summary_row + 4, column=11).value = total_ar
            ws.cell(row=summary_row + 4, column=11).number_format = '#,##0.00'
            ws.cell(row=summary_row + 4, column=11).font = Font(bold=True)

            wb.save(file_path)
            QMessageBox.information(
                self, "Export Successful",
                f"✓ Exported {len(filtered_txns)} {self.txn_type_combo.currentText()} transactions to:\n{file_path}"
            )
            logger.info(f"[BIRBookPage] Exported {len(filtered_txns)} transactions to {file_path}")

        except Exception as e:
            logger.error(f"[BIRBookPage] Export error: {e}")
            QMessageBox.critical(self, "Export Error", f"Failed to export to Excel:\n{str(e)}")

    def _generate_monthly_report(self):
        """Generate monthly Excel report with separate sheets per branch."""
        selected_corp = self.corporation_combo.currentData()
        if not selected_corp:
            QMessageBox.warning(self, "No Selection", "Please select a corporation first.")
            return

        selected_date = self.date_picker.date()
        year = selected_date.year()
        month = selected_date.month()

        try:
            import openpyxl
            from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
        except ImportError:
            QMessageBox.warning(self, "Missing Library", "openpyxl is required. Please install it.")
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self, "Save Monthly Report",
            f"BIR_Book_{selected_corp}_{year}-{month:02d}.xlsx",
            "Excel Files (*.xlsx);;All Files (*)"
        )

        if not file_path:
            return

        try:
            self.info_label.setText("⏳ Generating monthly report...")

            # Query all transactions for the selected month and corporation
            query = """
                SELECT date, branch, corporation,
                       sendout_detailed_principal, sendout_detailed_sc, sendout_detailed_commission,
                       payout_detailed_principal, payout_detailed_sc, payout_detailed_commission,
                       international_detailed_principal, international_detailed_sc, international_detailed_commission
                FROM payable_tbl_brand_a
                WHERE corporation = %s
                AND YEAR(date) = %s
                AND MONTH(date) = %s
                ORDER BY date, branch
            """

            result = self.db.execute_query(query, (selected_corp, year, month))

            if not result:
                QMessageBox.warning(self, "No Data", f"No transactions found for {selected_corp} in {year}-{month:02d}")
                self.info_label.setText("No data for selected period")
                return

            # Collect all transactions
            all_txns = []
            for record in result:
                date = record.get("date", "")
                branch = record.get("branch", "")

                sections = [("sendout", "Sendout"), ("payout", "Payout"), ("international", "International")]

                for section_key, _ in sections:
                    for field_type in ("principal", "sc", "commission"):
                        col_name = f"{section_key}_detailed_{field_type}"
                        json_str = record.get(col_name)

                        if json_str:
                            try:
                                transactions = json.loads(json_str)
                                for txn in transactions:
                                    txn_with_meta = {
                                        'date': date,
                                        'branch': branch,
                                        '_type': section_key,
                                        **txn
                                    }
                                    all_txns.append(txn_with_meta)
                            except (json.JSONDecodeError, TypeError) as e:
                                logger.error(f"JSON parse error: {e}")

            if not all_txns:
                QMessageBox.warning(self, "No Data", "No detailed transactions found for this period.")
                self.info_label.setText("No detailed transactions")
                return

            # Create Excel workbook with separate sheets per branch
            wb = openpyxl.Workbook()
            wb.remove(wb.active)

            header_fill = PatternFill(start_color="366092", end_color="366092", fill_type="solid")
            header_font = Font(bold=True, color="FFFFFF", size=11)
            header_alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
            border = Border(
                left=Side(style='thin'),
                right=Side(style='thin'),
                top=Side(style='thin'),
                bottom=Side(style='thin')
            )
            totals_fill = PatternFill(start_color="E0E7FF", end_color="E0E7FF", fill_type="solid")
            totals_font = Font(bold=True, color="3730A3")

            columns = [
                "Date", "Branch", "Code", "Receiver", "Sender", "Principal",
                "Commission", "SC", "Total SC", "Income (43%)", "A/R Palawan",
                "KYC Docs", "Business Name", "Relationship", "Source Funds", "Purpose", "Evaluation"
            ]

            # Group by branch
            branches = {}
            for txn in all_txns:
                branch = txn.get('branch', 'Unknown')
                if branch not in branches:
                    branches[branch] = []
                branches[branch].append(txn)

            # Create sheet per branch
            for branch_name, branch_txns in sorted(branches.items()):
                ws = wb.create_sheet(title=branch_name[:31])

                # Headers
                for col_idx, col_name in enumerate(columns, 1):
                    cell = ws.cell(row=1, column=col_idx)
                    cell.value = col_name
                    cell.fill = header_fill
                    cell.font = header_font
                    cell.alignment = header_alignment
                    cell.border = border

                # Data rows
                for row_idx, txn in enumerate(branch_txns, 2):
                    ws.cell(row=row_idx, column=1).value = str(txn.get("date", ""))
                    ws.cell(row=row_idx, column=2).value = txn.get("branch", "")
                    ws.cell(row=row_idx, column=3).value = txn.get("code", "")
                    ws.cell(row=row_idx, column=4).value = txn.get("receiver", "")
                    ws.cell(row=row_idx, column=5).value = txn.get("sender", "")
                    ws.cell(row=row_idx, column=6).value = float(txn.get("principal", 0))
                    ws.cell(row=row_idx, column=7).value = float(txn.get("commission", 0))
                    ws.cell(row=row_idx, column=8).value = float(txn.get("sc", 0))
                    ws.cell(row=row_idx, column=9).value = float(txn.get("total_sc", 0))
                    ws.cell(row=row_idx, column=10).value = float(txn.get("income", 0))
                    ws.cell(row=row_idx, column=11).value = float(txn.get("ar_palawan", 0))
                    ws.cell(row=row_idx, column=12).value = txn.get("kyc_docs", "")
                    ws.cell(row=row_idx, column=13).value = txn.get("business_name", "")
                    ws.cell(row=row_idx, column=14).value = txn.get("relationship", "")
                    ws.cell(row=row_idx, column=15).value = txn.get("source_funds", "")
                    ws.cell(row=row_idx, column=16).value = txn.get("purpose", "")
                    ws.cell(row=row_idx, column=17).value = txn.get("evaluation", "")

                    # Format
                    for col in range(1, 18):
                        cell = ws.cell(row=row_idx, column=col)
                        cell.border = border
                        cell.alignment = Alignment(horizontal="left", vertical="top", wrap_text=True)
                        if col in [6, 7, 8, 9, 10, 11]:
                            cell.number_format = '#,##0.00'
                            cell.alignment = Alignment(horizontal="right", vertical="top")

                # Branch totals
                totals_row = len(branch_txns) + 2
                ws.cell(row=totals_row, column=3).value = "BRANCH TOTAL"
                ws.cell(row=totals_row, column=3).fill = totals_fill
                ws.cell(row=totals_row, column=3).font = totals_font

                for col in range(1, 18):
                    cell = ws.cell(row=totals_row, column=col)
                    cell.fill = totals_fill
                    cell.font = totals_font
                    cell.border = border

                total_principal = sum(float(t.get("principal", 0)) for t in branch_txns)
                total_commission = sum(float(t.get("commission", 0)) for t in branch_txns)
                total_sc = sum(float(t.get("sc", 0)) for t in branch_txns)
                total_total_sc = sum(float(t.get("total_sc", 0)) for t in branch_txns)
                total_income = sum(float(t.get("income", 0)) for t in branch_txns)
                total_ar = sum(float(t.get("ar_palawan", 0)) for t in branch_txns)

                ws.cell(row=totals_row, column=6).value = total_principal
                ws.cell(row=totals_row, column=6).number_format = '#,##0.00'
                ws.cell(row=totals_row, column=7).value = total_commission
                ws.cell(row=totals_row, column=7).number_format = '#,##0.00'
                ws.cell(row=totals_row, column=8).value = total_sc
                ws.cell(row=totals_row, column=8).number_format = '#,##0.00'
                ws.cell(row=totals_row, column=9).value = total_total_sc
                ws.cell(row=totals_row, column=9).number_format = '#,##0.00'
                ws.cell(row=totals_row, column=10).value = total_income
                ws.cell(row=totals_row, column=10).number_format = '#,##0.00'
                ws.cell(row=totals_row, column=11).value = total_ar
                ws.cell(row=totals_row, column=11).number_format = '#,##0.00'

                # Column widths
                for col, width in [('A', 12), ('B', 15), ('C', 12), ('D', 15), ('E', 15), ('F', 12), ('G', 12), ('H', 10), ('I', 12), ('J', 12), ('K', 12), ('L', 15), ('M', 18), ('N', 15), ('O', 15), ('P', 15), ('Q', 15)]:
                    ws.column_dimensions[col].width = width

            wb.save(file_path)
            QMessageBox.information(self, "Report Generated", f"✓ Monthly report saved:\n{file_path}")
            self.info_label.setText(f"✓ Report generated for {year}-{month:02d} ({len(branches)} branches)")
            logger.info(f"[BIRBookPage] Generated monthly report for {selected_corp} {year}-{month:02d}")

        except Exception as e:
            logger.error(f"[BIRBookPage] Monthly report error: {e}")
            QMessageBox.critical(self, "Error", f"Failed to generate report:\n{str(e)}")
            self.info_label.setText("Report generation failed")

    def refresh(self):
        """Refresh data (called when tab is shown)."""
        self._load_corporations()
