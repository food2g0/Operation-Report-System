from PyQt5.QtWidgets import (
    QWidget, QScrollArea, QFrame, QGroupBox, QFormLayout,
    QHBoxLayout, QVBoxLayout, QLabel, QComboBox, QDateEdit,
    QPushButton, QCheckBox, QMessageBox,
)
from PyQt5.QtCore import Qt, QDate
import json

from Client.salary_detail_dialog import SalaryDetailDialog
from Client.dashboard.dialogs import FundTransferHODialog, MotorCarDetailDialog, EmpenaDetailDialog


def build_daily_cash_widget(self):
    main_widget = QWidget()
    scroll_area = QScrollArea()
    scroll_area.setWidgetResizable(True)
    scroll_area.setWidget(main_widget)

    layout = QVBoxLayout(main_widget)
    layout.setSpacing(15)

    layout.addWidget(self._build_header_frame())

    columns_layout = QHBoxLayout()
    columns_layout.setSpacing(15)
    columns_layout.addWidget(self._build_debit_box())
    columns_layout.addWidget(self._build_credit_box())
    layout.addLayout(columns_layout)

    totals_frame, results_frame = self._build_totals_and_results()
    layout.addWidget(totals_frame)
    layout.addWidget(results_frame)

    self._build_actions_and_palawan(layout)

    container = QWidget()
    container_layout = QVBoxLayout(container)
    container_layout.addWidget(scroll_area)
    return container

# ── Sub-builders ─────────────────────────────────────────────────────────

