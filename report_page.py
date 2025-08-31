from PyQt5.QtWidgets import (
    QWidget, QLabel, QVBoxLayout, QComboBox, QTableWidget, QTableWidgetItem,
    QDateEdit, QMessageBox, QHeaderView, QSizePolicy, QPushButton, QHBoxLayout,
    QApplication, QDesktopWidget, QScrollArea, QFrame, QLineEdit
)
from PyQt5.QtCore import Qt, QDate, QTimer
from PyQt5.QtGui import QFont, QColor, QBrush, QTextDocument
from PyQt5.QtPrintSupport import QPrinter, QPrintDialog
from db_connect import db_manager
import datetime


class ReportPage(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PEPP Reconciliation Report")

        # Get screen dimensions and maximize window
        self.setup_window_size()

        # Main layout
        self.main_layout = QVBoxLayout()
        self.main_layout.setContentsMargins(15, 15, 15, 15)
        self.main_layout.setSpacing(10)
        self.setLayout(self.main_layout)

        # Create components
        self.create_controls()
        self.create_report_table()
        self.create_buttons()

        # Load data
        self.load_corporations()

    def setup_window_size(self):
        """Setup window to be maximized and responsive"""
        desktop = QApplication.desktop()
        screen_geometry = desktop.screenGeometry()
        self.setMinimumSize(800, 600)
        self.showMaximized()

    def create_controls(self):
        """Create corporation and date selectors"""
        controls_frame = QFrame()
        controls_frame.setFrameStyle(QFrame.Box)
        controls_frame.setStyleSheet("""
            QFrame {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 5px;
                padding: 10px;
            }
        """)

        controls_layout = QHBoxLayout(controls_frame)
        controls_layout.setSpacing(20)

        # Corporation selector
        corp_label = QLabel("Corporation:")
        corp_label.setFont(QFont("Arial", 10, QFont.Bold))
        self.corp_selector = QComboBox()
        self.corp_selector.setMinimumWidth(200)
        self.corp_selector.currentTextChanged.connect(self.generate_report)

        # Date selector
        date_label = QLabel("Date:")
        date_label.setFont(QFont("Arial", 10, QFont.Bold))
        self.date_selector = QDateEdit(calendarPopup=True)
        self.date_selector.setDate(QDate.currentDate())
        self.date_selector.setDisplayFormat("yyyy-MM-dd")
        self.date_selector.dateChanged.connect(self.generate_report)

        # Partner Registry No field
        registry_label = QLabel("Partner Registry No:")
        registry_label.setFont(QFont("Arial", 10, QFont.Bold))
        self.registry_input = QLineEdit()
        self.registry_input.setPlaceholderText("e.g., P210021A")
        self.registry_input.setMaximumWidth(150)

        controls_layout.addWidget(corp_label)
        controls_layout.addWidget(self.corp_selector)
        controls_layout.addSpacing(30)
        controls_layout.addWidget(date_label)
        controls_layout.addWidget(self.date_selector)
        controls_layout.addSpacing(30)
        controls_layout.addWidget(registry_label)
        controls_layout.addWidget(self.registry_input)
        controls_layout.addStretch()

        self.main_layout.addWidget(controls_frame)

    def create_report_table(self):
        """Create the PEPP reconciliation report table"""
        self.table = QTableWidget()
        self.table.setColumnCount(4)  # Description, blank, Amount column 1, Amount column 2
        self.table.setHorizontalHeaderLabels(["", "", "", ""])

        # Hide headers for cleaner look
        self.table.horizontalHeader().hide()
        self.table.verticalHeader().hide()

        # Set column widths
        self.table.setColumnWidth(0, 400)  # Description column
        self.table.setColumnWidth(1, 50)  # Blank column
        self.table.setColumnWidth(2, 100)  # Amount column 1
        self.table.setColumnWidth(3, 150)  # Amount column 2

        # Style the table
        self.table.setStyleSheet("""
            QTableWidget {
                gridline-color: #d0d0d0;
                border: 1px solid #c0c0c0;
                background-color: white;
                font-size: 11px;
            }
            QTableWidget::item {
                border: 1px solid #e0e0e0;
                padding: 5px;
            }
        """)

        self.main_layout.addWidget(self.table)

    def create_buttons(self):
        """Create export and print buttons"""
        button_frame = QFrame()
        button_frame.setMaximumHeight(60)
        button_layout = QHBoxLayout(button_frame)

        button_style = """
            QPushButton {
                padding: 12px 24px;
                border: 2px solid #007bff;
                border-radius: 6px;
                background-color: #007bff;
                color: white;
                font-weight: bold;
                font-size: 11px;
                min-width: 120px;
            }
            QPushButton:hover {
                background-color: #0056b3;
            }
        """

        self.export_button = QPushButton("Export to Excel")
        self.export_button.clicked.connect(self.export_to_excel)
        self.export_button.setStyleSheet(button_style)

        self.print_button = QPushButton("Print Report")
        self.print_button.clicked.connect(self.print_report)
        self.print_button.setStyleSheet(button_style)

        button_layout.addStretch()
        button_layout.addWidget(self.export_button)
        button_layout.addSpacing(15)
        button_layout.addWidget(self.print_button)
        button_layout.addStretch()

        self.main_layout.addWidget(button_frame)

    def load_corporations(self):
        """Load unique corporations from the database"""
        self.corp_selector.clear()
        try:
            query = "SELECT DISTINCT corporation FROM daily_reports ORDER BY corporation"
            corporations = db_manager.execute_query(query)

            for corp in corporations:
                if isinstance(corp, dict):
                    self.corp_selector.addItem(corp['corporation'])
                else:
                    self.corp_selector.addItem(corp[0])

        except Exception as e:
            QMessageBox.critical(self, "Database Error", f"Error loading corporations: {str(e)}")

    def get_totals_from_database(self):
        """Get totals from payable_tbl for the selected corporation and date"""
        corp = self.corp_selector.currentText()
        selected_date = self.date_selector.date().toString("yyyy-MM-dd")

        if not corp:
            return None

        try:
            query = """
                    SELECT SUM(sendout_capital)          as total_sendout_capital, \
                           SUM(sendout_commission)       as total_sendout_commission, \
                           SUM(sendout_sc)               as total_sendout_sc, \
                           SUM(payout_capital)           as total_payout_capital, \
                           SUM(payout_commission)        as total_payout_commission, \
                           SUM(payout_sc)                as total_payout_sc, \
                           SUM(international_commission) as total_international_commission, \
                           SUM(skid)                     as total_skid, \
                           SUM(skir)                     as total_skir, \
                           SUM(cancellation)             as total_cancellation, \
                           SUM(inc)                      as total_inc
                    FROM payable_tbl
                    WHERE corporation = %s \
                      AND date = %s \
                    """

            result = db_manager.execute_query(query, (corp, selected_date))

            if result and result[0]:
                if isinstance(result[0], dict):
                    return result[0]
                else:
                    # Convert tuple to dict
                    keys = ['total_sendout_capital', 'total_sendout_commission', 'total_sendout_sc',
                            'total_payout_capital', 'total_payout_commission', 'total_payout_sc',
                            'total_international_commission', 'total_skid', 'total_skir',
                            'total_cancellation', 'total_inc']
                    return dict(zip(keys, result[0]))

            return None

        except Exception as e:
            QMessageBox.critical(self, "Database Error", f"Error retrieving totals: {str(e)}")
            return None

    def generate_report(self):
        """Generate the PEPP reconciliation report"""
        corp = self.corp_selector.currentText()
        selected_date = self.date_selector.date().toString("yyyy-MM-dd")

        if not corp:
            return

        # Get totals from database
        totals = self.get_totals_from_database()
        if not totals:
            QMessageBox.information(self, "No Data", f"No data found for {corp} on {selected_date}")
            return

        # Extract values with null checking
        sendout_capital = float(totals.get('total_sendout_capital') or 0)
        sendout_commission = float(totals.get('total_sendout_commission') or 0)
        sendout_sc = float(totals.get('total_sendout_sc') or 0)
        payout_capital = float(totals.get('total_payout_capital') or 0)
        payout_commission = float(totals.get('total_payout_commission') or 0)
        payout_sc = float(totals.get('total_payout_sc') or 0)
        international_commission = float(totals.get('total_international_commission') or 0)
        total_skid = float(totals.get('total_skid') or 0)
        total_skir = float(totals.get('total_skir') or 0)
        total_cancellation = float(totals.get('total_cancellation') or 0)
        total_inc = float(totals.get('total_inc') or 0)

        # Calculate derived values
        pepp_commission_61 = sendout_commission * 0.61
        skid_61 = total_skid * 0.61
        ajpi_commission_43 = payout_commission * 0.43
        ajpi_international_80 = international_commission * 0.80
        skir_57 = total_skir * 0.57

        # Calculate subtotals and totals
        send_subtotal = sendout_capital + pepp_commission_61 + sendout_sc
        send_subtotal_after_discount = send_subtotal - skid_61
        total_net_send = send_subtotal_after_discount - total_cancellation

        release_subtotal = payout_capital + ajpi_commission_43 + ajpi_international_80
        release_subtotal_with_inc = release_subtotal + total_inc
        total_net_released = release_subtotal_with_inc + skir_57

        net_receivable_payable = total_net_send - total_net_released

        # Clear and populate table
        self.table.setRowCount(0)

        # Report data structure
        report_data = [
            # Header
            ("Palawan Express Pera Padala - " + corp, "", "", ""),
            ("PEPP Reconciliation for", "", "Partner Registry No.", ""),
            (selected_date, "", self.registry_input.text() or "P210021A", ""),
            ("", "", "", ""),
            ("", "", "", ""),

            # Send Transaction Section
            ("Send Transaction", "", "", ""),
            (f"    PEPP Remittance from {corp}", "", "P", f"{sendout_capital:,.2f}"),
            ("    PEPP share: 61% of commission", "P", f"{sendout_commission:,.2f}", f"{pepp_commission_61:,.2f}"),
            ("    PEPP share: Service Charge", "", f"{sendout_sc:,.2f}", f"{sendout_sc:,.2f}"),
            ("        Subtotal", "", "", f"{send_subtotal:,.2f}"),
            ("    Less: Discount ( Suki Card)", "", f"({total_skid:,.2f})", f"({skid_61:,.2f})"),
            ("        Subtotal", "", "", f"{send_subtotal_after_discount:,.2f}"),
            ("    Less: Cancellation", "", f"({total_cancellation:,.2f})", f"({total_cancellation:,.2f})"),
            ("    Total Net Send", "", "", f"{total_net_send:,.2f}"),
            ("", "", "", ""),
            ("", "", "", ""),

            # Release Transaction Section
            ("    RELEASE Transaction (Payable to AJPI)", "", "", ""),
            ("    PEPP Remittances released at AJPI", "", "P", f"{payout_capital:,.2f}"),
            ("    AJPI share: 43% of commission", "P", f"{payout_commission:,.2f}", f"{ajpi_commission_43:,.2f}"),
            ("    AJPI share: 50% of commission (LBC Domestic Payout)", "", "", ""),
            ("    AJPI share: 80% of commission (International Payout)", "", f"{international_commission:,.2f}",
             f"{ajpi_international_80:,.2f}"),
            ("    Service Charge", "", f"{payout_sc:,.2f}", "-"),
            ("        Subtotal", "", "", f"{release_subtotal:,.2f}"),
            (f"    Add: AJPI Branch Incentives released on    {selected_date}", "", "", f"{total_inc:,.2f}"),
            ("        Subtotal", "", "", f"{release_subtotal_with_inc:,.2f}"),
            ("    Add: Rebates (Suki Card)", "", f"{skir_57:,.2f}", f"{total_skir:,.2f}"),
            ("    Total Net Released", "", "", f"{total_net_released:,.2f}"),
            ("", "", "", ""),
            ("", "", "", ""),

            # Summary Section
            ("    Net Send", "", "", f"{total_net_send:,.2f}"),
            ("    Less : Net Released", "", "", f"{total_net_released:,.2f}"),
            ("    Net Receivable / (Payable)", "", "", f"{net_receivable_payable:,.2f}"),
        ]

        # Populate table
        self.table.setRowCount(len(report_data))

        for row, (col1, col2, col3, col4) in enumerate(report_data):
            # Set items
            self.table.setItem(row, 0, QTableWidgetItem(col1))
            self.table.setItem(row, 1, QTableWidgetItem(col2))
            self.table.setItem(row, 2, QTableWidgetItem(col3))
            self.table.setItem(row, 3, QTableWidgetItem(col4))

            # Apply formatting
            for col in range(4):
                item = self.table.item(row, col)
                if item:
                    # Header rows styling
                    if row in [0, 1, 2]:
                        font = QFont()
                        font.setBold(True)
                        item.setFont(font)
                        if row == 0:
                            item.setTextAlignment(Qt.AlignCenter)

                    # Section headers
                    elif "Transaction" in col1 or col1.startswith("    RELEASE"):
                        font = QFont()
                        font.setBold(True)
                        item.setFont(font)

                    # Total rows
                    elif "Total Net" in col1 or "Net Receivable" in col1 or "Net Send" in col1:
                        font = QFont()
                        font.setBold(True)
                        item.setFont(font)
                        item.setBackground(QBrush(QColor("#f0f0f0")))

                    # Subtotal rows
                    elif "Subtotal" in col1:
                        font = QFont()
                        font.setBold(True)
                        item.setFont(font)
                        item.setBackground(QBrush(QColor("#f8f8f8")))

                    # Amount columns alignment
                    if col in [2, 3]:
                        item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                    else:
                        item.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)

        # Adjust row heights
        for row in range(self.table.rowCount()):
            self.table.setRowHeight(row, 25)

    def export_to_excel(self):
        """Export the PEPP report to Excel file"""
        if self.table.rowCount() == 0:
            QMessageBox.warning(self, "No Data", "Please generate a report first.")
            return

        try:
            import pandas as pd
            from openpyxl import Workbook
            from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
            from openpyxl.utils.dataframe import dataframe_to_rows
            import datetime

            # Get data from form
            corp = self.corp_selector.currentText()
            date = self.date_selector.date().toString("yyyy-MM-dd")
            registry_no = self.registry_input.text() or "P210021A"

            # Get totals
            totals = self.get_totals_from_database()
            if not totals:
                QMessageBox.warning(self, "No Data", "No data available for export.")
                return

            # Extract numbers
            sendout_capital = float(totals.get('total_sendout_capital') or 0)
            sendout_commission = float(totals.get('total_sendout_commission') or 0)
            sendout_sc = float(totals.get('total_sendout_sc') or 0)
            payout_capital = float(totals.get('total_payout_capital') or 0)
            payout_commission = float(totals.get('total_payout_commission') or 0)
            payout_sc = float(totals.get('total_payout_sc') or 0)
            international_commission = float(totals.get('total_international_commission') or 0)
            total_skid = float(totals.get('total_skid') or 0)
            total_skir = float(totals.get('total_skir') or 0)
            total_cancellation = float(totals.get('total_cancellation') or 0)
            total_inc = float(totals.get('total_inc') or 0)

            # Derived values
            pepp_commission_61 = sendout_commission * 0.61
            skid_61 = total_skid * 0.61
            ajpi_commission_43 = payout_commission * 0.43
            ajpi_international_80 = international_commission * 0.80
            skir_57 = total_skir * 0.57

            send_subtotal = sendout_capital + pepp_commission_61 + sendout_sc
            send_subtotal_after_discount = send_subtotal - skid_61
            total_net_send = send_subtotal_after_discount - total_cancellation

            release_subtotal = payout_capital + ajpi_commission_43 + ajpi_international_80
            release_subtotal_with_inc = release_subtotal + total_inc
            total_net_released = release_subtotal_with_inc + skir_57

            net_receivable_payable = total_net_send - total_net_released

            # Create workbook and worksheet
            workbook = Workbook()
            worksheet = workbook.active
            worksheet.title = "PEPP Reconciliation"

            # Define styles
            header_font = Font(bold=True, size=12)
            section_font = Font(bold=True, size=11)
            regular_font = Font(size=10)
            total_font = Font(bold=True, size=11)

            # Fill styles
            header_fill = PatternFill(start_color="E6F3FF", end_color="E6F3FF", fill_type="solid")
            subtotal_fill = PatternFill(start_color="F0F0F0", end_color="F0F0F0", fill_type="solid")
            total_fill = PatternFill(start_color="D9D9D9", end_color="D9D9D9", fill_type="solid")

            # Border style
            thin_border = Border(
                left=Side(style='thin'), right=Side(style='thin'),
                top=Side(style='thin'), bottom=Side(style='thin')
            )

            current_row = 1

            # Header section
            worksheet.merge_cells(f'A{current_row}:D{current_row}')
            worksheet[f'A{current_row}'] = f"Palawan Express Pera Padala - {corp}"
            worksheet[f'A{current_row}'].font = header_font
            worksheet[f'A{current_row}'].alignment = Alignment(horizontal='center')
            worksheet[f'A{current_row}'].fill = header_fill
            current_row += 1

            worksheet[f'A{current_row}'] = f"PEPP Reconciliation for {date}"
            worksheet[f'C{current_row}'] = "Partner Registry No."
            worksheet[f'D{current_row}'] = registry_no
            worksheet[f'A{current_row}'].font = header_font
            worksheet[f'C{current_row}'].font = header_font
            worksheet[f'D{current_row}'].font = header_font
            current_row += 2

            # Data rows with proper formatting
            data_rows = [
                # Send Transaction Section
                ("Send Transaction", "", "", "", "section"),
                (f"    PEPP Remittance from {corp}", "", "P", f"{sendout_capital:,.2f}", "indent"),
                ("    PEPP share: 61% of commission", "P", f"{sendout_commission:,.2f}", f"{pepp_commission_61:,.2f}",
                 "indent"),
                ("    PEPP share: Service Charge", "", f"{sendout_sc:,.2f}", f"{sendout_sc:,.2f}", "indent"),
                ("        Subtotal", "", "", f"{send_subtotal:,.2f}", "subtotal"),
                ("    Less: Discount (Suki Card)", "", f"({total_skid:,.2f})", f"({skid_61:,.2f})", "indent"),
                ("        Subtotal", "", "", f"{send_subtotal_after_discount:,.2f}", "subtotal"),
                ("    Less: Cancellation", "", f"({total_cancellation:,.2f})", f"({total_cancellation:,.2f})",
                 "indent"),
                ("    Total Net Send", "", "", f"{total_net_send:,.2f}", "total"),
                ("", "", "", "", "blank"),

                # Release Transaction Section
                ("    RELEASE Transaction (Payable to AJPI)", "", "", "", "section"),
                ("    PEPP Remittances released at AJPI", "", "P", f"{payout_capital:,.2f}", "indent"),
                ("    AJPI share: 43% of commission", "P", f"{payout_commission:,.2f}", f"{ajpi_commission_43:,.2f}",
                 "indent"),
                ("    AJPI share: 50% of commission (LBC Domestic Payout)", "", "", "", "indent"),
                ("    AJPI share: 80% of commission (International Payout)", "", f"{international_commission:,.2f}",
                 f"{ajpi_international_80:,.2f}", "indent"),
                ("    Service Charge", "", f"{payout_sc:,.2f}", "-", "indent"),
                ("        Subtotal", "", "", f"{release_subtotal:,.2f}", "subtotal"),
                (f"    Add: AJPI Branch Incentives released on {date}", "", "", f"{total_inc:,.2f}", "indent"),
                ("        Subtotal", "", "", f"{release_subtotal_with_inc:,.2f}", "subtotal"),
                ("    Add: Rebates (Suki Card)", "", f"{skir_57:,.2f}", f"{total_skir:,.2f}", "indent"),
                ("    Total Net Released", "", "", f"{total_net_released:,.2f}", "total"),
                ("", "", "", "", "blank"),

                # Summary Section
                ("    Net Send", "", "", f"{total_net_send:,.2f}", "regular"),
                ("    Less : Net Released", "", "", f"{total_net_released:,.2f}", "regular"),
                ("    Net Receivable / (Payable)", "", "", f"{net_receivable_payable:,.2f}", "total"),
            ]

            # Add data rows
            for row_data in data_rows:
                col1, col2, col3, col4, row_type = row_data

                worksheet[f'A{current_row}'] = col1
                worksheet[f'B{current_row}'] = col2
                worksheet[f'C{current_row}'] = col3
                worksheet[f'D{current_row}'] = col4

                # Apply formatting based on row type
                if row_type == "section":
                    worksheet[f'A{current_row}'].font = section_font
                    worksheet[f'B{current_row}'].font = section_font
                    worksheet[f'C{current_row}'].font = section_font
                    worksheet[f'D{current_row}'].font = section_font
                elif row_type == "total":
                    for col in ['A', 'B', 'C', 'D']:
                        worksheet[f'{col}{current_row}'].font = total_font
                        worksheet[f'{col}{current_row}'].fill = total_fill
                elif row_type == "subtotal":
                    for col in ['A', 'B', 'C', 'D']:
                        worksheet[f'{col}{current_row}'].font = total_font
                        worksheet[f'{col}{current_row}'].fill = subtotal_fill
                else:
                    for col in ['A', 'B', 'C', 'D']:
                        worksheet[f'{col}{current_row}'].font = regular_font

                # Right align amounts
                worksheet[f'C{current_row}'].alignment = Alignment(horizontal='right')
                worksheet[f'D{current_row}'].alignment = Alignment(horizontal='right')

                current_row += 1

            # Add signature section
            current_row += 2
            worksheet[f'A{current_row}'] = "Prepared by:"
            worksheet[f'C{current_row}'] = "Noted by:"
            worksheet[f'A{current_row}'].font = regular_font
            worksheet[f'C{current_row}'].font = regular_font
            current_row += 2

            worksheet[f'A{current_row}'] = "Rochelle G. Serrano"
            worksheet[f'C{current_row}'] = "Aimee M. Martinez"
            worksheet[f'A{current_row}'].font = regular_font
            worksheet[f'C{current_row}'].font = regular_font

            # Adjust column widths
            worksheet.column_dimensions['A'].width = 50
            worksheet.column_dimensions['B'].width = 8
            worksheet.column_dimensions['C'].width = 15
            worksheet.column_dimensions['D'].width = 18

            # Save file
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"PEPP_Reconciliation_{corp}_{date}_{timestamp}.xlsx"
            workbook.save(filename)

            QMessageBox.information(self, "Export Successful", f"Report exported as: {filename}")

        except ImportError as e:
            missing_lib = str(e).split("'")[1] if "'" in str(e) else "required library"
            QMessageBox.critical(self, "Missing Library",
                                 f"Required library '{missing_lib}' is missing.\n"
                                 f"Please install with: pip install pandas openpyxl")
        except Exception as e:
            QMessageBox.critical(self, "Export Error", f"Error exporting to Excel: {str(e)}")

    def print_report(self):
        """Print the PEPP report"""
        if self.table.rowCount() == 0:
            QMessageBox.warning(self, "No Data", "Please generate a report first.")
            return

        try:
            doc = QTextDocument()
            html = "<html><body style='font-family: Arial; font-size: 12px;'>"

            for row in range(self.table.rowCount()):
                line = ""
                for col in range(4):
                    item = self.table.item(row, col)
                    if item and item.text().strip():
                        if col == 0:
                            line += item.text()
                        else:
                            line += f"&nbsp;&nbsp;&nbsp;{item.text()}"

                if line.strip():
                    # Apply bold formatting for headers and totals
                    if any(keyword in line for keyword in
                           ["Palawan Express", "PEPP Reconciliation", "Transaction", "Total Net", "Net Receivable"]):
                        html += f"<p style='font-weight: bold;'>{line}</p>"
                    else:
                        html += f"<p>{line}</p>"
                else:
                    html += "<p>&nbsp;</p>"

            html += "</body></html>"
            doc.setHtml(html)

            printer = QPrinter()
            dialog = QPrintDialog(printer, self)
            if dialog.exec_() == QPrintDialog.Accepted:
                doc.print_(printer)
                QMessageBox.information(self, "Print Successful", "Report printed successfully!")

        except Exception as e:
            QMessageBox.critical(self, "Print Error", f"Error printing report: {str(e)}")


# Integration function to add to your main application
def add_pepp_report_to_main_app(main_window):
    """Add PEPP Report tab to the main application"""
    pepp_report_page = ReportPage()
    # Add to your tab widget or main window as needed
    # main_window.tab_widget.addTab(pepp_report_page, "PEPP Report")
    return pepp_report_page