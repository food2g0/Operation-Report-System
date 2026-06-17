"""BIR Book Tab - Display all Palawan transaction details from database."""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView, QDateEdit, QMessageBox,
    QSpinBox, QFileDialog
)
from PyQt5.QtCore import Qt, QDate
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
        self.date_picker.setDate(QDate.currentDate())
        self.date_picker.setCalendarPopup(True)
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
        """Find the most recent date with data in the database."""
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
                        from PyQt5.QtCore import QDate
                        latest_date = QDate(year, month, day)
                        self.date_picker.blockSignals(True)
                        self.date_picker.setDate(latest_date)
                        self.date_picker.blockSignals(False)
                        return True
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
        """Display the current page with grouped and collapsible rows."""
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

        # Display grouped transactions
        row_idx = 0
        self.group_rows = {}  # Track which rows are group headers

        for (date, branch), txns in groups.items():
            # First transaction shows date and branch
            if txns:
                self._add_table_row(txns[0], show_date_branch=True)
                self.group_rows[row_idx] = (date, branch, txns)
                row_idx += 1

                # Additional transactions don't show date/branch
                if len(txns) > 1:
                    # Add expandable "Show X more" row
                    self.table.insertRow(row_idx)
                    expand_item = QTableWidgetItem(f"+ Show {len(txns) - 1} more transaction{'s' if len(txns) - 1 > 1 else ''}")
                    expand_item.setStyleSheet("color: #0284C7; font-weight: 600;")
                    self.table.setItem(row_idx, 0, expand_item)
                    self.group_rows[row_idx] = ('expand', (date, branch, txns[1:]))
                    row_idx += 1

        # Add totals row
        self._add_totals_row(filtered_txns, row_idx)
        row_idx += 1

        self.page_info.setText(f"Page {self.current_page} of {total_pages}")
        self.info_label.setText(
            f"✓ Showing {len(page_transactions)} transactions | "
            f"Total: {len(filtered_txns)} | "
            f"Type: {self.txn_type_combo.currentText()} | "
            f"Date: {selected_date} | Corporation: {selected_corp}"
        )

    def _add_totals_row(self, transactions, row_idx):
        """Add a totals row at the bottom of the table."""
        self.table.insertRow(row_idx)

        # Calculate totals
        total_principal = sum(float(t.get("principal", 0)) for t in transactions)
        total_commission = sum(float(t.get("commission", 0)) for t in transactions)
        total_sc = sum(float(t.get("sc", 0)) for t in transactions)
        total_total_sc = sum(float(t.get("total_sc", 0)) for t in transactions)
        total_income = sum(float(t.get("income", 0)) for t in transactions)
        total_ar = sum(float(t.get("ar_palawan", 0)) for t in transactions)

        # Style for totals row
        totals_style = "background-color: #F1F5F9; font-weight: 700; color: #0F172A;"

        # Date column - TOTALS label
        label_item = QTableWidgetItem("TOTALS")
        label_item.setStyleSheet(totals_style)
        self.table.setItem(row_idx, 0, label_item)

        # Other columns until Principal
        for col in range(1, 5):
            item = QTableWidgetItem("")
            item.setStyleSheet(totals_style)
            self.table.setItem(row_idx, col, item)

        # Principal (column 5)
        principal_item = QTableWidgetItem(f"{total_principal:,.2f}")
        principal_item.setStyleSheet(totals_style)
        principal_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.table.setItem(row_idx, 5, principal_item)

        # Commission (column 6)
        commission_item = QTableWidgetItem(f"{total_commission:,.2f}")
        commission_item.setStyleSheet(totals_style)
        commission_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.table.setItem(row_idx, 6, commission_item)

        # SC (column 7)
        sc_item = QTableWidgetItem(f"{total_sc:,.2f}")
        sc_item.setStyleSheet(totals_style)
        sc_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.table.setItem(row_idx, 7, sc_item)

        # Total SC (column 8)
        total_sc_item = QTableWidgetItem(f"{total_total_sc:,.2f}")
        total_sc_item.setStyleSheet(totals_style)
        total_sc_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.table.setItem(row_idx, 8, total_sc_item)

        # Income (column 9)
        income_item = QTableWidgetItem(f"{total_income:,.2f}")
        income_item.setStyleSheet(totals_style)
        income_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.table.setItem(row_idx, 9, income_item)

        # A/R Palawan (column 10)
        ar_item = QTableWidgetItem(f"{total_ar:,.2f}")
        ar_item.setStyleSheet(totals_style)
        ar_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.table.setItem(row_idx, 10, ar_item)

        # Rest of columns
        for col in range(11, 18):
            item = QTableWidgetItem("")
            item.setStyleSheet(totals_style)
            self.table.setItem(row_idx, col, item)

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

    def _add_table_row(self, txn, show_date_branch=True):
        """Add a transaction row to the table."""
        row = self.table.rowCount()
        self.table.insertRow(row)

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
            self.table.setItem(row, col, item)

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

    def refresh(self):
        """Refresh data (called when tab is shown)."""
        self._load_corporations()
