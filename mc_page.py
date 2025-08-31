from PyQt5.QtWidgets import (
    QWidget, QLabel, QVBoxLayout, QComboBox, QTableWidget, QTableWidgetItem,
    QDateEdit, QMessageBox, QHeaderView, QSizePolicy, QPushButton, QHBoxLayout
)
from PyQt5.QtCore import Qt, QDate
from PyQt5.QtGui import QFont, QColor, QBrush, QTextDocument
from PyQt5.QtPrintSupport import QPrinter, QPrintDialog
from db_connect import db_manager
import datetime
from docx import Document


class MCPage(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("MC Transactions")
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

        # Add selectors to layout
        self.layout.addWidget(QLabel("Select Corporation:"))
        self.layout.addWidget(self.corp_selector)
        self.layout.addWidget(QLabel("Select Date:"))
        self.layout.addWidget(self.date_selector)

        # Table - Fixed to 3 columns
        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["Branch", "MC Buying", "MC Selling"])
        self.table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        header = self.table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Stretch)
        header.setStretchLastSection(True)

        self.layout.addWidget(self.table)

        # Export & Print Buttons
        self.export_button = QPushButton("Export to Word")
        self.export_button.clicked.connect(self.export_to_word)

        self.print_button = QPushButton("Print")
        self.print_button.clicked.connect(self.print_table)

        button_layout = QHBoxLayout()
        button_layout.addWidget(self.export_button)
        button_layout.addWidget(self.print_button)
        self.layout.addLayout(button_layout)

        self.load_corporations()

    def load_corporations(self):
        """Load unique corporations from the daily_reports table"""
        self.corp_selector.clear()
        try:
            # Get distinct corporations from daily_reports table
            query = "SELECT DISTINCT corporation FROM daily_reports ORDER BY corporation"
            corporations = db_manager.execute_query(query)

            for corp in corporations:
                self.corp_selector.addItem(corp['corporation'])

        except Exception as e:
            QMessageBox.critical(self, "Database Error", f"Error loading corporations: {str(e)}")

    def populate_table(self):
        """Populate table with MC transaction data from daily_reports"""
        corp = self.corp_selector.currentText()
        selected_date = self.date_selector.date().toString("yyyy-MM-dd")

        if not corp:
            return

        try:
            # Query to get MC data for the selected corporation and date
            query = """
                    SELECT branch, 
                           COALESCE(mc_out, 0) as mc_buying, 
                           COALESCE(mc_in, 0) as mc_selling
                    FROM daily_reports
                    WHERE corporation = %s 
                      AND date = %s
                    ORDER BY branch
                    """

            results = db_manager.execute_query(query, (corp, selected_date))

            self.table.setRowCount(0)

            if not results:
                QMessageBox.information(self, "No Data", f"No data found for {selected_date}.")
                return

            total_buying = 0.0
            total_selling = 0.0
            row_count = 0

            for row_data in results:
                branch_name = row_data['branch']
                mc_buying = float(row_data['mc_buying'] or 0)
                mc_selling = float(row_data['mc_selling'] or 0)

                # Add row to table
                self.table.insertRow(row_count)
                self.table.setItem(row_count, 0, QTableWidgetItem(branch_name))
                self.table.setItem(row_count, 1, QTableWidgetItem(f"{mc_buying:.2f}"))
                self.table.setItem(row_count, 2, QTableWidgetItem(f"{mc_selling:.2f}"))

                total_buying += mc_buying
                total_selling += mc_selling
                row_count += 1

            # Add totals row at the bottom
            self.table.insertRow(row_count)
            total_font = QFont()
            total_font.setBold(True)

            total_brush = QBrush(QColor("#f0f0f0"))

            items = [
                QTableWidgetItem("TOTAL"),
                QTableWidgetItem(f"{total_buying:.2f}"),
                QTableWidgetItem(f"{total_selling:.2f}")
            ]

            for col, item in enumerate(items):
                item.setFont(total_font)
                item.setBackground(total_brush)
                item.setTextAlignment(Qt.AlignCenter)
                self.table.setItem(row_count, col, item)

        except Exception as e:
            QMessageBox.critical(self, "Database Error", f"Error loading data: {str(e)}")

    def export_to_word(self):
        """Export table data to Word document"""
        try:
            document = Document()
            document.add_heading('MC Transaction Report', 0)

            corp = self.corp_selector.currentText()
            date = self.date_selector.date().toString("yyyy-MM-dd")
            document.add_paragraph(f"Corporation: {corp}")
            document.add_paragraph(f"Date: {date}")

            rows = self.table.rowCount()
            cols = self.table.columnCount()

            if rows == 0:
                QMessageBox.warning(self, "No Data", "No data to export.")
                return

            word_table = document.add_table(rows=rows + 1, cols=cols)
            word_table.style = 'Table Grid'

            # Add headers
            for col in range(cols):
                header_item = self.table.horizontalHeaderItem(col)
                word_table.cell(0, col).text = header_item.text() if header_item else ""

            # Add data
            for row in range(rows):
                for col in range(cols):
                    item = self.table.item(row, col)
                    word_table.cell(row + 1, col).text = item.text() if item else ""

            filename = f"MC_Report_{corp}_{date}.docx"
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
            html = "<h2>MC Transaction Report</h2>"
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