def _build_header_frame(self):
    header_frame = QFrame()
    header_frame.setStyleSheet("background-color: white; border-radius: 8px; padding: 10px;")
    header_layout = QVBoxLayout(header_frame)

    filter_type_layout = QHBoxLayout()
    filter_type_label = QLabel("Filter By:")
    filter_type_label.setProperty("class", "header")
    self.filter_type_selector = QComboBox()
    self.filter_type_selector.addItem("Corporation", "corporation")
    self.filter_type_selector.addItem("Group", "group")
    self.filter_type_selector.currentIndexChanged.connect(self.on_filter_type_changed)
    filter_type_layout.addWidget(filter_type_label)
    filter_type_layout.addWidget(self.filter_type_selector)
    filter_type_layout.addStretch()
    header_layout.addLayout(filter_type_layout)

    selection_layout = QHBoxLayout()
    selection_layout.setSpacing(15)

    self.corp_label = QLabel("Corporation:")
    self.corp_label.setProperty("class", "header")
    self.corp_selector = QComboBox()
    self.corp_selector.currentTextChanged.connect(self.load_branches)

    self.os_label = QLabel("Group:")
    self.os_label.setProperty("class", "header")
    self.os_selector = QComboBox()
    self.os_selector.currentTextChanged.connect(self.load_branches_by_os)
    self.os_label.setVisible(False)
    self.os_selector.setVisible(False)

    branch_label = QLabel("Branch:")
    branch_label.setProperty("class", "header")
    self.branch_selector = QComboBox()

    date_label = QLabel("Date:")
    date_label.setProperty("class", "header")
    self.date_picker = QDateEdit()
    self.date_picker.setDisplayFormat("dd MMM yyyy")
    self.date_picker.setCalendarPopup(True)
    self.date_picker.setDate(QDate.currentDate())
    _cal_style = (
        "QDateEdit{border:1px solid #bdc3c7;border-radius:4px;padding:5px 28px 5px 8px;"
        "background-color:white;font-size:11px;min-height:25px;min-width:130px;}"
        "QDateEdit:focus{border:2px solid #3498db;}"
        "QDateEdit::drop-down{subcontrol-origin:border;subcontrol-position:center right;"
        "width:28px;border-left:1px solid #bdc3c7;background-color:#ecf0f1;border-top-right-radius:4px;border-bottom-right-radius:4px;}"
        "QDateEdit::drop-down:hover{background-color:#d5dbdb;}"
        "QDateEdit::down-arrow{width:10px;height:10px;}"
        "QCalendarWidget{min-width:340px;min-height:280px;background:white;border:1px solid #dee2e6;border-radius:6px;}"
        "QCalendarWidget QWidget#qt_calendar_navigationbar{background-color:#343a40;min-height:42px;padding:4px 6px;border-radius:4px 4px 0 0;}"
        "QCalendarWidget QToolButton{color:#ecf0f1;font-size:14px;font-weight:bold;background-color:transparent;padding:6px 10px;border-radius:4px;margin:2px;}"
        "QCalendarWidget QToolButton:hover{background-color:#007bff;color:white;}"
        "QCalendarWidget QToolButton:pressed{background-color:#0056b3;color:white;}"
        "QCalendarWidget QSpinBox{color:#2c3e50;background-color:#ecf0f1;font-size:13px;font-weight:bold;border:1px solid #bdc3c7;border-radius:4px;padding:4px 8px;selection-background-color:#007bff;selection-color:white;}"
        "QCalendarWidget QAbstractItemView{background:white;selection-background-color:#007bff;selection-color:white;font-size:12px;alternate-background-color:#f8f9fa;}"
        "QCalendarWidget QAbstractItemView::item{padding:6px;border-radius:4px;}"
        "QCalendarWidget QAbstractItemView::item:alternate{background-color:#f8f9fa;}"
        "QCalendarWidget QAbstractItemView::item:selected{background-color:#007bff;color:white;font-weight:bold;}"
    )
    self.date_picker.setStyleSheet(_cal_style)

    self.load_button = QPushButton("Load Entry")
    self.load_button.setObjectName("loadButton")
    self.load_button.clicked.connect(self.load_entry_by_date)

    selection_layout.addWidget(self.corp_label)
    selection_layout.addWidget(self.corp_selector, 1)
    selection_layout.addWidget(self.os_label)
    selection_layout.addWidget(self.os_selector, 1)
    selection_layout.addWidget(branch_label)
    selection_layout.addWidget(self.branch_selector, 1)
    selection_layout.addWidget(date_label)
    selection_layout.addWidget(self.date_picker)
    selection_layout.addWidget(self.load_button)

    self.reviewed_checkbox = QCheckBox("Pending review")
    self.reviewed_checkbox.setStyleSheet("""
        QCheckBox {
            font-weight: bold; font-size: 12px; padding: 5px 10px;
            color: #c0392b;
        }
        QCheckBox::indicator { width: 18px; height: 18px; }
        QCheckBox::indicator:checked {
            background-color: #27ae60; border: 2px solid #1e8449; border-radius: 3px;
        }
        QCheckBox::indicator:unchecked {
            background-color: white; border: 2px solid #bdc3c7; border-radius: 3px;
        }
    """)
    self.reviewed_checkbox.setEnabled(False)
    self.reviewed_checkbox.toggled.connect(self._on_review_toggled)
    selection_layout.addWidget(self.reviewed_checkbox)

    header_layout.addLayout(selection_layout)

    balance_layout = QHBoxLayout()
    balance_label = QLabel("Beginning Balance:")
    balance_label.setProperty("class", "important")
    self.beginning_balance_input = self.create_money_input()
    self.beginning_balance_input.setReadOnly(True)
    balance_layout.addWidget(balance_label)
    balance_layout.addWidget(self.beginning_balance_input)
    balance_layout.addStretch()

    header_layout.addLayout(balance_layout)
    return header_frame

def _build_debit_box(self):
    debit_box = QGroupBox("CREDIT")
    debit_form = QFormLayout()
    debit_form.setSpacing(8)
    debit_form.setLabelAlignment(Qt.AlignLeft)

    for label in self.debit_fields.keys():
        field_input = self.create_money_input()
        field_input.setReadOnly(False)
        self.debit_inputs[label] = field_input

        lotes_input = self.create_lotes_input(read_only=False)
        self.debit_lotes_inputs[label] = lotes_input

        row = QHBoxLayout()
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(6)
        row.addWidget(field_input, 2)
        lotes_label = QLabel("Lotes:")
        row.addWidget(lotes_label)
        row.addWidget(lotes_input)

        field_label = QLabel(label)
        if any(keyword in label.lower() for keyword in ['interest', 'penalty', 'rescate']):
            field_label.setProperty("class", "important")

        if label == "MC In":
            mc_in_btn = QPushButton("View")
            mc_in_btn.setStyleSheet("""
                QPushButton {
                    background-color: #3B82F6; color: white;
                    border: none; border-radius: 5px;
                    font-size: 11px; font-weight: 700;
                    padding: 4px 8px;
                }
                QPushButton:hover { background-color: #2563EB; }
            """)
            mc_in_btn.setToolTip("Show MC In currency breakdown")
            mc_in_btn.clicked.connect(lambda checked, ft="MC In": self.show_mc_breakdown(ft))
            row.addWidget(mc_in_btn)

        elif label in ("Fund Transfer", "Fund Transfer from BRANCH"):
            from_branch_btn = QPushButton("View")
            from_branch_btn.setStyleSheet("""
                QPushButton {
                    background-color: #059669; color: white;
                    border: none; border-radius: 5px;
                    font-size: 11px; font-weight: 700;
                    padding: 4px 10px;
                }
                QPushButton:hover { background-color: #047857; }
            """)
            from_branch_btn.setToolTip("View source branch for this fund transfer")
            from_branch_btn.clicked.connect(self.show_from_branch_dest_info)
            self.from_branch_dest_btn = from_branch_btn
            row.addWidget(from_branch_btn)

        debit_form.addRow(field_label, row)

    debit_box.setLayout(debit_form)
    return debit_box

