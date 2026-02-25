from PyQt5.QtWidgets import (
    QWidget, QLabel, QVBoxLayout, QComboBox, QTableWidget, QTableWidgetItem,
    QDateEdit, QMessageBox, QHeaderView, QSizePolicy, QPushButton, QHBoxLayout
)
from PyQt5.QtCore import Qt, QDate
from PyQt5.QtGui import QFont, QColor, QBrush, QTextDocument
from PyQt5.QtPrintSupport import QPrinter, QPrintDialog
from db_connect_pooled import db_manager
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

        # Corporation selector
        self.corp_selector = QComboBox()
        self.corp_selector.currentTextChanged.connect(self.populate_table)

        # Date selector
        self.date_selector = QDateEdit(calendarPopup=True)
        self.date_selector.setDate(QDate.currentDate())
        self.date_selector.setDisplayFormat("yyyy-MM-dd")
        self.date_selector.dateChanged.connect(self.populate_table)

        # Registration status filter
        self.reg_filter_selector = QComboBox()
        self.reg_filter_selector.addItem("Registered Only", "registered")
        self.reg_filter_selector.addItem("Not Registered", "not_registered")
        self.reg_filter_selector.addItem("All Branches", "all")
        self.reg_filter_selector.currentIndexChanged.connect(self.populate_table)

        # Add selectors to layout
        self.layout.addWidget(QLabel("Select Corporation:"))
        self.layout.addWidget(self.corp_selector)
        self.layout.addWidget(QLabel("Select Date:"))
        self.layout.addWidget(self.date_selector)
        self.layout.addWidget(QLabel("Branch Status:"))
        self.layout.addWidget(self.reg_filter_selector)

        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["Branch", "Palawan In", "Palawan Out", "Total"])
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

    def populate_table(self):
        """Populate table with Palawan transaction data from daily_reports"""
        corp = self.corp_selector.currentText()
        selected_date = self.date_selector.date().toString("yyyy-MM-dd")
        reg_filter = self.reg_filter_selector.currentData()

        if not corp:
            return

        try:
            # Build query based on registration filter
            if reg_filter == "registered":
                query = f"""
                    SELECT dr.branch, 
                           COALESCE(dr.palawan_send_out, 0)   as palawan_send_out, 
                           COALESCE(dr.palawan_sc, 0)         as palawan_sc, 
                           COALESCE(dr.palawan_pay_out, 0)    as palawan_pay_out, 
                           COALESCE(dr.palawan_pay_out_incentives, 0) as palawan_pay_out_incentives
                    FROM {self.daily_table} dr
                    INNER JOIN branches b ON dr.branch COLLATE utf8mb4_general_ci = b.name COLLATE utf8mb4_general_ci
                    INNER JOIN corporations c ON b.corporation_id = c.id AND dr.corporation COLLATE utf8mb4_general_ci = c.name COLLATE utf8mb4_general_ci
                    WHERE dr.corporation = %s 
                      AND dr.date = %s
                      AND b.is_registered = 1
                    ORDER BY dr.branch
                """
            elif reg_filter == "not_registered":
                query = f"""
                    SELECT dr.branch, 
                           COALESCE(dr.palawan_send_out, 0)   as palawan_send_out, 
                           COALESCE(dr.palawan_sc, 0)         as palawan_sc, 
                           COALESCE(dr.palawan_pay_out, 0)    as palawan_pay_out, 
                           COALESCE(dr.palawan_pay_out_incentives, 0) as palawan_pay_out_incentives
                    FROM {self.daily_table} dr
                    INNER JOIN branches b ON dr.branch COLLATE utf8mb4_general_ci = b.name COLLATE utf8mb4_general_ci
                    INNER JOIN corporations c ON b.corporation_id = c.id AND dr.corporation COLLATE utf8mb4_general_ci = c.name COLLATE utf8mb4_general_ci
                    WHERE dr.corporation = %s 
                      AND dr.date = %s
                      AND b.is_registered = 0
                    ORDER BY dr.branch
                """
            else:
                query = f"""
                    SELECT branch, 
                           COALESCE(palawan_send_out, 0)   as palawan_send_out, 
                           COALESCE(palawan_sc, 0)         as palawan_sc, 
                           COALESCE(palawan_pay_out, 0)    as palawan_pay_out, 
                           COALESCE(palawan_pay_out_incentives, 0) as palawan_pay_out_incentives
                    FROM {self.daily_table}
                    WHERE corporation = %s 
                      AND date = %s
                    ORDER BY branch
                """

            results = db_manager.execute_query(query, (corp, selected_date))

            self.table.setRowCount(0)

            if not results:
                self.table.setRowCount(0)
                return

            total_in = 0.0
            total_out = 0.0
            row_count = 0

            for row_data in results:
                branch_name = row_data['branch']
                palawan_send_out = float(row_data['palawan_send_out'] or 0)
                palawan_sc = float(row_data['palawan_sc'] or 0)
                palawan_pay_out = float(row_data['palawan_pay_out'] or 0)
                palawan_incentives = float(row_data['palawan_pay_out_incentives'] or 0)

                # Calculate Palawan In and Out
                palawan_in = palawan_send_out + palawan_sc
                palawan_out = palawan_pay_out + palawan_incentives
                total = palawan_in + palawan_out

                # Add row to table
                self.table.insertRow(row_count)
                self.table.setItem(row_count, 0, QTableWidgetItem(branch_name))
                self.table.setItem(row_count, 1, QTableWidgetItem(f"{palawan_in:.2f}"))
                self.table.setItem(row_count, 2, QTableWidgetItem(f"{palawan_out:.2f}"))
                self.table.setItem(row_count, 3, QTableWidgetItem(f"{total:.2f}"))

                total_in += palawan_in
                total_out += palawan_out
                row_count += 1

            # Add totals row
            self.table.insertRow(row_count)
            total_font = QFont()
            total_font.setBold(True)

            total_brush = QBrush(QColor("#f0f0f0"))

            items = [
                QTableWidgetItem("TOTAL"),
                QTableWidgetItem(f"{total_in:.2f}"),
                QTableWidgetItem(f"{total_out:.2f}"),
                QTableWidgetItem(f"{(total_in + total_out):.2f}")
            ]

            for col, item in enumerate(items):
                item.setFont(total_font)
                item.setBackground(total_brush)
                item.setTextAlignment(Qt.AlignCenter)
                self.table.setItem(row_count, col, item)

        except Exception as e:
            QMessageBox.critical(self, "Database Error", f"Error loading data: {str(e)}")

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
            date = self.date_selector.date().toString("yyyy-MM-dd")

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
            html += f"<p><b>Corporation:</b> {self.corp_selector.currentText()}<br>"
            html += f"<b>Date:</b> {self.date_selector.date().toString('yyyy-MM-dd')}</p>"
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