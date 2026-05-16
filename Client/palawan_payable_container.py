"""
PalawanPayableContainer
-----------------------
A collapsible container shown at the bottom of ClientDashboard (Brand A).
Provides data-entry for Palawan Payable:
  - PALAWAN SEND-OUT   : Lotes, Principal, SC, Commission, TOTAL
  - PALAWAN PAY-OUT    : Lotes, Principal, SC, Commission, TOTAL
  - PALAWAN INTERNATIONAL: Lotes, Principal, SC, Commission, TOTAL

Data is saved to the `payable_brand_a` table and flows into payable_page.py.
"""

from PyQt5.QtWidgets import (
    QWidget, QLabel, QLineEdit, QVBoxLayout, QHBoxLayout,
    QGroupBox, QFormLayout, QPushButton, QFrame, QSizePolicy,
    QMessageBox
)
from PyQt5.QtGui import QDoubleValidator, QIntValidator
from PyQt5.QtCore import Qt
import logging

from Client.ui_scaling import _sz

logger = logging.getLogger(__name__)

_SLATE_50  = "#F8FAFC"
_SLATE_100 = "#F1F5F9"
_SLATE_200 = "#E2E8F0"
_SLATE_700 = "#334155"
_SLATE_800 = "#1E293B"
_WHITE     = "#FFFFFF"

_SO_COLOR   = "#0EA5E9"   # sky-500
_PO_COLOR   = "#10B981"   # emerald-500
_INT_COLOR  = "#8B5CF6"   # violet-500
_SAVE_COLOR = "#0F172A"
_SAVE_HOVER = "#1E293B"