def _build_credit_box(self):
    credit_box = QGroupBox("DEBIT")
    credit_form = QFormLayout()
    credit_form.setSpacing(8)
    credit_form.setLabelAlignment(Qt.AlignLeft)

    for label in self.credit_fields.keys():
        field_input = self.create_money_input()
        field_input.setReadOnly(False)
        self.credit_inputs[label] = field_input

        lotes_input = self.create_lotes_input(read_only=False)
        self.credit_lotes_inputs[label] = lotes_input

        row = QHBoxLayout()
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(6)
        row.addWidget(field_input, 2)

        if label == "Fund Transfer to HEAD OFFICE":
            bank_btn = QPushButton("View")
            bank_btn.setStyleSheet("""
                QPushButton {
                    background-color: #8B5CF6; color: white;
                    border: none; border-radius: 5px;
                    font-size: 11px; font-weight: 700;
                    padding: 4px 10px;
                }
                QPushButton:hover { background-color: #7C3AED; }
            """)
            bank_btn.setToolTip("View fund transfer breakdown")
            bank_btn.clicked.connect(self._show_ft_ho_breakdown)
            self.bank_account_btn = bank_btn
            row.addWidget(bank_btn)

        elif label == "Fund Transfer to BRANCH":
            branch_btn = QPushButton("View")
            branch_btn.setStyleSheet("""
                QPushButton {
                    background-color: #059669; color: white;
                    border: none; border-radius: 5px;
                    font-size: 11px; font-weight: 700;
                    padding: 4px 10px;
                }
                QPushButton:hover { background-color: #047857; }
            """)
            branch_btn.setToolTip("View destination branch for this fund transfer")
            branch_btn.clicked.connect(self.show_branch_dest_info)
            self.branch_dest_btn = branch_btn
            row.addWidget(branch_btn)
        else:
            lotes_label = QLabel("Lotes:")
            row.addWidget(lotes_label)
            row.addWidget(lotes_input)

        field_label = QLabel(label)
        if any(keyword in label.lower() for keyword in ['empeno', 'fund transfer', 'salary']):
            field_label.setProperty("class", "important")

        if label == "PC-Salary" and self._is_brand_a:
            breakdown_btn = QPushButton("View")
            breakdown_btn.setStyleSheet("""
                QPushButton {
                    background-color: #2563EB; color: white;
                    border: none; border-radius: 5px;
                    font-size: 12px; font-weight: 700;
                    padding: 4px 12px;
                }
                QPushButton:hover { background-color: #1D4ED8; }
            """)
            breakdown_btn.setToolTip("Show salary breakdown for P.C. Salary")
            breakdown_btn.clicked.connect(self._show_salary_breakdown)
            row.addWidget(breakdown_btn)

        if label == "Empeno Motor/Car":
            motor_btn = QPushButton("View")
            motor_btn.setStyleSheet("""
                QPushButton {
                    background-color: #D97706; color: white;
                    border: none; border-radius: 5px;
                    font-size: 11px; font-weight: 700;
                    padding: 4px 8px;
                }
                QPushButton:hover { background-color: #B45309; }
            """)
            motor_btn.setToolTip("Show Motor/Car breakdown")
            motor_btn.clicked.connect(self._show_motor_breakdown)
            row.addWidget(motor_btn)

        if label in ("Empeno JEW. (NEW)", "Empeno JEW (RENEW)"):
            breakdown_col = ('empeno_jew_new_breakdown'
                             if label == "Empeno JEW. (NEW)"
                             else 'empeno_jew_renew_breakdown')
            jew_btn = QPushButton("View")
            jew_btn.setStyleSheet("""
                QPushButton {
                    background-color: #7C3AED; color: white;
                    border: none; border-radius: 5px;
                    font-size: 11px; font-weight: 700;
                    padding: 4px 8px;
                }
                QPushButton:hover { background-color: #6D28D9; }
            """)
            jew_btn.setToolTip(f"Show {label} breakdown")
            jew_btn.clicked.connect(
                lambda checked=False, c=breakdown_col, l=label: self._show_jew_breakdown(c, l)
            )
            row.addWidget(jew_btn)

        if label == "MC Out":
            mc_out_btn = QPushButton("View")
            mc_out_btn.setStyleSheet("""
                QPushButton {
                    background-color: #DC2626; color: white;
                    border: none; border-radius: 5px;
                    font-size: 11px; font-weight: 700;
                    padding: 4px 8px;
                }
                QPushButton:hover { background-color: #B91C1C; }
            """)
            mc_out_btn.setToolTip("Show MC Out currency breakdown")
            mc_out_btn.clicked.connect(lambda checked, ft="MC Out": self.show_mc_breakdown(ft))
            row.addWidget(mc_out_btn)

        credit_form.addRow(field_label, row)

    credit_box.setLayout(credit_form)
    return credit_box

