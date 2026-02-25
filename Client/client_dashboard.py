import datetime
import json
import os
import time

from PyQt5.QtWidgets import (
    QWidget, QLabel, QLineEdit, QVBoxLayout, QHBoxLayout,
    QGroupBox, QPushButton, QSizePolicy, QDateEdit,
    QMessageBox, QScrollArea, QFrame, QGridLayout, QTabWidget,
    QComboBox, QApplication
)
from PyQt5.QtGui import QDoubleValidator, QFont, QFontDatabase
from PyQt5.QtCore import Qt, QDate, pyqtSignal, QTimer

from Client.cash_flow_tab import CashFlowTab
from Client.palawan_details_tab import PalawanDetailsTab
from Client.mc_currency_tab import MCCurrencyTab
from security import SessionManager

# Auto-updater (optional)
try:
    from auto_updater import check_for_updates, check_update_success
    from version import __version__
    AUTO_UPDATE_ENABLED = True
except ImportError:
    AUTO_UPDATE_ENABLED = False
    __version__ = "1.0.0"
    check_update_success = None


# ═══════════════════════════════════════════════════════════
#  3-COLOR DESIGN SYSTEM
#  Palette: Slate (neutral) · Indigo (primary) · Emerald (success/action)
# ═══════════════════════════════════════════════════════════

# Neutrals — slate scale
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

# Primary — indigo
_INDIGO_50  = "#EEF2FF"
_INDIGO_100 = "#E0E7FF"
_INDIGO_400 = "#818CF8"
_INDIGO_500 = "#0C0C0F"
_INDIGO_600 = "#0B0B0C"
_INDIGO_700 = "#111014"

# Accent — emerald (success / confirm)
_EMERALD_50  = "#ECFDF5"
_EMERALD_400 = "#34D399"
_EMERALD_500 = "#10B981"
_EMERALD_600 = "#059669"

# Semantic
_AMBER_400  = "#FBBF24"
_AMBER_500  = "#F59E0B"
_RED_400    = "#F87171"
_RED_500    = "#EF4444"
_WHITE      = "#FFFFFF"

# Aliases for readability
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


# ───────────────────────────────────────────────────────────
def _s(px: int) -> int:
    try:
        screen = QApplication.primaryScreen()
        if screen:
            dpi_ratio = screen.logicalDotsPerInch() / 96.0
            return max(1, round(px * min(dpi_ratio, 1.5)))
    except Exception:
        pass
    return px


