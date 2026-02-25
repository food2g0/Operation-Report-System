from PyQt5.QtWidgets import (
    QWidget, QLabel, QVBoxLayout, QComboBox, QTableWidget, QTableWidgetItem,
    QDateEdit, QMessageBox, QHeaderView, QSizePolicy, QPushButton, QHBoxLayout,
    QFileDialog
)
from PyQt5.QtCore import Qt, QDate
from PyQt5.QtGui import QFont, QColor, QBrush, QTextDocument
from PyQt5.QtPrintSupport import QPrinter, QPrintDialog
from db_connect_pooled import db_manager
import datetime


class MCPage(QWidget):
    def __init__(self, account_type=2):
        super().__init__()
        self.account_type = account_type
        # Set correct table based on brand: Brand A -> daily_reports_brand_a, Brand B -> daily_reports
        self.daily_table = "daily_reports_brand_a" if account_type == 1 else "daily_reports"
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
        self.export_button = QPushButton("📊 Export to Excel")
        self.export_button.clicked.connect(self.export_to_excel)
        self.export_button.setStyleSheet("""
            QPushButton {
                background-color: #217346;
                color: white;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1a5c38;
            }
        """)

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
        """Populate table with MC transaction data from daily_reports"""
        corp = self.corp_selector.currentText()
        selected_date = self.date_selector.date().toString("yyyy-MM-dd")

        if not corp:
            return

        try:
            # Query to get MC data for the selected corporation and date
            query = f"""
                    SELECT branch, 
                           COALESCE(mc_out, 0) as mc_buying, 
                           COALESCE(mc_in, 0) as mc_selling
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

    def export_to_excel(self):
        """Export table data to Excel with file dialog"""
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
        
        corp = self.corp_selector.currentText()
        date = self.date_selector.date().toString("yyyy-MM-dd")
        
        rows = self.table.rowCount()
        cols = self.table.columnCount()
        
        if rows == 0:
            QMessageBox.warning(self, "No Data", "No data to export.")
            return
        
        # File dialog for save location
        default_filename = f"MC_Report_{corp}_{date}.xlsx"
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
            ws.title = "MC Report"
            
            # Styles
            title_font = Font(bold=True, size=16)
            header_font = Font(bold=True, size=11, color="FFFFFF")
            header_fill = PatternFill(start_color="4472C4", end_color="4472C4", fill_type="solid")
            total_fill = PatternFill(start_color="E9ECEF", end_color="E9ECEF", fill_type="solid")
            border = Border(
                left=Side(style='thin'),
                right=Side(style='thin'),
                top=Side(style='thin'),
                bottom=Side(style='thin')
            )
            
            # Title
            ws.merge_cells('A1:C1')
            ws['A1'] = "MC Transaction Report"
            ws['A1'].font = title_font
            ws['A1'].alignment = Alignment(horizontal='center')
            
            # Info
            ws['A3'] = "Corporation:"
            ws['B3'] = corp
            ws['A4'] = "Date:"
            ws['B4'] = date
            ws['A3'].font = Font(bold=True)
            ws['A4'].font = Font(bold=True)
            
            # Headers (row 6)
            header_row = 6
            for col in range(cols):
                cell = ws.cell(row=header_row, column=col+1)
                header_item = self.table.horizontalHeaderItem(col)
                cell.value = header_item.text() if header_item else ""
                cell.font = header_font
                cell.fill = header_fill
                cell.border = border
                cell.alignment = Alignment(horizontal='center')
            
            # Data rows
            for row in range(rows):
                excel_row = header_row + 1 + row
                is_total_row = (row == rows - 1)
                
                for col in range(cols):
                    cell = ws.cell(row=excel_row, column=col+1)
                    item = self.table.item(row, col)
                    
                    if item:
                        text = item.text()
                        if col > 0:  # Numeric columns
                            try:
                                cell.value = float(text) if text else 0
                                cell.number_format = '#,##0.00'
                            except ValueError:
                                cell.value = text
                        else:
                            cell.value = text
                    
                    cell.border = border
                    cell.alignment = Alignment(horizontal='center')
                    
                    if is_total_row:
                        cell.fill = total_fill
                        cell.font = Font(bold=True)
            
            # Auto-adjust column widths
            ws.column_dimensions['A'].width = 20
            ws.column_dimensions['B'].width = 15
            ws.column_dimensions['C'].width = 15
            
            wb.save(file_path)
            QMessageBox.information(self, "Export Successful", f"Report exported to:\n{file_path}")
            
        except Exception as e:
            QMessageBox.critical(self, "Export Error", f"Error exporting to Excel: {str(e)}")

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