def _build_totals_and_results(self):
    totals_frame = QFrame()
    totals_frame.setStyleSheet(
        "background-color: #e8f5e9; border: 2px solid #81c784; border-radius: 8px; padding: 15px;")
    totals_layout = QHBoxLayout(totals_frame)

    debit_total_label = QLabel("Total Cash Receipt:")
    debit_total_label.setProperty("class", "important")
    debit_total_label.setStyleSheet("font-weight: bold; font-size: 12px; color: #2e7d32;")
    self.debit_total_display = self.create_display_field()
    self.debit_total_display.setStyleSheet(
        "background-color: #c8e6c9; border: 2px solid #66bb6a; font-weight: bold; font-size: 12px; color: #1b5e20;")

    credit_total_label = QLabel("Total Cash out:")
    credit_total_label.setProperty("class", "important")
    credit_total_label.setStyleSheet("font-weight: bold; font-size: 12px; color: #c62828;")
    self.credit_total_display = self.create_display_field()
    self.credit_total_display.setStyleSheet(
        "background-color: #ffcdd2; border: 2px solid #e57373; font-weight: bold; font-size: 12px; color: #b71c1c;")

    totals_layout.addWidget(debit_total_label)
    totals_layout.addWidget(self.debit_total_display, 1)
    totals_layout.addWidget(credit_total_label)
    totals_layout.addWidget(self.credit_total_display, 1)

    results_frame = QFrame()
    results_frame.setStyleSheet(
        "background-color: #fff3cd; border: 2px solid #ffeaa7; border-radius: 8px; padding: 15px;")
    results_layout = QHBoxLayout(results_frame)

    ending_label = QLabel("Ending Balance:")
    ending_label.setProperty("class", "important")
    self.ending_balance_display = self.create_display_field()
    self.ending_balance_display.setProperty("class", "result")

    cash_label = QLabel("Cash Count:")
    cash_label.setProperty("class", "important")
    self.cash_count_input = self.create_money_input()
    self.cash_count_input.setReadOnly(False)

    result_label = QLabel("⚖️ Short/Over:")
    result_label.setProperty("class", "important")
    self.cash_result_display = self.create_display_field()
    self.cash_result_display.setProperty("class", "result")

    results_layout.addWidget(ending_label)
    results_layout.addWidget(self.ending_balance_display, 1)
    results_layout.addWidget(cash_label)
    results_layout.addWidget(self.cash_count_input, 1)
    results_layout.addWidget(result_label)
    results_layout.addWidget(self.cash_result_display, 1)

    status_label = QLabel("Status:")
    status_label.setProperty("class", "important")
    self.variance_status_display = QLabel("—")
    self.variance_status_display.setStyleSheet(
        "font-weight: bold; font-size: 12px; padding: 5px 10px; border-radius: 4px;"
    )
    results_layout.addWidget(status_label)
    results_layout.addWidget(self.variance_status_display)

    return totals_frame, results_frame

