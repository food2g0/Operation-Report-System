import datetime
import time

from PyQt5.QtWidgets import (
    QWidget, QLabel, QLineEdit, QVBoxLayout, QHBoxLayout,
    QGroupBox, QPushButton, QSizePolicy, QDateEdit,
    QMessageBox, QScrollArea, QFrame, QGridLayout, QTabWidget,
    QComboBox
)
from PyQt5.QtGui import QDoubleValidator, QFont
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


_BG_APP      = "#F4F6F9"
_BG_CARD     = "#FFFFFF"
_BG_INPUT    = "#FFFFFF"
_BG_READONLY = "#F0F3F7"
_BG_HEADER   = "#0A2647"
_BG_SUMMARY  = "#0D2E55"

_BORDER      = "#D3DAE6"
_BORDER_FOCUS= "#1A73E8"
_BORDER_OK   = "#1DB954"

_TEXT_PRI    = "#0D1F3C"
_TEXT_SEC    = "#4B5E7A"
_TEXT_MUTED  = "#8A97AA"

_BLUE        = "#1A73E8"
_GREEN       = "#1DB954"
_ORANGE      = "#F59E0B"
_RED         = "#E53E3E"
_WHITE       = "#FFFFFF"
_PURPLE      = "#8B5CF6"





GLOBAL_QSS = f"""
QWidget {{
    background-color: {_BG_APP};
    font-family: 'Segoe UI', 'Helvetica Neue', Arial, sans-serif;
    font-size: 13px;
    color: {_TEXT_PRI};
}}

/* ── Group boxes (used inside tab content) ── */
QGroupBox {{
    background-color: {_BG_CARD};
    border: 1.5px solid {_BORDER};
    border-radius: 7px;
    margin-top: 16px;
    padding: 16px 14px 12px 14px;
    font-size: 10px;
    font-weight: 700;
    color: {_BLUE};
    letter-spacing: 0.9px;
    text-transform: uppercase;
}}
QGroupBox::title {{
    subcontrol-origin: margin;
    subcontrol-position: top left;
    left: 14px;
    top: 0px;
    padding: 0 8px;
    background-color: {_BG_CARD};
    color: {_BLUE};
}}

/* ── All editable inputs ── */
QLineEdit {{
    background-color: {_BG_INPUT};
    border: 1.5px solid {_BORDER};
    border-radius: 5px;
    padding: 7px 10px;
    font-size: 13px;
    font-weight: 500;
    color: {_TEXT_PRI};
    min-width: 130px;
    min-height: 34px;
    selection-background-color: {_BLUE};
    selection-color: {_WHITE};
}}
QLineEdit:focus {{
    border: 2px solid {_BORDER_FOCUS};
    background-color: #F0F7FF;
}}
QLineEdit:read-only {{
    background-color: {_BG_READONLY};
    color: {_TEXT_SEC};
    font-weight: 600;
    border-color: {_BORDER};
}}
QLineEdit:disabled {{
    background-color: #ECEEF2;
    color: {_TEXT_MUTED};
    border-color: #E2E8F0;
}}

/* ── Labels ── */
QLabel {{
    color: {_TEXT_SEC};
    font-size: 12px;
    font-weight: 500;
    min-width: 0;
    background: transparent;
}}

/* ── Buttons ── */
QPushButton {{
    background-color: {_BLUE};
    color: {_WHITE};
    border: none;
    padding: 9px 20px;
    border-radius: 6px;
    font-size: 12px;
    font-weight: 700;
    min-width: 90px;
    letter-spacing: 0.2px;
}}
QPushButton:hover   {{ background-color: #1558C0; }}
QPushButton:pressed {{ background-color: #0D449A; }}
QPushButton:disabled {{ background-color: #CBD5E1; color: #94A3B8; }}

/* ── Tabs ── */
QTabWidget::pane {{
    border: 1.5px solid {_BORDER};
    background-color: {_BG_CARD};
    border-radius: 0 6px 6px 6px;
}}
QTabBar::tab {{
    background-color: #E4EAF3;
    color: {_TEXT_SEC};
    border: 1.5px solid {_BORDER};
    border-bottom: none;
    padding: 9px 22px;
    margin-right: 3px;
    border-top-left-radius: 6px;
    border-top-right-radius: 6px;
    font-size: 12px;
    font-weight: 600;
}}
QTabBar::tab:selected {{
    background-color: {_BG_CARD};
    color: {_BLUE};
    font-weight: 700;
}}
QTabBar::tab:hover:!selected {{
    background-color: #D0DAE8;
    color: {_TEXT_PRI};
}}

/* ── Scroll bars ── */
QScrollArea {{ border: none; background: transparent; }}
QScrollBar:vertical {{
    background: #EDF0F5; width: 7px;
    border-radius: 4px; margin: 0;
}}
QScrollBar::handle:vertical {{
    background: #B0BEC8; border-radius: 4px; min-height: 28px;
}}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; border: none; }}
QScrollBar:horizontal {{
    background: #EDF0F5; height: 7px; border-radius: 4px;
}}
QScrollBar::handle:horizontal {{
    background: #B0BEC8; border-radius: 4px;
}}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{ width: 0; border: none; }}

/* ── Date edit ── */
QDateEdit {{
    background-color: {_BG_INPUT};
    border: 1.5px solid {_BORDER};
    border-radius: 5px;
    padding: 6px 10px;
    font-size: 13px;
    font-weight: 500;
    color: {_TEXT_PRI};
    min-height: 34px;
}}
QDateEdit:focus {{ border: 2px solid {_BORDER_FOCUS}; }}
QDateEdit::drop-down {{ border: none; width: 20px; }}

/* ── ComboBox ── */
QComboBox {{
    background-color: {_BG_INPUT};
    border: 1.5px solid {_BORDER};
    border-radius: 5px;
    padding: 7px 10px;
    font-size: 13px;
    font-weight: 600;
    color: {_TEXT_PRI};
    min-height: 34px;
    min-width: 140px;
}}
QComboBox:focus {{
    border: 2px solid {_BORDER_FOCUS};
    background-color: #F0F7FF;
}}
QComboBox::drop-down {{
    border: none;
    width: 30px;
}}
QComboBox::down-arrow {{
    image: url(data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTIiIGhlaWdodD0iOCIgdmlld0JveD0iMCAwIDEyIDgiIGZpbGw9Im5vbmUiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyI+PHBhdGggZD0iTTEgMUw2IDZMMTEgMSIgc3Ryb2tlPSIjNEI1RTdBIiBzdHJva2Utd2lkdGg9IjIiIHN0cm9rZS1saW5lY2FwPSJyb3VuZCIgc3Ryb2tlLWxpbmVqb2luPSJyb3VuZCIvPjwvc3ZnPg==);
    width: 12px;
    height: 8px;
}}
QComboBox QAbstractItemView {{
    background-color: {_BG_CARD};
    border: 1.5px solid {_BORDER};
    border-radius: 5px;
    selection-background-color: {_BLUE};
    selection-color: {_WHITE};
    padding: 4px;
}}
QComboBox QAbstractItemView::item {{
    padding: 8px 12px;
    border-radius: 3px;
}}
QComboBox QAbstractItemView::item:hover {{
    background-color: #E8F2FE;
    color: {_TEXT_PRI};
}}
"""

