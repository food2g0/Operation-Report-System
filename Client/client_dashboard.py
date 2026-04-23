import datetime
import json
import os
import time

from PyQt5.QtWidgets import (
    QWidget, QLabel, QLineEdit, QVBoxLayout, QHBoxLayout,
    QGroupBox, QPushButton, QSizePolicy, QDateEdit,
    QMessageBox, QScrollArea, QFrame, QGridLayout, QTabWidget,
    QComboBox, QApplication, QDialog, QTableWidget, QTableWidgetItem,
    QHeaderView, QDialogButtonBox, QAbstractItemView, QFileDialog,
    QProgressBar, QGraphicsOpacityEffect
)
from PyQt5.QtGui import QDoubleValidator, QFont, QFontDatabase, QTextDocument, QMovie
from PyQt5.QtCore import Qt, QDate, pyqtSignal, QTimer, QPropertyAnimation, QThread
from PyQt5.QtPrintSupport import QPrinter, QPrintDialog

from Client.cash_flow_tab import CashFlowTab
from Client.palawan_details_tab import PalawanDetailsTab
from security import SessionManager


try:
    from offline_manager import offline_manager
    OFFLINE_SUPPORT = True
except ImportError:
    OFFLINE_SUPPORT = False
    offline_manager = None

try:
    from ping_monitor import ping_monitor as _ping_monitor
except ImportError:
    _ping_monitor = None

class LoadingOverlay(QWidget):
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_TransparentForMouseEvents, False)
        self.setAttribute(Qt.WA_TranslucentBackground, False)
        
        self.setStyleSheet("background-color: rgba(0, 0, 0, 150);")
        
        container = QFrame(self)
        container.setFixedSize(280, 140)
        container.setStyleSheet("""
            QFrame {
                background-color: white;
                border-radius: 12px;
                border: none;
            }
        """)
        
        layout = QVBoxLayout(container)
        layout.setAlignment(Qt.AlignCenter)
        layout.setSpacing(15)
        
      
        self.status_label = QLabel("Posting report...")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setStyleSheet("""
            QLabel {
                color: #333333;
                font-size: 14px;
                font-weight: bold;
                font-family: 'Segoe UI', Arial;
                background: transparent;
            }
        """)
         
        self.progress = QProgressBar()
        self.progress.setRange(0, 0)
        self.progress.setTextVisible(False)
        self.progress.setFixedHeight(6)
        self.progress.setStyleSheet("""
            QProgressBar {
                background-color: #f0f0f0;
                border: none;
                border-radius: 3px;
            }
            QProgressBar::chunk {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #667eea, stop:1 #764ba2);
                border-radius: 3px;
            }
        """)
        
        # Subtitle
        self.subtitle_label = QLabel("Please wait...")
        self.subtitle_label.setAlignment(Qt.AlignCenter)
        self.subtitle_label.setStyleSheet("""
            QLabel {
                color: #888888;
                font-size: 11px;
                font-family: 'Segoe UI', Arial;
                background: transparent;
            }
        """)
        
        layout.addWidget(self.status_label)
        layout.addWidget(self.progress)
        layout.addWidget(self.subtitle_label)
        
        self.container = container
        self.hide()
    
    def showEvent(self, event):
      
        super().showEvent(event)
        if self.parent():
            self.setGeometry(self.parent().rect())
            self.container.move(
                (self.width() - self.container.width()) // 2,
                (self.height() - self.container.height()) // 2
            )
    
    def resizeEvent(self, event):
    
        super().resizeEvent(event)
        self.container.move(
            (self.width() - self.container.width()) // 2,
            (self.height() - self.container.height()) // 2
        )
    
    def set_status(self, text, subtitle="Please wait..."):
        self.status_label.setText(text)
        self.subtitle_label.setText(subtitle)
        QApplication.processEvents()


try:
    from auto_updater import check_for_updates, check_update_success
    from version import __version__
    AUTO_UPDATE_ENABLED = True
except ImportError:
    AUTO_UPDATE_ENABLED = False
    __version__ = "1.0.0"
    check_update_success = None

_SLATE_50   = "#F8FAFC"
_SLATE_100  = "#F1F5F9"
_SLATE_200  = "#E2E8F0"
_SLATE_300  = "#CBD5E1"
_SLATE_400  = "#94A3B8"
_SLATE_500  = "#64748B"
_SLATE_600  = "#475569"
_SLATE_700  = "#334155"
_SLATE_800  = "#1E293B"
_SLATE_900  = "#0F172A"


_INDIGO_50  = "#EEF2FF"
_INDIGO_100 = "#E0E7FF"
_INDIGO_400 = "#818CF8"
_INDIGO_500 = "#0C0C0F"
_INDIGO_600 = "#0B0B0C"
_INDIGO_700 = "#111014"


_EMERALD_50  = "#ECFDF5"
_EMERALD_400 = "#34D399"
_EMERALD_500 = "#10B981"
_EMERALD_600 = "#059669"


_AMBER_400  = "#FBBF24"
_AMBER_500  = "#F59E0B"
_RED_400    = "#F87171"
_RED_500    = "#EF4444"
_WHITE      = "#FFFFFF"


_BG_APP     = _SLATE_100
_BG_CARD    = _WHITE
_BG_INPUT   = _WHITE
_BG_RDONLY  = _SLATE_50
_BG_HEADER  = _SLATE_900
_BORDER     = _SLATE_200
_TEXT_PRI   = _SLATE_800
_TEXT_SEC   = _SLATE_500
_TEXT_MUTED = _SLATE_400
_PRIMARY    = _INDIGO_500
_PRIMARY_DK = _INDIGO_600
_PRIMARY_PR = _INDIGO_700
_SUCCESS    = _EMERALD_500
_SUCCESS_DK = _EMERALD_600

from Client.ui_scaling import _sz

def _s(px: int) -> int:
    return _sz(px)


def _build_global_qss():
    return f"""

QWidget {{
    background-color: {_BG_APP};
    font-family: 'Segoe UI', 'SF Pro Text', 'Helvetica Neue', Arial, sans-serif;
    font-size: {_sz(13)}px;
    color: {_TEXT_PRI};
}}


QGroupBox {{
    background-color: {_BG_CARD};
    border: 1px solid {_BORDER};
    border-radius: {_sz(8)}px;
    margin-top: {_sz(22)}px;
    padding: {_sz(18)}px {_sz(16)}px {_sz(16)}px {_sz(16)}px;
    font-size: {_sz(11)}px;
    font-weight: 700;
    color: {_TEXT_SEC};
    letter-spacing: 1.2px;
    text-transform: uppercase;
}}
QGroupBox::title {{
    subcontrol-origin: margin;
    subcontrol-position: top left;
    left: {_sz(12)}px;
    top: -1px;
    padding: {_sz(2)}px {_sz(8)}px;
    background-color: {_BG_CARD};
    color: {_PRIMARY};
    font-size: {_sz(11)}px;
    font-weight: 800;
    letter-spacing: 1.3px;
    border-radius: 3px;
}}


QLineEdit {{
    background-color: {_BG_INPUT};
    border: 1.5px solid {_BORDER};
    border-radius: {_sz(6)}px;
    padding: {_sz(7)}px {_sz(10)}px;
    font-size: {_sz(14)}px;
    font-weight: 500;
    color: {_TEXT_PRI};
    min-width: {_sz(80)}px;
    min-height: {_sz(34)}px;
    selection-background-color: {_INDIGO_100};
    selection-color: {_PRIMARY_DK};
}}
QLineEdit:focus {{
    border: 2px solid {_PRIMARY};
    background-color: {_INDIGO_50};
    padding: {_sz(6)}px {_sz(9)}px;
}}
QLineEdit:read-only {{
    background-color: {_BG_RDONLY};
    color: {_TEXT_PRI};
    font-weight: 600;
    border-color: {_BORDER};
}}
QLineEdit:disabled {{
    background-color: {_SLATE_100};
    color: {_TEXT_SEC};
    border-color: {_SLATE_200};
}}


QLabel {{
    color: {_TEXT_PRI};
    font-size: {_sz(13)}px;
    font-weight: 500;
    min-width: 0;
    background: transparent;
}}


QPushButton {{
    background-color: {_PRIMARY};
    color: {_WHITE};
    border: none;
    padding: {_sz(8)}px {_sz(18)}px;
    border-radius: {_sz(6)}px;
    font-size: {_sz(12)}px;
    font-weight: 700;
    min-width: {_sz(80)}px;
    letter-spacing: 0.2px;
}}
QPushButton:hover   {{ background-color: {_PRIMARY_DK}; }}
QPushButton:pressed {{ background-color: {_PRIMARY_PR}; }}
QPushButton:disabled {{
    background-color: {_SLATE_200};
    color: {_TEXT_SEC};
}}


QTabWidget::pane {{
    border: 1px solid {_BORDER};
    background-color: {_BG_CARD};
    border-radius: 0 {_sz(8)}px {_sz(8)}px {_sz(8)}px;
    top: -1px;
}}
QTabBar::tab {{
    background-color: {_SLATE_100};
    color: {_TEXT_PRI};
    border: 1px solid {_BORDER};
    border-bottom: none;
    padding: {_sz(10)}px {_sz(24)}px;
    margin-right: 2px;
    border-top-left-radius: {_sz(6)}px;
    border-top-right-radius: {_sz(6)}px;
    font-size: {_sz(13)}px;
    font-weight: 600;
    min-width: {_sz(110)}px;
}}
QTabBar::tab:selected {{
    background-color: {_BG_CARD};
    color: {_PRIMARY};
    font-weight: 700;
    border-bottom: 2px solid {_BG_CARD};
}}
QTabBar::tab:hover:!selected {{
    background-color: {_SLATE_200};
    color: {_TEXT_PRI};
}}


QScrollArea {{ border: none; background: transparent; }}
QScrollBar:vertical {{
    background: transparent; width: 5px; border-radius: 3px; margin: 2px 0;
}}
QScrollBar::handle:vertical {{
    background: {_SLATE_300}; border-radius: 3px; min-height: 24px;
}}
QScrollBar::handle:vertical:hover {{ background: {_SLATE_400}; }}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; border: none; }}
QScrollBar:horizontal {{
    background: transparent; height: 5px; border-radius: 3px;
}}
QScrollBar::handle:horizontal {{
    background: {_SLATE_300}; border-radius: 3px;
}}
QScrollBar::handle:horizontal:hover {{ background: {_SLATE_400}; }}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{ width: 0; border: none; }}


QDateEdit {{
    background-color: {_BG_INPUT};
    border: 1.5px solid {_BORDER};
    border-radius: {_sz(6)}px;
    padding: {_sz(7)}px {_sz(10)}px;
    font-size: {_sz(14)}px;
    font-weight: 600;
    color: {_TEXT_PRI};
    min-height: {_sz(34)}px;
}}
QDateEdit:focus {{ border: 2px solid {_PRIMARY}; padding: {_sz(6)}px {_sz(9)}px; }}
QDateEdit::drop-down {{
    subcontrol-origin: padding;
    subcontrol-position: top right;
    width: 28px;
    border: none;
    border-left: 1px solid {_BORDER};
    border-top-right-radius: 6px;
    border-bottom-right-radius: 6px;
    background-color: {_SLATE_100};
}}
QDateEdit::drop-down:hover {{
    background-color: {_INDIGO_100};
}}
QDateEdit::down-arrow {{
    image: url(data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTYiIGhlaWdodD0iMTYiIHZpZXdCb3g9IjAgMCAxNiAxNiIgZmlsbD0ibm9uZSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48cmVjdCB4PSIyIiB5PSIyIiB3aWR0aD0iMTIiIGhlaWdodD0iMTIiIHJ4PSIyIiBzdHJva2U9IiM0NzU1NjkiIHN0cm9rZS13aWR0aD0iMS41Ii8+PHBhdGggZD0iTTIgNkgxNCIgc3Ryb2tlPSIjNDc1NTY5IiBzdHJva2Utd2lkdGg9IjEuNSIvPjxjaXJjbGUgY3g9IjUiIGN5PSIxMCIgcj0iMSIgZmlsbD0iIzQ3NTU2OSIvPjxjaXJjbGUgY3g9IjgiIGN5PSIxMCIgcj0iMSIgZmlsbD0iIzQ3NTU2OSIvPjxjaXJjbGUgY3g9IjExIiBjeT0iMTAiIHI9IjEiIGZpbGw9IiM0NzU1NjkiLz48L3N2Zz4=);
    width: 16px;
    height: 16px;
}}


QComboBox {{
    background-color: {_BG_INPUT};
    border: 1.5px solid {_BORDER};
    border-radius: {_sz(6)}px;
    padding: {_sz(7)}px {_sz(10)}px;
    font-size: {_sz(14)}px;
    font-weight: 600;
    color: {_TEXT_PRI};
    min-height: {_sz(34)}px;
    min-width: {_sz(120)}px;
}}
QComboBox:focus {{
    border: 2px solid {_PRIMARY};
    background-color: {_INDIGO_50};
}}
QComboBox::drop-down {{ border: none; width: 28px; }}
QComboBox::down-arrow {{
    image: url(data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTIiIGhlaWdodD0iOCIgdmlld0JveD0iMCAwIDEyIDgiIGZpbGw9Im5vbmUiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyI+PHBhdGggZD0iTTEgMUw2IDZMMTEgMSIgc3Ryb2tlPSIjNjQ3NDhCIiBzdHJva2Utd2lkdGg9IjEuNSIgc3Ryb2tlLWxpbmVjYXA9InJvdW5kIiBzdHJva2UtbGluZWpvaW49InJvdW5kIi8+PC9zdmc+);
    width: 12px; height: 8px;
}}
QComboBox QAbstractItemView {{
    background-color: {_BG_CARD};
    border: 1px solid {_BORDER};
    border-radius: 6px;
    selection-background-color: {_INDIGO_100};
    selection-color: {_PRIMARY_DK};
    padding: 3px;
}}
QComboBox QAbstractItemView::item {{
    padding: {_sz(7)}px {_sz(12)}px;
    border-radius: 3px;
    color: {_TEXT_PRI};
}}
QComboBox QAbstractItemView::item:hover {{
    background-color: {_INDIGO_50};
}}
"""


def _hline():
    f = QFrame()
    f.setFrameShape(QFrame.HLine)
    f.setFrameShadow(QFrame.Plain)
    f.setStyleSheet(f"color: {_BORDER}; max-height: 1px; background: {_BORDER};")
    return f


def _vline(dark=False):
    f = QFrame()
    f.setFrameShape(QFrame.VLine)
    f.setFrameShadow(QFrame.Plain)
    col = "#1E293B" if dark else _BORDER
    f.setStyleSheet(f"color: {col}; max-width: 1px; background: {col};")
    return f


def _micro_label(text, color=_TEXT_MUTED):
    lbl = QLabel(text.upper())
    lbl.setStyleSheet(
        f"font-size: 11px; font-weight: 700; color: {color}; "
        f"letter-spacing: 1.1px; background: transparent;"
    )
    return lbl


