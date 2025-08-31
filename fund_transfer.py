from PyQt5.QtWidgets import (
    QWidget, QLabel, QVBoxLayout, QComboBox, QTableWidget, QTableWidgetItem,
    QDateEdit, QMessageBox, QHeaderView, QSizePolicy, QPushButton, QHBoxLayout,
    QAbstractItemView,
)
from PyQt5.QtPrintSupport import QPrinter, QPrintDialog
from PyQt5.QtGui import QFont, QColor, QBrush, QTextDocument
from PyQt5.QtCore import Qt, QDate
from db_connect import db_manager
from docx import Document
import datetime


class FundTransferPage(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Fund Transfer")
        self.resize(1100, 650)

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

        # Add selectors to layout
        self.layout.addWidget(QLabel("Select Corporation:"))
        self.layout.addWidget(self.corp_selector)
        self.layout.addWidget(QLabel("Select Date:"))
        self.layout.addWidget(self.date_selector)

        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["Branch", "Inventory", "Cash Count", "BR to Head Office", "BR to BR"])
        self.table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        # Set edit triggers - only allow editing for specific columns
        self.table.setEditTriggers(QAbstractItemView.DoubleClicked | QAbstractItemView.SelectedClicked)

        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

        # Connect item changed signal to handle data updates
        self.table.itemChanged.connect(self.on_item_changed)

        self.layout.addWidget(self.table)

        # Buttons
        button_layout = QHBoxLayout()
        self.export_btn = QPushButton("Export to Word")
        self.export_btn.clicked.connect(self.export_to_word)

        self.print_btn = QPushButton("Print")
        self.print_btn.clicked.connect(self.print_table)

        button_layout.addWidget(self.export_btn)
        button_layout.addWidget(self.print_btn)

        self.layout.addLayout(button_layout)

        # Add signature section
        signature_layout = QVBoxLayout()
        signature_layout.addWidget(QLabel(""))  # Spacer

        prepared_layout = QHBoxLayout()
        prepared_layout.addWidget(QLabel("Prepared by: ________________________"))
        prepared_layout.addStretch()

        approved_layout = QHBoxLayout()
        approved_layout.addWidget(QLabel("Approved by: ________________________"))
        approved_layout.addStretch()

        signature_layout.addLayout(prepared_layout)
        signature_layout.addLayout(approved_layout)

        self.layout.addLayout(signature_layout)

        self.load_corporations()

    def load_corporations(self):
        """Load unique corporations from the daily_reports table"""
        self.corp_selector.clear()
        try:
            query = "SELECT DISTINCT corporation FROM daily_reports ORDER BY corporation"
            corporations = db_manager.execute_query(query)

            if not corporations:
                print("No corporations found in database")
                QMessageBox.warning(self, "No Data", "No corporations found in database")
                return

            for corp in corporations:
                self.corp_selector.addItem(corp['corporation'])
                print(f"Added corporation: {corp['corporation']}")  # Debug

        except Exception as e:
            print(f"Error loading corporations: {e}")
            QMessageBox.critical(self, "Database Error", f"Error connecting to database: {str(e)}")

    def on_item_changed(self, item):
        """Handle when user edits a cell"""
        row = item.row()
        col = item.column()

        # Don't process if this is the total row (last row)
        if row == self.table.rowCount() - 1:
            return

        # Only allow editing for columns 1, 3, 4 (Inventory, BR to Head Office, BR to BR)
        if col not in [1, 3, 4]:
            return

        # Validate that the input is a number
        try:
            float(item.text())
        except ValueError:
            QMessageBox.warning(self, "Invalid Input", "Please enter a valid number.")
            item.setText("0.00")

        # Update totals when values change
        self.update_totals()

    def update_totals(self):
        """Update the total row calculations - only for Cash Count column"""
        if self.table.rowCount() < 2:  # Need at least 2 rows (1 data + 1 total)
            return

        total_cash_count = 0.0

        # Calculate total for Cash Count only (excluding the last row which is the total row)
        last_data_row = self.table.rowCount() - 1
        for row in range(last_data_row):
            # Cash Count
            cash_item = self.table.item(row, 2)
            if cash_item:
                try:
                    total_cash_count += float(cash_item.text())
                except ValueError:
                    pass

        # Update total row - temporarily disconnect signals to avoid recursion
        self.table.itemChanged.disconnect()

        # Update only Cash Count total cell
        total_row = self.table.rowCount() - 1
        cash_total_item = self.table.item(total_row, 2)
        if cash_total_item:
            cash_total_item.setText(f"{total_cash_count:.2f}")

        # Reconnect the signal
        self.table.itemChanged.connect(self.on_item_changed)

    def populate_table(self):
        """Populate table with data from daily_reports table only"""
        corp = self.corp_selector.currentText()
        selected_date = self.date_selector.date().toString("yyyy-MM-dd")

        if not corp:
            return

        try:
            # Get all branches for the corporation and date with cash count from daily_reports only
            query = """
                    SELECT branch,
                           COALESCE(cash_count, 0) as cash_count
                    FROM daily_reports
                    WHERE corporation = %s
                      AND date = %s
                    ORDER BY branch
                    """

            results = db_manager.execute_query(query, (corp, selected_date))
            self.table.setRowCount(0)

            if not results:
                print(f"No data found for {corp} on {selected_date}")
                QMessageBox.information(self, "No Data", f"No data found for {corp} on {selected_date}")
                return

            total_cash_count = 0.0
            row_count = 0

            print(f"Loading data for corporation: {corp}, date: {selected_date}")  # Debug

            for row_data in results:
                branch_name = row_data['branch']
                cash_count = float(row_data['cash_count'] or 0)
                # Set default values for manual input fields
                inventory = 0.00
                br_to_head = 0.00
                br_to_br = 0.00

                print(f"Processing branch: {branch_name}, cash: {cash_count}")  # Debug

                self.table.insertRow(row_count)

                # Create items for each column
                branch_item = QTableWidgetItem(branch_name)
                branch_item.setTextAlignment(Qt.AlignCenter)
                branch_item.setFlags(branch_item.flags() & ~Qt.ItemIsEditable)  # Make read-only

                inventory_item = QTableWidgetItem(f"{inventory:.2f}")
                inventory_item.setTextAlignment(Qt.AlignCenter)

                cash_item = QTableWidgetItem(f"{cash_count:.2f}")
                cash_item.setTextAlignment(Qt.AlignCenter)
                cash_item.setFlags(cash_item.flags() & ~Qt.ItemIsEditable)  # Make read-only

                br_head_item = QTableWidgetItem(f"{br_to_head:.2f}")
                br_head_item.setTextAlignment(Qt.AlignCenter)

                br_br_item = QTableWidgetItem(f"{br_to_br:.2f}")
                br_br_item.setTextAlignment(Qt.AlignCenter)

                # Set items in table
                self.table.setItem(row_count, 0, branch_item)
                self.table.setItem(row_count, 1, inventory_item)
                self.table.setItem(row_count, 2, cash_item)
                self.table.setItem(row_count, 3, br_head_item)
                self.table.setItem(row_count, 4, br_br_item)

                total_cash_count += cash_count
                row_count += 1

            # Add total row if we have data
            if row_count > 0:
                # Calculate total for Cash Count only
                total_cash_count = sum(float(self.table.item(i, 2).text()) for i in range(row_count))

                # Add total row (bold and highlighted)
                total_font = QFont()
                total_font.setBold(True)
                total_brush = QBrush(QColor("#e0e0e0"))

                self.table.insertRow(row_count)

                # Create total row items - only Cash Count has total, others are empty
                total_items = [
                    ("TOTAL", 0),
                    ("", 1),  # Empty for Inventory
                    (f"{total_cash_count:.2f}", 2),  # Cash Count total
                    ("", 3),  # Empty for BR to Head Office
                    ("", 4)  # Empty for BR to BR
                ]

                for text, col in total_items:
                    item = QTableWidgetItem(text)
                    item.setFont(total_font)
                    item.setBackground(total_brush)
                    item.setTextAlignment(Qt.AlignCenter)
                    item.setFlags(item.flags() & ~Qt.ItemIsEditable)  # Make total row read-only
                    self.table.setItem(row_count, col, item)

        except Exception as e:
            print(f"Error loading fund transfer data: {e}")
            QMessageBox.critical(self, "Error", f"Error loading data: {str(e)}")

    def export_to_word(self):
        """Export table data to Word document"""
        try:
            document = Document()
            document.add_heading('Fund Transfer Report', 0)

            # Add selected corp/date
            corp = self.corp_selector.currentText()
            date = self.date_selector.date().toString("yyyy-MM-dd")
            document.add_paragraph(f"Corporation: {corp}")
            document.add_paragraph(f"Date: {date}")

            # Create table in docx
            rows = self.table.rowCount()
            cols = self.table.columnCount()

            if rows == 0:
                QMessageBox.warning(self, "No Data", "No data to export.")
                return

            word_table = document.add_table(rows=rows + 1, cols=cols)
            word_table.style = 'Table Grid'

            # Headers
            for col in range(cols):
                header_item = self.table.horizontalHeaderItem(col)
                word_table.cell(0, col).text = header_item.text() if header_item else ""

            # Data
            for row in range(rows):
                for col in range(cols):
                    item = self.table.item(row, col)
                    word_table.cell(row + 1, col).text = item.text() if item else ""

            filename = f"Fund_Transfer_Report_{corp}_{date}.docx"
            document.save(filename)

            # Add signature lines
            document.add_paragraph("")  # Blank line
            document.add_paragraph("Prepared by: ________________________")
            document.add_paragraph("Approved by: ________________________")

            document.save(filename)
            QMessageBox.information(self, "Exported", f"Data exported to {filename}")

        except Exception as e:
            QMessageBox.critical(self, "Export Error", f"Error exporting to Word: {str(e)}")

    def print_table(self):
        """Print the table"""
        try:
            if self.table.rowCount() == 0:
                QMessageBox.warning(self, "No Data", "No data to print.")
                return

            doc = QTextDocument()
            html = "<h2>Fund Transfer Report</h2>"
            html += f"<p><b>Corporation:</b> {self.corp_selector.currentText()}<br>"
            html += f"<b>Date:</b> {self.date_selector.date().toString('yyyy-MM-dd')}</p>"
            html += "<table border='1' cellspacing='0' cellpadding='4' style='border-collapse: collapse;'>"

            # Headers
            html += "<tr style='background-color: #f0f0f0;'>"
            for col in range(self.table.columnCount()):
                header_item = self.table.horizontalHeaderItem(col)
                header_text = header_item.text() if header_item else ""
                html += f"<th style='padding: 8px; text-align: center;'>{header_text}</th>"
            html += "</tr>"

            # Data rows
            for row in range(self.table.rowCount()):
                html += "<tr>"
                for col in range(self.table.columnCount()):
                    item = self.table.item(row, col)
                    cell_text = item.text() if item else ""

                    # Check if this is the totals row (last row)
                    if row == self.table.rowCount() - 1:
                        html += f"<td style='padding: 8px; text-align: center; font-weight: bold; background-color: #e0e0e0;'>{cell_text}</td>"
                    else:
                        html += f"<td style='padding: 8px; text-align: center;'>{cell_text}</td>"
                html += "</tr>"

            html += "</table>"

            # Add signature lines to HTML
            html += "<br><br>"
            html += "<p>Prepared by: ________________________</p>"
            html += "<p>Approved by: ________________________</p>"

            doc.setHtml(html)

            printer = QPrinter()
            dialog = QPrintDialog(printer, self)
            if dialog.exec_() == QPrintDialog.Accepted:
                doc.print_(printer)

        except Exception as e:
            QMessageBox.critical(self, "Print Error", f"Error printing: {str(e)}")