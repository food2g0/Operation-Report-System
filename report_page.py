from PyQt5.QtWidgets import (
    QWidget, QLabel, QVBoxLayout, QComboBox, QTableWidget, QTableWidgetItem,
    QDateEdit, QMessageBox, QHeaderView, QSizePolicy, QPushButton, QHBoxLayout,
    QApplication, QDesktopWidget, QScrollArea, QFrame, QLineEdit
)
from PyQt5.QtCore import Qt, QDate, QTimer
from PyQt5.QtGui import QFont, QColor, QBrush, QTextDocument
from PyQt5.QtPrintSupport import QPrinter, QPrintDialog
from db_connect_pooled import db_manager
import datetime


class ReportPage(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PEPP Reconciliation Report")
        self.setup_window_size()

        self.main_layout = QVBoxLayout()
        self.main_layout.setContentsMargins(15, 15, 15, 15)
        self.main_layout.setSpacing(10)
        self.setLayout(self.main_layout)

        self.create_controls()
        self.create_report_table()
        self.create_buttons()

        self.load_corporations()

    # ─────────────────────────────────────────────────────────────────────────

    def setup_window_size(self):
        desktop = QApplication.desktop()
        self.setMinimumSize(800, 600)
        self.showMaximized()

    # ─────────────────────────────────────────────────────────────────────────

    def create_controls(self):
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

        corp_label = QLabel("Corporation:")
        corp_label.setFont(QFont("Arial", 10, QFont.Bold))
        self.corp_selector = QComboBox()
        self.corp_selector.setMinimumWidth(200)
        self.corp_selector.currentTextChanged.connect(self.generate_report)

        date_label = QLabel("Date:")
        date_label.setFont(QFont("Arial", 10, QFont.Bold))
        self.date_selector = QDateEdit(calendarPopup=True)
        self.date_selector.setDate(QDate.currentDate())
        self.date_selector.setDisplayFormat("yyyy-MM-dd")
        self.date_selector.dateChanged.connect(self.generate_report)

        registry_label = QLabel("Partner Registry No:")
        registry_label.setFont(QFont("Arial", 10, QFont.Bold))
        self.registry_input = QLineEdit()
        self.registry_input.setPlaceholderText("e.g., P210021A")
        self.registry_input.setMaximumWidth(150)
        # Re-generate report when registry number changes so header updates live
        self.registry_input.textChanged.connect(self.generate_report)

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

    # ─────────────────────────────────────────────────────────────────────────

    def create_report_table(self):
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["", "", "", ""])
        self.table.horizontalHeader().hide()
        self.table.verticalHeader().hide()
        self.table.setColumnWidth(0, 400)
        self.table.setColumnWidth(1, 50)
        self.table.setColumnWidth(2, 100)
        self.table.setColumnWidth(3, 150)
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

    # ─────────────────────────────────────────────────────────────────────────

    def create_buttons(self):
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
            QPushButton:hover { background-color: #0056b3; }
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

    # ─────────────────────────────────────────────────────────────────────────

    def load_corporations(self):
        self.corp_selector.clear()
        try:
            results = db_manager.execute_query(
                "SELECT DISTINCT corporation FROM daily_reports ORDER BY corporation"
            )
            for corp in results:
                self.corp_selector.addItem(
                    corp['corporation'] if isinstance(corp, dict) else corp[0]
                )
        except Exception as e:
            QMessageBox.critical(self, "Database Error", f"Error loading corporations: {str(e)}")

    # ─────────────────────────────────────────────────────────────────────────

    def get_totals_from_database(self):
        """Fetch aggregated totals from payable_tbl. Returns None if no rows exist."""
        corp          = self.corp_selector.currentText()
        selected_date = self.date_selector.date().toString("yyyy-MM-dd")

        if not corp:
            return None

        try:
            result = db_manager.execute_query("""
                SELECT SUM(sendout_capital)          AS total_sendout_capital,
                       SUM(sendout_commission)       AS total_sendout_commission,
                       SUM(sendout_sc)               AS total_sendout_sc,
                       SUM(payout_capital)           AS total_payout_capital,
                       SUM(payout_commission)        AS total_payout_commission,
                       SUM(payout_sc)                AS total_payout_sc,
                       SUM(international_commission) AS total_international_commission,
                       SUM(skid)                     AS total_skid,
                       SUM(skir)                     AS total_skir,
                       SUM(cancellation)             AS total_cancellation,
                       SUM(inc)                      AS total_inc
                FROM payable_tbl
                WHERE corporation = %s
                  AND date        = %s
            """, (corp, selected_date))

            if not result or not result[0]:
                return None

            row = result[0]

            # If every SUM came back NULL it means no matching rows at all
            if isinstance(row, dict):
                if all(v is None for v in row.values()):
                    return None
                return row
            else:
                if all(v is None for v in row):
                    return None
                keys = [
                    'total_sendout_capital', 'total_sendout_commission', 'total_sendout_sc',
                    'total_payout_capital',  'total_payout_commission',  'total_payout_sc',
                    'total_international_commission',
                    'total_skid', 'total_skir', 'total_cancellation', 'total_inc',
                ]
                return dict(zip(keys, row))

        except Exception as e:
            QMessageBox.critical(self, "Database Error", f"Error retrieving totals: {str(e)}")
            return None

    # ─────────────────────────────────────────────────────────────────────────

    def generate_report(self):
        """
        Auto-generates the report whenever corp/date/registry changes.
        If no data exists yet, clears the table silently — no popup.
        """
        corp          = self.corp_selector.currentText()
        selected_date = self.date_selector.date().toString("yyyy-MM-dd")

        if not corp:
            self.table.setRowCount(0)
            return

        totals = self.get_totals_from_database()

        # ── No data yet: clear table silently and exit ────────────────────────
        if not totals:
            self.table.setRowCount(0)
            return

        # ── Extract values ────────────────────────────────────────────────────
        sendout_capital          = float(totals.get('total_sendout_capital')          or 0)
        sendout_commission       = float(totals.get('total_sendout_commission')       or 0)
        sendout_sc               = float(totals.get('total_sendout_sc')               or 0)
        payout_capital           = float(totals.get('total_payout_capital')           or 0)
        payout_commission        = float(totals.get('total_payout_commission')        or 0)
        payout_sc                = float(totals.get('total_payout_sc')                or 0)
        international_commission = float(totals.get('total_international_commission') or 0)
        total_skid               = float(totals.get('total_skid')                     or 0)
        total_skir               = float(totals.get('total_skir')                     or 0)
        total_cancellation       = float(totals.get('total_cancellation')             or 0)
        total_inc                = float(totals.get('total_inc')                      or 0)

        # ── Derived calculations ──────────────────────────────────────────────
        pepp_commission_61       = sendout_commission       * 0.61
        skid_61                  = total_skid               * 0.61
        ajpi_commission_43       = payout_commission        * 0.43
        ajpi_international_80    = international_commission * 0.80
        skir_57                  = total_skir               * 0.57

        send_subtotal                = sendout_capital + pepp_commission_61 + sendout_sc
        send_subtotal_after_discount = send_subtotal - skid_61
        total_net_send               = send_subtotal_after_discount - total_cancellation

        release_subtotal             = payout_capital + ajpi_commission_43 + ajpi_international_80
        release_subtotal_with_inc    = release_subtotal + total_inc
        total_net_released           = release_subtotal_with_inc + skir_57

        net_receivable_payable       = total_net_send - total_net_released

        registry = self.registry_input.text().strip() or "P210021A"

        # ── Build report rows ─────────────────────────────────────────────────
        report_data = [
            # Header
            ("Palawan Express Pera Padala - " + corp, "",  "",            "",                      "header"),
            ("PEPP Reconciliation for",               "",  "Partner Registry No.", "",             "header"),
            (selected_date,                           "",  registry,      "",                      "header"),
            ("", "", "", "", "blank"),
            ("", "", "", "", "blank"),

            # Send Transaction
            ("Send Transaction",                                           "", "",                          "",                              "section"),
            (f"    PEPP Remittance from {corp}",                           "", "P",                         f"{sendout_capital:,.2f}",        "indent"),
            ("    PEPP share: 61% of commission",                          "P", f"{sendout_commission:,.2f}", f"{pepp_commission_61:,.2f}",   "indent"),
            ("    PEPP share: Service Charge",                             "", f"{sendout_sc:,.2f}",         f"{sendout_sc:,.2f}",            "indent"),
            ("        Subtotal",                                           "", "",                          f"{send_subtotal:,.2f}",          "subtotal"),
            ("    Less: Discount (Suki Card)",                             "", f"({total_skid:,.2f})",       f"({skid_61:,.2f})",             "indent"),
            ("        Subtotal",                                           "", "",                          f"{send_subtotal_after_discount:,.2f}", "subtotal"),
            ("    Less: Cancellation",                                     "", f"({total_cancellation:,.2f})", f"({total_cancellation:,.2f})", "indent"),
            ("    Total Net Send",                                         "", "",                          f"{total_net_send:,.2f}",         "total"),
            ("", "", "", "", "blank"),
            ("", "", "", "", "blank"),

            # Release Transaction
            ("    RELEASE Transaction (Payable to AJPI)",                  "", "",                          "",                              "section"),
            ("    PEPP Remittances released at AJPI",                      "", "P",                         f"{payout_capital:,.2f}",         "indent"),
            ("    AJPI share: 43% of commission",                          "P", f"{payout_commission:,.2f}", f"{ajpi_commission_43:,.2f}",    "indent"),
            ("    AJPI share: 50% of commission (LBC Domestic Payout)",    "", "",                          "",                              "indent"),
            ("    AJPI share: 80% of commission (International Payout)",   "", f"{international_commission:,.2f}", f"{ajpi_international_80:,.2f}", "indent"),
            ("    Service Charge",                                         "", f"{payout_sc:,.2f}",          "-",                             "indent"),
            ("        Subtotal",                                           "", "",                          f"{release_subtotal:,.2f}",       "subtotal"),
            (f"    Add: AJPI Branch Incentives released on {selected_date}", "", "",                        f"{total_inc:,.2f}",              "indent"),
            ("        Subtotal",                                           "", "",                          f"{release_subtotal_with_inc:,.2f}", "subtotal"),
            ("    Add: Rebates (Suki Card)",                               "", f"{total_skir:,.2f}",         f"{skir_57:,.2f}",               "indent"),
            ("    Total Net Released",                                     "", "",                          f"{total_net_released:,.2f}",     "total"),
            ("", "", "", "", "blank"),
            ("", "", "", "", "blank"),

            # Summary
            ("    Net Send",                    "", "", f"{total_net_send:,.2f}",         "regular"),
            ("    Less : Net Released",         "", "", f"{total_net_released:,.2f}",     "regular"),
            ("    Net Receivable / (Payable)",  "", "", f"{net_receivable_payable:,.2f}", "total"),
        ]

        # ── Populate table ────────────────────────────────────────────────────
        self.table.setRowCount(len(report_data))

        bold_font    = QFont(); bold_font.setBold(True)
        regular_font = QFont()

        for row, (col1, col2, col3, col4, row_type) in enumerate(report_data):
            for col, text in enumerate([col1, col2, col3, col4]):
                item = QTableWidgetItem(text)

                # Font
                if row_type in ("header", "section", "total", "subtotal"):
                    item.setFont(bold_font)
                else:
                    item.setFont(regular_font)

                # Background
                if row_type == "total":
                    item.setBackground(QBrush(QColor("#f0f0f0")))
                elif row_type == "subtotal":
                    item.setBackground(QBrush(QColor("#f8f8f8")))

                # Alignment
                if col in (2, 3):
                    item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                else:
                    item.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)

                item.setFlags(item.flags() & ~Qt.ItemIsEditable)  # read-only
                self.table.setItem(row, col, item)

            self.table.setRowHeight(row, 25)

        # Center the title row
        title_item = self.table.item(0, 0)
        if title_item:
            title_item.setTextAlignment(Qt.AlignCenter)

    # ─────────────────────────────────────────────────────────────────────────

    def export_to_excel(self):
        if self.table.rowCount() == 0:
            QMessageBox.warning(self, "No Data", "No report to export. Select a corporation and date first.")
            return

        try:
            from openpyxl import Workbook
            from openpyxl.styles import Font, Alignment, PatternFill, Border, Side

            corp          = self.corp_selector.currentText()
            date          = self.date_selector.date().toString("yyyy-MM-dd")
            registry      = self.registry_input.text().strip() or "P210021A"

            totals = self.get_totals_from_database()
            if not totals:
                QMessageBox.warning(self, "No Data", "No data available for export.")
                return

            sendout_capital          = float(totals.get('total_sendout_capital')          or 0)
            sendout_commission       = float(totals.get('total_sendout_commission')       or 0)
            sendout_sc               = float(totals.get('total_sendout_sc')               or 0)
            payout_capital           = float(totals.get('total_payout_capital')           or 0)
            payout_commission        = float(totals.get('total_payout_commission')        or 0)
            payout_sc                = float(totals.get('total_payout_sc')                or 0)
            international_commission = float(totals.get('total_international_commission') or 0)
            total_skid               = float(totals.get('total_skid')                     or 0)
            total_skir               = float(totals.get('total_skir')                     or 0)
            total_cancellation       = float(totals.get('total_cancellation')             or 0)
            total_inc                = float(totals.get('total_inc')                      or 0)

            pepp_commission_61       = sendout_commission       * 0.61
            skid_61                  = total_skid               * 0.61
            ajpi_commission_43       = payout_commission        * 0.43
            ajpi_international_80    = international_commission * 0.80
            skir_57                  = total_skir               * 0.57

            send_subtotal                = sendout_capital + pepp_commission_61 + sendout_sc
            send_subtotal_after_discount = send_subtotal - skid_61
            total_net_send               = send_subtotal_after_discount - total_cancellation
            release_subtotal             = payout_capital + ajpi_commission_43 + ajpi_international_80
            release_subtotal_with_inc    = release_subtotal + total_inc
            total_net_released           = release_subtotal_with_inc + skir_57
            net_receivable_payable       = total_net_send - total_net_released

            wb = Workbook()
            ws = wb.active
            ws.title = "PEPP Reconciliation"

            header_font   = Font(bold=True, size=12)
            section_font  = Font(bold=True, size=11)
            regular_font  = Font(size=10)
            total_font    = Font(bold=True, size=11)
            header_fill   = PatternFill(start_color="E6F3FF", end_color="E6F3FF", fill_type="solid")
            subtotal_fill = PatternFill(start_color="F0F0F0", end_color="F0F0F0", fill_type="solid")
            total_fill    = PatternFill(start_color="D9D9D9", end_color="D9D9D9", fill_type="solid")
            right_align   = Alignment(horizontal='right')
            center_align  = Alignment(horizontal='center')

            r = 1
            ws.merge_cells(f'A{r}:D{r}')
            ws[f'A{r}'] = f"Palawan Express Pera Padala - {corp}"
            ws[f'A{r}'].font = header_font
            ws[f'A{r}'].alignment = center_align
            ws[f'A{r}'].fill = header_fill
            r += 1

            ws[f'A{r}'] = f"PEPP Reconciliation for {date}"
            ws[f'C{r}'] = "Partner Registry No."
            ws[f'D{r}'] = registry
            for cell in [ws[f'A{r}'], ws[f'C{r}'], ws[f'D{r}']]:
                cell.font = header_font
            r += 2

            rows = [
                ("Send Transaction",                                           "", "",                              "",                                   "section"),
                (f"    PEPP Remittance from {corp}",                           "", "P",                             f"{sendout_capital:,.2f}",             "indent"),
                ("    PEPP share: 61% of commission",                          "P", f"{sendout_commission:,.2f}",   f"{pepp_commission_61:,.2f}",          "indent"),
                ("    PEPP share: Service Charge",                             "", f"{sendout_sc:,.2f}",            f"{sendout_sc:,.2f}",                  "indent"),
                ("        Subtotal",                                           "", "",                              f"{send_subtotal:,.2f}",               "subtotal"),
                ("    Less: Discount (Suki Card)",                             "", f"({total_skid:,.2f})",          f"({skid_61:,.2f})",                   "indent"),
                ("        Subtotal",                                           "", "",                              f"{send_subtotal_after_discount:,.2f}","subtotal"),
                ("    Less: Cancellation",                                     "", f"({total_cancellation:,.2f})",  f"({total_cancellation:,.2f})",        "indent"),
                ("    Total Net Send",                                         "", "",                              f"{total_net_send:,.2f}",              "total"),
                ("", "", "", "", "blank"),
                ("    RELEASE Transaction (Payable to AJPI)",                  "", "",                              "",                                   "section"),
                ("    PEPP Remittances released at AJPI",                      "", "P",                             f"{payout_capital:,.2f}",              "indent"),
                ("    AJPI share: 43% of commission",                          "P", f"{payout_commission:,.2f}",    f"{ajpi_commission_43:,.2f}",          "indent"),
                ("    AJPI share: 50% of commission (LBC Domestic Payout)",    "", "",                              "",                                   "indent"),
                ("    AJPI share: 80% of commission (International Payout)",   "", f"{international_commission:,.2f}", f"{ajpi_international_80:,.2f}",   "indent"),
                ("    Service Charge",                                         "", f"{payout_sc:,.2f}",             "-",                                  "indent"),
                ("        Subtotal",                                           "", "",                              f"{release_subtotal:,.2f}",            "subtotal"),
                (f"    Add: AJPI Branch Incentives released on {date}",        "", "",                              f"{total_inc:,.2f}",                   "indent"),
                ("        Subtotal",                                           "", "",                              f"{release_subtotal_with_inc:,.2f}",   "subtotal"),
                ("    Add: Rebates (Suki Card)",                               "", f"{total_skir:,.2f}",            f"{skir_57:,.2f}",                    "indent"),
                ("    Total Net Released",                                     "", "",                              f"{total_net_released:,.2f}",          "total"),
                ("", "", "", "", "blank"),
                ("    Net Send",                   "", "", f"{total_net_send:,.2f}",         "regular"),
                ("    Less : Net Released",        "", "", f"{total_net_released:,.2f}",     "regular"),
                ("    Net Receivable / (Payable)", "", "", f"{net_receivable_payable:,.2f}", "total"),
            ]

            for col1, col2, col3, col4, row_type in rows:
                ws[f'A{r}'] = col1
                ws[f'B{r}'] = col2
                ws[f'C{r}'] = col3
                ws[f'D{r}'] = col4

                if row_type == "section":
                    for c in ['A','B','C','D']: ws[f'{c}{r}'].font = section_font
                elif row_type == "total":
                    for c in ['A','B','C','D']:
                        ws[f'{c}{r}'].font = total_font
                        ws[f'{c}{r}'].fill = total_fill
                elif row_type == "subtotal":
                    for c in ['A','B','C','D']:
                        ws[f'{c}{r}'].font = total_font
                        ws[f'{c}{r}'].fill = subtotal_fill
                else:
                    for c in ['A','B','C','D']: ws[f'{c}{r}'].font = regular_font

                ws[f'C{r}'].alignment = right_align
                ws[f'D{r}'].alignment = right_align
                r += 1

            # Signature
            r += 2
            ws[f'A{r}'] = "Prepared by:"
            ws[f'C{r}'] = "Noted by:"
            r += 2
            ws[f'A{r}'] = "Rochelle G. Serrano"
            ws[f'C{r}'] = "Aimee M. Martinez"

            ws.column_dimensions['A'].width = 50
            ws.column_dimensions['B'].width = 8
            ws.column_dimensions['C'].width = 15
            ws.column_dimensions['D'].width = 18

            ts       = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"PEPP_Reconciliation_{corp}_{date}_{ts}.xlsx"
            wb.save(filename)
            QMessageBox.information(self, "Export Successful", f"Saved as:\n{filename}")

        except ImportError:
            QMessageBox.critical(self, "Missing Library",
                                 "openpyxl is required.\nInstall with: pip install openpyxl")
        except Exception as e:
            QMessageBox.critical(self, "Export Error", f"Error exporting: {str(e)}")

    # ─────────────────────────────────────────────────────────────────────────

    def print_report(self):
        if self.table.rowCount() == 0:
            QMessageBox.warning(self, "No Data", "No report to print. Select a corporation and date first.")
            return

        try:
            doc  = QTextDocument()
            html = "<html><body style='font-family:Arial; font-size:12px;'>"

            for row in range(self.table.rowCount()):
                parts = []
                for col in range(4):
                    item = self.table.item(row, col)
                    if item and item.text().strip():
                        parts.append(item.text() if col == 0 else f"&nbsp;&nbsp;&nbsp;{item.text()}")

                line = "".join(parts)
                if line.strip():
                    bold = any(kw in line for kw in [
                        "Palawan Express", "PEPP Reconciliation", "Transaction",
                        "Total Net", "Net Receivable", "Subtotal",
                    ])
                    tag = "b" if bold else "span"
                    html += f"<p><{tag}>{line}</{tag}></p>"
                else:
                    html += "<p>&nbsp;</p>"

            html += "</body></html>"
            doc.setHtml(html)

            printer = QPrinter()
            dialog  = QPrintDialog(printer, self)
            if dialog.exec_() == QPrintDialog.Accepted:
                doc.print_(printer)
                QMessageBox.information(self, "Print Successful", "Report printed successfully!")

        except Exception as e:
            QMessageBox.critical(self, "Print Error", f"Error printing: {str(e)}")