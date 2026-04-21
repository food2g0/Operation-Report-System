from PyQt5.QtWidgets import (
    QWidget, QLabel, QVBoxLayout, QComboBox, QTableWidget, QTableWidgetItem,
    QDateEdit, QMessageBox, QHeaderView, QSizePolicy, QPushButton, QHBoxLayout
)
from PyQt5.QtCore import Qt, QDate
from PyQt5.QtGui import QFont, QColor, QBrush, QTextDocument
from PyQt5.QtPrintSupport import QPrinter, QPrintDialog
from db_connect_pooled import db_manager
from db_worker import run_query_async
from date_range_widget import DateRangeWidget
import datetime
from docx import Document


class PalawanPage(QWidget):
    def __init__(self, account_type=2):
        super().__init__()
        self.account_type = account_type
        # Set correct table based on brand: Brand A -> daily_reports_brand_a, Brand B -> daily_reports
        self.daily_table = "daily_reports_brand_a" if account_type == 1 else "daily_reports"
        self.setWindowTitle("Palawan Transactions")
        self.resize(900, 600)

        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

        # Filter Type Selection (Corporation or OS)
        filter_type_layout = QHBoxLayout()
        self.filter_type_label = QLabel("Filter By:")
        filter_type_layout.addWidget(self.filter_type_label)
        self.filter_type_selector = QComboBox()
        self.filter_type_selector.addItem("Corporation", "corporation")
        self.filter_type_selector.addItem("Group", "group")
        self.filter_type_selector.currentIndexChanged.connect(self.on_filter_type_changed)
        filter_type_layout.addWidget(self.filter_type_selector)
        filter_type_layout.addStretch()
        self.layout.addLayout(filter_type_layout)

        # Corporation selector
        self.corp_label = QLabel("Select Corporation:")
        self.corp_selector = QComboBox()
        self.corp_selector.currentTextChanged.connect(self.populate_table)

        # OS selector (hidden by default)
        self.os_label = QLabel("Select Group:")
        self.os_selector = QComboBox()
        self.os_selector.currentTextChanged.connect(self.populate_table)
        self.os_label.setVisible(False)
        self.os_selector.setVisible(False)

        # Date selector
        self.date_range_widget = DateRangeWidget()
        self.date_range_widget.dateRangeChanged.connect(self.populate_table)
        self.date_selector = self.date_range_widget  # backward-compat

        # Registration status filter
        self.reg_filter_selector = QComboBox()
        self.reg_filter_selector.addItem("Registered Only", "registered")
        self.reg_filter_selector.addItem("Not Registered", "not_registered")
        self.reg_filter_selector.addItem("All Branches", "all")
        self.reg_filter_selector.currentIndexChanged.connect(self.populate_table)

        # Add selectors to layout
        self.layout.addWidget(self.corp_label)
        self.layout.addWidget(self.corp_selector)
        self.layout.addWidget(self.os_label)
        self.layout.addWidget(self.os_selector)
        self.layout.addWidget(QLabel("Select Date:"))
        self.layout.addWidget(self.date_range_widget)
        self.layout.addWidget(QLabel("Branch Status:"))
        self.layout.addWidget(self.reg_filter_selector)

        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(["Branch", "Palawan In", "Lotes In", "Palawan Out", "Lotes Out", "Total"])
        self.table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        header = self.table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Stretch)
        header.setStretchLastSection(True)

        self.layout.addWidget(self.table)

        # Export & Print Buttons
        self.export_button = QPushButton("Export to Excel")
        self.export_button.clicked.connect(self.export_to_excel)

        self.print_button = QPushButton("Print")
        self.print_button.clicked.connect(self.print_table)

        button_layout = QHBoxLayout()
        button_layout.addWidget(self.export_button)
        button_layout.addWidget(self.print_button)
        self.layout.addLayout(button_layout)

        self.load_corporations()
        self.load_os_options()

        # Brand A: filter by Group only, hide Corporation option
        if self.account_type == 1:
            self.filter_type_selector.setCurrentIndex(1)  # "Group"
            self.filter_type_selector.setVisible(False)
            self.filter_type_label.setVisible(False)
            self.corp_label.setVisible(False)
            self.corp_selector.setVisible(False)
            self.os_label.setVisible(True)
            self.os_selector.setVisible(True)

    def on_filter_type_changed(self, index):
        """Toggle between Corporation and OS filtering"""
        filter_type = self.filter_type_selector.currentData()
        
        if filter_type == "corporation":
            self.corp_label.setVisible(True)
            self.corp_selector.setVisible(True)
            self.os_label.setVisible(False)
            self.os_selector.setVisible(False)
        else:  # OS
            self.corp_label.setVisible(False)
            self.corp_selector.setVisible(False)
            self.os_label.setVisible(True)
            self.os_selector.setVisible(True)
        
        self.populate_table()

    def load_corporations(self):
        """Load unique corporations from the daily reports table"""
        self.corp_selector.clear()
        try:
            # Get distinct corporations from appropriate table
            query = f"SELECT DISTINCT corporation FROM {self.daily_table} ORDER BY corporation"
            corporations = db_manager.execute_query(query)

            self.corp_selector.blockSignals(True)
            for corp in corporations:
                self.corp_selector.addItem(corp['corporation'])
            self.corp_selector.blockSignals(False)

        except Exception as e:
            self.corp_selector.blockSignals(False)
            QMessageBox.critical(self, "Database Error", f"Error loading corporations: {str(e)}")

    def load_os_options(self):
        """Load OS names from branches table"""
        self.os_selector.clear()
        try:
            query = """
                SELECT DISTINCT os_name FROM branches 
                WHERE os_name IS NOT NULL AND os_name != '' 
                ORDER BY os_name
            """
            results = db_manager.execute_query(query)
            
            self.os_selector.blockSignals(True)
            for row in results:
                if row['os_name']:
                    self.os_selector.addItem(row['os_name'])
            self.os_selector.blockSignals(False)
            
        except Exception as e:
            self.os_selector.blockSignals(False)
            print(f"Error loading OS options: {e}")

    def populate_table(self):
        """Populate table with Palawan transaction data from daily_reports - shows ALL branches in group/corp"""
        filter_type = self.filter_type_selector.currentData()
        date_start, date_end = self.date_range_widget.get_date_range()
        is_range = self.date_range_widget.is_range_mode()
        reg_filter = self.reg_filter_selector.currentData()
        
        # Determine filter value based on filter type
        if filter_type == "corporation":
            filter_value = self.corp_selector.currentText()
            if not filter_value:
                return
        else:  # OS
            filter_value = self.os_selector.currentText()
            if not filter_value:
                return

        try:
            # Build date clause
            if is_range:
                date_clause = "dr.date >= %s AND dr.date <= %s"
                date_params = [date_start, date_end]
                agg_prefix = "SUM("
                agg_suffix = ")"
                group_by = " GROUP BY b.name"
            else:
                date_clause = "dr.date = %s"
                date_params = [date_start]
                agg_prefix = ""
                agg_suffix = ""
                group_by = ""

            # Build query based on filter type and registration filter
            select_cols = f"""
                SELECT b.name as branch, 
                       {agg_prefix}COALESCE(dr.palawan_send_out, 0){agg_suffix}   as palawan_send_out, 
                       {agg_prefix}COALESCE(dr.palawan_sc, 0){agg_suffix}         as palawan_sc, 
                       {agg_prefix}COALESCE(dr.palawan_pay_out, 0){agg_suffix}    as palawan_pay_out, 
                       {agg_prefix}COALESCE(dr.palawan_pay_out_incentives, 0){agg_suffix} as palawan_pay_out_incentives,
                       {agg_prefix}COALESCE(dr.palawan_send_out_lotes, 0){agg_suffix}   as palawan_send_out_lotes,
                       {agg_prefix}COALESCE(dr.palawan_sc_lotes, 0){agg_suffix}         as palawan_sc_lotes,
                       {agg_prefix}COALESCE(dr.palawan_pay_out_lotes, 0){agg_suffix}    as palawan_pay_out_lotes,
                       {agg_prefix}COALESCE(dr.palawan_pay_out_incentives_lotes, 0){agg_suffix} as palawan_pay_out_incentives_lotes
            """

            if filter_type == "corporation":
                # Get registration filter clause
                if reg_filter == "registered":
                    reg_clause = "AND b.is_registered = 1"
                elif reg_filter == "not_registered":
                    reg_clause = "AND b.is_registered = 0"
                else:
                    reg_clause = ""
                
                # Use LEFT JOIN to show all branches, including those without entries
                query = f"""
                    {select_cols}
                    FROM branches b
                    LEFT JOIN corporations c ON (b.corporation_id = c.id OR b.sub_corporation_id = c.id)
                    LEFT JOIN {self.daily_table} dr ON b.name COLLATE utf8mb4_general_ci = dr.branch COLLATE utf8mb4_general_ci
                        AND dr.corporation = %s 
                        AND {date_clause}
                    WHERE (b.corporation_id = (SELECT id FROM corporations WHERE name = %s)
                           OR b.sub_corporation_id = (SELECT id FROM corporations WHERE name = %s))
                    {reg_clause}
                    {group_by}
                    ORDER BY b.name
                """
                params = date_params + [filter_value, filter_value, filter_value]
            else:
                # Filter by OS - show all branches in the OS group
                if reg_filter == "registered":
                    reg_clause = "AND b.is_registered = 1"
                elif reg_filter == "not_registered":
                    reg_clause = "AND b.is_registered = 0"
                else:
                    reg_clause = ""
                
                # Use LEFT JOIN to show all branches in the group
                query = f"""
                    {select_cols}
                    FROM branches b
                    LEFT JOIN {self.daily_table} dr ON b.name COLLATE utf8mb4_general_ci = dr.branch COLLATE utf8mb4_general_ci
                        AND dr.date >= %s AND dr.date <= %s
                    WHERE b.os_name = %s
                    {reg_clause}
                    {group_by}
                    ORDER BY b.name
                """
                params = [date_start, date_end, filter_value]

            run_query_async(
                parent=self,
                query=query,
                params=tuple(params),
                on_result=self._on_populate_result,
                on_error=self._on_populate_error,
                loading_message="\u23f3  Loading palawan data\u2026",
            )

        except Exception as e:
            QMessageBox.critical(self, "Database Error", f"Error loading data: {str(e)}")

    def _on_populate_error(self, err):
        QMessageBox.critical(self, "Database Error", f"Error loading data: {err}")

    def _on_populate_result(self, results):
        self.table.setRowCount(0)

        if not results:
            return

        total_in = 0.0
        total_out = 0.0
        total_lotes_in = 0
        total_lotes_out = 0
        row_count = 0

        for row_data in results:
            branch_name = row_data['branch']
            palawan_send_out = float(row_data['palawan_send_out'] or 0)
            palawan_sc = float(row_data['palawan_sc'] or 0)
            palawan_pay_out = float(row_data['palawan_pay_out'] or 0)
            palawan_incentives = float(row_data['palawan_pay_out_incentives'] or 0)
            palawan_send_out_lotes = int(row_data.get('palawan_send_out_lotes') or 0)
            palawan_sc_lotes = int(row_data.get('palawan_sc_lotes') or 0)
            palawan_pay_out_lotes = int(row_data.get('palawan_pay_out_lotes') or 0)
            palawan_incentives_lotes = int(row_data.get('palawan_pay_out_incentives_lotes') or 0)

            # Calculate Palawan In and Out
            palawan_in = palawan_send_out + palawan_sc
            palawan_out = palawan_pay_out + palawan_incentives
            lotes_in = palawan_send_out_lotes + palawan_sc_lotes
            lotes_out = palawan_pay_out_lotes + palawan_incentives_lotes
            total = palawan_in + palawan_out

            # Add row to table
            self.table.insertRow(row_count)
            self.table.setItem(row_count, 0, QTableWidgetItem(branch_name))
            self.table.setItem(row_count, 1, QTableWidgetItem(f"{palawan_in:.2f}"))
            self.table.setItem(row_count, 2, QTableWidgetItem(str(lotes_in)))
            self.table.setItem(row_count, 3, QTableWidgetItem(f"{palawan_out:.2f}"))
            self.table.setItem(row_count, 4, QTableWidgetItem(str(lotes_out)))
            self.table.setItem(row_count, 5, QTableWidgetItem(f"{total:.2f}"))

            total_in += palawan_in
            total_out += palawan_out
            total_lotes_in += lotes_in
            total_lotes_out += lotes_out
            row_count += 1

        # Add totals row
        self.table.insertRow(row_count)
        total_font = QFont()
        total_font.setBold(True)

        total_brush = QBrush(QColor("#f0f0f0"))

        items = [
            QTableWidgetItem("TOTAL"),
            QTableWidgetItem(f"{total_in:.2f}"),
            QTableWidgetItem(str(total_lotes_in)),
            QTableWidgetItem(f"{total_out:.2f}"),
            QTableWidgetItem(str(total_lotes_out)),
            QTableWidgetItem(f"{(total_in + total_out):.2f}")
        ]

        for col, item in enumerate(items):
            item.setFont(total_font)
            item.setBackground(total_brush)
            item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row_count, col, item)

    def export_to_excel(self):
        """Export table data to an Excel (.xlsx) file using openpyxl"""
        try:
            try:
                from openpyxl import Workbook
            except ImportError:
                QMessageBox.critical(
                    self,
                    "Missing Dependency",
                    "The openpyxl package is required to export to Excel.\nInstall with: pip install openpyxl"
                )
                return

            corp = self.corp_selector.currentText()
            date_start, date_end = self.date_range_widget.get_date_range()
            date = date_start if date_start == date_end else f"{date_start}_to_{date_end}"

            rows = self.table.rowCount()
            cols = self.table.columnCount()

            if rows == 0:
                QMessageBox.warning(self, "No Data", "No data to export.")
                return

            wb = Workbook()
            ws = wb.active
            ws.title = "Palawan Report"

            # Add headers
            headers = []
            for col in range(cols):
                header_item = self.table.horizontalHeaderItem(col)
                headers.append(header_item.text() if header_item else "")
            ws.append(headers)

            # Add data rows
            for row in range(rows):
                row_vals = []
                for col in range(cols):
                    item = self.table.item(row, col)
                    row_vals.append(item.text() if item else "")
                ws.append(row_vals)

            filename = f"Palawan_Report_{corp}_{date}.xlsx"
            wb.save(filename)
            QMessageBox.information(self, "Exported", f"Data exported to {filename}")

        except Exception as e:
            QMessageBox.critical(self, "Export Error", f"Error exporting to Excel: {str(e)}")

    def print_table(self):
        """Print the table"""
        try:
            if self.table.rowCount() == 0:
                QMessageBox.warning(self, "No Data", "No data to print.")
                return

            doc = QTextDocument()
            html = "<h2>Palawan Transaction Report</h2>"
            date_start, date_end = self.date_range_widget.get_date_range()
            date_display = date_start if date_start == date_end else f"{date_start} to {date_end}"
            html += f"<p><b>Corporation:</b> {self.corp_selector.currentText()}<br>"
            html += f"<b>Date:</b> {date_display}</p>"
            html += "<table border='1' cellspacing='0' cellpadding='4' style='border-collapse: collapse;'>"

            # Add headers
            html += "<tr style='background-color: #f0f0f0;'>"
            for col in range(self.table.columnCount()):
                header_item = self.table.horizontalHeaderItem(col)
                header_text = header_item.text() if header_item else ""
                html += f"<th style='padding: 8px; text-align: center;'>{header_text}</th>"
            html += "</tr>"

            # Add data rows
            for row in range(self.table.rowCount()):
                html += "<tr>"
                for col in range(self.table.columnCount()):
                    item = self.table.item(row, col)
                    cell_text = item.text() if item else ""

                    # Check if this is the totals row (last row)
                    if row == self.table.rowCount() - 1:
                        html += f"<td style='padding: 8px; text-align: center; font-weight: bold; background-color: #f0f0f0;'>{cell_text}</td>"
                    else:
                        html += f"<td style='padding: 8px; text-align: center;'>{cell_text}</td>"
                html += "</tr>"

            html += "</table>"
            doc.setHtml(html)

            printer = QPrinter()
            dialog = QPrintDialog(printer, self)
            if dialog.exec_() == QPrintDialog.Accepted:
                doc.print_(printer)

        except Exception as e:
            QMessageBox.critical(self, "Print Error", f"Error printing: {str(e)}")