def _build_actions_and_palawan(self, layout):
    action_layout = QHBoxLayout()
    action_layout.addStretch()

    save_button = QPushButton("Save Changes")
    save_button.setObjectName("saveButton")
    save_button.setStyleSheet("""
        QPushButton {
            background-color: #27ae60;
            color: white;
        }
        QPushButton:hover {
            background-color: #219a52;
        }
    """)
    save_button.clicked.connect(self.save_entry)

    reset_button = QPushButton("Reset Entry")
    reset_button.setObjectName("resetButton")
    reset_button.setStyleSheet("""
        QPushButton {
            background-color: #E67E22;
            color: white;
        }
        QPushButton:hover {
            background-color: #D35400;
        }
    """)
    reset_button.clicked.connect(self.reset_entry)

    export_button = QPushButton("Export to Excel")
    export_button.setObjectName("exportButton")
    export_button.setStyleSheet("""
        QPushButton {
            background-color: #217346;
            color: white;
        }
        QPushButton:hover {
            background-color: #1a5c38;
        }
    """)
    export_button.clicked.connect(self.export_daily_cash_to_excel)

    full_brand_btn = QPushButton("Generate Report")
    full_brand_btn.setObjectName("fullBrandReportButton")
    full_brand_btn.setStyleSheet("""
        QPushButton {
            background-color: #27AE60;
            color: white;
        }
        QPushButton:hover {
            background-color: #1E8449;
        }
    """)
    full_brand_btn.clicked.connect(self.show_full_brand_report_dialog)

    action_layout.addWidget(save_button)
    action_layout.addWidget(reset_button)
    action_layout.addWidget(export_button)
    action_layout.addWidget(full_brand_btn)
    layout.addLayout(action_layout)

    self.palawan_inputs = {}
    self.palawan_total_displays = {}
    palawan_collapsible = self._build_palawan_collapsible()
    layout.addWidget(palawan_collapsible)

    for inp in self.debit_inputs.values():
        inp.textChanged.connect(self._recalc_totals)
    for inp in self.credit_inputs.values():
        inp.textChanged.connect(self._recalc_totals)
    self.beginning_balance_input.textChanged.connect(self._recalc_totals)
    self.cash_count_input.textChanged.connect(self._recalc_totals)

# ── Breakdown dialog handlers ─────────────────────────────────────────────

def _show_ft_ho_breakdown(self):
    entry = self.get_current_entry_data()
    if not entry:
        QMessageBox.information(self, "No Entry Loaded",
            "Please load an entry first by selecting a branch and date, then clicking Load.")
        return
    breakdown = []
    raw = entry.get('ft_ho_breakdown')
    if raw:
        try:
            breakdown = json.loads(raw)
        except Exception:
            breakdown = []
    if not breakdown:
        if self.selected_bank_account:
            self.show_bank_account_info()
        else:
            QMessageBox.information(self, "No Breakdown",
                "No Fund Transfer to HEAD OFFICE breakdown data found.\n\n"
                "The client needs to submit using the new breakdown format.")
        return
    dlg = FundTransferHODialog("Fund Transfer to HEAD OFFICE", parent=self)
    dlg.setWindowTitle("Fund Transfer to HEAD OFFICE Breakdown (View Only)")
    dlg.setMinimumSize(750, 460)
    while dlg.table.rowCount() > 0:
        dlg.table.removeRow(0)
    dlg._rows_data = []
    for bank_display, bank_id, amt in breakdown:
        row_idx = dlg.table.rowCount()
        dlg.table.insertRow(row_idx)
        bank_label = QLabel(f"  {bank_display}")
        bank_label.setStyleSheet(
            "font-size: 12px; font-weight: 600; color: #1E293B; padding: 4px 6px;"
        )
        bank_label.setToolTip(bank_display)
        dlg.table.setCellWidget(row_idx, 0, bank_label)
        amt_label = QLabel(f"  {amt:,.2f}")
        amt_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        amt_label.setStyleSheet(
            "font-size: 13px; font-weight: 700; color: #0F766E; padding: 4px 8px;"
        )
        dlg.table.setCellWidget(row_idx, 1, amt_label)
        empty = QLabel("")
        dlg.table.setCellWidget(row_idx, 2, empty)
    dlg._recalc()
    for child in dlg.findChildren(QPushButton):
        if "Add" in child.text():
            child.setVisible(False)
        if child.text() == "Post":
            child.setText("Close")
    dlg.exec_()