# ═══════════════════════════════════════════════════════════
#  GLOBAL QSS — coherent 3-color system
# ═══════════════════════════════════════════════════════════
GLOBAL_QSS = f"""
/* ─── Base ─────────────────────────────────────────────── */
QWidget {{
    background-color: {_BG_APP};
    font-family: 'Segoe UI', 'SF Pro Text', 'Helvetica Neue', Arial, sans-serif;
    font-size: 12px;
    color: {_TEXT_PRI};
}}

/* ─── Cards / GroupBoxes ───────────────────────────────── */
QGroupBox {{
    background-color: {_BG_CARD};
    border: 1px solid {_BORDER};
    border-radius: 8px;
    margin-top: 20px;
    padding: 16px 14px 14px 14px;
    font-size: 9px;
    font-weight: 700;
    color: {_TEXT_MUTED};
    letter-spacing: 1.2px;
    text-transform: uppercase;
}}
QGroupBox::title {{
    subcontrol-origin: margin;
    subcontrol-position: top left;
    left: 12px;
    top: -1px;
    padding: 2px 8px;
    background-color: {_BG_CARD};
    color: {_PRIMARY};
    font-size: 9px;
    font-weight: 800;
    letter-spacing: 1.3px;
    border-radius: 3px;
}}

/* ─── Text inputs ──────────────────────────────────────── */
QLineEdit {{
    background-color: {_BG_INPUT};
    border: 1.5px solid {_BORDER};
    border-radius: 6px;
    padding: 7px 10px;
    font-size: 12px;
    font-weight: 500;
    color: {_TEXT_PRI};
    min-width: 80px;
    min-height: 32px;
    selection-background-color: {_INDIGO_100};
    selection-color: {_PRIMARY_DK};
}}
QLineEdit:focus {{
    border: 2px solid {_PRIMARY};
    background-color: {_INDIGO_50};
    padding: 6px 9px;
}}
QLineEdit:read-only {{
    background-color: {_BG_RDONLY};
    color: {_TEXT_SEC};
    font-weight: 600;
    border-color: {_BORDER};
}}
QLineEdit:disabled {{
    background-color: {_SLATE_100};
    color: {_TEXT_MUTED};
    border-color: {_SLATE_200};
}}

/* ─── Labels ───────────────────────────────────────────── */
QLabel {{
    color: {_TEXT_SEC};
    font-size: 11px;
    font-weight: 500;
    min-width: 0;
    background: transparent;
}}

/* ─── Buttons ──────────────────────────────────────────── */
QPushButton {{
    background-color: {_PRIMARY};
    color: {_WHITE};
    border: none;
    padding: 8px 18px;
    border-radius: 6px;
    font-size: 11px;
    font-weight: 700;
    min-width: 80px;
    letter-spacing: 0.2px;
}}
QPushButton:hover   {{ background-color: {_PRIMARY_DK}; }}
QPushButton:pressed {{ background-color: {_PRIMARY_PR}; }}
QPushButton:disabled {{
    background-color: {_SLATE_200};
    color: {_TEXT_MUTED};
}}

/* ─── Tab widget ───────────────────────────────────────── */
QTabWidget::pane {{
    border: 1px solid {_BORDER};
    background-color: {_BG_CARD};
    border-radius: 0 8px 8px 8px;
    top: -1px;
}}
QTabBar::tab {{
    background-color: {_SLATE_100};
    color: {_TEXT_SEC};
    border: 1px solid {_BORDER};
    border-bottom: none;
    padding: 8px 22px;
    margin-right: 2px;
    border-top-left-radius: 6px;
    border-top-right-radius: 6px;
    font-size: 11px;
    font-weight: 600;
    min-width: 100px;
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

/* ─── Scrollbars ───────────────────────────────────────── */
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

/* ─── DateEdit ─────────────────────────────────────────── */
QDateEdit {{
    background-color: {_BG_INPUT};
    border: 1.5px solid {_BORDER};
    border-radius: 6px;
    padding: 7px 10px;
    font-size: 12px;
    font-weight: 600;
    color: {_TEXT_PRI};
    min-height: 32px;
}}
QDateEdit:focus {{ border: 2px solid {_PRIMARY}; padding: 6px 9px; }}
QDateEdit::drop-down {{ border: none; width: 22px; }}

/* ─── ComboBox ─────────────────────────────────────────── */
QComboBox {{
    background-color: {_BG_INPUT};
    border: 1.5px solid {_BORDER};
    border-radius: 6px;
    padding: 7px 10px;
    font-size: 12px;
    font-weight: 600;
    color: {_TEXT_PRI};
    min-height: 32px;
    min-width: 120px;
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
    padding: 7px 12px;
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
        f"font-size: 9px; font-weight: 700; color: {color}; "
        f"letter-spacing: 1.1px; background: transparent;"
    )
    return lbl


# ═══════════════════════════════════════════════════════════
class ClientDashboard(QWidget):
    logout_requested = pyqtSignal()
    brand_changed    = pyqtSignal(str)

    def __init__(self, username, branch, corporation, db_manager):
        super().__init__()
        self.user_email  = username
        self.corporation = corporation
        self.branch      = branch
        self.db_manager  = db_manager
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
        self.setStyleSheet(GLOBAL_QSS)

        lay = QVBoxLayout(self)
        lay.setSpacing(6)
        lay.setContentsMargins(12, 10, 12, 8)

        lay.addWidget(self._build_header(username, branch, corporation))
        lay.addWidget(self._build_toolbar())
        lay.addWidget(self._build_tabs(), stretch=1)
        lay.addWidget(self._build_summary_strip())
        lay.addWidget(self._build_footer())

        self.on_date_changed()
        self._connect_shared_fields()

        from PyQt5.QtCore import QTimer as _QT
        _QT.singleShot(300, self._load_draft)
        self.showMaximized()

        if AUTO_UPDATE_ENABLED and check_update_success:
            check_update_success(parent=self)

    # ───────────────────────────────────────────────────────
    #  HEADER
    # ───────────────────────────────────────────────────────
    def _build_header(self, username, branch, corporation):
        bar = QFrame()
        bar.setFixedHeight(48)
        bar.setStyleSheet(f"""
            QFrame {{
                background-color: {_SLATE_900};
                border-radius: 8px;
            }}
            QLabel {{ background: transparent; border: none; }}
        """)

        h = QHBoxLayout(bar)
        h.setContentsMargins(16, 0, 12, 0)
        h.setSpacing(10)

        # App name
        app_lbl = QLabel("Daily Cash Report")
        app_lbl.setStyleSheet(
            f"font-size: 13px; font-weight: 800; color: {_WHITE}; "
            f"letter-spacing: 0.2px; background: transparent;"
        )
        h.addWidget(app_lbl)

        # Separator dot
        dot = QLabel("·")
        dot.setStyleSheet(f"font-size: 16px; color: {_SLATE_600}; background: transparent;")
        h.addWidget(dot)

        # User info
        info_lbl = QLabel(f"{username}  ·  {branch}  ·  {corporation}")
        info_lbl.setStyleSheet(
            f"font-size: 12px; font-weight: 400; color: {_SLATE_400}; background: transparent;"
        )
        h.addWidget(info_lbl)
        h.addStretch()

        if AUTO_UPDATE_ENABLED:
            upd_btn = QPushButton(f"v{__version__}")
            upd_btn.setFixedSize(68, 28)
            upd_btn.setStyleSheet(f"""
                QPushButton {{
                    background: rgba(99,102,241,0.15);
                    color: {_INDIGO_400};
                    border: 1px solid rgba(99,102,241,0.3);
                    border-radius: 5px;
                    font-size: 10px; font-weight: 700;
                }}
                QPushButton:hover {{ background: rgba(99,102,241,0.25); }}
            """)
            upd_btn.clicked.connect(self.check_for_updates)
            upd_btn.setToolTip("Check for updates")
            h.addWidget(upd_btn, alignment=Qt.AlignVCenter)
            h.addSpacing(8)

        logout_btn = QPushButton("Sign out")
        logout_btn.setFixedSize(82, 28)
        logout_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                color: {_SLATE_400};
                border: 1px solid {_SLATE_700};
                border-radius: 5px;
                font-size: 11px; font-weight: 600;
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

    # ───────────────────────────────────────────────────────
    #  TOOLBAR  — date + both beginning balances (redesigned)
    # ───────────────────────────────────────────────────────
    def _build_toolbar(self):
        bar = QFrame()
        bar.setObjectName("toolbar")
        bar.setStyleSheet(f"""
            QFrame#toolbar {{
                background-color: {_BG_CARD};
                border: 1px solid {_BORDER};
                border-radius: 8px;
            }}
        """)

        outer = QHBoxLayout(bar)
        outer.setContentsMargins(16, 10, 16, 10)
        outer.setSpacing(0)

        # ── Date ──────────────────────────────────────────────
        date_col = QVBoxLayout()
        date_col.setSpacing(5)

        date_title = QLabel("Report Date")
        date_title.setStyleSheet(
            f"font-size: 11px; font-weight: 700; color: {_TEXT_PRI}; background: transparent;"
        )
        date_col.addWidget(date_title)

        self.date_picker = QDateEdit()
        self.date_picker.setCalendarPopup(True)
        self.date_picker.setDate(QDate.currentDate())
        self.date_picker.setFixedWidth(150)
        self.date_picker.setFixedHeight(36)
        self.date_picker.dateChanged.connect(self.on_date_changed)
        date_col.addWidget(self.date_picker)
        date_col.addStretch(1)

        outer.addLayout(date_col)
        outer.addSpacing(18)

        # ── Brand A ───────────────────────────────────────────
        outer.addLayout(self._build_balance_column("A"), stretch=1)

        outer.addSpacing(18)

        # ── Brand B ───────────────────────────────────────────
        outer.addLayout(self._build_balance_column("B"), stretch=1)

        # Back-compat
        self.beginning_balance_input = self.beginning_balance_input_a
        self.balance_status_label    = self.balance_status_label_a
        self.auto_fill_button        = self.auto_fill_button_a

        return bar

    def _build_balance_column(self, brand: str) -> QVBoxLayout:
        """
        Redesigned beginning balance panel.

        Layout:
          [Label: "Brand A — Opening Balance"]
          ┌──────────────────────────────┐   <- read-only amount field (full-width)
          │  Loaded from previous day    │
          └──────────────────────────────┘
          [ ↓ Load Previous Day ]  ← subdued text-style button
          status text below
        """
        is_a  = brand == "A"
        label = "Brand A" if is_a else "Brand B"

        col = QVBoxLayout()
        col.setSpacing(5)

        # ── Section label ──────────────────────────────────
        title = QLabel(f"{label}  —  Opening Balance")
        title.setStyleSheet(
            f"font-size: 11px; font-weight: 700; color: {_TEXT_PRI}; background: transparent;"
        )
        col.addWidget(title)

        # ── Amount field (full width, clearly read-only) ───
        bb_input = QLineEdit()
        bb_input.setValidator(QDoubleValidator(0.0, 1e12, 2))
        bb_input.setPlaceholderText("—")
        bb_input.setReadOnly(True)
        bb_input.setFixedHeight(36)
        bb_input.setStyleSheet(f"""
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
        bb_input.textChanged.connect(self.recalculate_all)
        col.addWidget(bb_input)

        # ── Action row: load button + status text ──────────
        action_row = QHBoxLayout()
        action_row.setSpacing(10)
        action_row.setContentsMargins(0, 0, 0, 0)

        load_btn = QPushButton("↓  Load Previous Day")
        load_btn.setFixedHeight(26)
        load_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                color: {_PRIMARY};
                border: 1.5px solid {_INDIGO_100};
                border-radius: 5px;
                font-size: 10px;
                font-weight: 700;
                padding: 4px 12px;
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

    # ───────────────────────────────────────────────────────
    #  TABS
    # ───────────────────────────────────────────────────────
    def _build_tabs(self):
        tw = QTabWidget()
        tw.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        self.cash_flow_tab_a = CashFlowTab(self, "Brand A")
        self.cash_flow_tab_b = CashFlowTab(self, "Brand B")
        self.palawan_tab     = PalawanDetailsTab(self)
        self.mc_currency_tab = MCCurrencyTab(self)

        self.cash_flow_tab = self.cash_flow_tab_a

        tw.addTab(self.cash_flow_tab_a,  "Brand A — Cash Flow")
        tw.addTab(self.cash_flow_tab_b,  "Brand B — Cash Flow")
        tw.addTab(self.palawan_tab,      "Palawan Details")
        tw.addTab(self.mc_currency_tab,  "MC Currency")

        return tw

    # ───────────────────────────────────────────────────────
    #  SUMMARY STRIP
    # ───────────────────────────────────────────────────────
    def _build_summary_strip(self):
        strip = QFrame()
        strip.setFixedHeight(96)
        strip.setStyleSheet(f"""
            QFrame {{
                background-color: {_SLATE_900};
                border-radius: 8px;
            }}
        """)

        h = QHBoxLayout(strip)
        h.setContentsMargins(16, 8, 16, 8)
        h.setSpacing(0)

        col_a, self.ending_balance_display_a, self.cash_count_input_a, \
            self.cash_result_display_a, self.variance_status_label_a = \
            self._build_brand_summary("A")

        col_b, self.ending_balance_display_b, self.cash_count_input_b, \
            self.cash_result_display_b, self.variance_status_label_b = \
            self._build_brand_summary("B")

        # Back-compat
        self.ending_balance_display  = self.ending_balance_display_a
        self.cash_count_input        = self.cash_count_input_a
        self.cash_result_display     = self.cash_result_display_a
        self.variance_status_label   = self.variance_status_label_a

        self.cash_count_input_a.textChanged.connect(self.recalculate_all)
        self.cash_count_input_a.textChanged.connect(self.update_cash_result)
        self.cash_count_input_b.textChanged.connect(self.recalculate_all)
        self.cash_count_input_b.textChanged.connect(self.update_cash_result)

        h.addLayout(col_a, stretch=1)
        h.addSpacing(16)
        h.addLayout(col_b, stretch=1)

        return strip

    def _build_brand_summary(self, brand: str):
        is_a   = brand == "A"
        accent = _INDIGO_400 if is_a else _EMERALD_400

        def _cap(t):
            l = QLabel(t)
            l.setAlignment(Qt.AlignCenter)
            l.setStyleSheet(
                f"font-size: 8px; font-weight: 700; color: {_SLATE_500}; "
                f"letter-spacing: 1.1px; background: transparent; text-transform: uppercase;"
            )
            return l

        def _val(init="0.00"):
            l = QLabel(init)
            l.setAlignment(Qt.AlignCenter)
            l.setStyleSheet(
                f"font-size: 15px; font-weight: 800; color: {_WHITE}; background: transparent;"
            )
            return l

        def _cc_inp():
            inp = QLineEdit()
            inp.setValidator(QDoubleValidator(0.0, 1e12, 2))
            inp.setPlaceholderText("0.00")
            inp.setAlignment(Qt.AlignCenter)
            inp.setFixedHeight(28)
            inp.setStyleSheet(f"""
                QLineEdit {{
                    background: rgba(255,255,255,0.06);
                    border: 1.5px solid {_SLATE_700};
                    border-radius: 5px;
                    color: {_WHITE};
                    font-size: 13px;
                    font-weight: 700;
                    padding: 2px 8px;
                }}
                QLineEdit:focus {{
                    border: 2px solid {accent};
                    background: rgba(255,255,255,0.1);
                }}
            """)
            return inp

        col = QVBoxLayout()
        col.setSpacing(2)
        col.setContentsMargins(6, 0, 6, 0)

        # Brand pill
        pill_row = QHBoxLayout()
        pill_row.setAlignment(Qt.AlignCenter)
        pill = QLabel(f"BRAND {'A' if is_a else 'B'}")
        pill.setAlignment(Qt.AlignCenter)
        pill.setStyleSheet(
            f"font-size: 8px; font-weight: 800; color: {accent}; letter-spacing: 1.5px; "
            f"background: transparent; padding: 1px 0;"
        )
        pill_row.addWidget(pill)
        col.addLayout(pill_row)

        # Metrics row
        row = QHBoxLayout()
        row.setSpacing(3)

        def _metric(cap_w, val_w):
            mc = QVBoxLayout()
            mc.setSpacing(1)
            mc.addWidget(cap_w)
            mc.addWidget(val_w, alignment=Qt.AlignCenter)
            return mc

        eb_val  = _val()
        cc_inp  = _cc_inp()
        var_val = _val()

        status_lbl = QLabel("—")
        status_lbl.setAlignment(Qt.AlignCenter)
        status_lbl.setStyleSheet(
            f"font-size: 10px; font-weight: 700; color: {_SLATE_500}; "
            f"min-width: 90px; background: transparent;"
        )

        row.addLayout(_metric(_cap("Ending Bal"),  eb_val),  stretch=2)
        row.addWidget(_vline(dark=True))
        row.addLayout(_metric(_cap("Cash Count"),  cc_inp),  stretch=2)
        row.addWidget(_vline(dark=True))
        row.addLayout(_metric(_cap("Variance"),    var_val), stretch=2)
        row.addWidget(_vline(dark=True))
        row.addLayout(_metric(_cap("Status"),      status_lbl), stretch=3)

        col.addLayout(row)
        return col, eb_val, cc_inp, var_val, status_lbl

    # ───────────────────────────────────────────────────────
    #  FOOTER
    # ───────────────────────────────────────────────────────
    def _build_footer(self):
        bar = QFrame()
        bar.setFixedHeight(48)
        row = QHBoxLayout(bar)
        row.setContentsMargins(0, 6, 0, 2)
        row.setSpacing(10)
        row.addStretch()

        self.draft_button = QPushButton("Save Draft")
        self.draft_button.setFixedSize(120, 34)
        self.draft_button.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                color: {_SLATE_600};
                font-size: 11px;
                font-weight: 700;
                border: 1.5px solid {_SLATE_300};
                border-radius: 6px;
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
        self.post_button.setFixedSize(158, 34)
        self.post_button.setStyleSheet(f"""
            QPushButton {{
                background-color: {_SUCCESS};
                color: {_WHITE};
                font-size: 12px;
                font-weight: 800;
                border-radius: 6px;
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

        row.addWidget(self.draft_button)
        row.addWidget(self.post_button)
        return bar

    # ───────────────────────────────────────────────────────
    #  HELPERS
    # ───────────────────────────────────────────────────────
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
                total += float(field.text().strip() or 0)
            except ValueError:
                pass
        return total

    # ───────────────────────────────────────────────────────
    #  SESSION / AUTH
    # ───────────────────────────────────────────────────────
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

    # ───────────────────────────────────────────────────────
    #  DATA / DB HELPERS
    # ───────────────────────────────────────────────────────
    def get_current_brand(self):
        return "Both"

    def get_previous_day_ending_balance(self, selected_date, brand="Brand A"):
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

    def check_existing_entry(self, selected_date, brand="Brand A"):
        try:
            table_name = "daily_reports_brand_a" if brand == "Brand A" else "daily_reports"
            q = f"""SELECT COUNT(*) as count FROM {table_name}
                    WHERE date=%s AND branch=%s AND corporation=%s"""
            result = self.db_manager.execute_query(
                q, (selected_date, self.branch, self.corporation))
            if result and len(result) > 0:
                return result[0].get('count', 0) > 0
        except Exception as e:
            print(f"check_existing_entry({brand}): {e}")
        return False

    # ───────────────────────────────────────────────────────
    #  DATE CHANGED
    # ───────────────────────────────────────────────────────
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

        self.beginning_balance_auto_filled_a = False
        self.beginning_balance_auto_filled_b = False
        self.previous_day_balance_a = self.previous_day_date_a = None
        self.previous_day_balance_b = self.previous_day_date_b = None

        exists_a = self.check_existing_entry(sd, "Brand A")
        exists_b = self.check_existing_entry(sd, "Brand B")

        if exists_a and exists_b:
            for brand in ("A", "B"):
                self._set_status_brand(brand, "Already submitted", _RED_500, bold=True)
            self.auto_fill_button_a.setEnabled(False)
            self.auto_fill_button_b.setEnabled(False)
            self.post_button.setEnabled(False)
            self._toggle_inputs(False)
            return

        self._toggle_inputs(True)

        for brand, exists, bf in [("A", exists_a, "Brand A"), ("B", exists_b, "Brand B")]:
            bb_input = self.beginning_balance_input_a if brand == "A" else self.beginning_balance_input_b
            af_btn   = self.auto_fill_button_a        if brand == "A" else self.auto_fill_button_b
            cf_tab   = self.cash_flow_tab_a           if brand == "A" else self.cash_flow_tab_b
            cc_input = self.cash_count_input_a        if brand == "A" else self.cash_count_input_b

            if exists:
                self._set_status_brand(brand, "Already submitted", _RED_500, bold=True)
                af_btn.setEnabled(False)
                bb_input.setEnabled(False)
                cc_input.setEnabled(False)
                if hasattr(cf_tab, 'set_enabled'):
                    cf_tab.set_enabled(False)
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

        self.recalculate_all()

    def _set_status(self, text, color, bold=False):
        self._set_status_brand("A", text, color, bold)

    def _set_status_brand(self, brand, text, color, bold=False):
        lbl = self.balance_status_label_a if brand == "A" else self.balance_status_label_b
        w   = "700" if bold else "500"
        lbl.setText(text)
        lbl.setStyleSheet(
            f"font-size: 10px; font-weight: {w}; color: {color}; background: transparent;"
        )

    # ───────────────────────────────────────────────────────
    #  AUTO-FILL BEGINNING BALANCE
    # ───────────────────────────────────────────────────────
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
                    font-size: 10px;
                    font-weight: 700;
                    padding: 4px 12px;
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
                    self.palawan_tab, self.mc_currency_tab):
            if hasattr(tab, 'set_enabled'):
                tab.set_enabled(enabled)

    def disable_all_inputs(self):
        self._toggle_inputs(False)

    def enable_all_inputs(self):
        self._toggle_inputs(True)

    # ───────────────────────────────────────────────────────
    #  RECALCULATE
    # ───────────────────────────────────────────────────────
    def recalculate_all(self):
        for brand in ("a", "b"):
            bb  = getattr(self, f"beginning_balance_input_{brand}")
            cft = getattr(self, f"cash_flow_tab_{brand}")
            eb  = getattr(self, f"ending_balance_display_{brand}")
            try:
                beg = float(bb.text().strip() or 0)
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
        self.mc_currency_tab.calculate_mc_totals()
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
            cc_val  = float(cc.text().strip() or 0)
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
                        f"font-size: 10px; font-weight: 700; color: {_EMERALD_400}; background: transparent;"
                    )
                else:
                    stl.setText("Fill required fields")
                    stl.setStyleSheet(
                        f"font-size: 10px; font-weight: 600; color: {_SLATE_500}; background: transparent;"
                    )
            elif diff > 0:
                var.setStyleSheet(font + f"color: {_AMBER_400};")
                stl.setText(f"Over  +{diff:,.2f}")
                stl.setStyleSheet(
                    f"font-size: 10px; font-weight: 700; color: {_AMBER_400}; background: transparent;"
                )
            else:
                var.setStyleSheet(font + f"color: {_RED_400};")
                stl.setText(f"Short  {diff:,.2f}")
                stl.setStyleSheet(
                    f"font-size: 10px; font-weight: 700; color: {_RED_400}; background: transparent;"
                )

            return has_req
        except ValueError:
            var.setText("—")
            stl.setText("Invalid input")
            stl.setStyleSheet(
                f"font-size: 10px; font-weight: 600; color: {_RED_500}; background: transparent;"
            )
            return False

    def _set_var_status(self, text, color):
        self.variance_status_label_a.setText(text)
        self.variance_status_label_a.setStyleSheet(
            f"font-size: 10px; font-weight: 700; color: {color}; background: transparent;"
        )

    # ───────────────────────────────────────────────────────
    #  OPTIONAL TABS CHECK
    # ───────────────────────────────────────────────────────
    def _check_optional_tabs_empty(self):
        empty_tabs = []
        try:
            if all(v == 0 or v == 0.0 for v in self.palawan_tab.get_data().values()):
                empty_tabs.append("Palawan Details")
        except Exception:
            empty_tabs.append("Palawan Details")
        try:
            if all(v == 0 or v == 0.0 for v in self.mc_currency_tab.get_data().values()):
                empty_tabs.append("MC Currency")
        except Exception:
            empty_tabs.append("MC Currency")

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

    # ───────────────────────────────────────────────────────
    #  POST
    # ───────────────────────────────────────────────────────
    def handle_post(self):
        try:
            sd = self.date_picker.date().toString("yyyy-MM-dd")
            if not self._check_optional_tabs_empty():
                return
            if not self.validate_all_requirements():
                return

            pal = self.palawan_tab.get_data()
            mcc = self.mc_currency_tab.get_data()

            brand_specs = [
                ("Brand A", self.cash_flow_tab_a,
                 self.beginning_balance_input_a, self.cash_count_input_a,
                 "daily_reports_brand_a"),
                ("Brand B", self.cash_flow_tab_b,
                 self.beginning_balance_input_b, self.cash_count_input_b,
                 "daily_reports"),
            ]

            results = []
            for brand_full, cf_tab, bb_input, cc_input, table_name in brand_specs:
                if self.check_existing_entry(sd, brand_full):
                    results.append((brand_full, "skipped", None))
                    continue

                cf        = cf_tab.get_data()
                beginning = float(bb_input.text().strip())
                deb = sum(v for k, v in cf['debit'].items()  if not k.endswith('_lotes'))
                cre = sum(v for k, v in cf['credit'].items() if not k.endswith('_lotes'))
                ending      = beginning + deb - cre
                cash_count  = float(cc_input.text().strip())
                cash_result = cash_count - ending
                variance_status = (
                    "balanced" if abs(cash_result) < 0.01
                    else "over"  if cash_result > 0
                    else "short"
                )

                all_vals = {**cf['debit'], **cf['credit'], **pal, **mcc}
                cols = [
                    'date', 'username', 'branch', 'corporation',
                    'beginning_balance', 'debit_total', 'credit_total',
                    'ending_balance', 'cash_count', 'cash_result', 'variance_status'
                ] + list(all_vals.keys())
                vals = [
                    sd, self.user_email, self.branch, self.corporation,
                    beginning, beginning + deb, cre,
                    ending, cash_count, cash_result, variance_status
                ] + list(all_vals.values())

                ph    = ', '.join(['%s'] * len(cols))
                query = f"INSERT INTO {table_name} ({', '.join(cols)}) VALUES ({ph})"
                upd   = ', '.join(f"{c}=VALUES({c})" for c in cols
                                  if c not in ('date', 'username'))
                if upd:
                    query += " ON DUPLICATE KEY UPDATE " + upd

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
                    results.append((brand_full, "success", None))
                elif rows is None:
                    results.append((brand_full, "error",
                                    str(last_err) if last_err else "Unknown error"))
                else:
                    results.append((brand_full, "no_rows", None))

            successes = [b for b, s, _ in results if s == "success"]
            errors    = [(b, e) for b, s, e in results if s == "error"]
            skipped   = [b for b, s, _ in results if s == "skipped"]

            if errors:
                self._msg("Database Error",
                          "Some brands failed:\n\n" +
                          "\n".join(f"{b}: {e}" for b, e in errors),
                          QMessageBox.Critical)
                return

            if successes:
                parts = f"Posted: {', '.join(successes)}"
                if skipped:
                    parts += f"\nSkipped (already exists): {', '.join(skipped)}"
                self._msg_success(f"Report for {sd}\n\n{parts}")
                self._delete_draft()
                self.on_date_changed()
                self.clear_all_fields()
            elif skipped and not successes:
                self._msg("Nothing to Post",
                          "All brands already have entries for this date.",
                          QMessageBox.Information)

        except Exception as e:
            self._msg("Error", f"Failed to post: {e}", QMessageBox.Critical)

    # ───────────────────────────────────────────────────────
    #  VALIDATE
    # ───────────────────────────────────────────────────────
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
            if self.check_existing_entry(sd, brand_full):
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
                    cur_beg = float(bb_input.text().strip())
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
                cc_val = float(cc_input.text().strip())
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

    # ───────────────────────────────────────────────────────
    #  CLEAR / RESET
    # ───────────────────────────────────────────────────────
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
                (self.mc_currency_tab, 'clear_fields'),
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
                    font-size: 10px;
                    font-weight: 700;
                    padding: 4px 12px;
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
            (self.mc_currency_tab, 'clear_fields'),
        ]:
            if hasattr(tab, meth):
                getattr(tab, meth)()
        self.on_date_changed()

    # ───────────────────────────────────────────────────────
    #  SHARED FIELD CARRY (Brand A → Brand B)
    # ───────────────────────────────────────────────────────
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

    # ───────────────────────────────────────────────────────
    #  DRAFT SAVE / LOAD / DELETE
    # ───────────────────────────────────────────────────────
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
            draft = {
                "saved_at": datetime.datetime.now().isoformat(),
                "date": sd,
                "brand_a": {
                    "beginning_balance": self.beginning_balance_input_a.text(),
                    "beginning_balance_auto_filled": self.beginning_balance_auto_filled_a,
                    "cash_count": self.cash_count_input_a.text(),
                    "cash_flow": self.cash_flow_tab_a.get_raw_field_values(),
                },
                "brand_b": {
                    "beginning_balance": self.beginning_balance_input_b.text(),
                    "beginning_balance_auto_filled": self.beginning_balance_auto_filled_b,
                    "cash_count": self.cash_count_input_b.text(),
                    "cash_flow": self.cash_flow_tab_b.get_raw_field_values(),
                },
                "palawan":     self._collect_palawan_for_draft(),
                "mc_currency": self._collect_mc_for_draft(),
            }
            with open(self._get_draft_path(), "w", encoding="utf-8") as f:
                json.dump(draft, f, indent=2, ensure_ascii=False)
            self._msg_success(
                f"Draft saved for {sd}.\n\n"
                "Your data will be automatically restored when you return."
            )
        except Exception as e:
            self._msg("Save Draft Error", f"Could not save draft:\n{e}", QMessageBox.Warning)

    def _collect_palawan_for_draft(self):
        d = {}
        for section in ("sendout", "payout", "international"):
            for k, w in getattr(self.palawan_tab, f"{section}_inputs", {}).items():
                d[f"{section}:{k}"] = w.text()
        for k, w in getattr(self.palawan_tab, "lotes_inputs", {}).items():
            d[f"lotes:{k}"] = w.text()
        return d

    def _collect_mc_for_draft(self):
        return [
            {
                "currency_index": e['currency_combo'].currentIndex(),
                "quantity": e['quantity_input'].text(),
                "rate": e['rate_input'].text(),
            }
            for e in self.mc_currency_tab.currency_entries
        ]

    def _load_draft(self):
        try:
            path = self._get_draft_path()
            if not os.path.exists(path):
                return
            with open(path, "r", encoding="utf-8") as f:
                draft = json.load(f)

            saved_date = draft.get("date", "")
            saved_at   = draft.get("saved_at", "")[:19].replace("T", " ")

            reply = QMessageBox.question(
                self, "Restore Draft",
                f"A saved draft was found:\n\n"
                f"  Date : {saved_date}\n"
                f"  Saved: {saved_at}\n\n"
                f"Do you want to restore it?",
                QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes
            )
            if reply != QMessageBox.Yes:
                return

            qdate = QDate.fromString(saved_date, "yyyy-MM-dd")
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

            mc_entries = draft.get("mc_currency", [])
            while len(self.mc_currency_tab.currency_entries) < len(mc_entries):
                self.mc_currency_tab.add_currency_entry()
            for i, ed in enumerate(mc_entries):
                if i < len(self.mc_currency_tab.currency_entries):
                    e = self.mc_currency_tab.currency_entries[i]
                    e['currency_combo'].setCurrentIndex(ed.get("currency_index", 0))
                    e['quantity_input'].setText(ed.get("quantity", ""))
                    e['rate_input'].setText(ed.get("rate", ""))
            self.mc_currency_tab.calculate_totals()
            self.recalculate_all()

        except Exception as e:
            print(f"_load_draft error (non-fatal): {e}")

    def _delete_draft(self):
        try:
            path = self._get_draft_path()
            if os.path.exists(path):
                os.remove(path)
        except Exception:
            pass

    # ───────────────────────────────────────────────────────
    #  MESSAGE DIALOGS
    # ───────────────────────────────────────────────────────
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

    # ───────────────────────────────────────────────────────
    #  LEGACY ALIASES
    # ───────────────────────────────────────────────────────
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
        pass  # Deprecated; kept for backward compatibility