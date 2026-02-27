"""
Daily Transaction Page
──────────────────────
Pulls data from daily_reports_brand_a.  Each branch is a row.
28 column-groups, most with Lotes + Capital sub-columns.
INSURANCE has four sub-columns (20s, 30s, 60s, 90s).
"""

from PyQt5.QtWidgets import (
    QWidget, QLabel, QVBoxLayout, QHBoxLayout, QComboBox, QTableWidget,
    QTableWidgetItem, QDateEdit, QMessageBox, QHeaderView, QSizePolicy,
    QPushButton, QScrollArea, QFrame, QFileDialog, QApplication
)
from PyQt5.QtCore import Qt, QDate, QTimer
from PyQt5.QtGui import QFont, QColor, QBrush, QPainter
from PyQt5.QtPrintSupport import QPrinter, QPrintDialog
from db_connect_pooled import db_manager
import datetime

# ═══════════════════════════════════════════════════════════════════════════
# Column definition: (header_group, sub_cols, db_expression_map)
#   sub_cols is a list of (sub_header, db_cols_to_sum, is_lotes)
# ═══════════════════════════════════════════════════════════════════════════
COLUMN_GROUPS = [
    ("JEWELRY", [
        ("Lotes", ["empeno_jew_new_lotes", "empeno_jew_renew_lotes"], True),
        ("Capital", ["empeno_jew_new", "empeno_jew_renew"], False),
    ]),
    ("STORAGE", [
        ("Lotes", ["empeno_sto_new_lotes", "fund_empeno_sto_renew_lotes"], True),
        ("Capital", ["empeno_sto_new", "fund_empeno_sto_renew"], False),
    ]),
    ("MOTOR/CAR", [
        ("Lotes", ["empeno_motor_car_lotes"], True),
        ("Capital", ["empeno_motor_car"], False),
    ]),
    ("MC", [
        ("Lotes", ["mc_out_lotes"], True),
        ("Capital", ["mc_out"], False),
    ]),
    ("SILVER", [
        ("Lotes", ["empeno_silver_lotes"], True),
        ("Capital", ["empeno_silver"], False),
    ]),
    ("PALAWAN", [
        ("Lotes", ["palawan_send_out_lotes", "palawan_sc_lotes",
                    "palawan_pay_out_lotes", "palawan_pay_out_incentives_lotes"], True),
        ("Capital", ["palawan_send_out", "palawan_sc",
                      "palawan_pay_out", "palawan_pay_out_incentives"], False),
    ]),
    ("INSURANCE", [
        ("20s", ["insurance_20"], False),
        ("30s", ["insurance_philam_30"], False),
        ("60s", ["insurance_philam_60"], False),
        ("90s", ["insurance_philam_90"], False),
    ]),
    ("O.S.F", [
        ("Lotes", ["osf_storage_lotes", "osf_silver_lotes", "osf_motor_lotes"], True),
        ("Capital", ["osf_storage", "osf_silver", "osf_motor"], False),
    ]),
    ("RESCATE JEW.", [
        ("Lotes", ["rescate_jewelry_lotes"], True),
        ("Capital", ["rescate_jewelry"], False),
    ]),
    ("RESCATE STO.", [
        ("Lotes", ["cr_storage_lotes", "rescate_silver_lotes",
                    "res_storage_lotes", "res_motor_lotes"], True),
        ("Capital", ["cr_storage", "rescate_silver", "res_storage", "res_motor"], False),
    ]),
    ("GCASH IN", [
        ("Lotes", ["gcash_in_lotes"], True),
        ("Capital", ["gcash_in"], False),
    ]),
    ("GCASH OUT", [
        ("Lotes", ["gcash_out_lotes"], True),
        ("Capital", ["gcash_out"], False),
    ]),
    ("MONEYGRAM", [
        ("Lotes", ["moneygram_lotes"], True),
        ("Capital", ["moneygram"], False),
    ]),
    ("TRANSFAST", [
        ("Lotes", ["transfast_lotes"], True),
        ("Capital", ["transfast"], False),
    ]),
    ("RIA", [
        ("Lotes", ["ria_in_sc_lotes"], True),
        ("Capital", ["ria_in_sc"], False),
    ]),
    ("I2I REM. IN", [
        ("Lotes", ["i2i_remittance_in_lotes"], True),
        ("Capital", ["i2i_remittance_in"], False),
    ]),
    ("I2I BILLS", [
        ("Lotes", ["i2i_bills_payment_lotes"], True),
        ("Capital", ["i2i_bills_payment"], False),
    ]),
    ("I2I INSTAPAY", [
        ("Lotes", ["i2i_instapay_lotes"], True),
        ("Capital", ["i2i_instapay"], False),
    ]),
    ("SENDAH LOAD", [
        ("Lotes", ["sendah_load_sc_lotes"], True),
        ("Capital", ["sendah_load_sc"], False),
    ]),
    ("SENDAH BILLS", [
        ("Lotes", ["sendah_bills_sc_lotes"], True),
        ("Capital", ["sendah_bills_sc"], False),
    ]),
    ("PAYMAYA", [
        ("Lotes", ["paymaya_in_lotes"], True),
        ("Capital", ["paymaya_in"], False),
    ]),
    ("SMART $ IN", [
        ("Lotes", ["smart_money_sc_lotes"], True),
        ("Capital", ["smart_money_sc"], False),
    ]),
    ("SMART $ OUT", [
        ("Lotes", ["smart_money_po_lotes"], True),
        ("Capital", ["smart_money_po"], False),
    ]),
    ("GCASH PADALA", [
        ("Lotes", ["gcash_padala_sendah_lotes"], True),
        ("Capital", ["gcash_padala_sendah"], False),
    ]),
    ("PAL PAY IN", [
        ("Lotes", ["palawan_pay_cash_in_sc_lotes"], True),
        ("Capital", ["palawan_pay_cash_in_sc"], False),
    ]),
    ("PAL PAY OUT", [
        ("Lotes", ["palawan_pay_cash_out_lotes"], True),
        ("Capital", ["palawan_pay_cash_out"], False),
    ]),
    ("REMITLY", [
        ("Lotes", ["remitly_lotes"], True),
        ("Capital", ["remitly"], False),
    ]),
]

