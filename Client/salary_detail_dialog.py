from PyQt5.QtWidgets import QDialog, QVBoxLayout, QTableWidget, QHeaderView, QAbstractItemView, QPushButton, QLabel, QLineEdit, QDialogButtonBox, QHBoxLayout, QFrame
from PyQt5.QtGui import QDoubleValidator
from PyQt5.QtCore import Qt

class SalaryDetailDialog(QDialog):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Employee Salary Breakdown")
        self.setMinimumSize(520, 420)
        self.setModal(True)
        self._rows_data = []

        root = QVBoxLayout(self)
        root.setSpacing(12)
        root.setContentsMargins(16, 16, 16, 16)

        title = QLabel("Breakdown for P.C. Salary")
        title.setStyleSheet("font-size: 15px; font-weight: 800; color: #1E293B;")
        root.addWidget(title)

        self.table = QTableWidget(0, 3)
        self.table.setHorizontalHeaderLabels(["Employee Name", "Salary", ""])
        hh = self.table.horizontalHeader()
        hh.setSectionResizeMode(0, QHeaderView.Stretch)
        hh.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        hh.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.table.setSelectionMode(QAbstractItemView.NoSelection)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.setStyleSheet("""
            QTableWidget { border: 1px solid #E2E8F0; border-radius: 6px; }
            QHeaderView::section { background: #F1F5F9; font-weight: 700;
                                   font-size: 13px; padding: 6px; border: none; }
            QTableWidget::item { padding: 4px 8px; }
        """)
        root.addWidget(self.table)

        add_btn = QPushButton("+ Add Employee")
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
        ta_title = QLabel("Total Salary")
        ta_title.setStyleSheet("font-size: 13px; font-weight: 700; color: #64748B;")
        self._total_salary_lbl = QLabel("0.00")
        self._total_salary_lbl.setStyleSheet(
            "font-size: 18px; font-weight: 800; color: #0F766E;"
        )
        ta_sub = QLabel("(pasted to field)")
        ta_sub.setStyleSheet("font-size: 12px; color: #94A3B8;")
        ta_box.addWidget(ta_title)
        ta_box.addWidget(self._total_salary_lbl)
        ta_box.addWidget(ta_sub)

        totals_layout.addLayout(ta_box)
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

        name_edit = QLineEdit()
        name_edit.setPlaceholderText("Employee Name")
        name_edit.setStyleSheet(
            "border: 1px solid #CBD5E1; border-radius: 5px;"
            "padding: 5px 8px; font-size: 12px;"
        )
        self.table.setCellWidget(row, 0, name_edit)

        salary_edit = QLineEdit()
        salary_edit.setPlaceholderText("0.00")
        salary_edit.setValidator(QDoubleValidator(0.0, 1e12, 2))
        salary_edit.setStyleSheet(
            "border: 1px solid #CBD5E1; border-radius: 5px;"
            "padding: 5px 8px; font-size: 12px;"
        )
        self.table.setCellWidget(row, 1, salary_edit)

        rem_btn = QPushButton("✕")
        rem_btn.setFixedWidth(28)
        rem_btn.setStyleSheet(
            "QPushButton{background:#FEE2E2;color:#DC2626;border:none;"
            "border-radius:4px;font-weight:700;font-size:11px;}"
            "QPushButton:hover{background:#FECACA;}"
        )
        rem_btn.clicked.connect(lambda _, b=rem_btn: self._remove_row_by_widget(b))
        self.table.setCellWidget(row, 2, rem_btn)

        self._rows_data.append((name_edit, salary_edit))
        name_edit.textChanged.connect(self._recalc)
        salary_edit.textChanged.connect(self._recalc)
        self.table.resizeRowsToContents()

    def _remove_row_by_widget(self, btn):
        for r in range(self.table.rowCount()):
            if self.table.cellWidget(r, 2) is btn:
                self.table.removeRow(r)
                self._rows_data = []
                for rr in range(self.table.rowCount()):
                    ne = self.table.cellWidget(rr, 0)
                    se = self.table.cellWidget(rr, 1)
                    if ne and se:
                        self._rows_data.append((ne, se))
                self._recalc()
                return

    def _recalc(self, *_):
        total_salary = 0.0
        for name_edit, salary_edit in self._rows_data:
            try:
                salary = float(salary_edit.text().strip() or 0)
            except ValueError:
                salary = 0.0
            total_salary += salary
        self._total_salary_lbl.setText(f"{total_salary:,.2f}")

    def get_total_salary(self) -> float:
        try:
            return float(self._total_salary_lbl.text().replace(',', ''))
        except ValueError:
            return 0.0

    def get_salary_breakdown(self):
        """Return list of (name, salary) tuples."""
        result = []
        for name_edit, salary_edit in self._rows_data:
            name = name_edit.text().strip()
            try:
                salary = float(salary_edit.text().strip() or 0)
            except ValueError:
                salary = 0.0
            if name:
                result.append((name, salary))
        return result