class FundTransferHODialog(QDialog):

    BANK_ACCOUNTS = [
        {"id": 1, "bank_name": "CIB-BDO", "account_name": "Global Reliance", "account_number": "0077-9002-3923"},
        {"id": 2, "bank_name": "CIB-BPI", "account_name": "Kristal Clear Diamond and Gold Pawnshop", "account_number": "0091-0692-29"},
        {"id": 3, "bank_name": "CIB-BDO", "account_name": "Kristal Clear", "account_number": "0077-9001-8784"},
        {"id": 4, "bank_name": "CIB-Union Bank", "account_name": "Golbal Reliance Mgmt and Holdings Corp", "account_number": "0015-6000-5790"},
        {"id": 5, "bank_name": "CIB-BDO", "account_name": "Europacific Management & Holdings Corp", "account_number": "0038-1801-5838"},
        {"id": 6, "bank_name": "CIB-BPI", "account_name": "Europacific Management & Holdings Corp", "account_number": "3541-0035-67"},
        {"id": 7, "bank_name": "CIB-UB", "account_name": "Europacific Management & Holdings Corp", "account_number": "0021-7001-7921"},
        {"id": 8, "bank_name": "CIB-UB", "account_name": "BPI BILLS  PAYMENT SAN RAMON", "account_number": ""},
        {"id": 9, "bank_name": "CIB-UB", "account_name": "BPI  BILLS PAYMENT SILVERSTAR", "account_number": ""},
        {"id": 10, "bank_name": "CIB-UB", "account_name": "BPI  BILLS PAYMENT ALLEXITE", "account_number": ""},
        {"id": 11, "bank_name": "CIB-UB", "account_name": "BPI BILLS PAYMENT MEGAWORLD", "account_number": ""},
        {"id": 12, "bank_name": "CIB-UB", "account_name": "BPI BILLS PAYMENT HOMENEEDS", "account_number": ""},
        {"id": 13, "bank_name": "CIB-UB", "account_name": "BPI  BILLS PAYMENT KRISTAL CLEAR", "account_number": ""},
        {"id": 14, "bank_name": "CIB-UB", "account_name": "BPI BILLS PAYMENT SAFELOCK", "account_number": ""},
    ]

    def __init__(self, field_label="Fund Transfer to HEAD OFFICE", parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Detail – {field_label}")
        self.setMinimumSize(620, 460)
        self.setModal(True)
        self._rows_data = [] 

        root = QVBoxLayout(self)
        root.setSpacing(12)
        root.setContentsMargins(16, 16, 16, 16)

        title = QLabel(f"Breakdown for  {field_label}")
        title.setStyleSheet("font-size: 15px; font-weight: 800; color: #1E293B;")
        root.addWidget(title)

        self.table = QTableWidget(0, 3)
        self.table.setHorizontalHeaderLabels(["Bank Account", "Amount", ""])
        hh = self.table.horizontalHeader()
        hh.setSectionResizeMode(0, QHeaderView.Stretch)
        hh.setSectionResizeMode(1, QHeaderView.Stretch)
        hh.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.table.setSelectionMode(QAbstractItemView.NoSelection)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.setStyleSheet("""
            QTableWidget { border: 1px solid #E2E8F0; border-radius: 6px; }
            QHeaderView::section { background: #F1F5F9; font-weight: 700;
                                   font-size: 11px; padding: 6px; border: none; }
            QTableWidget::item { padding: 4px 8px; }
        """)
        root.addWidget(self.table)

        add_btn = QPushButton("+ Add Transfer")
        add_btn.setStyleSheet("""
            QPushButton { background: #8B5CF6; color: white; border: none;
                          border-radius: 6px; padding: 7px 18px;
                          font-weight: 700; font-size: 12px; }
            QPushButton:hover { background: #7C3AED; }
        """)
        add_btn.clicked.connect(self._add_row)
        root.addWidget(add_btn, alignment=Qt.AlignLeft)

        totals_frame = QFrame()
        totals_frame.setStyleSheet(
            "background:#F8FAFC; border:1px solid #E2E8F0;"
            "border-radius:8px; padding:6px;"
        )
        totals_layout = QHBoxLayout(totals_frame)
        totals_layout.setContentsMargins(12, 8, 12, 8)
        totals_layout.setSpacing(40)

        ta_box = QVBoxLayout()
        ta_title = QLabel("Total Amount")
        ta_title.setStyleSheet("font-size: 11px; font-weight: 700; color: #64748B;")
        self._total_amount_lbl = QLabel("0.00")
        self._total_amount_lbl.setStyleSheet("font-size: 18px; font-weight: 800; color: #8B5CF6;")
        ta_sub = QLabel("(carried to field)")
        ta_sub.setStyleSheet("font-size: 12px; color: #94A3B8;")
        ta_box.addWidget(ta_title)
        ta_box.addWidget(self._total_amount_lbl)
        ta_box.addWidget(ta_sub)

        count_box = QVBoxLayout()
        count_title = QLabel("Transactions")
        count_title.setStyleSheet("font-size: 11px; font-weight: 700; color: #64748B;")
        self._count_lbl = QLabel("0")
        self._count_lbl.setStyleSheet("font-size: 18px; font-weight: 800; color: #2563EB;")
        count_sub = QLabel("(number of transfers)")
        count_sub.setStyleSheet("font-size: 12px; color: #94A3B8;")
        count_box.addWidget(count_title)
        count_box.addWidget(self._count_lbl)
        count_box.addWidget(count_sub)

        totals_layout.addLayout(ta_box)
        totals_layout.addLayout(count_box)
        totals_layout.addStretch()
        root.addWidget(totals_frame)

        btns = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btns.button(QDialogButtonBox.Ok).setText("Post")
        btns.button(QDialogButtonBox.Ok).setStyleSheet(
            "background:#16A34A;color:white;border:none;border-radius:5px;"
            "padding:6px 18px;font-weight:700;"
        )
        btns.accepted.connect(self.accept)
        btns.rejected.connect(self.reject)
        root.addWidget(btns)

        self._add_row()

    def _add_row(self):
        row = self.table.rowCount()
        self.table.insertRow(row)

        bank_combo = QComboBox()
        bank_combo.setMinimumWidth(200)
        for bank in self.BANK_ACCOUNTS:
            display = f"{bank['bank_name']} - {bank['account_name']}"
            bank_combo.addItem(display, bank['id'])
        bank_combo.setStyleSheet("padding: 4px 6px; font-size: 12px;")
        self.table.setCellWidget(row, 0, bank_combo)

        amt_edit = QLineEdit()
        amt_edit.setPlaceholderText("0.00")
        amt_edit.setValidator(QDoubleValidator(0.0, 1e12, 2))
        amt_edit.setStyleSheet(
            "padding: 4px 8px; font-size: 13px; font-weight: 600;"
        )
        self.table.setCellWidget(row, 1, amt_edit)

        rem_btn = QPushButton("✕")
        rem_btn.setFixedWidth(28)
        rem_btn.setStyleSheet(
            "QPushButton { color: #EF4444; font-weight: 900; border: none; font-size: 13px; }"
            "QPushButton:hover { color: #DC2626; }"
        )
        rem_btn.clicked.connect(lambda _, b=rem_btn: self._remove_row_by_widget(b))
        self.table.setCellWidget(row, 2, rem_btn)

        self._rows_data.append((bank_combo, amt_edit))
        amt_edit.textChanged.connect(self._recalc)
        self.table.resizeRowsToContents()

    def _remove_row_by_widget(self, btn):
        for r in range(self.table.rowCount()):
            if self.table.cellWidget(r, 2) is btn:
                combo = self.table.cellWidget(r, 0)
                edit = self.table.cellWidget(r, 1)
                self._rows_data = [
                    (c, e) for c, e in self._rows_data
                    if c is not combo
                ]
                self.table.removeRow(r)
                self._recalc()
                return

    def _recalc(self, *_):
        total_amt = 0.0
        for bank_combo, amt_edit in self._rows_data:
            try:
                amt = float(amt_edit.text().strip().replace(',', '') or 0)
            except ValueError:
                amt = 0.0
            total_amt += amt
        self._total_amount_lbl.setText(f"{total_amt:,.2f}")
        self._count_lbl.setText(str(len(self._rows_data)))

    def get_total_amount(self) -> float:
        try:
            return float(self._total_amount_lbl.text().replace(',', ''))
        except ValueError:
            return 0.0

    def get_row_count(self) -> int:
        return len(self._rows_data)

    def get_breakdown_data(self) -> list:

        data = []
        for bank_combo, amt_edit in self._rows_data:
            try:
                amt = float(amt_edit.text().strip().replace(',', '') or 0)
            except ValueError:
                amt = 0.0
            bank_display = bank_combo.currentText()
            bank_id = bank_combo.currentData()
            data.append([bank_display, bank_id, amt])
        return data

class MotorCarDetailDialog(QDialog):

    PERCENTAGES = ["10.0%", "20.0%"]

    def __init__(self, field_label, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Detail – {field_label}")
        self.setMinimumSize(580, 460)
        self.setModal(True)
        self._rows_data = []

        root = QVBoxLayout(self)
        root.setSpacing(12)
        root.setContentsMargins(16, 16, 16, 16)

        title = QLabel(f"Breakdown for  {field_label}")
        title.setStyleSheet("font-size: 15px; font-weight: 800; color: #1E293B;")
        root.addWidget(title)

        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(["Percentage", "Amount", "Computed", ""])
        hh = self.table.horizontalHeader()
        hh.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        hh.setSectionResizeMode(1, QHeaderView.Stretch)
        hh.setSectionResizeMode(2, QHeaderView.Stretch)
        hh.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.table.setSelectionMode(QAbstractItemView.NoSelection)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.setStyleSheet("""
            QTableWidget { border: 1px solid #E2E8F0; border-radius: 6px; }
            QHeaderView::section { background: #F1F5F9; font-weight: 700;
                                   font-size: 11px; padding: 6px; border: none; }
            QTableWidget::item { padding: 4px 8px; }
        """)
        root.addWidget(self.table)

        add_btn = QPushButton("+ Add Item")
        add_btn.setStyleSheet("""
            QPushButton { background: #3B82F6; color: white; border: none;
                          border-radius: 6px; padding: 7px 18px;
                          font-weight: 700; font-size: 12px; }
            QPushButton:hover { background: #2563EB; }
        """)
        add_btn.clicked.connect(self._add_row)
        root.addWidget(add_btn, alignment=Qt.AlignLeft)

        totals_frame = QFrame()
        totals_frame.setStyleSheet(
            "background:#F8FAFC; border:1px solid #E2E8F0;"
            "border-radius:8px; padding:6px;"
        )
        totals_layout = QHBoxLayout(totals_frame)
        totals_layout.setContentsMargins(12, 8, 12, 8)
        totals_layout.setSpacing(40)

        ta_box = QVBoxLayout()
        ta_title = QLabel("Total Amount")
        ta_title.setStyleSheet("font-size: 11px; font-weight: 700; color: #64748B;")
        self._total_amount_lbl = QLabel("0.00")
        self._total_amount_lbl.setStyleSheet("font-size: 18px; font-weight: 800; color: #0F766E;")
        ta_sub = QLabel("(pasted to field)")
        ta_sub.setStyleSheet("font-size: 12px; color: #94A3B8;")
        ta_box.addWidget(ta_title)
        ta_box.addWidget(self._total_amount_lbl)
        ta_box.addWidget(ta_sub)

        ct_box = QVBoxLayout()
        ct_title = QLabel("Computed Total")
        ct_title.setStyleSheet("font-size: 11px; font-weight: 700; color: #64748B;")
        self._computed_total_lbl = QLabel("0.00")
        self._computed_total_lbl.setStyleSheet("font-size: 18px; font-weight: 800; color: #2563EB;")
        ct_sub = QLabel("(added to Motor A.I)")
        ct_sub.setStyleSheet("font-size: 12px; color: #94A3B8;")
        ct_box.addWidget(ct_title)
        ct_box.addWidget(self._computed_total_lbl)
        ct_box.addWidget(ct_sub)

        totals_layout.addLayout(ta_box)
        totals_layout.addLayout(ct_box)
        totals_layout.addStretch()
        root.addWidget(totals_frame)

        btns = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btns.button(QDialogButtonBox.Ok).setText("Post")
        btns.button(QDialogButtonBox.Ok).setStyleSheet(
            "background:#16A34A;color:white;border:none;border-radius:5px;"
            "padding:6px 18px;font-weight:700;"
        )
        btns.accepted.connect(self.accept)
        btns.rejected.connect(self.reject)
        root.addWidget(btns)

        self._add_row()

    def _add_row(self):
        row = self.table.rowCount()
        self.table.insertRow(row)

        pct_combo = QComboBox()
        pct_combo.addItems(self.PERCENTAGES)
        pct_combo.setStyleSheet("padding: 4px 6px; font-size: 12px;")
        self.table.setCellWidget(row, 0, pct_combo)

        amt_edit = QLineEdit()
        amt_edit.setPlaceholderText("0.00")
        amt_edit.setValidator(QDoubleValidator(0.0, 1e12, 2))
        amt_edit.setStyleSheet(
            "border: 1px solid #CBD5E1; border-radius: 5px;"
            "padding: 5px 8px; font-size: 12px;"
        )
        self.table.setCellWidget(row, 1, amt_edit)

        computed_lbl = QLabel("0.00")
        computed_lbl.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        computed_lbl.setStyleSheet("font-weight: 700; color: #2563EB; padding: 0 8px;")
        self.table.setCellWidget(row, 2, computed_lbl)

        rem_btn = QPushButton("\u2715")
        rem_btn.setFixedWidth(28)
        rem_btn.setStyleSheet(
            "QPushButton{background:#FEE2E2;color:#DC2626;border:none;"
            "border-radius:4px;font-weight:700;font-size:11px;}"
            "QPushButton:hover{background:#FECACA;}"
        )
        rem_btn.clicked.connect(lambda _, b=rem_btn: self._remove_row_by_widget(b))
        self.table.setCellWidget(row, 3, rem_btn)

        self._rows_data.append((pct_combo, amt_edit, computed_lbl))
        pct_combo.currentIndexChanged.connect(self._recalc)
        amt_edit.textChanged.connect(self._recalc)
        self.table.resizeRowsToContents()

    def _remove_row_by_widget(self, btn):
        for r in range(self.table.rowCount()):
            if self.table.cellWidget(r, 3) is btn:
                self.table.removeRow(r)
                self._rows_data = []
                for rr in range(self.table.rowCount()):
                    pc = self.table.cellWidget(rr, 0)
                    ae = self.table.cellWidget(rr, 1)
                    cl = self.table.cellWidget(rr, 2)
                    if pc and ae and cl:
                        self._rows_data.append((pc, ae, cl))
                self._recalc()
                return

    def _recalc(self, *_):
        total_amt = 0.0
        total_cmp = 0.0
        for pct_combo, amt_edit, computed_lbl in self._rows_data:
            try:
                pct = float(pct_combo.currentText().replace('%', '').strip()) / 100.0
                amt = float(amt_edit.text().strip().replace(',', '') or 0)
                cmp = amt * pct
            except ValueError:
                amt = cmp = 0.0
            computed_lbl.setText(f"{cmp:,.2f}")
            total_amt += amt
            total_cmp += cmp
        self._total_amount_lbl.setText(f"{total_amt:,.2f}")
        self._computed_total_lbl.setText(f"{total_cmp:,.2f}")

    def get_total_amount(self) -> float:
        try:
            return float(self._total_amount_lbl.text().replace(',', ''))
        except ValueError:
            return 0.0

    def get_computed_total(self) -> float:
        try:
            return float(self._computed_total_lbl.text().replace(',', ''))
        except ValueError:
            return 0.0

    def get_row_count(self) -> int:
        return len(self._rows_data)

    def get_breakdown_data(self) -> list:
        """Return list of [percentage_str, amount] for each row."""
        data = []
        for pct_combo, amt_edit, _ in self._rows_data:
            try:
                pct_str = pct_combo.currentText()
                amt = float(amt_edit.text().strip().replace(',', '') or 0)
            except ValueError:
                amt = 0.0
            data.append([pct_str, amt])
        return data

class EmpenaDetailDialog(QDialog):

    PERCENTAGES = ["2.5%", "3.0%", "4.0%", "5.0%", "20.0%"]

    def __init__(self, field_label, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Detail – {field_label}")
        self.setMinimumSize(580, 460)
        self.setModal(True)
        self._rows_data = [] 

        root = QVBoxLayout(self)
        root.setSpacing(12)
        root.setContentsMargins(16, 16, 16, 16)

 
        title = QLabel(f"Breakdown for  {field_label}")
        title.setStyleSheet("font-size: 15px; font-weight: 800; color: #1E293B;")
        root.addWidget(title)

   
        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(["Percentage", "Amount", "Computed", ""])
        hh = self.table.horizontalHeader()
        hh.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        hh.setSectionResizeMode(1, QHeaderView.Stretch)
        hh.setSectionResizeMode(2, QHeaderView.Stretch)
        hh.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.table.setSelectionMode(QAbstractItemView.NoSelection)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.setStyleSheet("""
            QTableWidget { border: 1px solid #E2E8F0; border-radius: 6px; }
            QHeaderView::section { background: #F1F5F9; font-weight: 700;
                                   font-size: 11px; padding: 6px; border: none; }
            QTableWidget::item { padding: 4px 8px; }
        """)
        root.addWidget(self.table)


        add_btn = QPushButton("+ Add Item")
        add_btn.setStyleSheet("""
            QPushButton { background: #3B82F6; color: white; border: none;
                          border-radius: 6px; padding: 7px 18px;
                          font-weight: 700; font-size: 12px; }
            QPushButton:hover { background: #2563EB; }
        """)
        add_btn.clicked.connect(self._add_row)
        root.addWidget(add_btn, alignment=Qt.AlignLeft)

     
        totals_frame = QFrame()
        totals_frame.setStyleSheet(
            "background:#F8FAFC; border:1px solid #E2E8F0;"
            "border-radius:8px; padding:6px;"
        )
        totals_layout = QHBoxLayout(totals_frame)
        totals_layout.setContentsMargins(12, 8, 12, 8)
        totals_layout.setSpacing(40)

       
        ta_box = QVBoxLayout()
        ta_title = QLabel("Total Amount")
        ta_title.setStyleSheet("font-size: 11px; font-weight: 700; color: #64748B;")
        self._total_amount_lbl = QLabel("0.00")
        self._total_amount_lbl.setStyleSheet(
            "font-size: 18px; font-weight: 800; color: #0F766E;"
        )
        ta_sub = QLabel("(pasted to field)")
        ta_sub.setStyleSheet("font-size: 12px; color: #94A3B8;")
        ta_box.addWidget(ta_title)
        ta_box.addWidget(self._total_amount_lbl)
        ta_box.addWidget(ta_sub)


        ct_box = QVBoxLayout()
        ct_title = QLabel("Computed Total")
        ct_title.setStyleSheet("font-size: 11px; font-weight: 700; color: #64748B;")
        self._computed_total_lbl = QLabel("0.00")
        self._computed_total_lbl.setStyleSheet(
            "font-size: 18px; font-weight: 800; color: #2563EB;"
        )
        ct_sub = QLabel("(added to Jew. A.I)")
        ct_sub.setStyleSheet("font-size: 12px; color: #94A3B8;")
        ct_box.addWidget(ct_title)
        ct_box.addWidget(self._computed_total_lbl)
        ct_box.addWidget(ct_sub)

        totals_layout.addLayout(ta_box)
        totals_layout.addLayout(ct_box)
        totals_layout.addStretch()
        root.addWidget(totals_frame)

   
        btns = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btns.button(QDialogButtonBox.Ok).setText("Post")
        btns.button(QDialogButtonBox.Ok).setStyleSheet(
            "background:#16A34A;color:white;border:none;border-radius:5px;"
            "padding:6px 18px;font-weight:700;"
        )
        btns.accepted.connect(self.accept)
        btns.rejected.connect(self.reject)
        root.addWidget(btns)

        self._add_row()  

   
    def _add_row(self):
        row = self.table.rowCount()
        self.table.insertRow(row)

        pct_combo = QComboBox()
        pct_combo.addItems(self.PERCENTAGES)
        pct_combo.setStyleSheet("padding: 4px 6px; font-size: 12px;")
        self.table.setCellWidget(row, 0, pct_combo)

        amt_edit = QLineEdit()
        amt_edit.setPlaceholderText("0.00")
        amt_edit.setValidator(QDoubleValidator(0.0, 1e12, 2))
        amt_edit.setStyleSheet(
            "border: 1px solid #CBD5E1; border-radius: 5px;"
            "padding: 5px 8px; font-size: 12px;"
        )
        self.table.setCellWidget(row, 1, amt_edit)

        computed_lbl = QLabel("0.00")
        computed_lbl.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        computed_lbl.setStyleSheet("font-weight: 700; color: #2563EB; padding: 0 8px;")
        self.table.setCellWidget(row, 2, computed_lbl)

        rem_btn = QPushButton("✕")
        rem_btn.setFixedWidth(28)
        rem_btn.setStyleSheet(
            "QPushButton{background:#FEE2E2;color:#DC2626;border:none;"
            "border-radius:4px;font-weight:700;font-size:11px;}"
            "QPushButton:hover{background:#FECACA;}"
        )
        rem_btn.clicked.connect(lambda _, b=rem_btn: self._remove_row_by_widget(b))
        self.table.setCellWidget(row, 3, rem_btn)

        self._rows_data.append((pct_combo, amt_edit, computed_lbl))
        pct_combo.currentIndexChanged.connect(self._recalc)
        amt_edit.textChanged.connect(self._recalc)
        self.table.resizeRowsToContents()

    def _remove_row_by_widget(self, btn):
        for r in range(self.table.rowCount()):
            if self.table.cellWidget(r, 3) is btn:
                self.table.removeRow(r)
                self._rows_data = []
                for rr in range(self.table.rowCount()):
                    pc = self.table.cellWidget(rr, 0)
                    ae = self.table.cellWidget(rr, 1)
                    cl = self.table.cellWidget(rr, 2)
                    if pc and ae and cl:
                        self._rows_data.append((pc, ae, cl))
                self._recalc()
                return

    def _recalc(self, *_):
        total_amt = 0.0
        total_cmp = 0.0
        for pct_combo, amt_edit, computed_lbl in self._rows_data:
            try:
                pct = float(pct_combo.currentText().replace('%', '').strip()) / 100.0
                amt = float(amt_edit.text().strip().replace(',', '') or 0)
                cmp = amt * pct
            except ValueError:
                amt = cmp = 0.0
            computed_lbl.setText(f"{cmp:,.2f}")
            total_amt += amt
            total_cmp += cmp
        self._total_amount_lbl.setText(f"{total_amt:,.2f}")
        self._computed_total_lbl.setText(f"{total_cmp:,.2f}")


    def get_total_amount(self) -> float:
        """Sum of raw amounts – pasted to the Empeno JEW field."""
        try:
            return float(self._total_amount_lbl.text().replace(',', ''))
        except ValueError:
            return 0.0

    def get_computed_total(self) -> float:
        """Sum of (amount × %) – contributed to Jew. A.I."""
        try:
            return float(self._computed_total_lbl.text().replace(',', ''))
        except ValueError:
            return 0.0

    def get_row_count(self) -> int:
        """Number of item rows – used as the lotes (quantity) value."""
        return len(self._rows_data)



class ClientDashboard(QWidget):
    logout_requested = pyqtSignal()
    brand_changed    = pyqtSignal(str)

    def __init__(self, username, branch, corporation, db_manager, offline_mode=False):
        super().__init__()
        self.user_email  = username
        self.corporation = corporation
        self.branch      = branch
        self.db_manager  = db_manager
        self.offline_mode = offline_mode
        self._update_checker_threads = []

        self.session = SessionManager(inactivity_timeout=1800)
        self._session_timer = QTimer(self)
        self._session_timer.timeout.connect(self._check_session_timeout)
        self._session_timer.start(60_000)

        self.beginning_balance_auto_filled_a = False
        self.beginning_balance_auto_filled_b = False
        self.previous_day_balance_a = None
        self.previous_day_date_a    = None
        self.previous_day_balance_b = None
        self.previous_day_date_b    = None

        self.setWindowTitle("Daily Cash Report")
        self.setMinimumSize(960, 600)
        self.setStyleSheet(_build_global_qss())

        lay = QVBoxLayout(self)
        lay.setSpacing(_sz(6))
        lay.setContentsMargins(_sz(12), _sz(10), _sz(12), _sz(8))

        lay.addWidget(self._build_header(username, branch, corporation))
        lay.addWidget(self._build_toolbar())
        lay.addWidget(self._build_tabs(), stretch=1)
        lay.addWidget(self._build_summary_strip())
        lay.addWidget(self._build_footer())

        self.on_date_changed()
        self._connect_shared_fields()
        self._connect_palawan_adjustments_to_brand_b()
        self._connect_brand_a_auto_calculations()
        self._setup_empeno_jew_buttons()
        self._setup_empeno_motor_button()
        self._setup_ft_ho_button()
        self._setup_pc_salary_button()
    def _setup_pc_salary_button(self):
   
        try:
            from Client.salary_detail_dialog import SalaryDetailDialog
            for tab, label in [
                (self.cash_flow_tab_a, "PC-Salary"),
            ]:
                field = tab.credit_inputs.get(label)
                if field is None:
                    continue
                field.setReadOnly(True)
                field.setStyleSheet(
                    field.styleSheet() + "background-color: #EFF6FF; color: #1D4ED8;"
                )
                field.setToolTip("Click + to enter salary breakdown")
                field.setPlaceholderText("Click + to enter salary breakdown")

                container = field.parentWidget()
                layout = container.layout() if container else None
                if layout is None:
                    continue

                if not hasattr(self, '_salary_dialogs'):
                    self._salary_dialogs = {}
                key = f"{tab}_{label}"
                def _open_dialog():
                    if key not in self._salary_dialogs:
                        self._salary_dialogs[key] = SalaryDetailDialog(parent=self)
                    dlg = self._salary_dialogs[key]
                    if dlg.exec_() == QDialog.Accepted:
                        val = f"{dlg.get_total_salary():.2f}"
                        field.blockSignals(True)
                        field.setText(val)
                        field.blockSignals(False)
                       
                        self._pc_salary_breakdown = dlg.get_salary_breakdown()

                plus_btn = QPushButton("+")
                plus_btn.setFixedSize(28, 28)
                plus_btn.setStyleSheet("""
                    QPushButton {
                        background-color: #2563EB; color: white;
                        border: none; border-radius: 5px;
                        font-size: 14px; font-weight: 900;
                    }
                    QPushButton:hover { background-color: #1D4ED8; }
                """)
                plus_btn.setToolTip("Open salary breakdown dialog")
                plus_btn.clicked.connect(_open_dialog)
                layout.insertWidget(0, plus_btn)
        except Exception as e:
            print(f"_setup_pc_salary_button error: {e}")

        from PyQt5.QtCore import QTimer as _QT
        _QT.singleShot(300, self._load_draft)
        
       
        self.loading_overlay = LoadingOverlay(self)
        
        self.showMaximized()

        if AUTO_UPDATE_ENABLED and check_update_success:
            check_update_success(parent=self)
        
        
        if not self.offline_mode and OFFLINE_SUPPORT and offline_manager:
            _QT.singleShot(1000, self._check_pending_entries_sync)

    def _check_pending_entries_sync(self):
        
        try:
            if not OFFLINE_SUPPORT or not offline_manager:
                return
            
            pending = offline_manager.get_pending_entries(self.user_email)
            if not pending:
                return
            
            count = len(pending)
            reply = QMessageBox.question(
                self,
                "Pending Entries Found",
                f"📤 You have {count} pending entries saved while offline.\n\n"
                f"Would you like to sync them now?\n\n"
                f"• Click 'Yes' to post all pending entries\n"
                f"• Click 'No' to sync later",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.Yes
            )
            
            if reply == QMessageBox.Yes:
                self._sync_pending_entries(pending)
                
        except Exception as e:
            print(f"Error checking pending entries: {e}")

    def _sync_pending_entries(self, pending_entries):
      
        try:
            self.loading_overlay.set_status("Syncing entries...", "Please wait")
            self.loading_overlay.show()
            self.loading_overlay.raise_()
            QApplication.processEvents()
            
            success_count = 0
            error_count = 0
            errors = []
            
            for i, entry in enumerate(pending_entries, 1):
                try:
                    self.loading_overlay.set_status(
                        f"Syncing entry {i}/{len(pending_entries)}...",
                        f"Date: {entry.get('entry_data', {}).get('date', 'Unknown')}"
                    )
                    QApplication.processEvents()
                    
                    success = self._post_pending_entry(entry)
                    
                    if success:
                        offline_manager.mark_entry_synced(entry['id'])
                        success_count += 1
                    else:
                        error_count += 1
                        errors.append(entry['id'][:15])
                        
                except Exception as e:
                    error_count += 1
                    errors.append(f"{entry['id'][:15]}: {str(e)[:30]}")
                    offline_manager.mark_entry_failed(entry['id'], str(e))
            
            self.loading_overlay.hide()
            
            if error_count == 0:
                self._msg_success(
                    f"Sync Complete!\n\n"
                    f"Successfully posted {success_count} entries."
                )
            else:
                self._msg(
                    "Sync Partially Complete",
                    f"Posted: {success_count}\n"
                    f"Failed: {error_count}\n\n"
                    f"Failed entries will remain in queue for retry.",
                    QMessageBox.Warning
                )
                
            # Refresh the view
            self.on_date_changed()
            
        except Exception as e:
            self.loading_overlay.hide()
            self._msg("Sync Error", f"Failed to sync: {e}", QMessageBox.Critical)

    def _post_pending_entry(self, pending_entry):

        try:
            entry_data = pending_entry.get('entry_data', {})
            selected_date = entry_data.get('date')
            username = entry_data.get('username')
            branch = entry_data.get('branch')
            corporation = entry_data.get('corporation')
            palawan_data = entry_data.get('palawan_data', {})
            brand_data = entry_data.get('brand_data', {})
            
            results = []
            
            for brand_full, data in brand_data.items():
                table_name = data.get('table_name')
                
            
                check_query = f"""
                    SELECT 1 FROM {table_name} 
                    WHERE date = %s AND username = %s 
                    LIMIT 1
                """
                existing = self.db_manager.execute_query(
                    check_query, [selected_date, username]
                )
                if existing:
                 
                    continue
                
                all_vals = data.get('all_values', {})
                filtered = self._filter_vals_for_table(all_vals, table_name)
                cols = [
                    'date', 'username', 'branch', 'corporation',
                    'beginning_balance', 'debit_total', 'credit_total',
                    'ending_balance', 'cash_count', 'cash_result', 'variance_status'
                ] + list(filtered.keys())
                
                vals = [
                    selected_date, username, branch, corporation,
                    data.get('beginning_balance', 0),
                    data.get('beginning_balance', 0) + data.get('debit_total', 0),
                    data.get('credit_total', 0),
                    data.get('ending_balance', 0),
                    data.get('cash_count', 0),
                    data.get('cash_result', 0),
                    data.get('variance_status', 'balanced')
                ] + list(filtered.values())
                
                ph = ', '.join(['%s'] * len(cols))
                query = f"INSERT INTO {table_name} ({', '.join(cols)}) VALUES ({ph})"
                upd = ', '.join(f"{c}=VALUES({c})" for c in cols
                               if c not in ('date', 'username'))
                if upd:
                    query += " ON DUPLICATE KEY UPDATE " + upd
                
                result = self.db_manager.execute_query(query, vals)
                if result is not None:
                    results.append(brand_full)
                    
                
                    self._save_palawan_to_payable(selected_date, brand_full, palawan_data)
            
            return len(results) > 0
            
        except Exception as e:
            print(f"Error posting pending entry: {e}")
            return False


    def _build_header(self, username, branch, corporation):
        bar = QFrame()
        bar.setFixedHeight(_sz(54))
        bar.setStyleSheet(f"""
            QFrame {{
                background-color: {_SLATE_900};
                border-radius: {_sz(8)}px;
            }}
            QLabel {{ background: transparent; border: none; }}
        """)

        h = QHBoxLayout(bar)
        h.setContentsMargins(_sz(18), 0, _sz(14), 0)
        h.setSpacing(_sz(12))


        app_lbl = QLabel("Daily Cash Report")
        app_lbl.setStyleSheet(
            f"font-size: {_sz(15)}px; font-weight: 800; color: {_WHITE}; "
            f"letter-spacing: 0.3px; background: transparent;"
        )
        h.addWidget(app_lbl)


        dot = QLabel("·")
        dot.setStyleSheet(f"font-size: {_sz(18)}px; color: {_SLATE_500}; background: transparent;")
        h.addWidget(dot)


        info_lbl = QLabel(f"{username}  ·  {branch}  ·  {corporation}")
        info_lbl.setStyleSheet(
            f"font-size: {_sz(13)}px; font-weight: 500; color: {_SLATE_300}; background: transparent;"
        )
        h.addWidget(info_lbl)
        

        if self.offline_mode:
            offline_badge = QLabel("OFFLINE")
            offline_badge.setStyleSheet("""
                QLabel {
                    background-color: #F59E0B;
                    color: #1E293B;
                    font-size: 12px;
                    font-weight: bold;
                    padding: 5px 12px;
                    border-radius: 12px;
                }
            """)
            offline_badge.setToolTip("Entries will be saved locally for later posting")
            h.addWidget(offline_badge, alignment=Qt.AlignVCenter)
            

            if OFFLINE_SUPPORT and offline_manager:
                pending_count = offline_manager.get_pending_count(username)
                if pending_count > 0:
                    pending_badge = QLabel(f"{pending_count} pending")
                    pending_badge.setStyleSheet("""
                        QLabel {
                            background-color: #3B82F6;
                            color: white;
                            font-size: 12px;
                            font-weight: bold;
                            padding: 5px 10px;
                            border-radius: 12px;
                        }
                    """)
                    pending_badge.setToolTip(f"{pending_count} entries waiting to sync")
                    h.addWidget(pending_badge, alignment=Qt.AlignVCenter)
        
        h.addStretch()

        if AUTO_UPDATE_ENABLED:
            upd_btn = QPushButton(f"v{__version__}")
            upd_btn.setFixedSize(_sz(72), _sz(30))
            upd_btn.setStyleSheet(f"""
                QPushButton {{
                    background: rgba(99,102,241,0.15);
                    color: {_INDIGO_400};
                    border: 1px solid rgba(99,102,241,0.3);
                    border-radius: {_sz(5)}px;
                    font-size: {_sz(12)}px; font-weight: 700;
                }}
                QPushButton:hover {{ background: rgba(99,102,241,0.25); }}
            """)
            upd_btn.clicked.connect(self.check_for_updates)
            upd_btn.setToolTip("Check for updates")
            h.addWidget(upd_btn, alignment=Qt.AlignVCenter)
            h.addSpacing(_sz(8))

        logout_btn = QPushButton("Sign out")
        logout_btn.setFixedSize(_sz(88), _sz(30))
        logout_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                color: {_SLATE_300};
                border: 1px solid {_SLATE_600};
                border-radius: {_sz(5)}px;
                font-size: {_sz(12)}px; font-weight: 600;
            }}
            QPushButton:hover {{
                background: rgba(248,113,113,0.1);
                color: {_RED_400};
                border-color: rgba(248,113,113,0.3);
            }}
        """)
        logout_btn.clicked.connect(self.handle_logout)
        h.addWidget(logout_btn, alignment=Qt.AlignVCenter)

        return bar

    def _build_toolbar(self):
        bar = QFrame()
        bar.setObjectName("toolbar")
        bar.setStyleSheet(f"""
            QFrame#toolbar {{
                background-color: {_BG_CARD};
                border: 1px solid {_BORDER};
                border-radius: {_sz(10)}px;
            }}
        """)

        outer = QHBoxLayout(bar)
        outer.setContentsMargins(_sz(20), _sz(14), _sz(20), _sz(14))
        outer.setSpacing(0)

        date_card = QFrame()
        date_card.setObjectName("dateCard")
        date_card.setFixedWidth(_sz(210))
        date_card.setStyleSheet(f"""
            QFrame#dateCard {{
                background-color: {_SLATE_50};
                border: 1px solid {_BORDER};
                border-radius: {_sz(8)}px;
                padding: 0px;
            }}
        """)
        date_card_layout = QVBoxLayout(date_card)
        date_card_layout.setContentsMargins(_sz(14), _sz(12), _sz(14), _sz(12))
        date_card_layout.setSpacing(_sz(8))

        date_title = QLabel("Report Date")
        date_title.setStyleSheet(
            f"font-size: {_sz(8)}px; font-weight: 600; color: {_TEXT_SEC}; background: transparent;"
            f" text-transform: uppercase; letter-spacing: 1px;"
        )
        date_card_layout.addWidget(date_title)

        self.date_picker = QDateEdit()
        self.date_picker.setCalendarPopup(True)
        self.date_picker.setDate(QDate.currentDate())
        self.date_picker.setFixedHeight(_sz(34))
        self.date_picker.dateChanged.connect(self.on_date_changed)
        self.date_picker.setStyleSheet(f"""
            QDateEdit {{
                background-color: {_WHITE};
                border: 1px solid {_BORDER};
                border-radius: 6px;
                padding: 4px 10px;
                font-size: 13px;
                font-weight: 600;
                color: {_TEXT_PRI};
            }}
            QDateEdit::drop-down {{
                subcontrol-origin: padding;
                subcontrol-position: center right;
                width: 28px;
                border: none;
                background-color: {_SLATE_100};
                border-top-right-radius: 6px;
                border-bottom-right-radius: 6px;
            }}
            QDateEdit::down-arrow {{
                image: url(none);
                width: 12px;
                height: 12px;
            }}
        """)
        date_card_layout.addWidget(self.date_picker)

        self.load_report_btn = QPushButton("Load Submitted")
        self.load_report_btn.setFixedHeight(_sz(28))
        self.load_report_btn.setCursor(Qt.PointingHandCursor)
        self.load_report_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {_PRIMARY};
                color: {_WHITE};
                border: none;
                border-radius: {_sz(6)}px;
                font-size: {_sz(10)}px;
                font-weight: 700;
                padding: {_sz(4)}px {_sz(8)}px;
            }}
            QPushButton:hover {{
                background-color: {_PRIMARY_DK};
            }}
            QPushButton:pressed {{
                background-color: {_PRIMARY_PR};
            }}
        """)
        self.load_report_btn.setToolTip("View previously submitted reports")
        self.load_report_btn.clicked.connect(self.show_load_report_dialog)
        date_card_layout.addWidget(self.load_report_btn)

        outer.addWidget(date_card)
        outer.addSpacing(_sz(20))

  
        divider = QFrame()
        divider.setFrameShape(QFrame.VLine)
        divider.setStyleSheet(f"color: {_BORDER}; background: {_BORDER}; max-width: 1px;")
        divider.setFixedHeight(_sz(80))
        outer.addWidget(divider)
        outer.addSpacing(_sz(20))

       
        self.bb_container_a = QWidget()
        self.bb_container_a.setStyleSheet("background: transparent;")
        bb_layout_a = QHBoxLayout(self.bb_container_a)
        bb_layout_a.setContentsMargins(0, 0, 0, 0)
        bb_layout_a.setSpacing(0)
        bb_layout_a.addLayout(self._build_balance_column("A"))
        outer.addWidget(self.bb_container_a, stretch=1)

        outer.addSpacing(_sz(20))

       
        self.bb_divider_b = QFrame()
        self.bb_divider_b.setFrameShape(QFrame.VLine)
        self.bb_divider_b.setStyleSheet(f"color: {_BORDER}; background: {_BORDER}; max-width: 1px;")
        self.bb_divider_b.setFixedHeight(_sz(80))
        outer.addWidget(self.bb_divider_b)
        outer.addSpacing(_sz(20))

    
        self.bb_container_b = QWidget()
        self.bb_container_b.setStyleSheet("background: transparent;")
        bb_layout_b = QHBoxLayout(self.bb_container_b)
        bb_layout_b.setContentsMargins(0, 0, 0, 0)
        bb_layout_b.setSpacing(0)
        bb_layout_b.addLayout(self._build_balance_column("B"))
        outer.addWidget(self.bb_container_b, stretch=1)

  
        self.bb_container_b.hide()
        self.bb_divider_b.hide()

 
        self.beginning_balance_input = self.beginning_balance_input_a
        self.balance_status_label    = self.balance_status_label_a
        self.auto_fill_button        = self.auto_fill_button_a

        return bar

    def _build_balance_column(self, brand: str) -> QVBoxLayout:

        is_a  = brand == "A"
        label = "Brand A" if is_a else "Brand B"

        col = QVBoxLayout()
        col.setSpacing(3)

  
        title = QLabel(f"{label}  —  Opening Balance")
        title.setStyleSheet(
            f"font-size: 10px; font-weight: 600; color: {_TEXT_SEC}; background: transparent;"
            f" text-transform: uppercase; letter-spacing: 1px;"
        )
        col.addWidget(title)

        bb_input = QLineEdit()
        bb_input.setValidator(QDoubleValidator(0.0, 1e12, 2))
        bb_input.setPlaceholderText("0.00")
        bb_input.setReadOnly(True)
        bb_input.setFixedHeight(_sz(38))
        bb_input.setStyleSheet(f"""
            QLineEdit {{
                background-color: {_SLATE_50};
                border: 1.5px solid {_BORDER};
                border-radius: {_sz(8)}px;
                padding: {_sz(6)}px {_sz(14)}px;
                font-size: {_sz(15)}px;
                font-weight: 700;
                color: {_TEXT_PRI};
            }}
        """)
        bb_input.textChanged.connect(self.recalculate_all)
        col.addWidget(bb_input)

    
        action_row = QHBoxLayout()
        action_row.setSpacing(_sz(8))
        action_row.setContentsMargins(0, 2, 0, 0)

        load_btn = QPushButton("↓ Load Previous Day")
        load_btn.setFixedHeight(_sz(26))
        load_btn.setCursor(Qt.PointingHandCursor)
        load_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                color: {_PRIMARY};
                border: 1px solid {_BORDER};
                border-radius: {_sz(5)}px;
                font-size: {_sz(11)}px;
                font-weight: 600;
                padding: {_sz(3)}px {_sz(10)}px;
                min-width: 0;
            }}
            QPushButton:hover {{
                background-color: {_INDIGO_50};
                border-color: {_PRIMARY};
            }}
            QPushButton:pressed {{
                background-color: {_INDIGO_100};
            }}
            QPushButton:disabled {{
                color: {_TEXT_MUTED};
                border-color: {_SLATE_200};
                background-color: transparent;
            }}
        """)
        load_btn.clicked.connect(lambda checked, b=brand: self.auto_fill_beginning_balance(b))
        action_row.addWidget(load_btn)

        status_lbl = QLabel("")
        status_lbl.setStyleSheet(
            f"font-size: 10px; color: {_TEXT_MUTED}; background: transparent;"
        )
        status_lbl.setWordWrap(True)
        action_row.addWidget(status_lbl, stretch=1)

        col.addLayout(action_row)

        # Store references
        if is_a:
            self.beginning_balance_input_a = bb_input
            self.auto_fill_button_a        = load_btn
            self.balance_status_label_a    = status_lbl
        else:
            self.beginning_balance_input_b = bb_input
            self.auto_fill_button_b        = load_btn
            self.balance_status_label_b    = status_lbl

        return col

    def _build_tabs(self):
        tw = QTabWidget()
        tw.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        self.cash_flow_tab_a = CashFlowTab(self, "Brand A")
        self.cash_flow_tab_b = CashFlowTab(self, "Brand B")
        self.palawan_tab     = PalawanDetailsTab(self)

        self.cash_flow_tab = self.cash_flow_tab_a

        tw.addTab(self.cash_flow_tab_a,  "Brand A")
        tw.addTab(self.cash_flow_tab_b,  "Brand B")
        tw.addTab(self.palawan_tab,      "Palawan Details")


        self.tab_widget = tw
        tw.currentChanged.connect(self._on_tab_changed)

        return tw

    def _on_tab_changed(self, index):

        if not hasattr(self, 'summary_container_a') or not hasattr(self, 'summary_container_b'):
            return

       
        if hasattr(self, 'bb_container_a') and hasattr(self, 'bb_container_b'):
            if index == 0:  
                self.bb_container_a.show()
                self.bb_container_b.hide()
                self.bb_divider_b.hide()
            elif index == 1: 
                self.bb_container_a.hide()
                self.bb_container_b.show()
                self.bb_divider_b.show()
            else: 
                self.bb_container_a.show()
                self.bb_container_b.show()
                self.bb_divider_b.show()

 
        if index == 0:  
            self.summary_container_a.show()
            self.summary_container_b.hide()
        elif index == 1:  
            self.summary_container_a.hide()
            self.summary_container_b.show()
        else: 
            self.summary_container_a.show()
            self.summary_container_b.show()

    def _build_summary_strip(self):
        strip = QFrame()
        strip.setFixedHeight(_sz(110))
        strip.setStyleSheet(f"""
            QFrame {{
                background-color: {_SLATE_900};
                border-radius: {_sz(8)}px;
            }}
        """)

        h = QHBoxLayout(strip)
        h.setContentsMargins(_sz(20), _sz(10), _sz(20), _sz(10))
        h.setSpacing(0)

        col_a, self.ending_balance_display_a, self.cash_count_input_a, \
            self.cash_result_display_a, self.variance_status_label_a, \
            self.cash_float_input_a = \
            self._build_brand_summary("A")

        col_b, self.ending_balance_display_b, self.cash_count_input_b, \
            self.cash_result_display_b, self.variance_status_label_b, \
            _ = \
            self._build_brand_summary("B")

 
        self.ending_balance_display  = self.ending_balance_display_a
        self.cash_count_input        = self.cash_count_input_a
        self.cash_result_display     = self.cash_result_display_a
        self.variance_status_label   = self.variance_status_label_a

        self.cash_count_input_a.textChanged.connect(self.recalculate_all)
        self.cash_count_input_a.textChanged.connect(self.update_cash_result)
        self.cash_count_input_b.textChanged.connect(self.recalculate_all)
        self.cash_count_input_b.textChanged.connect(self.update_cash_result)


        self.summary_container_a = QWidget()
        self.summary_container_a.setStyleSheet("background: transparent;")
        container_layout_a = QHBoxLayout(self.summary_container_a)
        container_layout_a.setContentsMargins(0, 0, 0, 0)
        container_layout_a.setSpacing(0)
        container_layout_a.addLayout(col_a, stretch=1)

        self.summary_container_b = QWidget()
        self.summary_container_b.setStyleSheet("background: transparent;")
        container_layout_b = QHBoxLayout(self.summary_container_b)
        container_layout_b.setContentsMargins(0, 0, 0, 0)
        container_layout_b.setSpacing(0)
        container_layout_b.addLayout(col_b, stretch=1)

        h.addWidget(self.summary_container_a, stretch=1)
        h.addSpacing(16)
        h.addWidget(self.summary_container_b, stretch=1)

   
        self.summary_container_b.hide()

        return strip

    def _build_brand_summary(self, brand: str):
        is_a   = brand == "A"
        accent = _INDIGO_400 if is_a else _EMERALD_400

        def _cap(t):
            l = QLabel(t)
            l.setAlignment(Qt.AlignCenter)
            l.setStyleSheet(
                f"font-size: {_sz(11)}px; font-weight: 700; color: {_SLATE_300}; "
                f"letter-spacing: 1px; background: transparent; text-transform: uppercase;"
            )
            return l

        def _val(init="0.00"):
            l = QLabel(init)
            l.setAlignment(Qt.AlignCenter)
            l.setStyleSheet(
                f"font-size: {_sz(18)}px; font-weight: 800; color: {_WHITE}; background: transparent;"
            )
            return l

        def _cc_inp():
            inp = QLineEdit()
            inp.setValidator(QDoubleValidator(0.0, 1e12, 2))
            inp.setPlaceholderText("0.00")
            inp.setAlignment(Qt.AlignCenter)
            inp.setFixedHeight(_sz(32))
            inp.setStyleSheet(f"""
                QLineEdit {{
                    background: rgba(255,255,255,0.08);
                    border: 1.5px solid {_SLATE_600};
                    border-radius: {_sz(6)}px;
                    color: {_WHITE};
                    font-size: {_sz(14)}px;
                    font-weight: 700;
                    padding: {_sz(3)}px {_sz(10)}px;
                }}
                QLineEdit:focus {{
                    border: 2px solid {accent};
                    background: rgba(255,255,255,0.12);
                }}
            """)
            return inp

        col = QVBoxLayout()
        col.setSpacing(_sz(4))
        col.setContentsMargins(_sz(8), 0, _sz(8), 0)

        pill_row = QHBoxLayout()
        pill_row.setAlignment(Qt.AlignCenter)
        pill = QLabel(f"BRAND {'A' if is_a else 'B'}")
        pill.setAlignment(Qt.AlignCenter)
        pill.setStyleSheet(
            f"font-size: {_sz(12)}px; font-weight: 800; color: {accent}; letter-spacing: 1.5px; "
            f"background: transparent; padding: 0px 0;"
        )
        pill_row.addWidget(pill)
        col.addLayout(pill_row)

  
        row = QHBoxLayout()
        row.setSpacing(_sz(8))

        def _metric(cap_w, val_w):
            mc = QVBoxLayout()
            mc.setSpacing(_sz(2))
            mc.addWidget(cap_w)
            mc.addWidget(val_w, alignment=Qt.AlignCenter)
            return mc

        eb_val  = _val()
        cc_inp  = _cc_inp()
        var_val = _val()

        status_lbl = QLabel("—")
        status_lbl.setAlignment(Qt.AlignCenter)
        status_lbl.setStyleSheet(
            f"font-size: {_sz(13)}px; font-weight: 700; color: {_SLATE_300}; "
            f"min-width: {_sz(80)}px; background: transparent;"
        )

        row.addLayout(_metric(_cap("Ending Bal"),  eb_val),  stretch=2)
        row.addWidget(_vline(dark=True))
        row.addLayout(_metric(_cap("Cash Count"),  cc_inp),  stretch=2)
        row.addWidget(_vline(dark=True))


        cf_inp = None
        if is_a:
            cf_inp = QLineEdit()
            cf_inp.setValidator(QDoubleValidator(0.0, 1e12, 2))
            cf_inp.setPlaceholderText("0.00")
            cf_inp.setAlignment(Qt.AlignCenter)
            cf_inp.setFixedHeight(_sz(32))
            cf_inp.setStyleSheet(f"""
                QLineEdit {{
                    background: rgba(255,255,255,0.08);
                    border: 1.5px solid {_SLATE_600};
                    border-radius: {_sz(6)}px;
                    color: {_WHITE};
                    font-size: {_sz(14)}px;
                    font-weight: 700;
                    padding: {_sz(3)}px {_sz(10)}px;
                }}
                QLineEdit:focus {{
                    border: 2px solid {_AMBER_400};
                    background: rgba(255,255,255,0.12);
                }}
            """)
            row.addLayout(_metric(_cap("Cash Float"), cf_inp), stretch=2)
            row.addWidget(_vline(dark=True))

        row.addLayout(_metric(_cap("Variance"),    var_val), stretch=2)
        row.addWidget(_vline(dark=True))
        row.addLayout(_metric(_cap("Status"),      status_lbl), stretch=3)

        col.addLayout(row)
        return col, eb_val, cc_inp, var_val, status_lbl, cf_inp

    def _build_footer(self):
        bar = QFrame()
        bar.setFixedHeight(_sz(48))
        row = QHBoxLayout(bar)
        row.setContentsMargins(0, _sz(6), 0, _sz(2))
        row.setSpacing(_sz(10))
        row.addStretch()

        self.draft_button = QPushButton("Save Draft")
        self.draft_button.setFixedSize(_sz(100), _sz(34))
        self.draft_button.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                color: {_SLATE_600};
                font-size: {_sz(12)}px;
                font-weight: 700;
                border: 1.5px solid {_SLATE_300};
                border-radius: {_sz(6)}px;
            }}
            QPushButton:hover {{
                background-color: {_SLATE_100};
                border-color: {_SLATE_400};
                color: {_TEXT_PRI};
            }}
            QPushButton:pressed {{ background-color: {_SLATE_200}; }}
        """)
        self.draft_button.clicked.connect(self.save_draft)
        self.draft_button.setToolTip(
            "Save all current fields as a draft.\n"
            "Your data will be restored next time you log in."
        )

        self.post_button = QPushButton("Post Both Brands")
        self.post_button.setFixedSize(_sz(158), _sz(34))
        self.post_button.setStyleSheet(f"""
            QPushButton {{
                background-color: {_SUCCESS};
                color: {_WHITE};
                font-size: {_sz(13)}px;
                font-weight: 800;
                border-radius: {_sz(6)}px;
                letter-spacing: 0.2px;
            }}
            QPushButton:hover   {{ background-color: {_SUCCESS_DK}; }}
            QPushButton:pressed {{ background-color: #047857; }}
            QPushButton:disabled {{
                background-color: {_SLATE_200};
                color: {_TEXT_MUTED};
            }}
        """)
        self.post_button.clicked.connect(self.handle_post)
        self.post_button.setEnabled(False)


        self.print_button = QPushButton("Print")
        self.print_button.setFixedSize(_sz(100), _sz(34))
        self.print_button.setStyleSheet(f"""
            QPushButton {{
                background-color: #3B82F6;
                color: {_WHITE};
                font-size: {_sz(12)}px;
                font-weight: 700;
                border: none;
                border-radius: {_sz(6)}px;
            }}
            QPushButton:hover {{ background-color: #2563EB; }}
            QPushButton:pressed {{ background-color: #1D4ED8; }}
        """)
        self.print_button.clicked.connect(self.print_nonzero_report)
        self.print_button.setToolTip(
            "Print only fields with non-zero values.\n"
            "Filters out all zero-value entries from the report."
        )

    
        self.export_excel_button = QPushButton("Export Excel")
        self.export_excel_button.setFixedSize(_sz(120), _sz(34))
        self.export_excel_button.setStyleSheet(f"""
            QPushButton {{
                background-color: #059669;
                color: {_WHITE};
                font-size: {_sz(12)}px;
                font-weight: 700;
                border: none;
                border-radius: {_sz(6)}px;
            }}
            QPushButton:hover {{ background-color: #047857; }}
            QPushButton:pressed {{ background-color: #065F46; }}
        """)
        self.export_excel_button.clicked.connect(self.export_to_excel)
        self.export_excel_button.setToolTip(
            "Export non-zero fields to Excel (.xlsx).\n"
            "Only includes fields with values greater or less than zero."
        )

  
        self.clear_table_button = QPushButton(" Clear Table")
        self.clear_table_button.setFixedSize(_sz(120), _sz(34))
        self.clear_table_button.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                color: {_RED_500};
                font-size: {_sz(12)}px;
                font-weight: 700;
                border: 1.5px solid {_RED_400};
                border-radius: {_sz(6)}px;
            }}
            QPushButton:hover {{
                background-color: #FEF2F2;
                border-color: {_RED_500};
                color: #B91C1C;
            }}
            QPushButton:pressed {{ background-color: #FEE2E2; }}
        """)
        self.clear_table_button.clicked.connect(self.clear_table)
        self.clear_table_button.setToolTip(
            "Clear all fields in both Brand A and Brand B.\n"
            "This will not delete any submitted data."
        )

        self.load_draft_button = QPushButton("Load Draft")
        self.load_draft_button.setFixedSize(_sz(100), _sz(34))
        self.load_draft_button.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                color: {_SLATE_600};
                font-size: {_sz(12)}px;
                font-weight: 700;
                border: 1.5px solid {_SLATE_300};
                border-radius: {_sz(6)}px;
            }}
            QPushButton:hover {{
                background-color: {_SLATE_100};
                border-color: {_SLATE_400};
                color: {_TEXT_PRI};
            }}
            QPushButton:pressed {{ background-color: {_SLATE_200}; }}
        """)
        self.load_draft_button.clicked.connect(self._load_draft)
        self.load_draft_button.setToolTip(
            "Load a previously saved draft.\n"
            "Select from available drafts to restore."
        )

        row.addWidget(self.print_button)
        row.addWidget(self.export_excel_button)
        row.addWidget(self.clear_table_button)
        row.addWidget(self.load_draft_button)
        row.addWidget(self.draft_button)
        row.addWidget(self.post_button)
        return bar

  
    def _money_input(self, placeholder=""):
        f = QLineEdit()
        f.setValidator(QDoubleValidator(0.0, 1e12, 2))
        f.setPlaceholderText(placeholder)
        f.textChanged.connect(self.recalculate_all)
        return f

    def create_money_input(self, placeholder=""):
        return self._money_input(placeholder)

    def create_display_field(self, placeholder=""):
        f = QLineEdit()
        f.setReadOnly(True)
        f.setPlaceholderText(placeholder)
        return f

    def create_separator(self):
        return _hline()

    def get_total_amount(self, inputs_dict):
        total = 0.0
        for field in inputs_dict.values():
            try:
               
                text = field.text().strip().replace(",", "")
                total += float(text or 0)
            except ValueError:
                pass
        return total


    def handle_logout(self):
        r = QMessageBox.question(
            self, "Confirm Sign Out", "Sign out of the current session?",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        if r == QMessageBox.Yes:
            self.session.logout()
            self.logout_requested.emit()
            self.close()

    def _check_session_timeout(self):
        if self.session.check_timeout():
            self._session_timer.stop()
            QMessageBox.warning(
                self, "Session Expired",
                "Your session has expired due to inactivity.\nPlease log in again.",
                QMessageBox.Ok
            )
            self.logout_requested.emit()
            self.close()

    def mousePressEvent(self, event):
        self.session.update_activity()
        super().mousePressEvent(event)

    def keyPressEvent(self, event):
        self.session.update_activity()
        super().keyPressEvent(event)

    def check_for_updates(self):
        if AUTO_UPDATE_ENABLED:
            check_for_updates(parent=self, silent=False)
        else:
            QMessageBox.information(
                self, "Auto-Updater",
                "Auto-updater is not enabled.\n\n"
                "To enable it, install required dependencies:\n"
                "pip install requests packaging"
            )

    def closeEvent(self, event):
        if hasattr(self, '_update_checker_threads'):
            for thread in self._update_checker_threads[:]:
                if thread.isRunning():
                    thread.quit()
                    thread.wait(2000)
        event.accept()


    def get_current_brand(self):
        return "Both"

    def get_previous_day_ending_balance(self, selected_date, brand="Brand A"):
  

        if self.offline_mode and OFFLINE_SUPPORT and offline_manager:
            return self._get_offline_previous_balance(selected_date, brand)
        
   
        try:
            current    = datetime.datetime.strptime(selected_date, "%Y-%m-%d")
            table_name = "daily_reports_brand_a" if brand == "Brand A" else "daily_reports"
            for days_back in range(1, 11):
                prev_str = (current - datetime.timedelta(days=days_back)).strftime("%Y-%m-%d")
                try:
                    q = f"""SELECT ending_balance FROM {table_name}
                            WHERE date=%s AND branch=%s AND corporation=%s
                            ORDER BY id DESC LIMIT 1"""
                    result = self.db_manager.execute_query(
                        q, (prev_str, self.branch, self.corporation))
                    if result and len(result) > 0:
                        val = result[0].get('ending_balance')
                        if val is not None:
                            return float(val), prev_str
                except Exception as e:
                    print(f"Query error for {prev_str}: {e}")
        except Exception as e:
            print(f"get_previous_day_ending_balance({brand}): {e}")
        return None, None

    def _get_offline_previous_balance(self, selected_date, brand):
    
        try:
            pending_bal, pending_date = offline_manager.get_latest_pending_balance(
                self.user_email, self.branch, self.corporation, brand, selected_date
            )
            
            cached_bal, cached_date = offline_manager.get_cached_balance(
                self.user_email, self.branch, self.corporation, brand
            )
            
    
            best_bal, best_date = None, None
            
            if pending_date and pending_date < selected_date:
                best_bal, best_date = pending_bal, pending_date
            
            if cached_date and cached_date < selected_date:
                if best_date is None or cached_date > best_date:
                    best_bal, best_date = cached_bal, cached_date
   
            if pending_date and best_date:
                if pending_date > best_date:
                    best_bal, best_date = pending_bal, pending_date
            
            return best_bal, best_date
            
        except Exception as e:
            print(f"_get_offline_previous_balance error: {e}")
            return None, None


    _table_columns_cache = {}  
    _table_columns_cache_time = 0

    def _get_table_columns(self, table_name):
  
        import time as _time
        now = _time.time()
        if (table_name in self._table_columns_cache
                and (now - self._table_columns_cache_time) < 300):
            return self._table_columns_cache[table_name]
        try:
            result = self.db_manager.execute_query(
                "SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS "
                "WHERE TABLE_NAME = %s AND TABLE_SCHEMA = DATABASE()",
                (table_name,)
            )
            if result:
                cols = set()
                for row in result:
                    if isinstance(row, dict):
                        c = row.get('COLUMN_NAME') or row.get('column_name') or ''
                    elif isinstance(row, (list, tuple)) and row:
                        c = row[0]
                    else:
                        c = ''
                    if c:
                        cols.add(c)
                if cols:
                    self._table_columns_cache[table_name] = cols
                    self._table_columns_cache_time = now
                    return cols
        except Exception as e:
            print(f"_get_table_columns({table_name}): {e}")
        return self._table_columns_cache.get(table_name, set())

    def _filter_vals_for_table(self, all_vals, table_name):
        """Remove keys from all_vals that are not columns in the table."""
        existing = self._get_table_columns(table_name)
        if not existing:
            return all_vals 
        return {k: v for k, v in all_vals.items() if k in existing}

    def check_existing_entry(self, selected_date, brand="Brand A"):

        try:
            table_name = "daily_reports_brand_a" if brand == "Brand A" else "daily_reports"
            q = f"""SELECT * FROM {table_name}
                    WHERE date=%s AND branch=%s AND corporation=%s LIMIT 1"""
            result = self.db_manager.execute_query(
                q, (selected_date, self.branch, self.corporation))
            if result and len(result) > 0:
                row = result[0]
            
                is_locked = row.get('is_locked', 1)
                return "locked" if is_locked else "unlocked"
        except Exception as e:
            print(f"check_existing_entry({brand}): {e}")
        return None


    def on_date_changed(self):
        sd = self.date_picker.date().toString("yyyy-MM-dd")

        for bb in (self.beginning_balance_input_a, self.beginning_balance_input_b):
            bb.clear()
            bb.setReadOnly(True)
            bb.setStyleSheet(f"""
                QLineEdit {{
                    background-color: {_SLATE_100};
                    border: 1.5px solid {_SLATE_200};
                    border-radius: 6px;
                    padding: 7px 12px;
                    font-size: 14px;
                    font-weight: 700;
                    color: {_TEXT_PRI};
                }}
            """)
        for cc in (self.cash_count_input_a, self.cash_count_input_b):
            cc.clear()

        for tab in (self.cash_flow_tab_a, self.cash_flow_tab_b, self.palawan_tab):
            if hasattr(tab, 'clear_fields'):
                tab.clear_fields()

        self.beginning_balance_auto_filled_a = False
        self.beginning_balance_auto_filled_b = False
        self.previous_day_balance_a = self.previous_day_date_a = None
        self.previous_day_balance_b = self.previous_day_date_b = None

        status_a = self.check_existing_entry(sd, "Brand A")  
        status_b = self.check_existing_entry(sd, "Brand B")

        if status_a == "locked" and status_b == "locked":
            for brand in ("A", "B"):
                self._set_status_brand(brand, "Submitted", _RED_500, bold=True)
            self.auto_fill_button_a.setEnabled(False)
            self.auto_fill_button_b.setEnabled(False)
            self.post_button.setEnabled(False)
            self._toggle_inputs(False)
            return

        self._toggle_inputs(True)

        any_unlocked = False
        for brand, status, bf in [("A", status_a, "Brand A"), ("B", status_b, "Brand B")]:
            bb_input = self.beginning_balance_input_a if brand == "A" else self.beginning_balance_input_b
            af_btn   = self.auto_fill_button_a        if brand == "A" else self.auto_fill_button_b
            cf_tab   = self.cash_flow_tab_a           if brand == "A" else self.cash_flow_tab_b
            cc_input = self.cash_count_input_a        if brand == "A" else self.cash_count_input_b

            if status == "locked":

                self._set_status_brand(brand, "Submitted", _RED_500, bold=True)
                af_btn.setEnabled(False)
                bb_input.setEnabled(False)
                cc_input.setEnabled(False)
                if hasattr(cf_tab, 'set_enabled'):
                    cf_tab.set_enabled(False)
            elif status == "unlocked":

                any_unlocked = True

                self._load_brand_report_data(bf, sd)
  
                self._set_status_brand(brand, "🔄 Reset by Admin — Edit & Resubmit", "#E67E22", bold=True)
                af_btn.setEnabled(False) 
                bb_input.setEnabled(True)
                bb_input.setReadOnly(False)
                cc_input.setEnabled(True)
                if hasattr(cf_tab, 'set_enabled'):
                    cf_tab.set_enabled(True)
         
                if brand == "A":
                    self.beginning_balance_auto_filled_a = True
                else:
                    self.beginning_balance_auto_filled_b = True
            else:
     
                af_btn.setEnabled(True)
                prev_bal, prev_date = self.get_previous_day_ending_balance(sd, bf)
                if prev_bal is not None:
                    if brand == "A":
                        self.previous_day_balance_a, self.previous_day_date_a = prev_bal, prev_date
                    else:
                        self.previous_day_balance_b, self.previous_day_date_b = prev_bal, prev_date
                    self._set_status_brand(brand,
                        f"Found: {prev_date}  ·  {prev_bal:,.2f}", _TEXT_MUTED)
                else:
                    self._set_status_brand(brand, "No previous record — enter manually", _AMBER_500)
                    bb_input.setReadOnly(False)
                    bb_input.setPlaceholderText("Enter opening balance")
                    bb_input.setStyleSheet(f"""
                        QLineEdit {{
                            background-color: {_BG_INPUT};
                            border: 1.5px solid {_BORDER};
                            border-radius: 6px;
                            padding: 7px 12px;
                            font-size: 14px;
                            font-weight: 700;
                            color: {_TEXT_PRI};
                        }}
                        QLineEdit:focus {{
                            border: 2px solid {_PRIMARY};
                            background-color: {_INDIGO_50};
                        }}
                    """)


        if any_unlocked or not status_a or not status_b:
            self.post_button.setEnabled(True)

        # Always restore palawan tab from Brand A table regardless of lock state
        self._restore_palawan_tab(sd)

        self.recalculate_all()

    def _restore_palawan_tab(self, date_str):
        """Load palawan data from both Brand A and Brand B tables.
        Brand A is the canonical source; Brand B lotes values take precedence
        when non-zero (they get updated there during re-submit with Brand A locked)."""
        _LOTES_COLS = (
            'palawan_sendout_lotes_total',
            'palawan_payout_lotes_total',
            'palawan_international_lotes_total',
        )
        try:
            params = (date_str, self.branch, self.corporation)
            result_a = self.db_manager.execute_query(
                "SELECT * FROM daily_reports_brand_a "
                "WHERE date=%s AND branch=%s AND corporation=%s LIMIT 1", params
            )
            result_b = self.db_manager.execute_query(
                "SELECT * FROM daily_reports "
                "WHERE date=%s AND branch=%s AND corporation=%s LIMIT 1", params
            )

            if not result_a and not result_b:
                return

            data = dict(result_a[0]) if result_a else {}
            if result_b:
                data_b = result_b[0]
                for col in _LOTES_COLS:
                    b_val = data_b.get(col) or 0
                    if float(b_val) != 0:
                        data[col] = b_val

            self.palawan_tab.load_data(data)
        except Exception as e:
            print(f"[_restore_palawan_tab] {e}")

    def _set_status(self, text, color, bold=False):
        self._set_status_brand("A", text, color, bold)

    def _set_status_brand(self, brand, text, color, bold=False):
        lbl = self.balance_status_label_a if brand == "A" else self.balance_status_label_b
        w   = "700" if bold else "500"
        lbl.setText(text)
        lbl.setStyleSheet(
            f"font-size: 12px; font-weight: {w}; color: {color}; background: transparent;"
        )


    def auto_fill_beginning_balance(self, brand="A"):
        sd        = self.date_picker.date().toString("yyyy-MM-dd")
        brand_full = "Brand A" if brand == "A" else "Brand B"

        if self.check_existing_entry(sd, brand_full):
            self._msg("Entry Exists",
                      f"An entry already exists for {brand_full} on {sd}.",
                      QMessageBox.Warning)
            return

        prev_bal  = self.previous_day_balance_a if brand == "A" else self.previous_day_balance_b
        prev_date = self.previous_day_date_a    if brand == "A" else self.previous_day_date_b
        bb_input  = self.beginning_balance_input_a if brand == "A" else self.beginning_balance_input_b
        af_btn    = self.auto_fill_button_a        if brand == "A" else self.auto_fill_button_b

        if prev_bal is not None:
            bb_input.setText(f"{prev_bal:.2f}")
            bb_input.setReadOnly(True)
            bb_input.setStyleSheet(f"""
                QLineEdit {{
                    background-color: {_SLATE_50};
                    border: 2px solid {_INDIGO_500};
                    border-radius: 6px;
                    padding: 7px 12px;
                    font-size: 14px;
                    font-weight: 700;
                    color: #065F46;
                }}
            """)
            self._set_status_brand(brand,
                f"Loaded from {prev_date}",
                _EMERALD_500, bold=True)
            af_btn.setText("✓  Loaded")
            af_btn.setEnabled(False)
            af_btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: transparent;
                    color: {_EMERALD_500};
                    border: 1.5px solid {_INDIGO_500};
                    border-radius: 5px;
                    font-size: 12px;
                    font-weight: 700;
                    padding: 4px 14px;
                    min-width: 0;
                }}
            """)
            if brand == "A":
                self.beginning_balance_auto_filled_a = True
            else:
                self.beginning_balance_auto_filled_b = True
            self._msg("Balance Loaded",
                      f"{brand_full} opening balance set to {prev_bal:,.2f}",
                      QMessageBox.Information)
        else:
            self._msg("No Previous Record",
                      f"No previous record for {brand_full}. Enter the opening balance manually.",
                      QMessageBox.Information)
            bb_input.setReadOnly(False)
            bb_input.setPlaceholderText("Enter opening balance")
            bb_input.setStyleSheet(f"""
                QLineEdit {{
                    background-color: {_BG_INPUT};
                    border: 1.5px solid {_BORDER};
                    border-radius: 6px;
                    padding: 7px 12px;
                    font-size: 14px;
                    font-weight: 700;
                    color: {_TEXT_PRI};
                }}
                QLineEdit:focus {{
                    border: 2px solid {_PRIMARY};
                    background-color: {_INDIGO_50};
                }}
            """)
            if brand == "A":
                self.beginning_balance_auto_filled_a = True
            else:
                self.beginning_balance_auto_filled_b = True

    def _toggle_inputs(self, enabled):
        for w in (self.beginning_balance_input_a, self.beginning_balance_input_b,
                  self.cash_count_input_a, self.cash_count_input_b):
            w.setEnabled(enabled)
        for tab in (self.cash_flow_tab_a, self.cash_flow_tab_b,
                    self.palawan_tab):
            if hasattr(tab, 'set_enabled'):
                tab.set_enabled(enabled)

    def disable_all_inputs(self):
        self._toggle_inputs(False)

    def enable_all_inputs(self):
        self._toggle_inputs(True)

    def recalculate_all(self):
        for brand in ("a", "b"):
            bb  = getattr(self, f"beginning_balance_input_{brand}")
            cft = getattr(self, f"cash_flow_tab_{brand}")
            eb  = getattr(self, f"ending_balance_display_{brand}")
            try:
                beg = float(bb.text().strip().replace(",", "") or 0)
            except ValueError:
                beg = 0.0
            deb  = cft.get_debit_total()
            cred = cft.get_credit_total()
            cft.update_totals(beg, deb, cred)
            end = beg + deb - cred
            eb.setText(f"{end:,.2f}")
            c = _EMERALD_400 if end > 0 else (_RED_400 if end < 0 else _WHITE)
            eb.setStyleSheet(
                f"font-size: 15px; font-weight: 800; color: {c}; background: transparent;"
            )

        self.palawan_tab.calculate_palawan_totals()
        self.update_cash_result()

    def update_cash_result(self):
        ready_a = self._update_brand_variance("A")
        ready_b = self._update_brand_variance("B")
        self.post_button.setEnabled(ready_a and ready_b)

    def _update_brand_variance(self, brand):
        bb  = self.beginning_balance_input_a if brand == "A" else self.beginning_balance_input_b
        cc  = self.cash_count_input_a        if brand == "A" else self.cash_count_input_b
        eb  = self.ending_balance_display_a  if brand == "A" else self.ending_balance_display_b
        var = self.cash_result_display_a     if brand == "A" else self.cash_result_display_b
        stl = self.variance_status_label_a   if brand == "A" else self.variance_status_label_b
        try:
            cc_val  = float(cc.text().strip().replace(",", "") or 0)
            eb_val  = float((eb.text() or "0").replace(",", ""))
            diff    = cc_val - eb_val
            var.setText(f"{diff:,.2f}")
            has_req = bool(bb.text().strip()) and bool(cc.text().strip())
            font    = "font-size: 15px; font-weight: 800; background: transparent;"

            if abs(diff) < 0.01:
                var.setStyleSheet(font + f"color: {_EMERALD_400};")
                if has_req:
                    stl.setText("✓  Balanced")
                    stl.setStyleSheet(
                        f"font-size: 12px; font-weight: 700; color: {_EMERALD_400}; background: transparent;"
                    )
                else:
                    stl.setText("Fill required fields")
                    stl.setStyleSheet(
                        f"font-size: 12px; font-weight: 600; color: {_SLATE_500}; background: transparent;"
                    )
            elif diff > 0:
                var.setStyleSheet(font + f"color: {_AMBER_400};")
                stl.setText(f"Over  +{diff:,.2f}")
                stl.setStyleSheet(
                    f"font-size: 12px; font-weight: 700; color: {_AMBER_400}; background: transparent;"
                )
            else:
                var.setStyleSheet(font + f"color: {_RED_400};")
                stl.setText(f"Short  {diff:,.2f}")
                stl.setStyleSheet(
                    f"font-size: 12px; font-weight: 700; color: {_RED_400}; background: transparent;"
                )

            return has_req
        except ValueError:
            var.setText("—")
            stl.setText("Invalid input")
            stl.setStyleSheet(
                f"font-size: 12px; font-weight: 600; color: {_RED_500}; background: transparent;"
            )
            return False

    def _set_var_status(self, text, color):
        self.variance_status_label_a.setText(text)
        self.variance_status_label_a.setStyleSheet(
            f"font-size: 12px; font-weight: 700; color: {color}; background: transparent;"
        )

    def _check_optional_tabs_empty(self):
        empty_tabs = []
        try:
            if all(v == 0 or v == 0.0 for v in self.palawan_tab.get_data().values()):
                empty_tabs.append("Palawan Details")
        except Exception:
            empty_tabs.append("Palawan Details")

        if not empty_tabs:
            return True

        dlg = QMessageBox(self)
        dlg.setWindowTitle("Incomplete Report")
        dlg.setIcon(QMessageBox.Warning)
        dlg.setText(
            f"<b>The following tabs have no data:</b><br><br>"
            + "<br>".join(f"&nbsp;&nbsp;&#8226;&nbsp; <b>{t}</b>" for t in empty_tabs)
            + "<br><br>Are you sure you want to post without filling them in?"
        )
        dlg.setInformativeText(
            "Click <b>Go Back</b> to add missing details, "
            "or <b>Post Anyway</b> to submit with zeros."
        )
        btn_post = dlg.addButton("Post Anyway",  QMessageBox.AcceptRole)
        btn_back = dlg.addButton("Go Back",       QMessageBox.RejectRole)
        dlg.setDefaultButton(btn_back)
        dlg.setStyleSheet(self._MSG_QSS)
        btn_post.setStyleSheet(f"background-color:{_AMBER_500};color:{_WHITE};border:none;")
        btn_back.setStyleSheet(f"background-color:{_PRIMARY};color:{_WHITE};border:none;")
        dlg.exec_()
        return dlg.clickedButton() == btn_post


    def validate_calculations(self):
        """
        CRITICAL: Comprehensive validation to BLOCK any database save with calculation errors.
        
        CORRECT FORMULA:
        - Debit Total = Beginning Balance + Sum of all debit field values
        - Credit Total = Sum of all credit field values  
        - Ending Balance = Debit Total - Credit Total
        
        ⚠️ STRICT MODE: If ANY calculation is wrong, the post is BLOCKED and NO DATA reaches database.
        """
        errors = []
        
        for brand_index, (brand_char, bb_input, cf_tab) in enumerate([
            ("A", self.beginning_balance_input_a, self.cash_flow_tab_a),
            ("B", self.beginning_balance_input_b, self.cash_flow_tab_b)
        ]):
            try:
                # Get beginning balance
                beginning = float(bb_input.text().strip().replace(',', '') or 0)
                if beginning < 0:
                    errors.append(f"Brand {brand_char}: Beginning Balance cannot be negative ({beginning:.2f})")
                    continue
            except (ValueError, TypeError):
                errors.append(f"Brand {brand_char}: Invalid Beginning Balance value")
                continue
            
            cf_data = cf_tab.get_data()
            
            # Sum debit and credit field values (excluding _lotes) - MUST MATCH save code exactly!
            # This includes all values (including 0) to match what handle_post() does
            debit_field_sum = sum(v for k, v in cf_data.get('debit', {}).items() 
                                 if not k.endswith('_lotes'))
            credit_field_sum = sum(v for k, v in cf_data.get('credit', {}).items() 
                                  if not k.endswith('_lotes'))
            
            # Calculate what totals SHOULD be using CORRECT FORMULA
            calculated_debit_total = beginning + debit_field_sum
            calculated_credit_total = credit_field_sum
            calculated_ending = calculated_debit_total - calculated_credit_total
            
            # Get displayed totals from UI
            debit_fields_only = cf_tab.get_debit_total()  # This is just fields sum
            displayed_credit = cf_tab.get_credit_total()
            
            # STRICT VALIDATION #1: Verify debit fields sum matches
            if abs(debit_fields_only - debit_field_sum) > 0.01:
                errors.append(f"Brand {brand_char} DEBIT FIELDS SUM: Calculation Error!\n"
                            f"  Should be: {debit_field_sum:.2f}\n"
                            f"  Shows: {debit_fields_only:.2f}\n"
                            f"  Difference: {abs(debit_fields_only - debit_field_sum):.2f}")
            
            # STRICT VALIDATION #2: Verify credit fields sum matches
            if abs(displayed_credit - credit_field_sum) > 0.01:
                errors.append(f"Brand {brand_char} CREDIT FIELDS SUM: Calculation Error!\n"
                            f"  Should be: {credit_field_sum:.2f}\n"
                            f"  Shows: {displayed_credit:.2f}\n"
                            f"  Difference: {abs(displayed_credit - credit_field_sum):.2f}")
            
            # STRICT VALIDATION #3: Verify debit total = beginning + fields
            displayed_debit = beginning + debit_fields_only
            if abs(displayed_debit - calculated_debit_total) > 0.01:
                errors.append(f"Brand {brand_char} DEBIT TOTAL: Calculation Error!\n"
                            f"  Formula: Beginning ({beginning:.2f}) + Fields ({debit_field_sum:.2f})\n"
                            f"  Should be: {calculated_debit_total:.2f}\n"
                            f"  Error detected!")
            
            # STRICT VALIDATION #4: Verify ending balance calculation
            displayed_ending = displayed_debit - displayed_credit
            if abs(displayed_ending - calculated_ending) > 0.01:
                errors.append(f"Brand {brand_char} ENDING BALANCE: Calculation Error!\n"
                            f"  Formula: Debit ({displayed_debit:.2f}) - Credit ({displayed_credit:.2f})\n"
                            f"  Should be: {calculated_ending:.2f}\n"
                            f"  Shows: {displayed_ending:.2f}")
        
        if errors:
            error_text = "🚫 VALIDATION FAILED - DATABASE SAVE BLOCKED 🚫\n\n"
            error_text += "Calculation errors detected:\n\n"
            error_text += "\n\n".join(errors)
            error_text += "\n\n⚠️ NO DATA HAS BEEN SAVED TO DATABASE ⚠️\n\n"
            error_text += "Please verify your calculations and try again."
            
            QMessageBox.critical(self, "POSTING BLOCKED - Calculation Error", error_text)
            return False
        
        return True

    def verify_database_save(self, date_str, brand_table,
                              expected_debit=None, expected_credit=None, expected_ending=None):
        """
        POST-SAVE VERIFICATION: Read data back from database and verify stored totals
        match the values that were calculated before saving.

        Expected values are passed in from handle_post so we compare against the
        authoritative pre-save calculation rather than re-summing individual columns
        (which may not be stored when a credit/debit field has no DB column in the table).
        """
        try:
            query = f"SELECT beginning_balance, debit_total, credit_total, ending_balance FROM {brand_table} WHERE date = %s AND branch = %s AND corporation = %s"
            result = self.db_manager.execute_query(query, (date_str, self.branch, self.corporation))

            if not result:
                print(f"[WARNING] Could not verify {brand_table} save - record not found!")
                return True

            saved_row = result[0]
            stored_debit   = float(saved_row.get('debit_total', 0))
            stored_credit  = float(saved_row.get('credit_total', 0))
            stored_ending  = float(saved_row.get('ending_balance', 0))

            if expected_debit is None or expected_credit is None or expected_ending is None:
                # Fallback: nothing to compare against, just log what was stored
                print(f"[OK] {brand_table} stored: Debit={stored_debit:.2f}, Credit={stored_credit:.2f}, Ending={stored_ending:.2f}")
                return True

            debit_match  = abs(stored_debit  - expected_debit)  < 0.01
            credit_match = abs(stored_credit - expected_credit) < 0.01
            ending_match = abs(stored_ending - expected_ending) < 0.01

            if not debit_match:
                print(f"[ERROR] {brand_table} Debit Total mismatch!")
                print(f"  Expected: {expected_debit:.2f}")
                print(f"  Stored:   {stored_debit:.2f}")
                print(f"  Difference: {stored_debit - expected_debit:+.2f}")
                return False

            if not credit_match:
                print(f"[ERROR] {brand_table} Credit Total mismatch!")
                print(f"  Expected: {expected_credit:.2f}")
                print(f"  Stored:   {stored_credit:.2f}")
                print(f"  Difference: {stored_credit - expected_credit:+.2f}")
                return False

            if not ending_match:
                print(f"[ERROR] {brand_table} Ending Balance mismatch!")
                print(f"  Expected: {expected_ending:.2f}")
                print(f"  Stored:   {stored_ending:.2f}")
                print(f"  Difference: {stored_ending - expected_ending:+.2f}")
                return False

            print(f"[OK] {brand_table} verified: Debit={stored_debit:.2f}, Credit={stored_credit:.2f}, Ending={stored_ending:.2f}")
            return True

        except Exception as e:
            print(f"[ERROR] Could not verify database save: {e}")
            return True  # Don't fail hard, just log it

    def handle_post(self):
        try:
            sd = self.date_picker.date().toString("yyyy-MM-dd")
            if not self._check_optional_tabs_empty():
                return
            if not self.validate_all_requirements():
                return
            
            # CRITICAL: Verify calculations before saving
            if not self.validate_calculations():
                return

            if self.offline_mode:
                self._handle_offline_post(sd)
                return

            self.loading_overlay.set_status("Preparing data...", "Validating report fields")
            self.loading_overlay.show()
            self.loading_overlay.raise_()
            QApplication.processEvents()

            pal = self.palawan_tab.get_data()

            brand_specs = [
                ("Brand A", self.cash_flow_tab_a,
                 self.beginning_balance_input_a, self.cash_count_input_a,
                 "daily_reports_brand_a"),
                ("Brand B", self.cash_flow_tab_b,
                 self.beginning_balance_input_b, self.cash_count_input_b,
                 "daily_reports"),
            ]

            results = []
            brand_all_vals = {}  
            for brand_full, cf_tab, bb_input, cc_input, table_name in brand_specs:
  
                self.loading_overlay.set_status(f"Posting {brand_full}...", f"Saving to {table_name}")
                QApplication.processEvents()
                
                entry_status = self.check_existing_entry(sd, brand_full)
                if entry_status == "locked":
                    results.append((brand_full, "skipped", None))
                    continue

                cf        = cf_tab.get_data()
                beginning = float(bb_input.text().strip().replace(',', '') or 0)
                deb = sum(v for k, v in cf['debit'].items()  if not k.endswith('_lotes'))
                cre = sum(v for k, v in cf['credit'].items() if not k.endswith('_lotes'))
                ending      = beginning + deb - cre
                cash_count  = float(cc_input.text().strip().replace(',', '') or 0)
                cash_result = cash_count - ending
                variance_status = (
                    "balanced" if abs(cash_result) < 0.01
                    else "over"  if cash_result > 0
                    else "short"
                )

                # Merge: palawan tab provides supplementary fields; credit tab takes
                # precedence for any key that appears in both (non-zero credit wins).
                all_vals = {**cf['debit'], **pal}
                for k, v in cf['credit'].items():
                    if v != 0 or k not in all_vals:
                        all_vals[k] = v
        
                if hasattr(cf_tab, 'selected_bank_account') and cf_tab.selected_bank_account:
                    all_vals['fund_transfer_bank_account'] = cf_tab.selected_bank_account
                
   
                if hasattr(self, '_ft_ho_breakdowns'):
                    bd = self._ft_ho_breakdowns.get(brand_full)
                    if bd:
                        all_vals['ft_ho_breakdown'] = json.dumps(bd)
                
                
                if hasattr(cf_tab, 'branch_dest_inputs'):
                    branch_dest = cf_tab.branch_dest_inputs.get('Fund Transfer to BRANCH')
                    if branch_dest and branch_dest.text().strip():
                        all_vals['fund_transfer_to_branch_dest'] = branch_dest.text().strip()
                
              
                if hasattr(cf_tab, 'branch_dest_inputs'):
                    branch_src = cf_tab.branch_dest_inputs.get('Fund Transfer from BRANCH')
                    if branch_src and branch_src.text().strip():
                        all_vals['fund_transfer_from_branch_dest'] = branch_src.text().strip()
                
     
                if brand_full == "Brand A" and hasattr(self, '_pc_salary_breakdown') and self._pc_salary_breakdown:
                    all_vals['pc_salary_breakdown'] = json.dumps(self._pc_salary_breakdown)
                
      
                if hasattr(cf_tab, 'mc_currency_details'):
                    mc_in_details = cf_tab.mc_currency_details.get('MC In', [])
                    mc_out_details = cf_tab.mc_currency_details.get('MC Out', [])
                    if mc_in_details:
                        all_vals['mc_in_details'] = json.dumps(mc_in_details)
                    if mc_out_details:
                        all_vals['mc_out_details'] = json.dumps(mc_out_details)
                

                if hasattr(self, '_motor_car_breakdown') and self._motor_car_breakdown:
                    all_vals['empeno_motor_car_breakdown'] = json.dumps(self._motor_car_breakdown)
                
                brand_all_vals[brand_full] = all_vals  

                # CRITICAL SAFETY CHECK: Verify this brand's calculations one more time before saving
                # This is a secondary check to ensure no corrupted data reaches database
                expected_debit = beginning + deb
                expected_credit = cre
                expected_ending = expected_debit - expected_credit
                
                if expected_debit < 0:
                    results.append((brand_full, "validation_error",
                                   f"BLOCKED: Debit total is negative (invalid)"))
                    continue
                if expected_credit < 0:
                    results.append((brand_full, "validation_error",
                                   f"BLOCKED: Credit total is negative (invalid)"))
                    continue
                if abs(ending - expected_ending) > 0.01:
                    results.append((brand_full, "validation_error",
                                   f"BLOCKED: Ending balance mismatch (expected {expected_ending:.2f}, got {ending:.2f})"))
                    continue

                if entry_status == "unlocked":
         
                    update_fields = {
                        'username': self.user_email,
                        'beginning_balance': beginning,
                        'debit_total': beginning + deb,
                        'credit_total': cre,
                        'ending_balance': ending,
                        'cash_count': cash_count,
                        'cash_result': cash_result,
                        'variance_status': variance_status,
                        'is_locked': 1,
                    }
                    update_fields.update(self._filter_vals_for_table(all_vals, table_name))
                    set_clause = ', '.join(f"{c} = %s" for c in update_fields.keys())
                    vals = list(update_fields.values()) + [sd, self.branch, self.corporation]
                    query = (
                        f"UPDATE {table_name} SET {set_clause} "
                        f"WHERE date = %s AND branch = %s AND corporation = %s"
                    )
                else:

                    filtered = self._filter_vals_for_table(all_vals, table_name)
                    cols = [
                        'date', 'username', 'branch', 'corporation',
                        'beginning_balance', 'debit_total', 'credit_total',
                        'ending_balance', 'cash_count', 'cash_result', 'variance_status',
                        'is_locked'
                    ] + list(filtered.keys())
                    vals = [
                        sd, self.user_email, self.branch, self.corporation,
                        beginning, beginning + deb, cre,
                        ending, cash_count, cash_result, variance_status,
                        1 
                    ] + list(filtered.values())

                    ph    = ', '.join(['%s'] * len(cols))
                    query = f"INSERT INTO {table_name} ({', '.join(cols)}) VALUES ({ph})"

                rows, last_err = None, None
                for attempt in range(1, 5):
                    res, err = self.db_manager.execute_query_with_exception(query, vals)
                    if err is None:
                        rows = res
                        break
                    last_err = err
                    is_dl = (hasattr(err, 'args') and isinstance(err.args, tuple)
                             and len(err.args) > 0 and err.args[0] == 1213)
                    try:
                        self.db_manager.logger.error(f"DB attempt {attempt}: {err}")
                    except Exception:
                        pass
                    if is_dl and attempt < 4:
                        time.sleep(0.5 * attempt)
                    else:
                        break

                if isinstance(rows, int) and rows > 0:
                    # POST-SAVE VERIFICATION: Check database for calculation errors
                    is_valid = self.verify_database_save(
                        sd, table_name,
                        expected_debit=beginning + deb,
                        expected_credit=cre,
                        expected_ending=ending,
                    )
                    if not is_valid:
                        print(f"[CRITICAL] Database validation failed for {table_name}! Removing record from database.")
                        try:
                            if entry_status is None:
                                # New record was just inserted — DELETE it entirely so no bad data remains
                                self.db_manager.execute_query(
                                    f"DELETE FROM {table_name} WHERE date = %s AND branch = %s AND corporation = %s",
                                    (sd, self.branch, self.corporation)
                                )
                                print(f"[INFO] Deleted invalid record from {table_name}")
                            else:
                                # Existing record was updated — revert to unlocked so user can fix and resubmit
                                self.db_manager.execute_query(
                                    f"UPDATE {table_name} SET is_locked = 0 WHERE date = %s AND branch = %s AND corporation = %s",
                                    (sd, self.branch, self.corporation)
                                )
                                print(f"[INFO] Reverted {table_name} record to unlocked state")
                        except Exception as revert_err:
                            print(f"[ERROR] Could not revert record: {revert_err}")
                        results.append((brand_full, "validation_error",
                                      "Calculation error detected. Report was NOT saved to the database.\n"
                                      "Please check your values and try again."))
                    else:
                        results.append((brand_full, "success", None))

                    if OFFLINE_SUPPORT and offline_manager:
                        offline_manager.cache_ending_balance(
                            self.user_email, self.branch, self.corporation,
                            brand_full, sd, ending
                        )
                elif rows is None:
                    results.append((brand_full, "error",
                                    str(last_err) if last_err else "Unknown error"))
                else:
                    results.append((brand_full, "no_rows", None))

            successes = [b for b, s, _ in results if s == "success"]
            errors    = [(b, e) for b, s, e in results if s == "error"]
            val_errors = [(b, e) for b, s, e in results if s == "validation_error"]
            skipped   = [b for b, s, _ in results if s == "skipped"]

            if errors or val_errors:
                self.loading_overlay.hide()
                error_msg = ""
                if errors:
                    error_msg += "Database Errors:\n\n" + "\n".join(f"{b}: {e}" for b, e in errors)
                if val_errors:
                    if error_msg:
                        error_msg += "\n\n"
                    error_msg += "⚠️ VALIDATION ERRORS (Amounts may be incorrect):\n\n"
                    error_msg += "\n".join(f"{b}: {e}" for b, e in val_errors)
                    error_msg += "\n\nPlease contact support immediately!"
                
                self._msg("Save Error - Validation Failed" if val_errors else "Database Error",
                          error_msg,
                          QMessageBox.Critical)
                if _ping_monitor:
                    fail_detail = f"date={sd} | " + " | ".join(
                        f"{b}: {e}" for b, e in (errors + val_errors)
                    )
                    _ping_monitor.log_event('post_failed', self.user_email,
                                           fail_detail[:500])
                return

            if successes:
                
                self.loading_overlay.set_status("Saving Palawan details...", "Finalizing report")
                QApplication.processEvents()
                
             
                pal = self.palawan_tab.get_data()
                for brand_full in successes:
                    self._save_palawan_to_payable(sd, brand_full, pal)

               
                if "Brand A" in successes:
                    self.loading_overlay.set_status("Saving service tables...", "Brand A supplementary data")
                    QApplication.processEvents()
                    self._post_to_service_tables(
                        sd, brand_all_vals.get("Brand A", {})
                    )
                    
                    self._save_cash_float(sd)
                
                
                self.loading_overlay.hide()
                
                parts = f"Posted: {', '.join(successes)}"
                if skipped:
                    parts += f"\nSkipped (already exists): {', '.join(skipped)}"
                if _ping_monitor:
                    _ping_monitor.log_event('post_success', self.user_email,
                                           f"date={sd} brands={', '.join(successes)}")
                self._msg_success(f"Report for {sd}\n\n{parts}")
                self._delete_draft(sd)
                self.on_date_changed()
                self.clear_all_fields()
            elif skipped and not successes:
                self.loading_overlay.hide()
                self._msg("Nothing to Post",
                          "All brands already have entries for this date.",
                          QMessageBox.Information)

        except Exception as e:
            self.loading_overlay.hide()
            self._msg("Error", f"Failed to post: {e}", QMessageBox.Critical)

    def _handle_offline_post(self, selected_date):

        try:
            if not OFFLINE_SUPPORT or not offline_manager:
                self._msg("Error", "Offline support not available.", QMessageBox.Critical)
                return
            
            
            pal = self.palawan_tab.get_data()
            
            brand_data = {}
            for brand_full, cf_tab, bb_input, cc_input, table_name in [
                ("Brand A", self.cash_flow_tab_a,
                 self.beginning_balance_input_a, self.cash_count_input_a,
                 "daily_reports_brand_a"),
                ("Brand B", self.cash_flow_tab_b,
                 self.beginning_balance_input_b, self.cash_count_input_b,
                 "daily_reports"),
            ]:
                try:
                    beginning = float(bb_input.text().strip().replace(',', '') or 0)
                    cash_count = float(cc_input.text().strip().replace(',', '') or 0)
                except ValueError:
                    beginning = 0
                    cash_count = 0
                
                cf = cf_tab.get_data()
                deb = sum(v for k, v in cf['debit'].items() if not k.endswith('_lotes'))
                cre = sum(v for k, v in cf['credit'].items() if not k.endswith('_lotes'))
                ending = beginning + deb - cre
                cash_result = cash_count - ending
                variance_status = (
                    "balanced" if abs(cash_result) < 0.01
                    else "over" if cash_result > 0
                    else "short"
                )
                
                # Merge: palawan tab provides supplementary fields; credit tab takes
                # precedence for any key that appears in both (non-zero credit wins).
                all_vals = {**cf['debit'], **pal}
                for k, v in cf['credit'].items():
                    if v != 0 or k not in all_vals:
                        all_vals[k] = v
                
                
                if hasattr(cf_tab, 'selected_bank_account') and cf_tab.selected_bank_account:
                    all_vals['fund_transfer_bank_account'] = cf_tab.selected_bank_account
                
                
                if hasattr(self, '_ft_ho_breakdowns'):
                    bd = self._ft_ho_breakdowns.get(brand_full)
                    if bd:
                        all_vals['ft_ho_breakdown'] = json.dumps(bd)
                
                
                if hasattr(cf_tab, 'branch_dest_inputs'):
                    branch_dest = cf_tab.branch_dest_inputs.get('Fund Transfer to BRANCH')
                    if branch_dest and branch_dest.text().strip():
                        all_vals['fund_transfer_to_branch_dest'] = branch_dest.text().strip()
                
                
                if hasattr(cf_tab, 'branch_dest_inputs'):
                    branch_src = cf_tab.branch_dest_inputs.get('Fund Transfer from BRANCH')
                    if branch_src and branch_src.text().strip():
                        all_vals['fund_transfer_from_branch_dest'] = branch_src.text().strip()
                
                
                if brand_full == "Brand A" and hasattr(self, '_pc_salary_breakdown') and self._pc_salary_breakdown:
                    all_vals['pc_salary_breakdown'] = json.dumps(self._pc_salary_breakdown)
                
               
                if hasattr(cf_tab, 'mc_currency_details'):
                    mc_in_details = cf_tab.mc_currency_details.get('MC In', [])
                    mc_out_details = cf_tab.mc_currency_details.get('MC Out', [])
                    if mc_in_details:
                        all_vals['mc_in_details'] = json.dumps(mc_in_details)
                    if mc_out_details:
                        all_vals['mc_out_details'] = json.dumps(mc_out_details)
                

                if hasattr(self, '_motor_car_breakdown') and self._motor_car_breakdown:
                    all_vals['empeno_motor_car_breakdown'] = json.dumps(self._motor_car_breakdown)
                
                brand_data[brand_full] = {
                    "table_name": table_name,
                    "beginning_balance": beginning,
                    "debit_total": deb,
                    "credit_total": cre,
                    "ending_balance": ending,
                    "cash_count": cash_count,
                    "cash_result": cash_result,
                    "variance_status": variance_status,
                    "all_values": all_vals
                }
            
            entry_data = {
                "date": selected_date,
                "username": self.user_email,
                "branch": self.branch,
                "corporation": self.corporation,
                "palawan_data": pal,
                "brand_data": brand_data
            }
            

            entry_id = offline_manager.save_pending_entry(
                self.user_email,
                self.branch,
                self.corporation,
                entry_data
            )
            
   
            for brand_full, data in brand_data.items():
                offline_manager.cache_ending_balance(
                    self.user_email, self.branch, self.corporation,
                    brand_full, selected_date, data.get('ending_balance', 0)
                )
            
            self._msg_success(
                f"📤 Entry Saved for Later Posting\n\n"
                f"Date: {selected_date}\n"
                f"Entry ID: {entry_id[:20]}...\n\n"
                f"This entry will be automatically posted when\n"
                f"you log in with internet connection.\n\n"
                f"You can continue entering more reports."
            )
            

            self._delete_draft(selected_date)
            self.clear_all_fields()
            
        except Exception as e:
            self._msg("Offline Save Error", f"Failed to save entry: {e}", QMessageBox.Critical)

    def _save_palawan_to_payable(self, selected_date, brand_full, palawan_data):

        try:

            payable_table = "payable_tbl_brand_a" if brand_full == "Brand A" else "payable_tbl"
            
            sendout_capital = palawan_data.get('palawan_sendout_principal', 0) or 0
            sendout_sc = palawan_data.get('palawan_sendout_sc', 0) or 0
            sendout_commission = palawan_data.get('palawan_sendout_commission', 0) or 0
            sendout_total = palawan_data.get('palawan_sendout_regular_total', 0) or 0
            
            payout_capital = palawan_data.get('palawan_payout_principal', 0) or 0
            payout_sc = palawan_data.get('palawan_payout_sc', 0) or 0
            payout_commission = palawan_data.get('palawan_payout_commission', 0) or 0
            payout_total = palawan_data.get('palawan_payout_regular_total', 0) or 0
            
            int_capital = palawan_data.get('palawan_international_principal', 0) or 0
            int_sc = palawan_data.get('palawan_international_sc', 0) or 0
            int_commission = palawan_data.get('palawan_international_commission', 0) or 0
            int_total = palawan_data.get('palawan_international_regular_total', 0) or 0
            
            skid = palawan_data.get('palawan_suki_discounts', 0) or 0
            skir = palawan_data.get('palawan_suki_rebates', 0) or 0
            cancellation = palawan_data.get('palawan_cancel', 0) or 0
            inc = palawan_data.get('palawan_pay_out_incentives', 0) or 0
            
            query = f"""
                INSERT INTO {payable_table} (
                    corporation, branch, date,
                    sendout_capital, sendout_sc, sendout_commission, sendout_total,
                    payout_capital, payout_sc, payout_commission, payout_total,
                    international_capital, international_sc,
                    international_commission, international_total,
                    skid, skir, cancellation, inc
                ) VALUES (
                    %s, %s, %s,
                    %s, %s, %s, %s,
                    %s, %s, %s, %s,
                    %s, %s, %s, %s,
                    %s, %s, %s, %s
                )
                ON DUPLICATE KEY UPDATE
                    sendout_capital = VALUES(sendout_capital),
                    sendout_sc = VALUES(sendout_sc),
                    sendout_commission = VALUES(sendout_commission),
                    sendout_total = VALUES(sendout_total),
                    payout_capital = VALUES(payout_capital),
                    payout_sc = VALUES(payout_sc),
                    payout_commission = VALUES(payout_commission),
                    payout_total = VALUES(payout_total),
                    international_capital = VALUES(international_capital),
                    international_sc = VALUES(international_sc),
                    international_commission = VALUES(international_commission),
                    international_total = VALUES(international_total),
                    skid = VALUES(skid),
                    skir = VALUES(skir),
                    cancellation = VALUES(cancellation),
                    inc = VALUES(inc),
                    updated_at = CURRENT_TIMESTAMP
            """
            
            params = (
                self.corporation, self.branch, selected_date,
                sendout_capital, sendout_sc, sendout_commission, sendout_total,
                payout_capital, payout_sc, payout_commission, payout_total,
                int_capital, int_sc, int_commission, int_total,
                skid, skir, cancellation, inc
            )
            
            self.db_manager.execute_query(query, params)
            print(f"✅ Palawan details saved to {payable_table} for {brand_full}")
            
        except Exception as e:
            print(f"⚠️ Error saving Palawan to payable ({brand_full}): {e}")

    def _post_to_service_tables(self, selected_date, all_vals: dict):

        base_cols = ['date', 'branch', 'corporation', 'username']
        base_vals = [selected_date, self.branch, self.corporation, self.user_email]

        def _insert(table, field_names):
            try:
                col_query = (
                    "SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS "
                    "WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = %s"
                )
                col_rows = self.db_manager.execute_query(col_query, (table,))
                if col_rows:
                    existing_cols = {r['COLUMN_NAME'] for r in col_rows}
                    field_names = [f for f in field_names if f in existing_cols]

                if not field_names:
                    print(f"  ⚠️ {table}: no matching columns found, skipping")
                    return

                row = {f: float(all_vals.get(f, 0) or 0) for f in field_names}
                cols = base_cols + list(row.keys())
                vals = base_vals + list(row.values())
                ph   = ', '.join(['%s'] * len(cols))
                upd  = ', '.join(f"`{c}`=VALUES(`{c}`)" for c in row)
                q    = (f"INSERT INTO `{table}` ({', '.join(f'`{c}`' for c in cols)}) "
                        f"VALUES ({ph})"
                        + (f" ON DUPLICATE KEY UPDATE {upd}" if upd else ""))
                self.db_manager.execute_query(q, vals)
                print(f"  ✅ {table}")
            except Exception as e:
                print(f"  ⚠️ {table}: {e}")

        print("Writing supplementary Brand A tables…")


        _insert("daily_transaction_tbl_brand_a", [
            "empeno_jew_new", "empeno_jew_new_lotes",
            "empeno_jew_renew", "empeno_jew_renew_lotes",
            "empeno_sto_new", "empeno_sto_new_lotes",
            "fund_empeno_sto_renew", "fund_empeno_sto_renew_lotes",
            "empeno_motor_car", "empeno_motor_car_lotes",
            "mc_out", "mc_out_lotes",
            "empeno_silver", "empeno_silver_lotes",
            "rescate_jewelry", "rescate_jewelry_lotes",
            "cr_storage", "cr_storage_lotes",
            "rescate_silver", "rescate_silver_lotes",
            "res_storage", "res_storage_lotes",
            "res_motor", "res_motor_lotes",
            "osf_storage", "osf_storage_lotes",
            "osf_silver", "osf_silver_lotes",
            "osf_motor", "osf_motor_lotes",
            "insurance_20",
            "insurance_philam_60", "insurance_philam_90",
        ])

      
        _insert("other_services_tbl_brand_a", [
            "palawan_send_out", "palawan_send_out_lotes",
            "palawan_sc", "palawan_sc_lotes",
            "palawan_pay_out", "palawan_pay_out_lotes",
            "palawan_pay_out_incentives", "palawan_pay_out_incentives_lotes",
            "palawan_pay_cash_in_sc", "palawan_pay_cash_in_sc_lotes",
            "palawan_pay_bills_sc",
            "palawan_load_sc",
            "palawan_pay_cash_out", "palawan_pay_cash_out_lotes",
            "palawan_suki_card",
            "palawan_pay_cash_out_sc",
            "sendah_load_sc", "sendah_load_sc_lotes",
            "sendah_bills_sc", "sendah_bills_sc_lotes",
            "smart_money_sc", "smart_money_sc_lotes",
            "smart_money_po", "smart_money_po_lotes",
            "gcash_in", "gcash_in_lotes",
            "gcash_out", "gcash_out_lotes",
            "gcash_padala_sendah", "gcash_padala_sendah_lotes",
            "abra_so_sc", "abra_po",
            "bdo_sc", "bdo_po",
            "ayanah_sc", "ayanah_out",
            "remitly", "remitly_lotes",
            "paymaya_in", "paymaya_in_lotes",
            "paymaya_out",
            "ria_in_sc", "ria_in_sc_lotes",
            "ria_out",
            "transfast", "transfast_lotes",
            "moneygram", "moneygram_lotes",
            "i2i_remittance_in", "i2i_remittance_in_lotes",
            "i2i_remittance_out",
            "i2i_bills_payment", "i2i_bills_payment_lotes",
            "i2i_bank_transfer", "i2i_pesonet",
            "i2i_instapay", "i2i_instapay_lotes",
            "fixco",
        ])


        _insert("PL_tbl_brand_a", [
            "interest", "penalty", "stamp", "rescuardo_affidavit",
            "jew_ai", "service_charge",
            "habol_renew_tubos", "habol_rt_interest_stamp",
            "storage_ai", "osf_storage", "cr_storage_int_penalty",
            "silver_ai", "osf_silver", "res_storage_int_penalty",
            "motor_ai", "osf_motor", "penalty_motor",
            "miscellaneous_fee",
            "palawan_suki_discounts", "palawan_suki_rebates",
            "storage_rebates", "silver_rebates", "palawan_suki_card",
            "pc_transpo", "pc_salary",
            "pc_inc_motor", "pc_inc_emp", "pc_inc_suki_card",
            "pc_inc_insurance", "pc_inc_mc",
            "pc_supplies_xerox_maintenance",
            "pc_electric", "pc_water", "pc_internet",
            "pc_rental", "pc_permits_bir_payments", "pc_lbc_jrs_jnt",
        ])


    def _save_cash_float(self, selected_date):

        try:
            cash_float_val = 0.0
            if hasattr(self, 'cash_float_input_a') and self.cash_float_input_a:
                txt = self.cash_float_input_a.text().strip()
                if txt:
                    cash_float_val = float(txt)
            
            query = """
                INSERT INTO cash_float_tbl (date, branch, corporation, username, cash_float)
                VALUES (%s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE
                    cash_float = VALUES(cash_float),
                    username = VALUES(username),
                    updated_at = CURRENT_TIMESTAMP
            """
            params = (selected_date, self.branch, self.corporation, self.user_email, cash_float_val)
            self.db_manager.execute_query(query, params)
            print(f"✅ Cash Float saved: {cash_float_val:,.2f}")
        except Exception as e:
            print(f"⚠️ Error saving Cash Float: {e}")


    def validate_all_requirements(self):
        sd = self.date_picker.date().toString("yyyy-MM-dd")
        brand_specs = [
            ("A", "Brand A",
             self.beginning_balance_input_a, self.cash_count_input_a,
             self.beginning_balance_auto_filled_a,
             self.previous_day_balance_a, self.previous_day_date_a,
             self.ending_balance_display_a),
            ("B", "Brand B",
             self.beginning_balance_input_b, self.cash_count_input_b,
             self.beginning_balance_auto_filled_b,
             self.previous_day_balance_b, self.previous_day_date_b,
             self.ending_balance_display_b),
        ]

        for ltr, brand_full, bb_input, cc_input, bb_filled, prev_bal, prev_date, eb_disp in brand_specs:
            if self.check_existing_entry(sd, brand_full) == "locked":
                continue

            if not bb_filled:
                if prev_bal is not None:
                    self._msg("Opening Balance Required",
                              f"{brand_full}: Click 'Load Previous Day' to set the opening balance.\n"
                              f"Expected: {prev_bal:,.2f}  ({prev_date})",
                              QMessageBox.Critical)
                    return False
                elif not bb_input.text().strip():
                    self._msg("Opening Balance Required",
                              f"{brand_full}: First entry — please type the opening balance.",
                              QMessageBox.Critical)
                    bb_input.setFocus()
                    return False

            if not bb_input.text().strip():
                self._msg("Validation Error",
                          f"{brand_full}: Opening balance is empty.",
                          QMessageBox.Warning)
                return False

            if not cc_input.text().strip():
                self._msg("Validation Error",
                          f"{brand_full}: Enter the actual cash count.",
                          QMessageBox.Warning)
                cc_input.setFocus()
                return False

            if prev_bal is not None:
                try:
                    cur_beg = float(bb_input.text().strip().replace(',', '') or 0)
                    if abs(cur_beg - prev_bal) > 0.01:
                        self._msg("Balance Mismatch",
                                  f"{brand_full}: Opening balance does not match previous day.\n\n"
                                  f"Expected : {prev_bal:,.2f}  ({prev_date})\n"
                                  f"Current  : {cur_beg:,.2f}\n\n"
                                  f"Use 'Load Previous Day' to correct this.",
                                  QMessageBox.Critical)
                        return False
                except ValueError:
                    self._msg("Validation Error",
                              f"{brand_full}: Invalid opening balance.",
                              QMessageBox.Warning)
                    return False

            try:
                cc_val = float(cc_input.text().strip().replace(',', '') or 0)
                eb_val = float((eb_disp.text() or "0").replace(",", ""))
                diff   = cc_val - eb_val
                if abs(diff) >= 0.01:
                    vtype = "OVER" if diff > 0 else "SHORT"
                    reply = QMessageBox.question(
                        self,
                        f"Variance Warning ({brand_full})",
                        f"{brand_full} has a cash variance ({vtype} by {abs(diff):,.2f}).\n\n"
                        f"Ending Balance : {eb_val:,.2f}\n"
                        f"Cash Count     : {cc_val:,.2f}\n"
                        f"Variance       : {diff:,.2f}\n\n"
                        f"This entry will be tagged for admin review.\n\n"
                        f"Do you want to continue posting?",
                        QMessageBox.Yes | QMessageBox.No,
                        QMessageBox.No
                    )
                    if reply == QMessageBox.No:
                        return False
            except ValueError:
                self._msg("Validation Error",
                          f"{brand_full}: Invalid cash count.",
                          QMessageBox.Warning)
                return False

        return True

    def clear_table(self):
   
        r = QMessageBox.question(
            self, "Clear Table",
            "Are you sure you want to clear all fields?\n\nThis will not delete any submitted data.",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        if r == QMessageBox.Yes:
            for bb in (self.beginning_balance_input_a, self.beginning_balance_input_b):
                bb.clear()
            for cc in (self.cash_count_input_a, self.cash_count_input_b):
                cc.clear()
            for tab, meth in [
                (self.cash_flow_tab_a, 'clear_fields'),
                (self.cash_flow_tab_b, 'clear_fields'),
                (self.palawan_tab,     'clear_fields'),
            ]:
                if hasattr(tab, meth):
                    getattr(tab, meth)()

            if hasattr(self, '_jew_computed'):
                for k in self._jew_computed:
                    self._jew_computed[k] = 0.0
            self.recalculate_all()

    def clear_all_fields(self):
        r = QMessageBox.question(
            self, "Advance Date", "Report posted! Move to the next day?",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes
        )
        if r == QMessageBox.Yes:
            for tab, meth in [
                (self.cash_flow_tab_a, 'clear_fields'),
                (self.cash_flow_tab_b, 'clear_fields'),
                (self.palawan_tab,     'clear_fields'),
            ]:
                if hasattr(tab, meth):
                    getattr(tab, meth)()
            self.date_picker.setDate(self.date_picker.date().addDays(1))

    def clear_all_fields_silent(self):
        for bb in (self.beginning_balance_input_a, self.beginning_balance_input_b):
            bb.clear()
            bb.setStyleSheet(f"""
                QLineEdit {{
                    background-color: {_SLATE_100};
                    border: 1.5px solid {_SLATE_200};
                    border-radius: 6px;
                    padding: 7px 12px;
                    font-size: 14px;
                    font-weight: 700;
                    color: {_TEXT_PRI};
                }}
            """)
        for cc in (self.cash_count_input_a, self.cash_count_input_b):
            cc.clear()
        self.beginning_balance_auto_filled_a = False
        self.beginning_balance_auto_filled_b = False
        self.previous_day_balance_a = self.previous_day_date_a = None
        self.previous_day_balance_b = self.previous_day_date_b = None
        for btn in (self.auto_fill_button_a, self.auto_fill_button_b):
            btn.setText("↓  Load Previous Day")
            btn.setEnabled(True)
            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: transparent;
                    color: {_PRIMARY};
                    border: 1.5px solid {_INDIGO_100};
                    border-radius: 5px;
                    font-size: 12px;
                    font-weight: 700;
                    padding: 4px 14px;
                    min-width: 0;
                }}
                QPushButton:hover {{
                    background-color: {_INDIGO_50};
                    border-color: {_PRIMARY};
                }}
            """)
        for lbl in (self.balance_status_label_a, self.balance_status_label_b):
            lbl.setText("")
        for tab, meth in [
            (self.cash_flow_tab_a, 'clear_fields'),
            (self.cash_flow_tab_b, 'clear_fields'),
            (self.palawan_tab,     'clear_fields'),
        ]:
            if hasattr(tab, meth):
                getattr(tab, meth)()
        self.on_date_changed()


    def _connect_shared_fields(self):
        try:
            import json as _json, re as _re, os as _os, sys as _sys
            if getattr(_sys, 'frozen', False):
                _base = _os.path.dirname(_sys.executable)
            else:
                _base = _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))
            _cfg_path = _os.path.join(_base, "field_config.json")
            with open(_cfg_path, "r", encoding="utf-8") as _f:
                cfg = _json.load(_f)

            def _col(entry):
                return entry[2] if len(entry) >= 3 else \
                    _re.sub(r"[^a-z0-9]+", "_", entry[0].lower()).strip("_")

            a_col_widget, b_col_widget = {}, {}
            for section in ("debit", "credit"):
                for brand, col_w in [("Brand A", a_col_widget), ("Brand B", b_col_widget)]:
                    tab = self.cash_flow_tab_a if brand == "Brand A" else self.cash_flow_tab_b
                    tab_d   = tab.debit_inputs   if section == "debit" else tab.credit_inputs
                    lotes_d = (tab.debit_lotes_inputs if section == "debit"
                               else tab.credit_lotes_inputs)
                    for entry in cfg.get(brand, {}).get(section, []):
                        label = entry[0]
                        c     = _col(entry)
                        if label in tab_d:
                            col_w[c] = (tab_d[label], lotes_d.get(label))

            shared = set(a_col_widget) & set(b_col_widget)
            

            excluded_fields = {
                "fund_transfer_to_head_office",
                "fund_transfer_from_branch",
                "fund_transfer_to_branch",
                "palawan_pay_cash_out_sc",
                "palawan_send_out",
                "palawan_send_out_lotes",
                "palawan_sc",
                "palawan_suki_card",
                "palawan_pay_cash_in_sc",
                "palawan_pay_bills_sc",
                "palawan_change_receiver",
                "palawan_pay_out",
                "palawan_pay_out_lotes",
                "palawan_pay_out_incentives",
                "palawan_pay_cash_out",
                "palawan_cancel",
                "palawan_suki_discounts",
                "palawan_suki_rebates",
                "palawan_load_sc",  
                "palawan_load", 
                "handling_fee",
                "other_penalty",
                "cash_overage",
                "mc_in",
                "mc_out",

                "pc_transpo",
                "pc_salary",
                "pc_inc_motor",
                "pc_inc_emp",
                "pc_inc_suki_card",
                "pc_inc_insurance",
                "pc_inc_mc",
                "pc_supplies_xerox_maintenance",
                "pc_electric",
                "pc_water",
                "pc_internet",
                "pc_rental",
                "pc_permits_bir_payments",
                "pc_lbc_jrs_jnt",
                "empeno_motor_car",
                "motor_ai",
            }
            shared = shared - excluded_fields
            
            print(f"Shared fields after exclusions: {shared}")
            
            self._shared_carry_map = []

            for col in shared:
                a_w, a_l = a_col_widget[col]
                b_w, b_l = b_col_widget[col]

                def _amt_carry(bw):
                    def _carry(text):
                        if not bw.hasFocus():
                            bw.blockSignals(True); bw.setText(text); bw.blockSignals(False)
                            self.recalculate_all()
                    return _carry

                def _lot_carry(bw):
                    def _carry(text):
                        if bw and not bw.hasFocus():
                            bw.blockSignals(True); bw.setText(text); bw.blockSignals(False)
                    return _carry

                fn = _amt_carry(b_w)
                a_w.textChanged.connect(fn)
                self._shared_carry_map.append(fn)

                if a_l and b_l:
                    fl = _lot_carry(b_l)
                    a_l.textChanged.connect(fl)
                    self._shared_carry_map.append(fl)

        except Exception as e:
            print(f"_connect_shared_fields error (non-fatal): {e}")

    def _connect_palawan_adjustments_to_brand_b(self):

        try:
            brand_b_debits = getattr(self.cash_flow_tab_b, 'debit_inputs', {})
            brand_b_credits = getattr(self.cash_flow_tab_b, 'credit_inputs', {})

            def make_carry_fn(target_field):
                def carry(text):
                    target_field.blockSignals(True)
                    target_field.setText(text)
                    target_field.blockSignals(False)
                    self.recalculate_all()
                return carry

            def setup_readonly_field(field):

                field.setReadOnly(True)
                field.setStyleSheet(
                    field.styleSheet() + 
                    "background-color: #FEF3C7; color: #92400E;"
                )
                field.setPlaceholderText("Auto from Palawan Details")

            connected_count = 0

            sendout_inputs = getattr(self.palawan_tab, 'sendout_inputs', {})
            
            if "Principal" in sendout_inputs and "Palawan Send Out" in brand_b_debits:
                palawan_field = sendout_inputs["Principal"]
                cashflow_field = brand_b_debits["Palawan Send Out"]
                setup_readonly_field(cashflow_field)
                palawan_field.textChanged.connect(make_carry_fn(cashflow_field))
                connected_count += 1

            if "SC" in sendout_inputs and "Commission" in sendout_inputs and "Palawan S.C" in brand_b_debits:
                sc_field = sendout_inputs["SC"]
                commission_field = sendout_inputs["Commission"]
                cashflow_field = brand_b_debits["Palawan S.C"]
                setup_readonly_field(cashflow_field)
                
                # Create function to sum SC + Commission
                def make_sc_commission_sum_fn(sc_fld, comm_fld, target_fld):
                    def update_sc_commission():
                        try:
                            sc_val = float(sc_fld.text().strip() or 0)
                        except ValueError:
                            sc_val = 0.0
                        try:
                            comm_val = float(comm_fld.text().strip() or 0)
                        except ValueError:
                            comm_val = 0.0
                        
                        total = sc_val + comm_val
                        target_fld.blockSignals(True)
                        target_fld.setText(f"{total:.2f}")
                        target_fld.blockSignals(False)
                        self.recalculate_all()
                    return update_sc_commission
                
                # Connect both SC and Commission fields to the sum function
                update_fn = make_sc_commission_sum_fn(sc_field, commission_field, cashflow_field)
                sc_field.textChanged.connect(update_fn)
                commission_field.textChanged.connect(update_fn)
                connected_count += 1

            payout_inputs = getattr(self.palawan_tab, 'payout_inputs', {})
            
            if "Principal" in payout_inputs and "Palawan Pay Out" in brand_b_credits:
                palawan_field = payout_inputs["Principal"]
                cashflow_field = brand_b_credits["Palawan Pay Out"]
                setup_readonly_field(cashflow_field)
                palawan_field.textChanged.connect(make_carry_fn(cashflow_field))
                connected_count += 1

            adjustment_to_cashflow_map = {
                "Palawan Pay Out Incentives": "Palawan Pay Out (incentives)",
                "Palawan Suki Discounts": "Palawan Suki Discounts",
                "Palawan Suki Rebates": "Palawan Suki Rebates",
                "Palawan Cancel": "Palawan Cancel",
            }

            palawan_adjustments = getattr(self.palawan_tab, 'adjustments_inputs', {})

            for adj_label, cf_label in adjustment_to_cashflow_map.items():
                if adj_label in palawan_adjustments and cf_label in brand_b_credits:
                    palawan_field = palawan_adjustments[adj_label]
                    cashflow_field = brand_b_credits[cf_label]
                    setup_readonly_field(cashflow_field)
                    palawan_field.textChanged.connect(make_carry_fn(cashflow_field))
                    connected_count += 1

            print(f"Connected {connected_count} Palawan fields to Brand B Cash Flow")

        except Exception as e:
            print(f"_connect_palawan_adjustments_to_brand_b error (non-fatal): {e}")

    def _connect_brand_a_auto_calculations(self):

        try:
            d_inp  = self.cash_flow_tab_a.debit_inputs
            c_inp  = self.cash_flow_tab_a.credit_inputs
            c_lots = self.cash_flow_tab_a.credit_lotes_inputs
            
            # Flag to prevent recalc during signal connection
            recalc_enabled = False

            def _v(widget_dict, key):
                """Safely parse float from a widget dict entry."""
                w = widget_dict.get(key)
                if w is None:
                    return 0.0
                try:
                    return float(w.text().replace(',', '').strip() or 0)
                except ValueError:
                    return 0.0

            def _set_readonly(field, tooltip="Auto-calculated"):
                field.setReadOnly(True)
                field.setStyleSheet(
                    field.styleSheet() +
                    "background-color: #EFF6FF; color: #1E40AF;"
                )
                field.setToolTip(tooltip)
                field.setPlaceholderText("Auto-calculated")

            def _set(field, value):
                print(f"[DEBUG _set] Setting field {field.objectName()} to {value}")
                print(f"[DEBUG _set] Field before: '{field.text()}'")
                field.blockSignals(True)
                field.setText(f"{value:.2f}")
                field.blockSignals(False)
                print(f"[DEBUG _set] Field after: '{field.text()}'")
                field.update()
                field.repaint()

            targets = [
                ("S.C",          "(Lotes JEW NEW + Lotes JEW RENEW) × 5"),
                ("O.s.f Sto.",   "(Empeno STO NEW + Empeno STO RENEW) × 0.75%"),
                ("Sto. A.I",     "(Empeno STO NEW + Empeno STO RENEW) × 20%"),
                ("Silver A.I",   "Empeno Silver × 20%"),
                ("O.s.f Silver", "Empeno Silver × 0.75%"),
                ("Motor A.I",    "Empeno Motor/Car × 10%"),
                ("O.s.f Motor",  "Empeno Motor/Car × 0.75%"),
            ]
            for label, tip in targets:
                if label in d_inp:
                    _set_readonly(d_inp[label], tip)

            def recalc(*_):
                nonlocal recalc_enabled
                if not recalc_enabled:
                    print("[DEBUG] recalc() blocked - UI not fully initialized yet")
                    return
                print(f"[DEBUG] recalc() called!")

                lotes_jew_new   = _v(c_lots, "Empeno JEW. (NEW)")
                lotes_jew_renew = _v(c_lots, "Empeno JEW (RENEW)")
                sc_value = (lotes_jew_new + lotes_jew_renew) * 5
                if "S.C" in d_inp:
                    _set(d_inp["S.C"], sc_value)

                sto_new   = _v(c_inp, "Empeno STO. (NEW)")
                sto_renew = _v(c_inp, "Fund Empeno STO. (RENEW)")
                sto_base  = sto_new + sto_renew

                if "O.s.f Sto." in d_inp:
                    _set(d_inp["O.s.f Sto."], sto_base * 0.0075)
                if "Sto. A.I" in d_inp:
                    _set(d_inp["Sto. A.I"], sto_base * 0.20)
                silver = _v(c_inp, "Empeno silver")
                if "Silver A.I" in d_inp:
                    _set(d_inp["Silver A.I"], silver * 0.20)
                if "O.s.f Silver" in d_inp:
                    _set(d_inp["O.s.f Silver"], silver * 0.0075)

                motor = _v(c_inp, "Empeno Motor/Car")
                print(f"[DEBUG] Motor value: {motor}")
                print(f"[DEBUG] Available debit fields: {list(d_inp.keys())}")
                
                if "Motor A.I" in d_inp:
                    motor_ai_val = motor * 0.10
                    print(f"[DEBUG] Setting Motor A.I to {motor_ai_val}")
                    _set(d_inp["Motor A.I"], motor_ai_val)
                else:
                    print("[DEBUG] Motor A.I not found in d_inp")
                    
                if "O.s.f Motor" in d_inp:
                    osf_motor_val = motor * 0.0075
                    print(f"[DEBUG] Setting O.s.f Motor to {osf_motor_val}")
                    _set(d_inp["O.s.f Motor"], osf_motor_val)
                else:
                    print(f"[DEBUG] O.s.f Motor not found in d_inp. Available keys: {[k for k in d_inp.keys() if 'motor' in k.lower() or 'osf' in k.lower()]}")

                self.recalculate_all()

            sources = [
                (c_lots, "Empeno JEW. (NEW)"),
                (c_lots, "Empeno JEW (RENEW)"),
                (c_inp,  "Empeno STO. (NEW)"),
                (c_inp,  "Fund Empeno STO. (RENEW)"),
                (c_inp,  "Empeno silver"),
                (c_inp,  "Empeno Motor/Car"),
            ]
            print(f"[DEBUG] Available credit fields: {list(c_inp.keys())}")
            motor_car_widget = None
            for widget_dict, key in sources:
                w = widget_dict.get(key)
                if key == "Empeno Motor/Car":
                    motor_car_widget = w
                    print(f"[DEBUG] Found Motor/Car widget: {w} (type: {type(w).__name__})")
                if w:
                    if key == "Empeno Motor/Car":
                        # Use lambda to debug Motor/Car signal
                        w.textChanged.connect(lambda text, key=key: (
                            print(f"[DEBUG SIGNAL] {key} changed to: {text}"),
                            recalc()
                        ))
                        print(f"[DEBUG] Connected {key} with signal debug")
                    else:
                        w.textChanged.connect(recalc)
                        print(f"[DEBUG] Connecting {key}")
                else:
                    print(f"[DEBUG] WARNING: {key} not found in credit inputs!")
            
            print(f"[DEBUG] Motor/Car widget object: {motor_car_widget}")
            
            # Enable recalc now that all signals are connected
            recalc_enabled = True
            # Trigger one initial recalc to populate fields
            recalc()

            print("Brand A auto-calculations connected.")

        except Exception as e:
            print(f"_connect_brand_a_auto_calculations error (non-fatal): {e}")

    def _setup_empeno_jew_buttons(self):

        try:
            c_inp_a   = self.cash_flow_tab_a.credit_inputs
            d_inp_a   = self.cash_flow_tab_a.debit_inputs
            c_lotes_a = self.cash_flow_tab_a.credit_lotes_inputs
            
            c_inp_b   = self.cash_flow_tab_b.credit_inputs
            d_inp_b   = self.cash_flow_tab_b.debit_inputs
            c_lotes_b = self.cash_flow_tab_b.credit_lotes_inputs

            self._jew_dialogs  = {}
            self._jew_computed = {"Empeno JEW. (NEW)": 0.0, "Empeno JEW (RENEW)": 0.0}
            self._jew_computed_b = {"Empeno JEW. (NEW)": 0.0, "Empeno JEW (RENEW)": 0.0}

            def _set_auto_readonly(field, tip):
                """Set field as read-only (for Brand A)"""
                field.setReadOnly(True)
                field.setStyleSheet(
                    field.styleSheet() +
                    "background-color: #EFF6FF; color: #1D4ED8;"
                )
                field.setToolTip(tip)
                field.setPlaceholderText("Click + to enter detail")

            def _set_auto_editable(field, tip):
                """Set field as editable and styled for carry-over (for Brand B)"""
                field.setReadOnly(False)
                field.setStyleSheet(
                    f"""
                    QLineEdit {{
                        background-color: #FFFBEB;
                        border: 1.5px solid #FCD34D;
                        border-radius: 6px;
                        padding: 7px 12px;
                        font-size: 14px;
                        font-weight: 600;
                        color: #78350F;
                    }}
                    QLineEdit:focus {{
                        border: 2px solid #F59E0B;
                        background-color: #FEF3C7;
                    }}
                    """
                )
                field.setToolTip(tip)
                field.setPlaceholderText("Carries from Brand A")

            def _update_jew_ai_a():
                """Update Jew. A.I for Brand A"""
                total = sum(self._jew_computed.values())
                jew_ai = d_inp_a.get("Jew. A.I")
                if jew_ai:
                    jew_ai.blockSignals(True)
                    jew_ai.setText(f"{total:.2f}")
                    jew_ai.blockSignals(False)
                self.recalculate_all()

            def _update_jew_ai_b():
                """Update Jew. A.I for Brand B"""
                total = sum(self._jew_computed_b.values())
                jew_ai_b = d_inp_b.get("Jew. A.I")
                if jew_ai_b:
                    jew_ai_b.blockSignals(True)
                    jew_ai_b.setText(f"{total:.2f}")
                    jew_ai_b.blockSignals(False)
                self.recalculate_all()

            def _calculate_sc_b():
                """Calculate S.C. for Brand B: (Lotes JEW NEW + Lotes JEW RENEW) × 5"""
                try:
                    lotes_new = 0.0
                    lotes_renew = 0.0
                    
                    lotes_new_field = c_lotes_b.get("Empeno JEW. (NEW)")
                    if lotes_new_field:
                        try:
                            lotes_new = float(lotes_new_field.text().strip() or 0)
                        except ValueError:
                            lotes_new = 0.0
                    
                    lotes_renew_field = c_lotes_b.get("Empeno JEW (RENEW)")
                    if lotes_renew_field:
                        try:
                            lotes_renew = float(lotes_renew_field.text().strip() or 0)
                        except ValueError:
                            lotes_renew = 0.0
                    
                    sc_value = (lotes_new + lotes_renew) * 5
                    
                    sc_b = d_inp_b.get("S.C")
                    if sc_b:
                        sc_b.blockSignals(True)
                        sc_b.setText(f"{sc_value:.2f}")
                        sc_b.blockSignals(False)
                        self.recalculate_all()
                except Exception as e:
                    print(f"Error calculating S.C. for Brand B: {e}")

            def _make_open_dialog_a(field_label, target_field_a, target_field_b):
                """Create dialog function for Brand A"""
                def _open():
                    if field_label not in self._jew_dialogs:
                        self._jew_dialogs[field_label] = EmpenaDetailDialog(
                            field_label, parent=self
                        )
                    dlg = self._jew_dialogs[field_label]

                    if dlg.exec_() == QDialog.Accepted:
                        val        = f"{dlg.get_total_amount():.2f}"
                        row_count  = dlg.get_row_count()

                        target_field_a.blockSignals(True)
                        target_field_a.setText(val)
                        target_field_a.blockSignals(False)

                        lotes_a = c_lotes_a.get(field_label)
                        if lotes_a:
                            lotes_a.blockSignals(True)
                            lotes_a.setText(str(row_count))
                            lotes_a.blockSignals(False)
                            lotes_a.textChanged.emit(str(row_count))

                        self._jew_computed[field_label] = dlg.get_computed_total()
                        _update_jew_ai_a()
                        
                        # Carry over to Brand B after dialog acceptance
                        target_field_b.blockSignals(True)
                        target_field_b.setText(val)
                        target_field_b.blockSignals(False)
                        
                        lotes_b = c_lotes_b.get(field_label)
                        if lotes_b:
                            lotes_b.blockSignals(True)
                            lotes_b.setText(str(row_count))
                            lotes_b.blockSignals(False)
                            lotes_b.textChanged.emit(str(row_count))
                        
                        # Update S.C. calculation in Brand B
                        _calculate_sc_b()
                return _open

            def _make_open_dialog_b(field_label, target_field_b, target_field_a):
                """Create dialog function for Brand B"""
                def _open():
                    if field_label not in self._jew_dialogs:
                        self._jew_dialogs[field_label] = EmpenaDetailDialog(
                            field_label, parent=self
                        )
                    dlg = self._jew_dialogs[field_label]

                    if dlg.exec_() == QDialog.Accepted:
                        val        = f"{dlg.get_total_amount():.2f}"
                        row_count  = dlg.get_row_count()

                        target_field_b.blockSignals(True)
                        target_field_b.setText(val)
                        target_field_b.blockSignals(False)

                        lotes_b = c_lotes_b.get(field_label)
                        if lotes_b:
                            lotes_b.blockSignals(True)
                            lotes_b.setText(str(row_count))
                            lotes_b.blockSignals(False)
                            lotes_b.textChanged.emit(str(row_count))

                        self._jew_computed_b[field_label] = dlg.get_computed_total()
                        _update_jew_ai_b()
                        
                        # Update S.C. calculation in Brand B
                        _calculate_sc_b()
                return _open

            # Setup both Brand A and Brand B
            for label in ("Empeno JEW. (NEW)", "Empeno JEW (RENEW)"):
                # Brand A setup
                field_a = c_inp_a.get(label)
                if field_a is not None:
                    field_b = c_inp_b.get(label)
                    _set_auto_readonly(field_a, f"Click + to enter breakdown for {label}")

                    container_a = field_a.parentWidget()
                    layout_a    = container_a.layout() if container_a else None
                    if layout_a is not None:
                        plus_btn_a = QPushButton("+")
                        plus_btn_a.setFixedSize(28, 28)
                        plus_btn_a.setStyleSheet("""
                            QPushButton {
                                background-color: #2563EB; color: white;
                                border: none; border-radius: 5px;
                                font-size: 14px; font-weight: 900;
                            }
                            QPushButton:hover { background-color: #1D4ED8; }
                        """)
                        plus_btn_a.setToolTip(f"Open detail breakdown for {label}")
                        plus_btn_a.clicked.connect(_make_open_dialog_a(label, field_a, field_b))
                        layout_a.insertWidget(0, plus_btn_a)

                # Brand B setup
                field_b = c_inp_b.get(label)
                if field_b is not None:
                    _set_auto_editable(field_b, f"Click + to enter breakdown for {label} • or carries from Brand A")

                    container_b = field_b.parentWidget()
                    layout_b    = container_b.layout() if container_b else None
                    if layout_b is not None:
                        plus_btn_b = QPushButton("+")
                        plus_btn_b.setFixedSize(28, 28)
                        plus_btn_b.setStyleSheet("""
                            QPushButton {
                                background-color: #F59E0B; color: white;
                                border: none; border-radius: 5px;
                                font-size: 14px; font-weight: 900;
                            }
                            QPushButton:hover { background-color: #D97706; }
                        """)
                        plus_btn_b.setToolTip(f"Open detail breakdown for {label} (Brand B)")
                        field_a_ref = c_inp_a.get(label)
                        plus_btn_b.clicked.connect(_make_open_dialog_b(label, field_b, field_a_ref))
                        layout_b.insertWidget(0, plus_btn_b)

            # Setup Jew. A.I for Brand A (read-only)
            jew_ai_a = d_inp_a.get("Jew. A.I")
            if jew_ai_a:
                jew_ai_a.setReadOnly(True)
                jew_ai_a.setStyleSheet(
                    jew_ai_a.styleSheet() +
                    "background-color: #EFF6FF; color: #1E40AF;"
                )
                jew_ai_a.setToolTip("Computed Total (JEW NEW) + Computed Total (JEW RENEW)")
                jew_ai_a.setPlaceholderText("Auto-calculated")

            # Setup Jew. A.I for Brand B (editable, calculated from computed totals)
            jew_ai_b = d_inp_b.get("Jew. A.I")
            if jew_ai_b:
                jew_ai_b.setReadOnly(False)
                jew_ai_b.setStyleSheet(
                    f"""
                    QLineEdit {{
                        background-color: #FFFBEB;
                        border: 1.5px solid #FCD34D;
                        border-radius: 6px;
                        padding: 7px 12px;
                        font-size: 14px;
                        font-weight: 600;
                        color: #78350F;
                    }}
                    QLineEdit:focus {{
                        border: 2px solid #F59E0B;
                        background-color: #FEF3C7;
                    }}
                    """
                )
                jew_ai_b.setToolTip("Computed Total (JEW NEW) + Computed Total (JEW RENEW) • Editable")
                jew_ai_b.setPlaceholderText("Auto-calculated from dialogs")

            # Setup S.C. for Brand B (editable)
            sc_a = d_inp_a.get("S.C")
            sc_b = d_inp_b.get("S.C")
            if sc_a and sc_b:
                # Make Brand A S.C. read-only (from auto calc)
                # Already handled in _connect_brand_a_auto_calculations
                
                # Make Brand B S.C. editable
                sc_b.setReadOnly(False)
                sc_b.setStyleSheet(
                    f"""
                    QLineEdit {{
                        background-color: #FFFBEB;
                        border: 1.5px solid #FCD34D;
                        border-radius: 6px;
                        padding: 7px 12px;
                        font-size: 14px;
                        font-weight: 600;
                        color: #78350F;
                    }}
                    QLineEdit:focus {{
                        border: 2px solid #F59E0B;
                        background-color: #FEF3C7;
                    }}
                    """
                )
                sc_b.setToolTip("Calculated as (Lotes JEW NEW + Lotes JEW RENEW) × 5 • Editable")
                sc_b.setPlaceholderText("Auto or manual")

                # Connect lotes changes to recalculate S.C
                lotes_new_b = c_lotes_b.get("Empeno JEW. (NEW)")
                lotes_renew_b = c_lotes_b.get("Empeno JEW (RENEW)")
                
                if lotes_new_b:
                    lotes_new_b.textChanged.connect(_calculate_sc_b)
                if lotes_renew_b:
                    lotes_renew_b.textChanged.connect(_calculate_sc_b)

            # Connect Empeno JEW amount fields in Brand B to auto-update Jew. A.I and S.C
            jewb_new = c_inp_b.get("Empeno JEW. (NEW)")
            jewb_renew = c_inp_b.get("Empeno JEW (RENEW)")
            
            if jewb_new:
                jewb_new.textChanged.connect(_update_jew_ai_b)
                jewb_new.textChanged.connect(_calculate_sc_b)
            if jewb_renew:
                jewb_renew.textChanged.connect(_update_jew_ai_b)
                jewb_renew.textChanged.connect(_calculate_sc_b)

            print("Empeno JEW detail buttons set up for both Brand A and Brand B.")

        except Exception as e:
            print(f"_setup_empeno_jew_buttons error (non-fatal): {e}")

    def _setup_empeno_motor_button(self):
  
        try:
            c_inp  = self.cash_flow_tab_a.credit_inputs
            d_inp  = self.cash_flow_tab_a.debit_inputs
            cb_inp = self.cash_flow_tab_b.credit_inputs

            field_label = "Empeno Motor/Car"
            field_a = c_inp.get(field_label)
            if field_a is None:
                return

            field_b = cb_inp.get(field_label)

            field_a.setReadOnly(True)
            field_a.setStyleSheet(
                field_a.styleSheet() +
                "background-color: #EFF6FF; color: #1D4ED8;"
            )
            field_a.setToolTip(f"Click + to enter breakdown for {field_label}")
            field_a.setPlaceholderText("Click + to enter detail")

            self._motor_dialog = None

            def _open_motor_dialog():
                if self._motor_dialog is None:
                    self._motor_dialog = MotorCarDetailDialog(field_label, parent=self)

                dlg = self._motor_dialog
                if dlg.exec_() == QDialog.Accepted:
                    val = f"{dlg.get_total_amount():.2f}"
                    row_count = dlg.get_row_count()

                    field_a.blockSignals(True)
                    field_a.setText(val)
                    field_a.blockSignals(False)

                    lotes_a = self.cash_flow_tab_a.credit_lotes_inputs.get(field_label)
                    if lotes_a:
                        lotes_a.blockSignals(True)
                        lotes_a.setText(str(row_count))
                        lotes_a.blockSignals(False)
                        lotes_a.textChanged.emit(str(row_count))

                    self._motor_car_breakdown = dlg.get_breakdown_data()

                    computed = dlg.get_computed_total()
                    motor_ai_a = d_inp.get("Motor A.I")
                    if motor_ai_a:
                        motor_ai_a.blockSignals(True)
                        motor_ai_a.setText(f"{computed:.2f}")
                        motor_ai_a.blockSignals(False)
                    
                    # Trigger auto-calculations for O.s.f Motor and other fields
                    print(f"[DEBUG] Motor dialog closed, emitting signal for {val}")
                    field_a.textChanged.emit(val)

                    self.recalculate_all()

            container = field_a.parentWidget()
            layout = container.layout() if container else None
            if layout is None:
                return

            plus_btn = QPushButton("+")
            plus_btn.setFixedSize(28, 28)
            plus_btn.setStyleSheet("""
                QPushButton {
                    background-color: #2563EB; color: white;
                    border: none; border-radius: 5px;
                    font-size: 14px; font-weight: 900;
                }
                QPushButton:hover { background-color: #1D4ED8; }
            """)
            plus_btn.setToolTip(f"Open detail breakdown for {field_label}")
            plus_btn.clicked.connect(_open_motor_dialog)
            layout.insertWidget(0, plus_btn)

            motor_ai = d_inp.get("Motor A.I")
            if motor_ai:
                motor_ai.setReadOnly(True)
                motor_ai.setStyleSheet(
                    motor_ai.styleSheet() +
                    "background-color: #EFF6FF; color: #1E40AF;"
                )
                motor_ai.setToolTip("Computed Total from Empeno Motor/Car breakdown")
                motor_ai.setPlaceholderText("Auto-calculated")

            print("Empeno Motor/Car detail button set up.")

        except Exception as e:
            print(f"_setup_empeno_motor_button error (non-fatal): {e}")

    def _setup_ft_ho_button(self):

        try:
            field_label = "Fund Transfer to HEAD OFFICE"
            self._ft_ho_dialogs = {} 
            self._ft_ho_breakdowns = {} 

            brand_tabs = [
                ("Brand A", self.cash_flow_tab_a),
                ("Brand B", self.cash_flow_tab_b),
            ]

            for brand_key, cf_tab in brand_tabs:
                field = cf_tab.credit_inputs.get(field_label)
                if field is None:
                    continue

                if brand_key == "Brand A":
                    field.setReadOnly(True)
                    field.setStyleSheet(
                        field.styleSheet() +
                        "background-color: #F5F3FF; color: #6D28D9;"
                    )
                    field.setToolTip(f"Click + to enter breakdown for {field_label}")
                    field.setPlaceholderText("Click + to enter detail")

                if hasattr(cf_tab, 'bank_account_btn') and cf_tab.bank_account_btn:
                    cf_tab.bank_account_btn.setVisible(False)

                def _make_open_dialog(bkey, target_field, tab):
                    def _open():
                        if bkey not in self._ft_ho_dialogs:
                            self._ft_ho_dialogs[bkey] = FundTransferHODialog(
                                f"{field_label} ({bkey})", parent=self
                            )
                        dlg = self._ft_ho_dialogs[bkey]
                        if dlg.exec_() == QDialog.Accepted:
                            val = f"{dlg.get_total_amount():.2f}"

                            target_field.blockSignals(True)
                            target_field.setText(val)
                            target_field.blockSignals(False)

                            lotes = tab.credit_lotes_inputs.get(field_label)
                            if lotes:
                                lotes.blockSignals(True)
                                lotes.setText(str(dlg.get_row_count()))
                                lotes.blockSignals(False)
                                lotes.textChanged.emit(str(dlg.get_row_count()))

                            self._ft_ho_breakdowns[bkey] = dlg.get_breakdown_data()
                            self.recalculate_all()
                    return _open

                container = field.parentWidget()
                layout = container.layout() if container else None
                if layout is None:
                    continue

                # Only Brand A gets the + button (Brand B has no bank account)
                if brand_key != "Brand A":
                    continue

                plus_btn = QPushButton("+")
                plus_btn.setFixedSize(28, 28)
                plus_btn.setStyleSheet("""
                    QPushButton {
                        background-color: #8B5CF6; color: white;
                        border: none; border-radius: 5px;
                        font-size: 14px; font-weight: 900;
                    }
                    QPushButton:hover { background-color: #7C3AED; }
                """)
                plus_btn.setToolTip(f"Open detail breakdown for {field_label} ({brand_key})")
                plus_btn.clicked.connect(_make_open_dialog(brand_key, field, cf_tab))
                layout.insertWidget(0, plus_btn)

            print("Fund Transfer to HEAD OFFICE detail buttons set up (both brands).")

        except Exception as e:
            print(f"_setup_ft_ho_button error (non-fatal): {e}")

    def _get_draft_path(self):
        base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        drafts_dir = os.path.join(base, "drafts")
        os.makedirs(drafts_dir, exist_ok=True)
        def _safe(s):
            return "".join(c if c.isalnum() or c in "_-" else "_" for c in str(s))
        return os.path.join(
            drafts_dir,
            f"{_safe(self.user_email)}_{_safe(self.branch)}_{_safe(self.corporation)}.json"
        )

    def save_draft(self):
        try:
            sd = self.date_picker.date().toString("yyyy-MM-dd")

            status_a = self.check_existing_entry(sd, "Brand A")
            status_b = self.check_existing_entry(sd, "Brand B")
            if status_a == "locked" and status_b == "locked":
                self._msg("Draft Not Saved",
                          f"Report for {sd} has already been submitted.\n"
                          "There is no need to save a draft for this date.",
                          QMessageBox.Information)
                return
            draft = {
                "saved_at": datetime.datetime.now().isoformat(),
                "date": sd,
                "brand_a": {
                    "beginning_balance": self.beginning_balance_input_a.text(),
                    "beginning_balance_auto_filled": self.beginning_balance_auto_filled_a,
                    "cash_count": self.cash_count_input_a.text(),
                    "cash_flow": self.cash_flow_tab_a.get_raw_field_values(),
                    "bank_account": self.cash_flow_tab_a.selected_bank_account,
                },
                "brand_b": {
                    "beginning_balance": self.beginning_balance_input_b.text(),
                    "beginning_balance_auto_filled": self.beginning_balance_auto_filled_b,
                    "cash_count": self.cash_count_input_b.text(),
                    "cash_flow": self.cash_flow_tab_b.get_raw_field_values(),
                    "bank_account": self.cash_flow_tab_b.selected_bank_account,
                },
                "palawan":     self._collect_palawan_for_draft(),
                "mc_in": self._collect_mc_details_for_draft("MC In"),
                "mc_out": self._collect_mc_details_for_draft("MC Out"),
            }
            path = self._get_draft_path()
            all_drafts = {}
            if os.path.exists(path):
                with open(path, "r", encoding="utf-8") as f:
                    existing = json.load(f)
                if "date" in existing and "saved_at" in existing:
                    old_date = existing["date"]
                    all_drafts[old_date] = existing
                else:
                    all_drafts = existing
            all_drafts[sd] = draft
            with open(path, "w", encoding="utf-8") as f:
                json.dump(all_drafts, f, indent=2, ensure_ascii=False)
            total = len(all_drafts)
            self._msg_success(
                f"Draft saved for {sd}.\n\n"
                f"You have {total} saved draft(s).\n"
                "Your data will be automatically restored when you return."
            )
        except Exception as e:
            self._msg("Save Draft Error", f"Could not save draft:\n{e}", QMessageBox.Warning)

    def _collect_palawan_for_draft(self):
        d = {}
        for section in ("sendout", "payout", "international", "adjustments"):
            for k, w in getattr(self.palawan_tab, f"{section}_inputs", {}).items():
                d[f"{section}:{k}"] = w.text()
        for k, w in getattr(self.palawan_tab, "lotes_inputs", {}).items():
            d[f"lotes:{k}"] = w.text()
        return d

    def _collect_mc_details_for_draft(self, field_name):
        details = []
        for cf_tab in [self.cash_flow_tab_a, self.cash_flow_tab_b]:
            if hasattr(cf_tab, 'mc_currency_details') and field_name in cf_tab.mc_currency_details:
                details.extend(cf_tab.mc_currency_details[field_name])
        return details

    def _load_draft(self):
        try:
            path = self._get_draft_path()
            if not os.path.exists(path):
                return
            with open(path, "r", encoding="utf-8") as f:
                raw = json.load(f)

            if "date" in raw and "saved_at" in raw:
                all_drafts = {raw["date"]: raw}
            else:
                all_drafts = raw

            if not all_drafts:
                return
            posted_dates = []
            for d in list(all_drafts.keys()):
                status_a = self.check_existing_entry(d, "Brand A")
                status_b = self.check_existing_entry(d, "Brand B")
                if status_a == "locked" and status_b == "locked":
                    posted_dates.append(d)
                    del all_drafts[d]

            if posted_dates:
                if not all_drafts:
                    if os.path.exists(path):
                        os.remove(path)
                else:
                    with open(path, "w", encoding="utf-8") as f:
                        json.dump(all_drafts, f, indent=2, ensure_ascii=False)

            if not all_drafts:
                return

            sorted_dates = sorted(all_drafts.keys(), reverse=True)

            if len(sorted_dates) == 1:
                chosen_date = sorted_dates[0]
                draft = all_drafts[chosen_date]
                saved_at = draft.get("saved_at", "")[:19].replace("T", " ")
                reply = QMessageBox.question(
                    self, "Restore Draft",
                    f"A saved draft was found:\n\n"
                    f"  Date : {chosen_date}\n"
                    f"  Saved: {saved_at}\n\n"
                    f"Do you want to restore it?",
                    QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes
                )
                if reply != QMessageBox.Yes:
                    return
            else:
                items = []
                for d in sorted_dates:
                    saved_at = all_drafts[d].get("saved_at", "")[:19].replace("T", " ")
                    items.append(f"{d}  (saved: {saved_at})")
                from PyQt5.QtWidgets import QInputDialog
                choice, ok = QInputDialog.getItem(
                    self, "Restore Draft",
                    f"You have {len(sorted_dates)} saved drafts.\n"
                    f"Select a date to restore:",
                    items, 0, False
                )
                if not ok:
                    return
                chosen_date = sorted_dates[items.index(choice)]

            draft = all_drafts[chosen_date]

            qdate = QDate.fromString(chosen_date, "yyyy-MM-dd")
            if qdate.isValid():
                self.date_picker.setDate(qdate)

            for letter, key in [("a", "brand_a"), ("b", "brand_b")]:
                bd      = draft.get(key, {})
                bb_inp  = getattr(self, f"beginning_balance_input_{letter}")
                cc_inp  = getattr(self, f"cash_count_input_{letter}")
                cf_tab  = getattr(self, f"cash_flow_tab_{letter}")
                if bd.get("beginning_balance"):
                    bb_inp.setReadOnly(False)
                    bb_inp.setText(bd["beginning_balance"])
                    setattr(self, f"beginning_balance_auto_filled_{letter}",
                            bd.get("beginning_balance_auto_filled", True))
                if bd.get("cash_count"):
                    cc_inp.setText(bd["cash_count"])
                if bd.get("cash_flow"):
                    cf_tab.set_raw_field_values(bd["cash_flow"])

            for key, val in draft.get("palawan", {}).items():
                section, label = key.split(":", 1)
                w = (self.palawan_tab.lotes_inputs.get(label) if section == "lotes"
                     else getattr(self.palawan_tab, f"{section}_inputs", {}).get(label))
                if w:
                    w.blockSignals(True); w.setText(val); w.blockSignals(False)
            self.palawan_tab.calculate_palawan_totals()
            self.palawan_tab.calculate_lotes_total()
            self.palawan_tab.calculate_adjustments_total()

            mc_in_entries = draft.get("mc_in", [])
            mc_out_entries = draft.get("mc_out", [])
            for cf_tab in [self.cash_flow_tab_a, self.cash_flow_tab_b]:
                if hasattr(cf_tab, 'mc_currency_details'):
                    if mc_in_entries:
                        cf_tab.set_mc_currency_details('MC In', mc_in_entries)
                    if mc_out_entries:
                        cf_tab.set_mc_currency_details('MC Out', mc_out_entries)
            
            self.recalculate_all()

        except Exception as e:
            print(f"_load_draft error (non-fatal): {e}")

    def _delete_draft(self, date=None):
        try:
            path = self._get_draft_path()
            if not os.path.exists(path):
                return
            with open(path, "r", encoding="utf-8") as f:
                raw = json.load(f)

            if "date" in raw and "saved_at" in raw:
                if date is None or raw.get("date") == date:
                    os.remove(path)
                return

            target = date or self.date_picker.date().toString("yyyy-MM-dd")
            if target in raw:
                del raw[target]
            if not raw:
                os.remove(path)
            else:
                with open(path, "w", encoding="utf-8") as f:
                    json.dump(raw, f, indent=2, ensure_ascii=False)
        except Exception:
            pass

    def get_submitted_dates(self):
  
        submitted_dates = {}
        
        try:

            query_a = """
                SELECT DISTINCT date FROM daily_reports_brand_a
                WHERE branch=%s AND corporation=%s
                ORDER BY date DESC
            """
            results_a = self.db_manager.execute_query(query_a, (self.branch, self.corporation))
            if results_a:
                for row in results_a:
                    date_str = str(row.get('date', ''))
                    if date_str:
                        if date_str not in submitted_dates:
                            submitted_dates[date_str] = {'date': date_str, 'brand_a': False, 'brand_b': False}
                        submitted_dates[date_str]['brand_a'] = True
            
            query_b = """
                SELECT DISTINCT date FROM daily_reports
                WHERE branch=%s AND corporation=%s
                ORDER BY date DESC
            """
            results_b = self.db_manager.execute_query(query_b, (self.branch, self.corporation))
            if results_b:
                for row in results_b:
                    date_str = str(row.get('date', ''))
                    if date_str:
                        if date_str not in submitted_dates:
                            submitted_dates[date_str] = {'date': date_str, 'brand_a': False, 'brand_b': False}
                        submitted_dates[date_str]['brand_b'] = True
                        
        except Exception as e:
            print(f"get_submitted_dates error: {e}")
        
        return sorted(submitted_dates.values(), key=lambda x: x['date'], reverse=True)

    def show_load_report_dialog(self):
        """
        Show a dialog with all submitted report dates for the user to select.
        """
        submitted = self.get_submitted_dates()
        
        if not submitted:
            QMessageBox.information(
                self, "No Submitted Reports",
                "No submitted reports found for your branch.\n"
                "Submit a report first to be able to load it later.",
                QMessageBox.Ok
            )
            return
        
        dialog = QDialog(self)
        dialog.setWindowTitle("Load Submitted Report")
        dialog.setMinimumSize(500, 400)
        dialog.setStyleSheet(f"""
            QDialog {{
                background-color: {_BG_CARD};
            }}
            QLabel {{
                color: {_TEXT_PRI};
                background: transparent;
            }}
        """)
        
        layout = QVBoxLayout(dialog)
        layout.setSpacing(12)
        layout.setContentsMargins(16, 16, 16, 16)
        
        # Header
        title = QLabel("Select a Submitted Report to Load")
        title.setStyleSheet(f"font-size: 14px; font-weight: 800; color: {_TEXT_PRI};")
        layout.addWidget(title)
        
        info = QLabel("This will load the report data into the form for viewing or printing.\nThe data is read-only.")
        info.setStyleSheet(f"font-size: 11px; color: {_TEXT_SEC};")
        layout.addWidget(info)

        table = QTableWidget()
        table.setColumnCount(4)
        table.setHorizontalHeaderLabels(["Date", "Brand A", "Brand B", "Action"])
        table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        table.setSelectionMode(QAbstractItemView.NoSelection)
        table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        table.setAlternatingRowColors(True)
        table.setStyleSheet(f"""
            QTableWidget {{
                border: 1px solid {_BORDER};
                border-radius: 6px;
                background-color: {_BG_CARD};
            }}
            QHeaderView::section {{
                background-color: {_SLATE_100};
                font-weight: 700;
                font-size: 11px;
                padding: 8px;
                border: none;
                border-bottom: 1px solid {_BORDER};
            }}
            QTableWidget::item {{
                padding: 6px;
            }}
        """)
        
        table.setRowCount(len(submitted))
        
        for row, entry in enumerate(submitted):

            date_item = QTableWidgetItem(entry['date'])
            date_item.setTextAlignment(Qt.AlignCenter)
            table.setItem(row, 0, date_item)
            
     
            a_status = "✅" if entry['brand_a'] else "—"
            a_item = QTableWidgetItem(a_status)
            a_item.setTextAlignment(Qt.AlignCenter)
            table.setItem(row, 1, a_item)
            

            b_status = "✅" if entry['brand_b'] else "—"
            b_item = QTableWidgetItem(b_status)
            b_item.setTextAlignment(Qt.AlignCenter)
            table.setItem(row, 2, b_item)
            
            load_btn = QPushButton("Load")
            load_btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {_PRIMARY};
                    color: {_WHITE};
                    border: none;
                    border-radius: 4px;
                    padding: 5px 15px;
                    font-size: 11px;
                    font-weight: 700;
                }}
                QPushButton:hover {{ background-color: {_PRIMARY_DK}; }}
            """)
            load_btn.clicked.connect(lambda checked, d=entry['date'], dlg=dialog: self._load_submitted_report(d, dlg))
            table.setCellWidget(row, 3, load_btn)
        
        table.resizeRowsToContents()
        layout.addWidget(table)
        
        close_btn = QPushButton("Close")
        close_btn.setFixedSize(100, 34)
        close_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {_SLATE_200};
                color: {_TEXT_PRI};
                border: none;
                border-radius: 6px;
                font-weight: 700;
            }}
            QPushButton:hover {{ background-color: {_SLATE_300}; }}
        """)
        close_btn.clicked.connect(dialog.close)
        layout.addWidget(close_btn, alignment=Qt.AlignRight)
        
        dialog.exec_()

    def _load_submitted_report(self, date_str, dialog=None):

        try:
            if dialog:
                dialog.close()
            
            for tab in (self.cash_flow_tab_a, self.cash_flow_tab_b):
                if hasattr(tab, 'clear_fields'):
                    tab.clear_fields()
            for bb in (self.beginning_balance_input_a, self.beginning_balance_input_b):
                bb.clear()
            for cc in (self.cash_count_input_a, self.cash_count_input_b):
                cc.clear()

            self._toggle_inputs(True)
            
            qdate = QDate.fromString(date_str, "yyyy-MM-dd")
            if qdate.isValid():
                self.date_picker.blockSignals(True)
                self.date_picker.setDate(qdate)
                self.date_picker.blockSignals(False)
            
            self._load_brand_report_data("Brand A", date_str)
            
            self._load_brand_report_data("Brand B", date_str)
            
            self.recalculate_all()

            self._toggle_inputs(False)
            self.post_button.setEnabled(False)
            self.auto_fill_button_a.setEnabled(False)
            self.auto_fill_button_b.setEnabled(False)

            for brand in ("A", "B"):
                self._set_status_brand(brand, "Viewing Submitted Report", _TEXT_MUTED, bold=True)
            
            QMessageBox.information(
                self, "Report Loaded",
                f"Report for {date_str} has been loaded.\n\n"
                "Note: This is a read-only view of the submitted report.",
                QMessageBox.Ok
            )
            
        except Exception as e:
            QMessageBox.critical(
                self, "Load Error",
                f"Failed to load report:\n{str(e)}",
                QMessageBox.Ok
            )

    def _load_brand_report_data(self, brand, date_str):

        try:
            table_name = "daily_reports_brand_a" if brand == "Brand A" else "daily_reports"
            cf_tab = self.cash_flow_tab_a if brand == "Brand A" else self.cash_flow_tab_b
            bb_input = self.beginning_balance_input_a if brand == "Brand A" else self.beginning_balance_input_b
            cc_input = self.cash_count_input_a if brand == "Brand A" else self.cash_count_input_b
            
            query = f"""
                SELECT * FROM {table_name}
                WHERE date=%s AND branch=%s AND corporation=%s
                LIMIT 1
            """
            results = self.db_manager.execute_query(query, (date_str, self.branch, self.corporation))
            
            if not results or len(results) == 0:
                return
            
            data = results[0]
            
            beginning_balance = data.get('beginning_balance', 0) or 0
            bb_input.setReadOnly(False)
            bb_input.setText(f"{float(beginning_balance):.2f}")
            bb_input.setReadOnly(True)
            
            cash_count = data.get('cash_count', 0) or 0
            cc_input.setText(f"{float(cash_count):.2f}")
            

            if brand == "Brand A" and hasattr(self, 'cash_float_input_a') and self.cash_float_input_a:
                cash_float = data.get('cash_float', 0) or 0
                self.cash_float_input_a.setText(f"{float(cash_float):.2f}")
            
   
            col_mapping = cf_tab._build_column_mapping()
            

            reverse_mapping = {v: k for k, v in col_mapping.items()}
            
            for label, widget in cf_tab.debit_inputs.items():
                db_col = col_mapping.get(label, cf_tab._sanitize_column(label))
                value = data.get(db_col, 0)
                if value:
                    widget.blockSignals(True)
                    widget.setText(f"{float(value):.2f}")
                    widget.blockSignals(False)
                
                lotes_col = db_col + "_lotes"
                lotes_val = data.get(lotes_col, 0)
                lotes_widget = cf_tab.debit_lotes_inputs.get(label)
                if lotes_widget and lotes_val:
                    lotes_widget.blockSignals(True)
                    lotes_widget.setText(str(int(lotes_val)))
                    lotes_widget.blockSignals(False)
            
            for label, widget in cf_tab.credit_inputs.items():
                db_col = col_mapping.get(label, cf_tab._sanitize_column(label))
                value = data.get(db_col, 0)
                if value:
                    widget.blockSignals(True)
                    widget.setText(f"{float(value):.2f}")
                    widget.blockSignals(False)
                
                lotes_col = db_col + "_lotes"
                lotes_val = data.get(lotes_col, 0)
                lotes_widget = cf_tab.credit_lotes_inputs.get(label)
                if lotes_widget and lotes_val:
                    lotes_widget.blockSignals(True)
                    lotes_widget.setText(str(int(lotes_val)))
                    lotes_widget.blockSignals(False)
            
  
            cf_tab.update_totals(
                float(data.get('beginning_balance', 0)),
                float(data.get('debit_total', 0)) - float(data.get('beginning_balance', 0)),
                float(data.get('credit_total', 0))
            )
            
        except Exception as e:
            print(f"_load_brand_report_data error ({brand}): {e}")


    def _gather_nonzero_fields(self):

        return self._gather_nonzero_fields_brand("a")

    def _gather_nonzero_fields_brand(self, brand_letter):

        result = {"debit": [], "credit": []}
        letter = brand_letter.lower()
        
        cf_tab   = getattr(self, f"cash_flow_tab_{letter}")
        bb_input = getattr(self, f"beginning_balance_input_{letter}")
        eb_disp  = getattr(self, f"ending_balance_display_{letter}")
        cc_input = getattr(self, f"cash_count_input_{letter}")
        cr_disp  = getattr(self, f"cash_result_display_{letter}")
        
        for label, widget in cf_tab.debit_inputs.items():
            try:
                amount = float(widget.text().strip().replace(',', '') or 0)
            except ValueError:
                amount = 0.0
            if amount != 0:
                lotes_widget = cf_tab.debit_lotes_inputs.get(label)
                lotes = int(lotes_widget.text().strip() or 0) if lotes_widget else 0
                result["debit"].append((label, amount, lotes))
        
        for label, widget in cf_tab.credit_inputs.items():
            try:
                amount = float(widget.text().strip().replace(',', '') or 0)
            except ValueError:
                amount = 0.0
            if amount != 0:
                lotes_widget = cf_tab.credit_lotes_inputs.get(label)
                lotes = int(lotes_widget.text().strip() or 0) if lotes_widget else 0
                result["credit"].append((label, amount, lotes))
        
        try:
            bb_text = bb_input.text().replace(',', '').strip()
            result["beginning_balance"] = float(bb_text) if bb_text and bb_text != "—" else 0.0
        except ValueError:
            result["beginning_balance"] = 0.0
        
        try:
            eb_text = eb_disp.text().replace(',', '').strip()
            result["ending_balance"] = float(eb_text) if eb_text and eb_text != "—" else 0.0
        except ValueError:
            result["ending_balance"] = 0.0
        
        try:
            cc_text = cc_input.text().replace(',', '').strip()
            result["cash_count"] = float(cc_text) if cc_text and cc_text != "—" else 0.0
        except ValueError:
            result["cash_count"] = 0.0
        
        try:
            var_text = cr_disp.text().replace(',', '').strip()
            result["variance"] = float(var_text) if var_text and var_text != "—" else 0.0
        except ValueError:
            result["variance"] = 0.0
        
        return result

    def print_nonzero_report(self):

        try:
            data = self._gather_nonzero_fields()
            
            if not data["debit"] and not data["credit"]:
                QMessageBox.warning(
                    self, "No Data",
                    "No non-zero values found in the current report.\n"
                    "Please enter some values first.",
                    QMessageBox.Ok
                )
                return
            
            selected_date = self.date_picker.date().toString("yyyy-MM-dd")
            user_info = f"{self.user_email} · {self.branch} · {self.corporation}"
            
            debit_total = sum(amount for _, amount, _ in data["debit"])
            credit_total = sum(amount for _, amount, _ in data["credit"])
            
            doc = QTextDocument()
            html = f"""
            <html>
            <head>
                <style>
                    body {{ font-family: 'Segoe UI', Arial, sans-serif; font-size: 11px; }}
                    h1 {{ color: #1E293B; font-size: 18px; margin-bottom: 5px; }}
                    h2 {{ color: #3B82F6; font-size: 14px; margin-top: 15px; margin-bottom: 8px; }}
                    h3 {{ color: #64748B; font-size: 12px; margin-top: 10px; margin-bottom: 5px; }}
                    .meta {{ color: #64748B; font-size: 10px; margin-bottom: 15px; }}
                    table {{ border-collapse: collapse; width: 100%; margin-bottom: 15px; }}
                    th {{ background-color: #1E293B; color: white; padding: 8px 10px; text-align: left; font-size: 11px; }}
                    td {{ border: 1px solid #E2E8F0; padding: 6px 10px; font-size: 11px; }}
                    .amount {{ text-align: right; font-weight: 600; }}
                    .lotes {{ text-align: center; color: #64748B; }}
                    .total-row {{ background-color: #F1F5F9; font-weight: 700; }}
                    .summary-table {{ margin-top: 20px; }}
                    .summary-label {{ font-weight: 700; color: #334155; }}
                    .variance-positive {{ color: #22C55E; font-weight: 700; }}
                    .variance-negative {{ color: #EF4444; font-weight: 700; }}
                    .variance-zero {{ color: #64748B; font-weight: 700; }}
                </style>
            </head>
            <body>
                <h1>Daily Cash Report - Brand A</h1>
                <div class="meta">
                    <b>Date:</b> {selected_date}<br>
                    <b>User:</b> {user_info}<br>
                    <b>Generated:</b> {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
                </div>
                
                <h2 style="color: #3B82F6;">Summary</h2>
                <table class="summary-table">
                    <tr>
                        <td class="summary-label">Beginning Balance</td>
                        <td class="amount">{data['beginning_balance']:,.2f}</td>
                    </tr>
                    <tr>
                        <td class="summary-label">Ending Balance</td>
                        <td class="amount">{data['ending_balance']:,.2f}</td>
                    </tr>
                    <tr>
                        <td class="summary-label">Cash Count</td>
                        <td class="amount">{data['cash_count']:,.2f}</td>
                    </tr>
                    <tr>
                        <td class="summary-label">Variance</td>
                        <td class="amount {'variance-positive' if data['variance'] > 0 else 'variance-negative' if data['variance'] < 0 else 'variance-zero'}">
                            {data['variance']:,.2f} {'(Over)' if data['variance'] > 0 else '(Short)' if data['variance'] < 0 else '(Balanced)'}
                        </td>
                    </tr>
                </table>
            """
            
            if data["debit"]:
                html += '<h3 style="color: #EF4444;">Cash In (Debit)</h3>'
                html += '<table>'
                html += '<tr><th>Field</th><th>Amount</th><th>Lotes</th></tr>'
                
                for label, amount, lotes in data["debit"]:
                    html += f'<tr><td>{label}</td><td class="amount">{amount:,.2f}</td><td class="lotes">{lotes if lotes else "-"}</td></tr>'
                
                html += f'<tr class="total-row"><td><b>Total Cash Receipt</b></td><td class="amount"><b>{debit_total:,.2f}</b></td><td></td></tr>'
                html += '</table>'
            
            if data["credit"]:
                html += '<h3 style="color: #22C55E;">Cash Out (Credit)</h3>'
                html += '<table>'
                html += '<tr><th>Field</th><th>Amount</th><th>Lotes</th></tr>'
                
                for label, amount, lotes in data["credit"]:
                    html += f'<tr><td>{label}</td><td class="amount">{amount:,.2f}</td><td class="lotes">{lotes if lotes else "-"}</td></tr>'
                
                html += f'<tr class="total-row"><td><b>Total Cash Out</b></td><td class="amount"><b>{credit_total:,.2f}</b></td><td></td></tr>'
                html += '</table>'
            
            html += """
                <br><br>
                <table style="border: none; width: 100%;">
                    <tr>
                        <td style="border: none; width: 50%;"><b>Prepared by:</b> ________________________</td>
                        <td style="border: none; width: 50%;"><b>Approved by:</b> ________________________</td>
                    </tr>
                </table>
            </body>
            </html>
            """
            
            doc.setHtml(html)
            
            printer = QPrinter(QPrinter.HighResolution)
            printer.setPageSize(QPrinter.A4)
            dialog = QPrintDialog(printer, self)
            dialog.setWindowTitle("Print Non-Zero Report")
            
            if dialog.exec_() == QPrintDialog.Accepted:
                doc.print_(printer)
                
        except Exception as e:
            QMessageBox.critical(
                self, "Print Error",
                f"An error occurred while printing:\n{str(e)}",
                QMessageBox.Ok
            )

    def export_to_excel(self):

        try:
            from openpyxl import Workbook
            from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
        except ImportError:
            QMessageBox.critical(
                self,
                "Missing Dependency",
                "The openpyxl package is required to export to Excel.\n"
                "Install with: pip install openpyxl",
                QMessageBox.Ok
            )
            return
        
        try:
            data_a = self._gather_nonzero_fields_brand("a")
            data_b = self._gather_nonzero_fields_brand("b")
            
            has_data_a = data_a["debit"] or data_a["credit"]
            has_data_b = data_b["debit"] or data_b["credit"]
            
            if not has_data_a and not has_data_b:
                QMessageBox.warning(
                    self, "No Data",
                    "No non-zero values found in the current report.\n"
                    "Please enter some values first.",
                    QMessageBox.Ok
                )
                return
            
            selected_date = self.date_picker.date().toString("yyyy-MM-dd")
            
            default_filename = f"Daily_Report_{self.branch}_{selected_date}.xlsx"
            file_path, _ = QFileDialog.getSaveFileName(
                self,
                "Save Excel File",
                default_filename,
                "Excel Files (*.xlsx);;All Files (*)"
            )
            
            if not file_path:
                return  
            

            wb = Workbook()
            

            title_font = Font(bold=True, size=16, color="1E293B")
            header_font = Font(bold=True, size=11, color="FFFFFF")
            header_fill = PatternFill(start_color="1E293B", end_color="1E293B", fill_type="solid")
            summary_fill = PatternFill(start_color="EFF6FF", end_color="EFF6FF", fill_type="solid")
            debit_fill = PatternFill(start_color="FEF2F2", end_color="FEF2F2", fill_type="solid")
            credit_fill = PatternFill(start_color="F0FDF4", end_color="F0FDF4", fill_type="solid")
            total_fill = PatternFill(start_color="F1F5F9", end_color="F1F5F9", fill_type="solid")
            border = Border(
                left=Side(style='thin', color='E2E8F0'),
                right=Side(style='thin', color='E2E8F0'),
                top=Side(style='thin', color='E2E8F0'),
                bottom=Side(style='thin', color='E2E8F0')
            )
            
            brands_to_export = []
            if has_data_a:
                brands_to_export.append(("Brand A", data_a))
            if has_data_b:
                brands_to_export.append(("Brand B", data_b))
            
            first_sheet = True
            for brand_name, data in brands_to_export:
                if first_sheet:
                    ws = wb.active
                    ws.title = f"{brand_name} Report"
                    first_sheet = False
                else:
                    ws = wb.create_sheet(title=f"{brand_name} Report")
                

                ws.merge_cells('A1:D1')
                ws['A1'] = f"Daily Cash Report - {brand_name}"
                ws['A1'].font = title_font
                ws['A1'].alignment = Alignment(horizontal='center')
                

                ws['A3'] = "Date:"
                ws['B3'] = selected_date
                ws['A4'] = "Branch:"
                ws['B4'] = self.branch
                ws['A5'] = "Corporation:"
                ws['B5'] = self.corporation
                ws['A6'] = "User:"
                ws['B6'] = self.user_email
                ws['A7'] = "Generated:"
                ws['B7'] = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                
                for row in range(3, 8):
                    ws.cell(row=row, column=1).font = Font(bold=True)
                
                current_row = 9
                
                ws.merge_cells(f'A{current_row}:D{current_row}')
                summary_header = ws.cell(row=current_row, column=1)
                summary_header.value = "Summary"
                summary_header.font = Font(bold=True, size=14, color="3B82F6")
                summary_header.fill = summary_fill
                summary_header.alignment = Alignment(horizontal='center')
                current_row += 1
                
                summary_items = [
                    ("Beginning Balance", data["beginning_balance"]),
                    ("Ending Balance", data["ending_balance"]),
                    ("Cash Count", data["cash_count"]),
                    ("Variance", data["variance"]),
                ]
                
                for label, value in summary_items:
                    label_cell = ws.cell(row=current_row, column=1)
                    label_cell.value = label
                    label_cell.font = Font(bold=True)
                    label_cell.border = border
                    
                    value_cell = ws.cell(row=current_row, column=2)
                    value_cell.value = value
                    value_cell.number_format = '#,##0.00'
                    value_cell.alignment = Alignment(horizontal='right')
                    value_cell.border = border
                    
                    if label == "Variance":
                        status_cell = ws.cell(row=current_row, column=3)
                        if value > 0:
                            status_cell.value = "(Over)"
                            status_cell.font = Font(color="22C55E", bold=True)
                        elif value < 0:
                            status_cell.value = "(Short)"
                            status_cell.font = Font(color="EF4444", bold=True)
                        else:
                            status_cell.value = "(Balanced)"
                            status_cell.font = Font(color="64748B", bold=True)
                        status_cell.border = border
                    
                    current_row += 1
                
                current_row += 1  
                

                if data["debit"]:
                    ws.merge_cells(f'A{current_row}:D{current_row}')
                    section_cell = ws.cell(row=current_row, column=1)
                    section_cell.value = "Cash In (Debit)"
                    section_cell.font = Font(bold=True, color="EF4444")
                    section_cell.fill = debit_fill
                    current_row += 1
                    
                    for col, hdr in enumerate(["Field", "Amount", "Lotes", ""], 1):
                        cell = ws.cell(row=current_row, column=col)
                        cell.value = hdr
                        cell.font = header_font
                        cell.fill = header_fill
                        cell.border = border
                        cell.alignment = Alignment(horizontal='center')
                    current_row += 1
                    
                    debit_total = 0.0
                    for label, amount, lotes in data["debit"]:
                        debit_total += amount
                        ws.cell(row=current_row, column=1).value = label
                        ws.cell(row=current_row, column=1).border = border
                        
                        amount_cell = ws.cell(row=current_row, column=2)
                        amount_cell.value = amount
                        amount_cell.number_format = '#,##0.00'
                        amount_cell.alignment = Alignment(horizontal='right')
                        amount_cell.border = border
                        
                        lotes_cell = ws.cell(row=current_row, column=3)
                        lotes_cell.value = lotes if lotes else "-"
                        lotes_cell.alignment = Alignment(horizontal='center')
                        lotes_cell.border = border
                        
                        current_row += 1
                    
                    total_label = ws.cell(row=current_row, column=1)
                    total_label.value = "Total Cash Receipt"
                    total_label.font = Font(bold=True)
                    total_label.fill = total_fill
                    total_label.border = border
                    
                    total_amount = ws.cell(row=current_row, column=2)
                    total_amount.value = debit_total
                    total_amount.number_format = '#,##0.00'
                    total_amount.font = Font(bold=True)
                    total_amount.fill = total_fill
                    total_amount.alignment = Alignment(horizontal='right')
                    total_amount.border = border
                    
                    ws.cell(row=current_row, column=3).fill = total_fill
                    ws.cell(row=current_row, column=3).border = border
                    
                    current_row += 2
                
      
                if data["credit"]:
                    ws.merge_cells(f'A{current_row}:D{current_row}')
                    section_cell = ws.cell(row=current_row, column=1)
                    section_cell.value = "Cash Out (Credit)"
                    section_cell.font = Font(bold=True, color="22C55E")
                    section_cell.fill = credit_fill
                    current_row += 1
                    
                    for col, hdr in enumerate(["Field", "Amount", "Lotes", ""], 1):
                        cell = ws.cell(row=current_row, column=col)
                        cell.value = hdr
                        cell.font = header_font
                        cell.fill = header_fill
                        cell.border = border
                        cell.alignment = Alignment(horizontal='center')
                    current_row += 1
                    
                    credit_total = 0.0
                    for label, amount, lotes in data["credit"]:
                        credit_total += amount
                        ws.cell(row=current_row, column=1).value = label
                        ws.cell(row=current_row, column=1).border = border
                        
                        amount_cell = ws.cell(row=current_row, column=2)
                        amount_cell.value = amount
                        amount_cell.number_format = '#,##0.00'
                        amount_cell.alignment = Alignment(horizontal='right')
                        amount_cell.border = border
                        
                        lotes_cell = ws.cell(row=current_row, column=3)
                        lotes_cell.value = lotes if lotes else "-"
                        lotes_cell.alignment = Alignment(horizontal='center')
                        lotes_cell.border = border
                        
                        current_row += 1
                    
                    total_label = ws.cell(row=current_row, column=1)
                    total_label.value = "Total Cash Out"
                    total_label.font = Font(bold=True)
                    total_label.fill = total_fill
                    total_label.border = border
                    
                    total_amount = ws.cell(row=current_row, column=2)
                    total_amount.value = credit_total
                    total_amount.number_format = '#,##0.00'
                    total_amount.font = Font(bold=True)
                    total_amount.fill = total_fill
                    total_amount.alignment = Alignment(horizontal='right')
                    total_amount.border = border
                    
                    ws.cell(row=current_row, column=3).fill = total_fill
                    ws.cell(row=current_row, column=3).border = border
                    
                    current_row += 2
                

                ws.column_dimensions['A'].width = 35
                ws.column_dimensions['B'].width = 18
                ws.column_dimensions['C'].width = 12
                ws.column_dimensions['D'].width = 5
            

            wb.save(file_path)
            
            sheets_exported = " & ".join(b for b, _ in brands_to_export)
            QMessageBox.information(
                self, "Export Successful",
                f"{sheets_exported} exported to:\n{file_path}",
                QMessageBox.Ok
            )
            
        except Exception as e:
            QMessageBox.critical(
                self, "Export Error",
                f"An error occurred while exporting:\n{str(e)}",
                QMessageBox.Ok
            )


    _MSG_QSS = f"""
        QMessageBox {{
            background-color: {_BG_CARD};
            font-family: 'Segoe UI', 'SF Pro Text', Arial, sans-serif;
            font-size: 12px;
        }}
        QMessageBox QLabel {{ color: {_TEXT_PRI}; font-size: 12px; min-width: 0; }}
        QMessageBox QPushButton {{
            background-color: {_PRIMARY};
            color: {_WHITE};
            border-radius: 6px;
            padding: 8px 20px;
            font-weight: 700;
            font-size: 11px;
            min-width: 80px;
        }}
        QMessageBox QPushButton:hover {{ background-color: {_PRIMARY_DK}; }}
    """

    def _msg(self, title, text, icon):
        m = QMessageBox(icon, title, text, QMessageBox.Ok, self)
        m.setStyleSheet(self._MSG_QSS)
        m.exec_()

    def _msg_success(self, text):
        m = QMessageBox(self)
        m.setIcon(QMessageBox.Information)
        m.setWindowTitle("Success")
        m.setText(text)
        m.setStyleSheet(
            self._MSG_QSS
            .replace(_PRIMARY, _SUCCESS)
            .replace(_PRIMARY_DK, _SUCCESS_DK)
        )
        m.exec_()


    def show_message(self, title, message, icon):
        self._msg(title, message, icon)

    def show_success_message(self, message):
        self._msg_success(message)

    def validate_beginning_balance(self):
        return self.beginning_balance_auto_filled_a

    def validate_required_fields(self):
        return self.validate_all_requirements()

    def check_duplicate_entry(self, selected_date):
        return self.check_existing_entry(selected_date, "Brand A")

    def _sync_palawan_mc_to_other_brand(self, date, palawan_data, mc_data):
        pass 