# Build flat column list from group definitions  ───────────────────────────
def _build_columns():
    """Return (headers, col_meta) where col_meta is list of dicts with
    group, sub, db_cols, is_lotes for each flat column."""
    headers = ["Branch"]
    col_meta = []
    for group_name, subs in COLUMN_GROUPS:
        for sub_header, db_cols, is_lotes in subs:
            headers.append(f"{group_name}\n{sub_header}")
            col_meta.append({
                "group": group_name,
                "sub": sub_header,
                "db_cols": db_cols,
                "is_lotes": is_lotes,
            })
    return headers, col_meta

HEADERS, COL_META = _build_columns()

# Color palette for column groups  ─────────────────────────────────────────
GROUP_COLORS = {
    "JEWELRY":      QColor("#dc3545"),
    "STORAGE":      QColor("#e67e22"),
    "MOTOR/CAR":    QColor("#8e44ad"),
    "MC":           QColor("#2980b9"),
    "SILVER":       QColor("#7f8c8d"),
    "PALAWAN":      QColor("#28a745"),
    "INSURANCE":    QColor("#17a2b8"),
    "O.S.F":        QColor("#6f42c1"),
    "RESCATE JEW.": QColor("#c0392b"),
    "RESCATE STO.": QColor("#d35400"),
    "GCASH IN":     QColor("#16a085"),
    "GCASH OUT":    QColor("#1abc9c"),
    "MONEYGRAM":    QColor("#2c3e50"),
    "TRANSFAST":    QColor("#34495e"),
    "RIA":          QColor("#e74c3c"),
    "I2I REM. IN":  QColor("#3498db"),
    "I2I BILLS":    QColor("#2471a3"),
    "I2I INSTAPAY": QColor("#1a5276"),
    "SENDAH LOAD":  QColor("#f39c12"),
    "SENDAH BILLS": QColor("#d4ac0d"),
    "PAYMAYA":      QColor("#27ae60"),
    "SMART $ IN":   QColor("#0e6655"),
    "SMART $ OUT":  QColor("#117864"),
    "GCASH PADALA": QColor("#148f77"),
    "PAL PAY IN":   QColor("#1e8449"),
    "PAL PAY OUT":  QColor("#196f3d"),
    "REMITLY":      QColor("#7d3c98"),
}