class PalawanPayableContainer(QWidget):
    """Container widget for Palawan Payable data entry (Brand A only)."""

    def __init__(self, parent_dashboard):
        super().__init__(parent_dashboard)
        self._dashboard = parent_dashboard
        self._collapsed = False
        self._setup_ui()

    # ──────────────────────────────────────────────────────────────────────
    # UI BUILD
    # ──────────────────────────────────────────────────────────────────────
    def _setup_ui(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, _sz(4), 0, 0)
        outer.setSpacing(0)

        # ── Header bar with toggle ────────────────────────────────────────
        header = QFrame()
        header.setFixedHeight(_sz(36))
        header.setStyleSheet(f"""
            QFrame {{
                background-color: {_SLATE_800};
                border-radius: {_sz(6)}px {_sz(6)}px 0 0;
            }}
        """)
        h_row = QHBoxLayout(header)
        h_row.setContentsMargins(_sz(14), 0, _sz(8), 0)
        h_row.setSpacing(_sz(8))

        title_lbl = QLabel("PALAWAN PAYABLE")
        title_lbl.setStyleSheet(
            f"color: #FFFFFF; font-size: {_sz(12)}px; font-weight: 800; "
            f"letter-spacing: 1.5px; background: transparent;"
        )
        h_row.addWidget(title_lbl, stretch=1)

        self._toggle_btn = QPushButton("▲ Collapse")
        self._toggle_btn.setFixedSize(_sz(90), _sz(24))
        self._toggle_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: #334155;
                color: #94A3B8;
                border: none;
                border-radius: {_sz(4)}px;
                font-size: {_sz(11)}px;
                font-weight: 600;
            }}
            QPushButton:hover {{ background-color: #475569; color: #F1F5F9; }}
        """)
        self._toggle_btn.clicked.connect(self._toggle_collapse)
        h_row.addWidget(self._toggle_btn)
        outer.addWidget(header)

        # ── Content area ──────────────────────────────────────────────────
        self._content = QWidget()
        self._content.setStyleSheet(f"""
            QWidget {{
                background-color: {_WHITE};
                border: 1px solid {_SLATE_200};
                border-top: none;
                border-radius: 0 0 {_sz(6)}px {_sz(6)}px;
            }}
        """)
        content_layout = QVBoxLayout(self._content)
        content_layout.setContentsMargins(_sz(12), _sz(10), _sz(12), _sz(10))
        content_layout.setSpacing(_sz(8))

        # Three section groups side by side
        sections_row = QHBoxLayout()
        sections_row.setSpacing(_sz(10))

        self._so_group,  self._so_fields  = self._make_section("PALAWAN SEND-OUT",       _SO_COLOR)
        self._po_group,  self._po_fields  = self._make_section("PALAWAN PAY-OUT",         _PO_COLOR)
        self._int_group, self._int_fields = self._make_section("PALAWAN INTERNATIONAL",   _INT_COLOR)

        sections_row.addWidget(self._so_group)
        sections_row.addWidget(self._po_group)
        sections_row.addWidget(self._int_group)
        content_layout.addLayout(sections_row)

        # Save button row
        btn_row = QHBoxLayout()
        btn_row.addStretch()
        self._save_btn = QPushButton("Save Palawan Payable")
        self._save_btn.setFixedHeight(_sz(34))
        self._save_btn.setMinimumWidth(_sz(200))
        self._save_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {_SAVE_COLOR};
                color: #FFFFFF;
                border: none;
                border-radius: {_sz(6)}px;
                font-size: {_sz(13)}px;
                font-weight: 700;
                padding: 0 {_sz(24)}px;
            }}
            QPushButton:hover   {{ background-color: {_SAVE_HOVER}; }}
            QPushButton:pressed {{ background-color: #000000; }}
        """)
        self._save_btn.clicked.connect(self._save)
        btn_row.addWidget(self._save_btn)
        content_layout.addLayout(btn_row)

        outer.addWidget(self._content)

    def _make_section(self, title: str, color: str):
        """Create one group box with Lotes + Principal + SC + Commission + TOTAL."""
        group = QGroupBox(title)
        group.setStyleSheet(f"""
            QGroupBox {{
                border: 2px solid {color};
                border-radius: {_sz(6)}px;
                margin-top: {_sz(22)}px;
                padding: {_sz(14)}px {_sz(12)}px {_sz(12)}px {_sz(12)}px;
                background-color: {_WHITE};
            }}
            QGroupBox::title {{
                color: {color};
                font-weight: 800;
                font-size: {_sz(12)}px;
                letter-spacing: 1px;
                padding: 1px {_sz(8)}px;
                background-color: {_WHITE};
                border-radius: {_sz(4)}px;
            }}
        """)
        form = QFormLayout()
        form.setSpacing(_sz(8))
        form.setContentsMargins(_sz(8), _sz(18), _sz(8), _sz(8))

        fields = {}

        # Lotes (integer)
        lotes_field = QLineEdit()
        lotes_field.setValidator(QIntValidator(0, 999999))
        lotes_field.setPlaceholderText("0")
        lotes_field.textChanged.connect(lambda: self._recalc_section(fields, total_display))
        lbl = QLabel("Lotes:")
        lbl.setStyleSheet(f"font-size: {_sz(13)}px; font-weight: 600; color: {_SLATE_700};")
        form.addRow(lbl, lotes_field)
        fields["lotes"] = lotes_field

        # Principal / SC / Commission (decimal)
        for key, label_text in [("principal", "Principal:"), ("sc", "SC:"), ("commission", "Commission:")]:
            f = QLineEdit()
            f.setValidator(QDoubleValidator(0.0, 1e12, 2))
            f.setPlaceholderText("0.00")
            f.textChanged.connect(lambda checked=False, flds=fields, td=None: None)  # placeholder
            lbl2 = QLabel(label_text)
            lbl2.setStyleSheet(f"font-size: {_sz(13)}px; font-weight: 600; color: {_SLATE_700};")
            form.addRow(lbl2, f)
            fields[key] = f

        # TOTAL (read-only display)
        total_display = QLineEdit("0.00")
        total_display.setReadOnly(True)
        total_display.setStyleSheet(
            f"font-weight: 800; font-size: {_sz(13)}px; color: {color}; "
            f"background-color: {_SLATE_50}; border: 1px solid {_SLATE_200}; "
            f"border-radius: {_sz(4)}px; padding: {_sz(6)}px {_sz(10)}px;"
        )
        total_lbl = QLabel("TOTAL:")
        total_lbl.setStyleSheet(f"font-weight: 700; color: {color}; font-size: {_sz(13)}px;")
        form.addRow(total_lbl, total_display)
        fields["total_display"] = total_display

        # Now fix up the textChanged connections now that total_display exists
        for key in ("principal", "sc", "commission"):
            fields[key].textChanged.connect(
                lambda _text, flds=fields, td=total_display: self._recalc_section(flds, td)
            )
        fields["lotes"].textChanged.disconnect()
        fields["lotes"].textChanged.connect(
            lambda _text, flds=fields, td=total_display: self._recalc_section(flds, td)
        )

        group.setLayout(form)
        return group, fields

    def _recalc_section(self, fields: dict, total_display: QLineEdit):
        total = 0.0
        for key in ("principal", "sc", "commission"):
            try:
                total += float(fields[key].text().strip() or 0)
            except ValueError:
                pass
        total_display.setText(f"{total:.2f}")

    # ──────────────────────────────────────────────────────────────────────
    # COLLAPSE / EXPAND
    # ──────────────────────────────────────────────────────────────────────
    def _toggle_collapse(self):
        self._collapsed = not self._collapsed
        self._content.setVisible(not self._collapsed)
        self._toggle_btn.setText("▼ Expand" if self._collapsed else "▲ Collapse")

    # ──────────────────────────────────────────────────────────────────────
    # DATA ACCESS
    # ──────────────────────────────────────────────────────────────────────
    def get_data(self) -> dict:
        """Return current field values as a dict for DB insertion."""
        def _int(f): 
            try: return int(float(f.text().strip() or 0))
            except ValueError: return 0
        def _dec(f):
            try: return float(f.text().strip() or 0)
            except ValueError: return 0.0

        sf, pf, inf = self._so_fields, self._po_fields, self._int_fields
        return {
            "so_lotes":       _int(sf["lotes"]),
            "so_principal":   _dec(sf["principal"]),
            "so_sc":          _dec(sf["sc"]),
            "so_commission":  _dec(sf["commission"]),
            "so_total":       _dec(sf["total_display"]),
            "po_lotes":       _int(pf["lotes"]),
            "po_principal":   _dec(pf["principal"]),
            "po_sc":          _dec(pf["sc"]),
            "po_commission":  _dec(pf["commission"]),
            "po_total":       _dec(pf["total_display"]),
            "int_lotes":      _int(inf["lotes"]),
            "int_principal":  _dec(inf["principal"]),
            "int_sc":         _dec(inf["sc"]),
            "int_commission": _dec(inf["commission"]),
            "int_total":      _dec(inf["total_display"]),
        }

    def load_data(self, data: dict):
        """Populate fields from a DB row dict."""
        def _set_int(f, val):
            f.blockSignals(True)
            try:
                n = int(float(val or 0))
            except (TypeError, ValueError):
                n = 0
            f.setText(str(n) if n else "")
            f.blockSignals(False)

        def _set_dec(f, val):
            f.blockSignals(True)
            v = float(val or 0)
            f.setText(f"{v:.2f}" if v else "")
            f.blockSignals(False)

        for prefix, fields in [("so", self._so_fields), ("po", self._po_fields), ("int", self._int_fields)]:
            _set_int(fields["lotes"],      data.get(f"{prefix}_lotes", 0))
            _set_dec(fields["principal"],  data.get(f"{prefix}_principal", 0))
            _set_dec(fields["sc"],         data.get(f"{prefix}_sc", 0))
            _set_dec(fields["commission"], data.get(f"{prefix}_commission", 0))
            # Recalc totals
            self._recalc_section(fields, fields["total_display"])

    def clear_fields(self):
        for fields in (self._so_fields, self._po_fields, self._int_fields):
            for key in ("lotes", "principal", "sc", "commission"):
                fields[key].blockSignals(True)
                fields[key].clear()
                fields[key].blockSignals(False)
            fields["total_display"].setText("0.00")

    def set_enabled(self, enabled: bool):
        for fields in (self._so_fields, self._po_fields, self._int_fields):
            for key in ("lotes", "principal", "sc", "commission"):
                fields[key].setEnabled(enabled)
        self._save_btn.setEnabled(enabled)

    # ──────────────────────────────────────────────────────────────────────
    # SAVE
    # ──────────────────────────────────────────────────────────────────────
    def _save(self):
        dash = self._dashboard
        sd = dash.date_picker.date().toString("yyyy-MM-dd")
        data = self.get_data()
        try:
            dash.db_manager.execute_query(
                """INSERT INTO payable_tbl_brand_a
                   (corporation, branch, date,
                    sendout_lotes, sendout_capital, sendout_sc, sendout_commission, sendout_total,
                    payout_lotes,  payout_capital,  payout_sc,  payout_commission,  payout_total,
                    international_lotes, international_capital, international_sc,
                    international_commission, international_total)
                   VALUES (%s,%s,%s, %s,%s,%s,%s,%s, %s,%s,%s,%s,%s, %s,%s,%s,%s,%s)
                   ON DUPLICATE KEY UPDATE
                    sendout_lotes=VALUES(sendout_lotes),
                    sendout_capital=VALUES(sendout_capital),
                    sendout_sc=VALUES(sendout_sc),
                    sendout_commission=VALUES(sendout_commission),
                    sendout_total=VALUES(sendout_total),
                    payout_lotes=VALUES(payout_lotes),
                    payout_capital=VALUES(payout_capital),
                    payout_sc=VALUES(payout_sc),
                    payout_commission=VALUES(payout_commission),
                    payout_total=VALUES(payout_total),
                    international_lotes=VALUES(international_lotes),
                    international_capital=VALUES(international_capital),
                    international_sc=VALUES(international_sc),
                    international_commission=VALUES(international_commission),
                    international_total=VALUES(international_total),
                    updated_at=CURRENT_TIMESTAMP
                """,
                (
                    dash.corporation, dash.branch, sd,
                    data["so_lotes"],  data["so_principal"],  data["so_sc"],
                    data["so_commission"],  data["so_total"],
                    data["po_lotes"],  data["po_principal"],  data["po_sc"],
                    data["po_commission"],  data["po_total"],
                    data["int_lotes"], data["int_principal"], data["int_sc"],
                    data["int_commission"], data["int_total"],
                )
            )
            QMessageBox.information(
                self, "Saved",
                f"Palawan Payable saved for {sd}."
            )
            logger.info("[PalawanPayable] saved for branch=%s date=%s", dash.branch, sd)
        except Exception as e:
            logger.error("[PalawanPayable] save error: %s", e)
            QMessageBox.critical(self, "Error", f"Failed to save Palawan Payable:\n{e}")
