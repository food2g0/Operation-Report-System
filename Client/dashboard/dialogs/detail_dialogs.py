"""Detail dialog classes for breaking down monetary amounts.

Provides reusable dialogs for:
- FundTransferHODialog: Fund transfer breakdowns by bank account
- MotorCarDetailDialog: Motor car breakdown with percentages
- EmpenaDetailDialog: Jewelry (empeno) breakdown with percentages
"""

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QFrame, QTableWidget, QTableWidgetItem, QComboBox, QHeaderView,
    QAbstractItemView, QDialogButtonBox
)
from PyQt5.QtGui import QDoubleValidator
from PyQt5.QtCore import Qt


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