class ColoredHeaderView(QHeaderView):
    """Custom header that paints each section with a per-group colour."""

    def __init__(self, orientation, parent=None):
        super().__init__(orientation, parent)
        self.colors = {}
        self.setFont(QFont("", 8, QFont.Bold))

    def paintSection(self, painter, rect, logicalIndex):
        painter.save()
        bg = self.colors.get(logicalIndex, QColor("#495057"))
        painter.fillRect(rect, bg)
        pen = painter.pen()
        pen.setColor(QColor("#333"))
        painter.setPen(pen)
        painter.drawRect(rect.adjusted(0, 0, -1, -1))
        painter.setPen(QColor("white"))
        painter.setFont(QFont("", 8, QFont.Bold))
        text = self.model().headerData(logicalIndex, self.orientation(), Qt.DisplayRole)
        painter.drawText(rect, Qt.AlignCenter | Qt.TextWordWrap, str(text) if text else "")
        painter.restore()


# ══════════════════════════════════════════════════════════════════════════
class DailyTransactionPage(QWidget):
    """Daily Transaction tab — Brand A data across 28 column categories."""

    def __init__(self):
        super().__init__()
        self._is_loading = False

        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(8)

        self._build_controls(layout)
        self._build_table(layout)
        self._build_buttons(layout)

        self.load_corporations()

    # ── Controls ──────────────────────────────────────────────────────────
    def _build_controls(self, parent):
        frame = QFrame()
        frame.setStyleSheet("""
            QFrame { background:#f8f9fa; border:1px solid #dee2e6;
                     border-radius:5px; padding:10px; }
        """)
        row = QHBoxLayout(frame)
        row.setSpacing(15)

        # Corporation
        row.addWidget(self._bold_label("Corporation:"))
        self.corp_selector = self._combo(220)
        self.corp_selector.currentTextChanged.connect(self.populate_table)
        row.addWidget(self.corp_selector)

        # Date
        row.addSpacing(20)
        row.addWidget(self._bold_label("Date:"))
        self.date_selector = QDateEdit(calendarPopup=True)
        self.date_selector.setDate(QDate.currentDate())
        self.date_selector.setDisplayFormat("yyyy-MM-dd")
        self.date_selector.setMinimumHeight(38)
        self.date_selector.setMinimumWidth(150)
        self.date_selector.dateChanged.connect(self.populate_table)
        self.date_selector.setStyleSheet(
            "QDateEdit{padding:8px;border:2px solid #dee2e6;border-radius:6px;"
            "background:white;font-size:13px;}"
            "QDateEdit:focus{border-color:#007bff;}"
        )
        row.addWidget(self.date_selector)

        # Branch Status
        row.addSpacing(20)
        row.addWidget(self._bold_label("Status:"))
        self.reg_filter_selector = self._combo(150)
        self.reg_filter_selector.addItem("Registered Only", "registered")
        self.reg_filter_selector.currentIndexChanged.connect(self.populate_table)
        row.addWidget(self.reg_filter_selector)

        # OS Filter
        row.addSpacing(20)
        row.addWidget(self._bold_label("OS Filter:"))
        self.os_filter_selector = self._combo(180)
        self.os_filter_selector.addItem("All (by Corporation)", None)
        self.os_filter_selector.currentIndexChanged.connect(self.populate_table)
        row.addWidget(self.os_filter_selector)

        row.addStretch()
        parent.addWidget(frame, 0)

    # ── Table ─────────────────────────────────────────────────────────────
    def _build_table(self, parent):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        self.table = QTableWidget()
        self.table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.table.setColumnCount(len(HEADERS))
        self.table.setHorizontalHeaderLabels(HEADERS)
        self.table.setMinimumHeight(300)
        self.table.verticalHeader().setDefaultSectionSize(32)
        self.table.setAlternatingRowColors(True)

        # Column widths
        self.table.setColumnWidth(0, 130)  # Branch
        for i in range(1, len(HEADERS)):
            self.table.setColumnWidth(i, 80)
        header = self.table.horizontalHeader()
        header.setStretchLastSection(False)
        for i in range(len(HEADERS)):
            header.setSectionResizeMode(i, QHeaderView.Interactive)
        header.setMinimumSectionSize(55)

        self._apply_header_colors()
        self._style_table()

        scroll.setWidget(self.table)
        parent.addWidget(scroll, 1)

    def _apply_header_colors(self):
        ch = ColoredHeaderView(Qt.Horizontal, self.table)
        ch.colors[0] = QColor("#495057")  # Branch
        col = 1
        for group_name, subs in COLUMN_GROUPS:
            base = GROUP_COLORS.get(group_name, QColor("#495057"))
            for _ in subs:
                ch.colors[col] = base
                col += 1
        ch.setDefaultAlignment(Qt.AlignCenter)
        ch.setMinimumSectionSize(55)
        ch.setDefaultSectionSize(80)
        self.table.setHorizontalHeader(ch)

    def _style_table(self):
        self.table.setStyleSheet("""
            QTableWidget {
                gridline-color:#d0d0d0; border:1px solid #c0c0c0;
                background-color:white; alternate-background-color:#f8f9fa;
                font-size:11px; selection-background-color:#e3f2fd;
            }
            QTableWidget::item { border:1px solid #e0e0e0; padding:4px; }
            QTableWidget::item:selected { background-color:#e3f2fd; color:black; }
            QHeaderView::section {
                padding:6px 2px; font-weight:bold; font-size:9px;
                border:1px solid #666; color:white;
            }
        """)

    # ── Buttons ───────────────────────────────────────────────────────────
    def _build_buttons(self, parent):
        frame = QFrame()
        frame.setFixedHeight(70)
        lay = QHBoxLayout(frame)

        def _btn(text, color1, color2, color3):
            b = QPushButton(text)
            b.setStyleSheet(f"""
                QPushButton{{padding:12px 24px;border:none;border-radius:8px;
                    background:{color1};color:white;font-weight:bold;font-size:12px;
                    min-width:130px;min-height:40px;}}
                QPushButton:hover{{background:{color2};}}
                QPushButton:pressed{{background:{color3};}}
            """)
            return b

        self.export_btn = _btn("📊 Export to Excel", "#217346", "#1a5c38", "#155724")
        self.export_btn.clicked.connect(self.export_to_excel)
        self.print_btn = _btn("🖨️ Print Report", "#6f42c1", "#5a2d91", "#4c1f75")
        self.print_btn.clicked.connect(self.print_table)

        lay.addStretch()
        lay.addWidget(self.export_btn)
        lay.addSpacing(15)
        lay.addWidget(self.print_btn)
        lay.addStretch()
        parent.addWidget(frame, 0)

    # ── Data ──────────────────────────────────────────────────────────────
    def load_corporations(self):
        self.corp_selector.blockSignals(True)
        self.corp_selector.clear()
        self.corp_selector.addItem("")  # All Corporations
        try:
            rows = db_manager.execute_query(
                "SELECT DISTINCT corporation FROM daily_reports_brand_a ORDER BY corporation"
            )
            for r in rows:
                self.corp_selector.addItem(r['corporation'])
        except Exception as e:
            print(f"Error loading corporations: {e}")
        finally:
            self.corp_selector.blockSignals(False)
        self._load_os_options()

    def _load_os_options(self):
        self.os_filter_selector.blockSignals(True)
        prev = self.os_filter_selector.currentData()
        self.os_filter_selector.clear()
        self.os_filter_selector.addItem("All (by Corporation)", None)
        try:
            rows = db_manager.execute_query(
                "SELECT DISTINCT os_name FROM branches "
                "WHERE os_name IS NOT NULL AND os_name != '' ORDER BY os_name"
            )
            if rows:
                for r in rows:
                    name = r['os_name'] if isinstance(r, dict) else r[0]
                    self.os_filter_selector.addItem(name, name)
            if prev:
                idx = self.os_filter_selector.findData(prev)
                if idx >= 0:
                    self.os_filter_selector.setCurrentIndex(idx)
        except Exception as e:
            print(f"Error loading OS options: {e}")
        finally:
            self.os_filter_selector.blockSignals(False)

    # ── Populate ──────────────────────────────────────────────────────────
    def populate_table(self):
        self._is_loading = True
        self.table.setRowCount(0)

        corp = self.corp_selector.currentText().strip()
        selected_date = self.date_selector.date().toString("yyyy-MM-dd")
        os_filter = self.os_filter_selector.currentData()
        reg_value = self.reg_filter_selector.currentData()

        if not corp and not os_filter:
            self._is_loading = False
            return

        # Build SELECT: gather all db columns we need
        needed_cols = set()
        for _, subs in COLUMN_GROUPS:
            for _, db_cols, _ in subs:
                needed_cols.update(db_cols)

        # Build COALESCE expressions
        select_parts = ["b.name AS branch"]
        for col in sorted(needed_cols):
            select_parts.append(f"COALESCE(dr.`{col}`, 0) AS `{col}`")

        where_parts = ["dr.date = %s"]
        params = [selected_date]

        if corp:
            where_parts.append("dr.corporation = %s")
            params.append(corp)
        if os_filter:
            where_parts.append("b.os_name = %s")
            params.append(os_filter)

        # Registration filter
        if reg_value == "registered":
            where_parts.append("b.is_registered = 1")
        elif reg_value == "not_registered":
            where_parts.append("(b.is_registered = 0 OR b.is_registered IS NULL)")

        sql = (
            f"SELECT {', '.join(select_parts)} "
            f"FROM daily_reports_brand_a dr "
            f"INNER JOIN branches b ON dr.branch COLLATE utf8mb4_general_ci = b.name COLLATE utf8mb4_general_ci "
            f"WHERE {' AND '.join(where_parts)} "
            f"ORDER BY b.name"
        )

        try:
            rows = db_manager.execute_query(sql, tuple(params))
        except Exception as e:
            QMessageBox.critical(self, "Query Error", str(e))
            self._is_loading = False
            return

        if not rows:
            self._is_loading = False
            return

        col_count = len(HEADERS)
        totals = [0.0] * col_count

        for row_data in rows:
            r = self.table.rowCount()
            self.table.insertRow(r)

            # Branch
            branch_item = QTableWidgetItem(row_data['branch'])
            branch_item.setFlags(branch_item.flags() & ~Qt.ItemIsEditable)
            branch_item.setFont(QFont("", 10, QFont.Bold))
            self.table.setItem(r, 0, branch_item)

            # Data columns
            for ci, meta in enumerate(COL_META, start=1):
                val = sum(float(row_data.get(c, 0) or 0) for c in meta['db_cols'])
                if meta['is_lotes']:
                    val = int(val)
                    txt = str(val)
                else:
                    txt = f"{val:,.2f}"
                item = QTableWidgetItem(txt)
                item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                self.table.setItem(r, ci, item)
                totals[ci] += val

        # Totals row
        r = self.table.rowCount()
        self.table.insertRow(r)
        total_label = QTableWidgetItem("TOTAL")
        total_label.setFont(QFont("", 10, QFont.Bold))
        total_label.setData(Qt.BackgroundRole, QBrush(QColor("#343a40")))
        total_label.setData(Qt.ForegroundRole, QBrush(QColor("#050505")))
        total_label.setFlags(total_label.flags() & ~Qt.ItemIsEditable)
        self.table.setItem(r, 0, total_label)

        for ci, meta in enumerate(COL_META, start=1):
            v = totals[ci]
            if meta['is_lotes']:
                txt = str(int(v))
            else:
                txt = f"{v:,.2f}"
            item = QTableWidgetItem(txt)
            item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            item.setFont(QFont("", 10, QFont.Bold))
            item.setData(Qt.BackgroundRole, QBrush(QColor("#343a40")))
            item.setData(Qt.ForegroundRole, QBrush(QColor("#050505")))
            item.setFlags(item.flags() & ~Qt.ItemIsEditable)
            self.table.setItem(r, ci, item)

        self._is_loading = False

    # ── Export ────────────────────────────────────────────────────────────
    def export_to_excel(self):
        try:
            from openpyxl import Workbook
            from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
        except ImportError:
            QMessageBox.warning(self, "Missing Package", "Install openpyxl:\npip install openpyxl")
            return

        if self.table.rowCount() == 0:
            QMessageBox.warning(self, "No Data", "Please load data first.")
            return

        path, _ = QFileDialog.getSaveFileName(
            self, "Save Excel", f"Daily_Transaction_{self.date_selector.date().toString('yyyy-MM-dd')}.xlsx",
            "Excel Files (*.xlsx)"
        )
        if not path:
            return

        wb = Workbook()
        ws = wb.active
        ws.title = "Daily Transaction"

        header_font = Font(bold=True, color="FFFFFF", size=9)
        header_fill = PatternFill("solid", fgColor="495057")
        thin = Side(style='thin')
        border = Border(left=thin, right=thin, top=thin, bottom=thin)

        # ── Report Header (Title, Date, OS) ───────────────────────────────
        title_font = Font(bold=True, size=14)
        info_font = Font(bold=True, size=11)
        
        # Row 1: Title "Daily Transaction"
        ws.cell(row=1, column=1, value="Daily Transaction").font = title_font
        
        # Row 2: Date
        selected_date = self.date_selector.date().toString("yyyy-MM-dd")
        ws.cell(row=2, column=1, value=f"Date: {selected_date}").font = info_font
        
        # Row 3: OS Name
        os_name = self.os_filter_selector.currentText() or "All"
        ws.cell(row=3, column=1, value=f"OS: {os_name}").font = info_font
        
        # Row 4: Empty row for spacing
        header_row = 5  # Column headers start at row 5

        # Column Headers
        for c in range(self.table.columnCount()):
            text = self.table.horizontalHeaderItem(c).text().replace("\n", " ")
            cell = ws.cell(row=header_row, column=c + 1, value=text)
            cell.font = header_font
            cell.fill = header_fill
            cell.border = border
            cell.alignment = Alignment(horizontal='center', wrap_text=True)

        # Data
        for r in range(self.table.rowCount()):
            for c in range(self.table.columnCount()):
                item = self.table.item(r, c)
                val = item.text() if item else ""
                # Try to write as number
                try:
                    num = float(val.replace(",", ""))
                    cell = ws.cell(row=r + header_row + 1, column=c + 1, value=num)
                    cell.number_format = '#,##0.00' if '.' in val else '#,##0'
                except ValueError:
                    cell = ws.cell(row=r + header_row + 1, column=c + 1, value=val)
                cell.border = border

        # Auto-width (cap at 18)
        for col_cells in ws.columns:
            max_len = max((len(str(c.value or "")) for c in col_cells), default=8)
            ws.column_dimensions[col_cells[0].column_letter].width = min(max_len + 2, 18)

        wb.save(path)
        QMessageBox.information(self, "Export Successful", f"Saved to:\n{path}")

    # ── Print ─────────────────────────────────────────────────────────────
    def print_table(self):
        if self.table.rowCount() == 0:
            QMessageBox.warning(self, "No Data", "Please load data first.")
            return
        printer = QPrinter(QPrinter.HighResolution)
        printer.setOrientation(QPrinter.Landscape)
        dlg = QPrintDialog(printer, self)
        if dlg.exec_() != QPrintDialog.Accepted:
            return

        painter = QPainter(printer)
        try:
            page = printer.pageRect()
            cols = self.table.columnCount()
            rows = self.table.rowCount()
            col_w = page.width() / max(cols, 1)
            row_h = 300
            y = 0
            # Header
            painter.setFont(QFont("Arial", 6, QFont.Bold))
            for c in range(cols):
                text = self.table.horizontalHeaderItem(c).text().replace("\n", " ")
                painter.drawText(int(c * col_w), y, int(col_w), row_h,
                                 Qt.AlignCenter | Qt.TextWordWrap, text)
            y += row_h
            # Data
            painter.setFont(QFont("Arial", 5))
            for r in range(rows):
                if y + row_h > page.height():
                    printer.newPage()
                    y = 0
                for c in range(cols):
                    item = self.table.item(r, c)
                    painter.drawText(int(c * col_w), y, int(col_w), row_h,
                                     Qt.AlignCenter, item.text() if item else "")
                y += row_h
        finally:
            painter.end()

    # ── Helpers ───────────────────────────────────────────────────────────
    @staticmethod
    def _bold_label(text):
        lbl = QLabel(text)
        lbl.setFont(QFont("Arial", 11, QFont.Bold))
        return lbl

    @staticmethod
    def _combo(min_w=160):
        cb = QComboBox()
        cb.setMinimumWidth(min_w)
        cb.setMinimumHeight(38)
        cb.setStyleSheet(
            "QComboBox{padding:8px;border:2px solid #dee2e6;border-radius:6px;"
            "background:white;font-size:13px;}"
            "QComboBox:focus{border-color:#007bff;}"
            "QComboBox::drop-down{width:28px;}"
        )
        return cb