def _hline():
    f = QFrame()
    f.setFrameShape(QFrame.HLine)
    f.setFrameShadow(QFrame.Plain)
    f.setStyleSheet(f"color: {_BORDER}; max-height: 1px; background: {_BORDER};")
    return f


def _vline():
    f = QFrame()
    f.setFrameShape(QFrame.VLine)
    f.setFrameShadow(QFrame.Plain)
    f.setStyleSheet("color: #2A4D78; max-width: 1px;")
    return f

class ClientDashboard(QWidget):
    logout_requested = pyqtSignal()
    brand_changed = pyqtSignal(str)  # Signal to notify tabs about brand change

    def __init__(self, username, branch, corporation, db_manager):
        super().__init__()
        self.user_email  = username
        self.corporation = corporation
        self.branch      = branch
        self.db_manager  = db_manager
        self._update_checker_threads = []  # Store update checker threads
        
        # Session management - 30 minute timeout (1800 seconds)
        self.session = SessionManager(inactivity_timeout=1800)
        self._session_timer = QTimer(self)
        self._session_timer.timeout.connect(self._check_session_timeout)
        self._session_timer.start(60000)  # Check every minute

        # Brand selection - Brand A is default
        self.current_brand = "Brand A"

        self.setWindowTitle("Daily Cash Report")
        self.setMinimumSize(1100, 700)

        self.beginning_balance_auto_filled = False
        self.previous_day_balance = None
        self.previous_day_date    = None

        self.setStyleSheet(GLOBAL_QSS)

        # ── Outer scroll ────────────────────────────────────────────
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)

        body = QWidget()
        scroll.setWidget(body)

        lay = QVBoxLayout(body)
        lay.setSpacing(10)
        lay.setContentsMargins(18, 18, 18, 18)

        lay.addWidget(self._build_header(username, branch, corporation))
        lay.addWidget(self._build_toolbar())
        lay.addWidget(self._build_tabs(), stretch=1)   # tabs get all free space
        lay.addWidget(self._build_summary_strip())
        lay.addWidget(self._build_footer())

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.addWidget(scroll)

        self.on_date_changed()
        self.showMaximized()
        
        # Check if the app was just updated and show success message
        if AUTO_UPDATE_ENABLED and check_update_success:
            check_update_success(parent=self)

    def _build_header(self, username, branch, corporation):
        bar = QFrame()
        bar.setFixedHeight(66)
        bar.setStyleSheet(f"""
            QFrame {{
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:0,
                    stop:0 {_BG_HEADER}, stop:0.55 #0E3460, stop:1 #1A5276
                );
                border-radius: 8px;
            }}
            QLabel {{ background: transparent; border: none; }}
        """)

        h = QHBoxLayout(bar)
        h.setContentsMargins(20, 0, 16, 0)
        h.setSpacing(0)

        left = QVBoxLayout()
        left.setSpacing(2)

        name_lbl = QLabel(f"\u2002{username}")
        name_lbl.setStyleSheet(
            f"font-size: 16px; font-weight: 800; color: {_WHITE}; letter-spacing: 0.3px;"
        )
        sub_lbl = QLabel(
            f"\u2002Daily Cash Report  \u00b7  {branch}  \u00b7  {corporation}"
        )
        sub_lbl.setStyleSheet(
            "font-size: 11px; font-weight: 500; color: #90B8D8; letter-spacing: 0.4px;"
        )
        left.addWidget(name_lbl)
        left.addWidget(sub_lbl)

        # Version/Update button
        if AUTO_UPDATE_ENABLED:
            update_btn = QPushButton(f"ℹ️ v{__version__}")
            update_btn.setFixedSize(88, 36)
            update_btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: rgba(22,160,133,0.85);
                    color: {_WHITE};
                    border: 1px solid rgba(22,160,133,0.4);
                    border-radius: 6px;
                    font-size: 11px; font-weight: 700;
                }}
                QPushButton:hover   {{ background-color: #16A085; }}
                QPushButton:pressed {{ background-color: #138D75; }}
            """)
            update_btn.clicked.connect(self.check_for_updates)
            update_btn.setToolTip("Check for updates")

        logout_btn = QPushButton("\u2302  Logout")
        logout_btn.setFixedSize(108, 36)
        logout_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: rgba(220,38,38,0.85);
                color: {_WHITE};
                border: 1px solid rgba(220,38,38,0.4);
                border-radius: 6px;
                font-size: 12px; font-weight: 700;
            }}
            QPushButton:hover   {{ background-color: #DC2626; }}
            QPushButton:pressed {{ background-color: #991B1B; }}
        """)
        logout_btn.clicked.connect(self.handle_logout)

        h.addLayout(left)
        h.addStretch()
        if AUTO_UPDATE_ENABLED:
            h.addWidget(update_btn, alignment=Qt.AlignVCenter)
            h.addSpacing(8)
        h.addWidget(logout_btn, alignment=Qt.AlignVCenter)
        return bar

    def handle_logout(self):
        r = QMessageBox.question(
            self, "Confirm Logout", "Log out of the current session?",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        if r == QMessageBox.Yes:
            self.session.logout()
            self.logout_requested.emit()
            self.close()
    
    def _check_session_timeout(self):
        """Check if session has timed out due to inactivity"""
        if self.session.check_timeout():
            self._session_timer.stop()
            QMessageBox.warning(
                self,
                "Session Expired",
                "Your session has expired due to inactivity.\nPlease log in again.",
                QMessageBox.Ok
            )
            self.logout_requested.emit()
            self.close()
    
    def mousePressEvent(self, event):
        """Reset session timer on mouse activity"""
        self.session.update_activity()
        super().mousePressEvent(event)
    
    def keyPressEvent(self, event):
        """Reset session timer on keyboard activity"""
        self.session.update_activity()
        super().keyPressEvent(event)
    
    def check_for_updates(self):
        """Manually check for application updates"""
        if AUTO_UPDATE_ENABLED:
            check_for_updates(parent=self, silent=False)
        else:
            QMessageBox.information(
                self,
                "Auto-Updater",
                "Auto-updater is not enabled.\n\n"
                "To enable it, install required dependencies:\n"
                "pip install requests packaging"
            )
    
    def closeEvent(self, event):
        """Clean up threads before closing"""
        # Wait for update checker threads to finish (max 2 seconds)
        if hasattr(self, '_update_checker_threads'):
            for thread in self._update_checker_threads[:]:
                if thread.isRunning():
                    thread.quit()
                    thread.wait(2000)  # Wait up to 2 seconds
        event.accept()

    def _build_toolbar(self):
        bar = QFrame()
        bar.setFixedHeight(56)
        bar.setStyleSheet(f"""
            QFrame {{
                background-color: {_BG_CARD};
                border: 1px solid {_BORDER};
                border-radius: 8px;
            }}
            QLabel {{
                font-size: 12px; font-weight: 600;
                color: {_TEXT_SEC};
                background: transparent;
                min-width: 0;
            }}
        """)

        h = QHBoxLayout(bar)
        h.setContentsMargins(18, 0, 18, 0)
        h.setSpacing(12)

        # Brand Selector
        h.addWidget(QLabel("Brand"))
        self.brand_selector = QComboBox()
        self.brand_selector.addItems(["Brand A", "Brand B"])
        self.brand_selector.setCurrentText("Brand A")  # Default to Brand A
        self.brand_selector.setFixedWidth(140)
        self.brand_selector.setStyleSheet(f"""
            QComboBox {{
                background-color: {_BG_INPUT};
                border: 2px solid {_PURPLE};
                font-weight: 700;
                color: {_PURPLE};
            }}
            QComboBox:focus {{
                border: 2px solid {_PURPLE};
                background-color: #F5F3FF;
            }}
        """)
        self.brand_selector.currentTextChanged.connect(self.on_brand_changed)
        h.addWidget(self.brand_selector)

        h.addWidget(_vline())

        h.addWidget(QLabel("Report Date"))
        self.date_picker = QDateEdit()
        self.date_picker.setCalendarPopup(True)
        self.date_picker.setDate(QDate.currentDate())
        self.date_picker.setFixedWidth(148)
        self.date_picker.dateChanged.connect(self.on_date_changed)
        h.addWidget(self.date_picker)

        h.addWidget(_vline())

        h.addWidget(QLabel("Beginning Balance"))
        self.beginning_balance_input = self._money_input("Loaded from previous day")
        self.beginning_balance_input.setReadOnly(True)
        self.beginning_balance_input.setFixedWidth(170)
        h.addWidget(self.beginning_balance_input)

        self.balance_status_label = QLabel("")
        self.balance_status_label.setStyleSheet(
            f"font-size: 11px; font-weight: 600; color: {_TEXT_MUTED}; min-width: 180px;"
        )
        h.addWidget(self.balance_status_label)

        self.auto_fill_button = QPushButton("\u2193  Load Prev Day")
        self.auto_fill_button.setFixedHeight(34)
        self.auto_fill_button.setFixedWidth(148)
        self.auto_fill_button.setStyleSheet(f"""
            QPushButton {{
                background-color: {_GREEN};
                font-size: 12px; font-weight: 700;
                border-radius: 6px;
            }}
            QPushButton:hover   {{ background-color: #17A349; }}
            QPushButton:pressed {{ background-color: #138C3D; }}
            QPushButton:disabled {{ background-color: #CBD5E1; color: #94A3B8; }}
        """)
        self.auto_fill_button.clicked.connect(self.auto_fill_beginning_balance)
        h.addWidget(self.auto_fill_button)
        h.addStretch()
        return bar

    def on_brand_changed(self, brand_name):
        """Handle brand switching"""
        if brand_name == self.current_brand:
            return
        
        # Check if there's unsaved data
        if self._has_unsaved_data():
            reply = QMessageBox.question(
                self,
                "Switch Brand",
                f"Switching to {brand_name} will clear all current data.\n\nDo you want to continue?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            
            if reply == QMessageBox.No:
                # Revert the combo box selection
                self.brand_selector.blockSignals(True)
                self.brand_selector.setCurrentText(self.current_brand)
                self.brand_selector.blockSignals(False)
                return
        
        # Update current brand
        old_brand = self.current_brand
        self.current_brand = brand_name
        
        # Clear all fields
        self.clear_all_fields_silent()
        
        # Notify tabs about brand change
        self.brand_changed.emit(brand_name)
        
        # Show confirmation
        self._msg(
            "Brand Switched",
            f"Successfully switched from {old_brand} to {brand_name}.\n\nAll fields have been cleared.",
            QMessageBox.Information
        )

    def _has_unsaved_data(self):
        """Check if there's any data entered in the form"""
        if self.beginning_balance_input.text().strip():
            return True
        if self.cash_count_input.text().strip():
            return True
        
        # Check tabs for data
        try:
            if hasattr(self, 'cash_flow_tab'):
                cf_data = self.cash_flow_tab.get_data()
                if any(v != 0 and v != 0.0 for section in cf_data.values() 
                       for v in (section.values() if isinstance(section, dict) else [section])):
                    return True
        except:
            pass
        
        try:
            if hasattr(self, 'palawan_tab'):
                pal_data = self.palawan_tab.get_data()
                if any(v != 0 and v != 0.0 for v in pal_data.values()):
                    return True
        except:
            pass
        
        try:
            if hasattr(self, 'mc_currency_tab'):
                mc_data = self.mc_currency_tab.get_data()
                if any(v != 0 and v != 0.0 for v in mc_data.values()):
                    return True
        except:
            pass
        
        return False

    def get_current_brand(self):
        """Get the currently selected brand"""
        return self.current_brand

    def _build_tabs(self):
        tw = QTabWidget()
        tw.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        self.cash_flow_tab   = CashFlowTab(self)
        self.palawan_tab     = PalawanDetailsTab(self)
        self.mc_currency_tab = MCCurrencyTab(self)

        tw.addTab(self.cash_flow_tab,   "  Cash Flow  ")
        tw.addTab(self.palawan_tab,     "  Palawan Details  ")
        tw.addTab(self.mc_currency_tab, "  MC Currency  ")

        return tw
    
    def _build_summary_strip(self):
        strip = QFrame()
        strip.setFixedHeight(86)
        strip.setStyleSheet(f"""
            QFrame {{
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:0,
                    stop:0 {_BG_SUMMARY}, stop:1 #0E3A68
                );
                border-radius: 8px;
            }}
        """)

        h = QHBoxLayout(strip)
        h.setContentsMargins(24, 10, 24, 10)
        h.setSpacing(0)

        # helper: metric widget (display label)
        def _metric(caption):
            outer = QWidget()
            outer.setStyleSheet("background: transparent;")
            col = QVBoxLayout(outer)
            col.setSpacing(4)
            col.setContentsMargins(14, 0, 14, 0)

            cap = QLabel(caption.upper())
            cap.setAlignment(Qt.AlignCenter)
            cap.setStyleSheet(
                "font-size: 9px; font-weight: 700; "
                "color: #6A8FAE; letter-spacing: 1px; background: transparent;"
            )

            val = QLabel("0.00")
            val.setAlignment(Qt.AlignCenter)
            val.setStyleSheet(
                f"font-size: 17px; font-weight: 800; color: {_WHITE}; background: transparent;"
            )

            col.addWidget(cap)
            col.addWidget(val)
            return outer, val

        # Ending balance
        w_eb, self.ending_balance_display = _metric("Ending Balance")

        w_cc = QWidget()
        w_cc.setStyleSheet("background: transparent;")
        cc_col = QVBoxLayout(w_cc)
        cc_col.setSpacing(4)
        cc_col.setContentsMargins(14, 0, 14, 0)

        cc_cap = QLabel("ACTUAL CASH COUNT")
        cc_cap.setAlignment(Qt.AlignCenter)
        cc_cap.setStyleSheet(
            "font-size: 9px; font-weight: 700; "
            "color: #6A8FAE; letter-spacing: 1px; background: transparent;"
        )

        self.cash_count_input = QLineEdit()
        self.cash_count_input.setValidator(QDoubleValidator(0.0, 1e12, 2))
        self.cash_count_input.setPlaceholderText("0.00")
        self.cash_count_input.setAlignment(Qt.AlignCenter)
        self.cash_count_input.setFixedWidth(178)
        self.cash_count_input.setFixedHeight(36)
        self.cash_count_input.setStyleSheet(f"""
            QLineEdit {{
                background-color: #152840;
                border: 1.5px solid #2E5A8A;
                border-radius: 5px;
                color: {_WHITE};
                font-size: 16px;
                font-weight: 700;
                padding: 4px 10px;
                letter-spacing: 0.5px;
            }}
            QLineEdit:focus {{
                border: 2px solid #5BA4E6;
                background-color: #1A3654;
            }}
            QLineEdit::placeholder {{ color: #5080A0; }}
        """)
        self.cash_count_input.textChanged.connect(self.recalculate_all)
        self.cash_count_input.textChanged.connect(self.update_cash_result)

        cc_col.addWidget(cc_cap)
        cc_col.addWidget(self.cash_count_input, alignment=Qt.AlignCenter)

        # Variance
        w_var, self.cash_result_display = _metric("Variance")

        # Status label
        self.variance_status_label = QLabel("—")
        self.variance_status_label.setAlignment(Qt.AlignCenter)
        self.variance_status_label.setStyleSheet(
            "font-size: 13px; font-weight: 700; color: #8AADCC; "
            "min-width: 230px; background: transparent;"
        )

        h.addWidget(w_eb,  stretch=2)
        h.addWidget(_vline())
        h.addWidget(w_cc,  stretch=2)
        h.addWidget(_vline())
        h.addWidget(w_var, stretch=2)
        h.addWidget(_vline())
        h.addWidget(self.variance_status_label, stretch=3)

        return strip

    def _build_footer(self):
        bar = QFrame()
        bar.setFixedHeight(52)
        row = QHBoxLayout(bar)
        row.setContentsMargins(0, 5, 0, 5)
        row.addStretch()

        self.post_button = QPushButton("  Post Report")
        self.post_button.setFixedSize(162, 42)
        self.post_button.setStyleSheet(f"""
            QPushButton {{
                background-color: {_GREEN};
                color: {_WHITE};
                font-size: 13px; font-weight: 800;
                border-radius: 7px; letter-spacing: 0.3px;
            }}
            QPushButton:hover   {{ background-color: #17A349; }}
            QPushButton:pressed {{ background-color: #138C3D; }}
            QPushButton:disabled {{ background-color: #CBD5E1; color: #94A3B8; }}
        """)
        self.post_button.clicked.connect(self.handle_post)
        self.post_button.setEnabled(False)

        row.addWidget(self.post_button)
        return bar

    def _money_input(self, placeholder=""):
        f = QLineEdit()
        f.setValidator(QDoubleValidator(0.0, 1e12, 2))
        f.setPlaceholderText(placeholder)
        f.textChanged.connect(self.recalculate_all)
        return f

    # Public aliases used by child tabs
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

    def get_previous_day_ending_balance(self, selected_date):
        try:
            current = datetime.datetime.strptime(selected_date, "%Y-%m-%d")
            
            # Determine which table to query based on current brand
            table_name = "daily_reports_brand_a" if self.current_brand == "Brand A" else "daily_reports"
            
            for days_back in range(1, 11):
                prev_str = (current - datetime.timedelta(days=days_back)).strftime("%Y-%m-%d")
                try:
                    query = f"""SELECT ending_balance FROM {table_name} 
                                WHERE date=%s AND branch=%s AND corporation=%s 
                                ORDER BY id DESC LIMIT 1"""
                    result = self.db_manager.execute_query(query, (prev_str, self.branch, self.corporation))
                    
                    if result and len(result) > 0:
                        val = result[0].get('ending_balance')
                        if val is not None:
                            return float(val), prev_str
                except Exception as e:
                    print(f"Query error for {prev_str}: {e}")
                    continue
        except Exception as e:
            print(f"get_previous_day_ending_balance: {e}")
        return None, None

    def check_existing_entry(self, selected_date):
        try:
            # Determine which table to query based on current brand
            table_name = "daily_reports_brand_a" if self.current_brand == "Brand A" else "daily_reports"
            
            query = f"""SELECT COUNT(*) as count FROM {table_name} 
                        WHERE date=%s AND branch=%s AND corporation=%s"""
            result = self.db_manager.execute_query(query, (selected_date, self.branch, self.corporation))
            
            if result and len(result) > 0:
                cnt = result[0].get('count', 0)
                return cnt > 0
        except Exception as e:
            print(f"check_existing_entry: {e}")
        return False

    def on_date_changed(self):
        sd = self.date_picker.date().toString("yyyy-MM-dd")
        self.beginning_balance_auto_filled = False
        self.previous_day_balance = None
        self.previous_day_date    = None
        self.beginning_balance_input.clear()
        self.beginning_balance_input.setReadOnly(True)
        self.beginning_balance_input.setStyleSheet("")
        self.cash_count_input.clear()

        if self.check_existing_entry(sd):
            self._set_status(
                f"\u26a0  Entry already submitted for {self.current_brand} on this date. Cannot submit again.", _RED, bold=True
            )
            self.auto_fill_button.setEnabled(False)
            self.post_button.setEnabled(False)
            self._toggle_inputs(False)
            return

        self._toggle_inputs(True)
        self.auto_fill_button.setEnabled(True)

        prev_bal, prev_date = self.get_previous_day_ending_balance(sd)
        if prev_bal is not None:
            self.previous_day_balance = prev_bal
            self.previous_day_date    = prev_date
            self._set_status(
                f"Previous  {prev_date}  \u2192  {prev_bal:,.2f}", _BLUE
            )
        else:
            self._set_status("No previous record — first entry", _ORANGE)
            self.beginning_balance_input.setReadOnly(False)
            self.beginning_balance_input.setPlaceholderText("Enter opening balance")
            self.beginning_balance_input.setStyleSheet(
                f"background-color: {_BG_INPUT}; color: {_TEXT_PRI};"
            )

        self.recalculate_all()

    def _set_status(self, text, color, bold=False):
        w = "700" if bold else "600"
        self.balance_status_label.setText(text)
        self.balance_status_label.setStyleSheet(
            f"font-size: 11px; font-weight: {w}; color: {color};"
        )

    def auto_fill_beginning_balance(self):
        sd = self.date_picker.date().toString("yyyy-MM-dd")
        if self.check_existing_entry(sd):
            self._msg("Entry Exists", f"An entry already exists for {self.current_brand} on {sd}.", QMessageBox.Warning)
            return
        if self.previous_day_balance is not None:
            self.beginning_balance_input.setText(f"{self.previous_day_balance:.2f}")
            self.beginning_balance_auto_filled = True
            self.beginning_balance_input.setReadOnly(True)
            self.beginning_balance_input.setStyleSheet(f"""
                QLineEdit {{
                    border: 2px solid {_BORDER_OK};
                    background-color: #F0FFF6;
                    color: #145C2F;
                    font-weight: 700;
                }}
            """)
            self._set_status(
                f"\u2713  Loaded from {self.previous_day_date}  \u2192  {self.previous_day_balance:,.2f}",
                _GREEN, bold=True
            )
            self.auto_fill_button.setText("\u2713  Loaded")
            self.auto_fill_button.setEnabled(False)
            self._msg(
                "Balance Loaded",
                f"Beginning balance set to {self.previous_day_balance:,.2f}",
                QMessageBox.Information
            )
        else:
            self._msg(
                "No Previous Record",
                "No previous day record found. Enter the opening balance manually.",
                QMessageBox.Information
            )
            self.beginning_balance_input.setReadOnly(False)
            self.beginning_balance_input.setPlaceholderText("Enter opening balance")
            self.beginning_balance_input.setStyleSheet(
                f"background-color: {_BG_INPUT}; color: {_TEXT_PRI};"
            )
            self.beginning_balance_auto_filled = True

    def _toggle_inputs(self, enabled):
        self.beginning_balance_input.setEnabled(enabled)
        self.cash_count_input.setEnabled(enabled)
        for tab in (self.cash_flow_tab, self.palawan_tab, self.mc_currency_tab):
            if hasattr(tab, 'set_enabled'):
                tab.set_enabled(enabled)

    def disable_all_inputs(self):
        self._toggle_inputs(False)

    def enable_all_inputs(self):
        self._toggle_inputs(True)

    def recalculate_all(self):
        try:
            beginning = float(self.beginning_balance_input.text().strip() or 0)
        except ValueError:
            beginning = 0.0

        debit  = self.cash_flow_tab.get_debit_total()
        credit = self.cash_flow_tab.get_credit_total()
        self.cash_flow_tab.update_totals(beginning, debit, credit)

        ending = beginning + debit - credit
        self.ending_balance_display.setText(f"{ending:,.2f}")

        color = "#58D68D" if ending > 0 else ("#EC7063" if ending < 0 else _WHITE)
        self.ending_balance_display.setStyleSheet(
            f"font-size: 17px; font-weight: 800; color: {color}; background: transparent;"
        )

        self.update_cash_result()
        self.palawan_tab.calculate_palawan_totals()
        self.mc_currency_tab.calculate_mc_totals()

    def update_cash_result(self):
        try:
            cc = float(self.cash_count_input.text().strip() or 0)
            eb = float(
                (self.ending_balance_display.text() or "0").replace(",", "")
            )
            diff = cc - eb
            self.cash_result_display.setText(f"{diff:,.2f}")

            has_req = (
                bool(self.beginning_balance_input.text().strip())
                and bool(self.cash_count_input.text().strip())
            )

            if abs(diff) < 0.01:
                self.cash_result_display.setStyleSheet(
                    "font-size: 17px; font-weight: 800; color: #58D68D; background: transparent;"
                )
                if has_req:
                    self._set_var_status(
                        "\u2713  No Variance \u2014 Ready to Post", "#58D68D"
                    )
                    self.post_button.setEnabled(True)
                else:
                    self._set_var_status(
                        "\u26a0  Fill required fields to post", _ORANGE
                    )
                    self.post_button.setEnabled(False)
            elif diff > 0:
                self.cash_result_display.setStyleSheet(
                    f"font-size: 17px; font-weight: 800; color: {_ORANGE}; background: transparent;"
                )
                self._set_var_status(f"\u26a0  OVER by {diff:,.2f} \u2014 Will be tagged", _ORANGE)
                if has_req:
                    self.post_button.setEnabled(True)
                else:
                    self.post_button.setEnabled(False)
            else:
                self.cash_result_display.setStyleSheet(
                    f"font-size: 17px; font-weight: 800; color: {_RED}; background: transparent;"
                )
                self._set_var_status(
                    f"\u2715  SHORT by {abs(diff):,.2f} \u2014 Will be tagged", _RED
                )
                if has_req:
                    self.post_button.setEnabled(True)
                else:
                    self.post_button.setEnabled(False)

        except ValueError:
            self.cash_result_display.setText("\u2014")
            self._set_var_status("\u26a0  Invalid input", _RED)
            self.post_button.setEnabled(False)

    def _set_var_status(self, text, color):
        self.variance_status_label.setText(text)
        self.variance_status_label.setStyleSheet(
            f"font-size: 13px; font-weight: 700; color: {color}; background: transparent;"
        )

    def _sync_palawan_mc_to_other_brand(self, date, palawan_data, mc_data):
        """Sync Palawan Details and MC Currency data to the other brand's table"""
        try:
            # Determine the OTHER table (opposite of current brand)
            other_table = "daily_reports" if self.current_brand == "Brand A" else "daily_reports_brand_a"
            
            # Combine Palawan and MC data
            shared_data = {**palawan_data, **mc_data}
            
            # Check if entry exists in other table
            check_query = f"""SELECT COUNT(*) as count FROM {other_table} 
                             WHERE date=%s AND branch=%s AND corporation=%s"""
            result = self.db_manager.execute_query(check_query, (date, self.branch, self.corporation))
            exists = result and len(result) > 0 and result[0].get('count', 0) > 0
            
            if exists:
                # Update existing record with Palawan and MC data only
                update_parts = [f"{col}=%s" for col in shared_data.keys()]
                update_sql = f"UPDATE {other_table} SET {', '.join(update_parts)} " \
                           "WHERE date=%s AND branch=%s AND corporation=%s"
                update_vals = list(shared_data.values()) + [date, self.branch, self.corporation]
                
                self.db_manager.execute_query(update_sql, tuple(update_vals))
                print(f"Synced Palawan/MC data to existing {other_table} entry")
            else:
                # Insert new record with only Palawan and MC data (other fields will be NULL/default)
                cols = ['date', 'username', 'branch', 'corporation'] + list(shared_data.keys())
                vals = [date, self.user_email, self.branch, self.corporation] + list(shared_data.values())
                
                ph = ', '.join(['%s'] * len(cols))
                cs = ', '.join(cols)
                insert_sql = f"INSERT INTO {other_table} ({cs}) VALUES ({ph})"
                
                self.db_manager.execute_query(insert_sql, tuple(vals))
                print(f"Created new {other_table} entry with Palawan/MC data")
                
        except Exception as e:
            print(f"Error syncing Palawan/MC to other brand: {e}")
            # Don't fail the main post operation if this sync fails

    def _check_optional_tabs_empty(self):
        empty_tabs = []
        try:
            pal_data = self.palawan_tab.get_data()
            if all(v == 0 or v == 0.0 for v in pal_data.values()):
                empty_tabs.append("Palawan Details")
        except Exception:
            empty_tabs.append("Palawan Details")
        try:
            mc_data = self.mc_currency_tab.get_data()
            if all(v == 0 or v == 0.0 for v in mc_data.values()):
                empty_tabs.append("MC Currency")
        except Exception:
            empty_tabs.append("MC Currency")

        if not empty_tabs:
            return True
        tab_list = "\n".join(f"   •  {t}" for t in empty_tabs)

        dlg = QMessageBox(self)
        dlg.setWindowTitle("Incomplete Report")
        dlg.setIcon(QMessageBox.Warning)
        dlg.setText(
            f"<b>The following tabs have no data:</b><br><br>"
            f"{'<br>'.join(f'&nbsp;&nbsp;&nbsp;&#8226;&nbsp; <b>{t}</b>' for t in empty_tabs)}"
            f"<br><br>"
            f"Are you sure you want to post without filling them in?"
        )
        dlg.setInformativeText(
            "You can click <b>Go Back</b> to add the missing details, "
            "or <b>Post Anyway</b> to submit with zeros."
        )
        btn_post   = dlg.addButton("Post Anyway",  QMessageBox.AcceptRole)
        btn_back   = dlg.addButton("Go Back",       QMessageBox.RejectRole)
        dlg.setDefaultButton(btn_back)
        dlg.setStyleSheet(f"""
            QMessageBox {{
                background-color: {_BG_CARD};
                font-family: 'Segoe UI', Arial, sans-serif;
                font-size: 13px;
            }}
            QMessageBox QLabel {{
                color: {_TEXT_PRI};
                font-size: 13px;
                min-width: 0;
                line-height: 1.5;
            }}
            QPushButton {{
                border-radius: 6px;
                padding: 9px 22px;
                font-size: 12px;
                font-weight: 700;
                min-width: 110px;
            }}
        """)
        btn_post.setStyleSheet(f"""
            QPushButton {{
                background-color: {_ORANGE};
                color: {_WHITE};
                border: none;
            }}
            QPushButton:hover   {{ background-color: #D97706; }}
            QPushButton:pressed {{ background-color: #B45309; }}
        """)
        btn_back.setStyleSheet(f"""
            QPushButton {{
                background-color: {_BLUE};
                color: {_WHITE};
                border: none;
            }}
            QPushButton:hover   {{ background-color: #1558C0; }}
            QPushButton:pressed {{ background-color: #0D449A; }}
        """)
        dlg.exec_()
        return dlg.clickedButton() == btn_post

    def handle_post(self):
        try:
            sd = self.date_picker.date().toString("yyyy-MM-dd")
            if not self.validate_all_requirements():
                return
            # ── Optional-tab warning ──────────────────────────────────
            if not self._check_optional_tabs_empty():
                return   # user chose "Go Back"
            if self.check_existing_entry(sd):
                self._msg("Duplicate Entry", f"Entry for {self.current_brand} on {sd} already exists.", QMessageBox.Critical)
                return

            beginning = float(self.beginning_balance_input.text().strip())
            cf  = self.cash_flow_tab.get_data()
            pal = self.palawan_tab.get_data()
            mcc = self.mc_currency_tab.get_data()

            deb = sum(v for k, v in cf['debit'].items()  if not k.endswith('_lotes'))
            cre = sum(v for k, v in cf['credit'].items() if not k.endswith('_lotes'))

            debit_total  = beginning + deb
            credit_total = cre
            ending       = beginning + deb - cre
            cash_count   = float(self.cash_count_input.text().strip())
            cash_result  = cash_count - ending
            
            # Determine variance status
            if abs(cash_result) < 0.01:
                variance_status = "balanced"
            elif cash_result > 0:
                variance_status = "over"
            else:
                variance_status = "short"

            all_vals = {**cf['debit'], **cf['credit'], **pal, **mcc}
            
            # Determine which table to insert into based on current brand
            table_name = "daily_reports_brand_a" if self.current_brand == "Brand A" else "daily_reports"
            
            cols = [
                'date', 'username', 'branch', 'corporation',
                'beginning_balance', 'debit_total', 'credit_total',
                'ending_balance', 'cash_count', 'cash_result', 'variance_status'
            ] + list(all_vals.keys())
            vals = [
                sd, self.user_email, self.branch, self.corporation,
                beginning, debit_total, credit_total,
                ending, cash_count, cash_result, variance_status
            ] + list(all_vals.values())

            ph    = ', '.join(['%s'] * len(cols))
            cs    = ', '.join(cols)
            query = f"INSERT INTO {table_name} ({cs}) VALUES ({ph})"
            upd   = ', '.join(f"{c}=VALUES({c})" for c in cols if c not in ('date', 'username'))
            if upd:
                query += " ON DUPLICATE KEY UPDATE " + upd

            rows, last_err = None, None
            for attempt in range(1, 5):
                res, err = self.db_manager.execute_query_with_exception(query, vals)
                if err is None:
                    rows = res
                    break
                last_err = err
                is_dl = (
                    hasattr(err, 'args') and isinstance(err.args, tuple)
                    and len(err.args) > 0 and err.args[0] == 1213
                )
                try:
                    self.db_manager.logger.error(f"DB attempt {attempt}: {err}")
                    with open('db_deadlock_retries.log', 'a') as lf:
                        lf.write(
                            f"{datetime.datetime.now().isoformat()} "
                            f"| attempt={attempt} | dl={is_dl} | {err}\n"
                        )
                except Exception:
                    pass
                if is_dl and attempt < 4:
                    time.sleep(0.5 * attempt)
                else:
                    break

            if isinstance(rows, int) and rows > 0:
                # Also insert Palawan and MC Currency data into the OTHER table
                self._sync_palawan_mc_to_other_brand(sd, pal, mcc)
                
                self._msg_success(f"Report for {self.current_brand} on {sd} posted successfully.")
                
                # Refresh to show entry exists and prevent duplicate submissions
                self.on_date_changed()
                
                # Ask if user wants to move to next day
                self.clear_all_fields()
            elif rows is None:
                detail = f"\n\n{last_err}" if last_err else ""
                self._msg("Database Error", f"Insert failed. Please retry.{detail}", QMessageBox.Critical)
            else:
                self._msg("Warning", "No rows were inserted.", QMessageBox.Warning)

        except Exception as e:
            self._msg("Error", f"Failed to post: {e}", QMessageBox.Critical)

    def validate_all_requirements(self):
        sd = self.date_picker.date().toString("yyyy-MM-dd")

        if self.check_existing_entry(sd):
            self._msg("Duplicate Entry", f"An entry for {self.current_brand} on {sd} already exists.", QMessageBox.Critical)
            return False

        if not self.beginning_balance_auto_filled:
            if self.previous_day_balance is not None:
                self._msg(
                    "Beginning Balance Required",
                    f"Click '\u2193 Load Prev Day' to set the opening balance.\n"
                    f"Expected:  {self.previous_day_balance:,.2f}  ({self.previous_day_date})",
                    QMessageBox.Critical
                )
                return False
            elif not self.beginning_balance_input.text().strip():
                self._msg(
                    "Beginning Balance Required",
                    "First entry: please type the opening balance.",
                    QMessageBox.Critical
                )
                self.beginning_balance_input.setFocus()
                return False

        if not self.beginning_balance_input.text().strip():
            self._msg("Validation Error", "Beginning balance is empty.", QMessageBox.Warning)
            return False

        if not self.cash_count_input.text().strip():
            self._msg("Validation Error", "Enter the actual cash count.", QMessageBox.Warning)
            self.cash_count_input.setFocus()
            return False

        if self.previous_day_balance is not None:
            try:
                cur_beg = float(self.beginning_balance_input.text().strip())
                if abs(cur_beg - self.previous_day_balance) > 0.01:
                    self._msg(
                        "Balance Mismatch",
                        f"Beginning balance does not match previous day.\n\n"
                        f"Expected : {self.previous_day_balance:,.2f}  ({self.previous_day_date})\n"
                        f"Current  : {cur_beg:,.2f}\n\n"
                        f"Use 'Load Prev Day' to correct this.",
                        QMessageBox.Critical
                    )
                    return False
            except ValueError:
                self._msg("Validation Error", "Invalid beginning balance.", QMessageBox.Warning)
                return False

        try:
            cc = float(self.cash_count_input.text().strip())
            eb = float(
                (self.ending_balance_display.text() or "0").replace(",", "")
            )
            diff = cc - eb
            # Allow posting with variance but warn user
            if abs(diff) >= 0.01:
                variance_type = "OVER" if diff > 0 else "SHORT"
                reply = QMessageBox.question(
                    self,
                    "Variance Warning",
                    f"You have a cash variance ({variance_type} by {abs(diff):,.2f}).\n\n"
                    f"Ending Balance : {eb:,.2f}\n"
                    f"Cash Count     : {cc:,.2f}\n"
                    f"Variance       : {diff:,.2f}\n\n"
                    f"This entry will be tagged for admin review.\n\n"
                    f"Do you want to continue posting?",
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.No
                )
                if reply == QMessageBox.No:
                    return False
        except ValueError:
            self._msg("Validation Error", "Invalid cash count.", QMessageBox.Warning)
            return False

        return True
    
    def clear_all_fields(self):
        r = QMessageBox.question(
            self, "Advance Date", "Report posted! Move to the next day?",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes
        )
        if r == QMessageBox.Yes:
            # Clear tabs first
            for tab, meth in [
                (self.cash_flow_tab,   'clear_fields'),
                (self.palawan_tab,     'clear_fields'),
                (self.mc_currency_tab, 'clear_fields'),
            ]:
                if hasattr(tab, meth):
                    getattr(tab, meth)()
            
            # Move to next day - on_date_changed() will be triggered automatically
            # and will load the previous day's ending balance
            self.date_picker.setDate(self.date_picker.date().addDays(1))

    def clear_all_fields_silent(self):
        """Clear all fields without showing dialogs (used when switching brands)"""
        self.beginning_balance_input.clear()
        self.cash_count_input.clear()
        self.beginning_balance_auto_filled = False
        self.previous_day_balance = None
        self.previous_day_date    = None
        self.auto_fill_button.setText("\u2193  Load Prev Day")
        self.auto_fill_button.setEnabled(True)
        self.beginning_balance_input.setStyleSheet("")
        self.balance_status_label.setText("")
        
        for tab, meth in [
            (self.cash_flow_tab,   'clear_fields'),
            (self.palawan_tab,     'clear_fields'),
            (self.mc_currency_tab, 'clear_fields'),
        ]:
            if hasattr(tab, meth):
                getattr(tab, meth)()
        
        self.on_date_changed()

    _MSG_QSS = f"""
        QMessageBox {{
            background-color: {_BG_CARD};
            font-family: 'Segoe UI', Arial, sans-serif;
            font-size: 13px;
        }}
        QMessageBox QLabel {{ color: {_TEXT_PRI}; font-size: 13px; min-width: 0; }}
        QMessageBox QPushButton {{
            background-color: {_BLUE}; color: {_WHITE};
            border-radius: 5px; padding: 8px 22px;
            font-weight: 700; font-size: 12px; min-width: 80px;
        }}
        QMessageBox QPushButton:hover {{ background-color: #1558C0; }}
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
            .replace(_BLUE, _GREEN)
            .replace("#1558C0", "#17A349")
        )
        m.exec_()

    # Legacy aliases
    def show_message(self, title, message, icon):
        self._msg(title, message, icon)

    def show_success_message(self, message):
        self._msg_success(message)

    def validate_beginning_balance(self):
        return self.beginning_balance_auto_filled

    def validate_required_fields(self):
        return self.validate_all_requirements()

    def check_duplicate_entry(self, selected_date):
        return self.check_existing_entry(selected_date)