def _show_salary_breakdown(self):
    entry = self.get_current_entry_data()
    breakdown = []
    if entry and entry.get('pc_salary_breakdown'):
        try:
            breakdown = json.loads(entry['pc_salary_breakdown'])
        except Exception:
            breakdown = []
    if not breakdown:
        QMessageBox.information(self, "No Breakdown",
            "No salary breakdown available for this entry.\n\n"
            "Please load an entry with salary breakdown data first.")
        return
    dlg = SalaryDetailDialog(parent=self)
    dlg.setWindowTitle("P.C. Salary Breakdown (View Only)")
    while dlg.table.rowCount() > 0:
        dlg.table.removeRow(0)
    dlg._rows_data = []
    for name, salary in breakdown:
        dlg._add_row()
        row_idx = dlg.table.rowCount() - 1
        dlg.table.cellWidget(row_idx, 0).setText(str(name))
        dlg.table.cellWidget(row_idx, 1).setText(str(salary))
        dlg.table.cellWidget(row_idx, 0).setReadOnly(True)
        dlg.table.cellWidget(row_idx, 1).setReadOnly(True)
    dlg._recalc()
    dlg.exec_()

def _show_motor_breakdown(self):
    entry = self.get_current_entry_data()
    breakdown = []
    if entry and entry.get('empeno_motor_car_breakdown'):
        try:
            breakdown = json.loads(entry['empeno_motor_car_breakdown'])
        except Exception:
            breakdown = []
    if not breakdown:
        QMessageBox.information(self, "No Breakdown",
            "No Motor/Car breakdown available for this entry.\n\n"
            "Please load an entry with Motor/Car breakdown data first.")
        return
    dlg = MotorCarDetailDialog("Empeno Motor/Car", parent=self)
    dlg.setWindowTitle("Empeno Motor/Car Breakdown (View Only)")
    while dlg.table.rowCount() > 0:
        dlg.table.removeRow(0)
    dlg._rows_data = []
    for pct_str, amt in breakdown:
        dlg._add_row()
        row_idx = dlg.table.rowCount() - 1
        combo = dlg.table.cellWidget(row_idx, 0)
        idx = combo.findText(pct_str)
        if idx >= 0:
            combo.setCurrentIndex(idx)
        combo.setEnabled(False)
        amt_edit = dlg.table.cellWidget(row_idx, 1)
        amt_edit.setText(f"{amt:.2f}")
        amt_edit.setReadOnly(True)
        rem_btn = dlg.table.cellWidget(row_idx, 3)
        if rem_btn:
            rem_btn.setVisible(False)
    dlg._recalc()
    dlg.exec_()

def _show_jew_breakdown(self, col, lbl):
    entry = self.get_current_entry_data()
    breakdown = []
    if entry and entry.get(col):
        try:
            breakdown = json.loads(entry[col])
        except Exception:
            breakdown = []
    if not breakdown:
        QMessageBox.information(self, "No Breakdown",
            f"No {lbl} breakdown available for this entry.\n\n"
            "Please load an entry with breakdown data first.")
        return
    dlg = EmpenaDetailDialog(lbl, parent=self)
    dlg.setWindowTitle(f"{lbl} Breakdown (View Only)")
    while dlg.table.rowCount() > 0:
        dlg.table.removeRow(0)
    dlg._rows_data = []
    for pct_str, amt in breakdown:
        dlg._add_row()
        row_idx = dlg.table.rowCount() - 1
        combo = dlg.table.cellWidget(row_idx, 0)
        idx = combo.findText(pct_str)
        if idx >= 0:
            combo.setCurrentIndex(idx)
        combo.setEnabled(False)
        amt_edit = dlg.table.cellWidget(row_idx, 1)
        amt_edit.setText(f"{amt:.2f}")
        amt_edit.setReadOnly(True)
        rem_btn = dlg.table.cellWidget(row_idx, 3)
        if rem_btn:
            rem_btn.setVisible(False)
    dlg._recalc()
    for child in dlg.findChildren(QPushButton):
        if "Add" in child.text():
            child.setVisible(False)
        if child.text() == "Post":
            child.setText("Close")
    dlg.exec_()

