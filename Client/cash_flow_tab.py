from PyQt5.QtWidgets import (
    QWidget, QLabel, QLineEdit, QVBoxLayout, QHBoxLayout,
    QGroupBox, QFormLayout, QScrollArea, QFrame
)
from PyQt5.QtGui import QDoubleValidator
from PyQt5.QtCore import Qt


class CashFlowTab(QWidget):
    def __init__(self, parent):
        super().__init__()
        self.parent = parent
        self.setup_ui()

    def setup_ui(self):
        """Setup the cash flow tab UI"""
        layout = QHBoxLayout(self)

        # === Debit Section ===
        debit_scroll = QScrollArea()
        debit_scroll.setWidgetResizable(True)
        debit_scroll.setMaximumHeight(600)

        debit_box = QGroupBox("Cash Outflow (Debit)")
        debit_form = QFormLayout()
        debit_form.setSpacing(8)
        debit_form.setContentsMargins(15, 20, 15, 15)

        debit_fields = [
            ("Rescate Jewelry", "Enter Rescate Jewelry"),
            ("Interest", "Enter Interest"),
            ("Penalty", "Enter Penalty"),
            ("Stamp", "Enter Stamp"),
            ("Resguardo/Affidavit", "Enter Resguardo/Affidavit"),
            ("HABOL Renew/Tubos", "Enter Habol Renew/Tubos"),
            ("Habol R/T Interest&Stamp", "Enter Habol R/T Interest&Stamp"),
            ("Jew. A.I", "Enter Jew. A.I"),
            ("S.C", "Enter S.C."),
            ("Fund Transfer from BRANCH", "Enter Fund Transfer from BRANCH"),
            ("Sendah Load + SC", "Enter Sendah Load + SC"),
            ("PPAY CO SC", "Enter PPAY CO SC"),
            ("Palawan Send Out", "Enter Palawan Send Out"),
            ("Palawan S.C", "Enter Palawan S.C"),
            ("Palawan Suki Card", "Enter Palawan Suki Card"),
            ("Palawan Pay Cash-In + SC", "Enter Palawan Pay Cash-In + SC"),
            ("Palawan Pay Bills + SC", "Enter Palawan Pay Bills + SC"),
            ("Palawan Load", "Enter Palawan Load"),
            ("Palawan Change Receiver", "Enter Palawan Change Receiver"),
            ("MC In", "Enter MC In"),
            ("Handling fee", "Enter Handling fee"),
            ("Other Penalty", "Enter Other Penalty"),
            ("Cash Shortage/Overage", "Enter Cash Shortage/Overage"),
        ]
        self.debit_inputs = self.build_input_group(debit_form, debit_fields)

        # Add separator and total
        debit_form.addRow(self.parent.create_separator(), QLabel(""))
        self.debit_total_display = self.parent.create_display_field("0.00")
        total_label = QLabel("Total Cash Out:")
        total_label.setStyleSheet("font-weight: bold; color: #c0392b; font-size: 12px;")
        debit_form.addRow(total_label, self.debit_total_display)

        debit_box.setLayout(debit_form)
        debit_scroll.setWidget(debit_box)

        # === Credit Section ===
        credit_scroll = QScrollArea()
        credit_scroll.setWidgetResizable(True)
        credit_scroll.setMaximumHeight(600)

        credit_box = QGroupBox("Cash Inflow (Credit)")
        credit_form = QFormLayout()
        credit_form.setSpacing(8)
        credit_form.setContentsMargins(15, 20, 15, 15)

        credit_fields = [
            ("Empeno JEW. (NEW)", "Enter Empeno Jew"),
            ("Empeno JEW (RENEW)", "Enter Empeno Jew"),
            ("Fund Transfer to HEAD OFFICE", "Enter Fund Transfer to HEAD OFFICE"),
            ("Fund Transfer to BRANCH", "Enter Fund Transfer to BRANCH"),
            ("Palawan Pay Out", "Enter Palawan Pay Out"),
            ("Palawan Pay Out (incentives)", "Enter Palawan Pay Out (incentives)"),
            ("Palawan Pay Cash Out", "Enter Palawan Pay Cash Out"),
            ("MC Out", "Enter MC Out"),
            ("PC-Salary", "Enter PC-Salary"),
            ("PC-Rental", "Enter PC-Rental"),
            ("PC-Electric", "Enter PC-Electric"),
            ("PC-Water", "Enter PC-Water"),
            ("PC-Internet", "Enter PC-Internet"),
            ("PC-Lbc/Jrs/Jnt", "Enter PC-Lbc/Jrs/Jnt"),
            ("PC-Permits/BIR Payments", "Enter PC-Permits/BIR Payments"),
            ("PC-Supplies/Xerox/Maintenance", "Enter PC-Supplies/Xerox/Maintenance"),
            ("PC-Transpo", "Enter PC-Transpo"),
            ("Palawan Cancel", "Enter Palawan Cancel"),
            ("Palawan Suki Discounts", "Enter Palawan Suki Discounts"),
            ("Palawan Suki Rebates", "Enter Palawan Suki Rebates"),
            ("OTHERS", "Enter Others"),
        ]
        self.credit_inputs = self.build_input_group(credit_form, credit_fields)

        # Add separator and total
        credit_form.addRow(self.parent.create_separator(), QLabel(""))
        self.credit_total_display = self.parent.create_display_field("0.00")
        total_label = QLabel("Total Cash In:")
        total_label.setStyleSheet("font-weight: bold; color: #27ae60; font-size: 12px;")
        credit_form.addRow(total_label, self.credit_total_display)

        credit_box.setLayout(credit_form)
        credit_scroll.setWidget(credit_box)

        # Add both sections to the tab
        layout.addWidget(debit_scroll)
        layout.addWidget(credit_scroll)

    def build_input_group(self, form_layout, fields):
        """Build input group for fields"""
        inputs = {}
        for label_text, placeholder in fields:
            field = self.create_money_input(placeholder)
            label = QLabel(label_text + ":")
            form_layout.addRow(label, field)
            inputs[label_text] = field
        return inputs

    def create_money_input(self, placeholder=""):
        """Create money input field"""
        field = QLineEdit()
        field.setValidator(QDoubleValidator(0.0, 1e12, 2))
        field.setPlaceholderText(placeholder)
        field.textChanged.connect(self.parent.recalculate_all)
        return field

    def get_debit_total(self):
        """Get total debit amount"""
        return self.parent.get_total_amount(self.debit_inputs)

    def get_credit_total(self):
        """Get total credit amount"""
        return self.parent.get_total_amount(self.credit_inputs)

    def update_totals(self, beginning, debit_total, credit_total):
        """Update the total displays"""
        self.debit_total_display.setText(f"{beginning + debit_total:.2f}")
        self.credit_total_display.setText(f"{beginning - credit_total:.2f}")

    def field_name_to_db_column(self, field_name):
        """Convert field display names to database column names"""
        mapping = {
            # Debit fields
            "Rescate Jewelry": "rescate_jewelry",
            "Interest": "interest",
            "Penalty": "penalty",
            "Stamp": "stamp",
            "Resguardo/Affidavit": "resguardo_affidavit",
            "HABOL Renew/Tubos": "habol_renew_tubos",
            "Habol R/T Interest&Stamp": "habol_rt_interest_stamp",
            "Jew. A.I": "jew_ai",
            "S.C": "sc",
            "Fund Transfer from BRANCH": "fund_transfer_from_branch",
            "Sendah Load + SC": "sendah_load_sc",
            "PPAY CO SC": "ppay_co_sc",
            "Palawan Send Out": "palawan_send_out",
            "Palawan S.C": "palawan_sc",
            "Palawan Suki Card": "palawan_suki_card",
            "Palawan Pay Cash-In + SC": "palawan_pay_cash_in_sc",
            "Palawan Pay Bills + SC": "palawan_pay_bills_sc",
            "Palawan Load": "palawan_load",
            "Palawan Change Receiver": "palawan_change_receiver",
            "MC In": "mc_in",
            "Handling fee": "handling_fee",
            "Other Penalty": "other_penalty",
            "Cash Shortage/Overage": "cash_shortage_overage",

            # Credit fields
            "Empeno JEW. (NEW)": "empeno_jew_new",
            "Empeno JEW (RENEW)": "empeno_jew_renew",
            "Fund Transfer to HEAD OFFICE": "fund_transfer_to_head_office",
            "Fund Transfer to BRANCH": "fund_transfer_to_branch",
            "Palawan Pay Out": "palawan_pay_out",
            "Palawan Pay Out (incentives)": "palawan_pay_out_incentives",
            "Palawan Pay Cash Out": "palawan_pay_cash_out",
            "MC Out": "mc_out",
            "PC-Salary": "pc_salary",
            "PC-Rental": "pc_rental",
            "PC-Electric": "pc_electric",
            "PC-Water": "pc_water",
            "PC-Internet": "pc_internet",
            "PC-Lbc/Jrs/Jnt": "pc_lbc_jrs_jnt",
            "PC-Permits/BIR Payments": "pc_permits_bir_payments",
            "PC-Supplies/Xerox/Maintenance": "pc_supplies_xerox_maintenance",
            "PC-Transpo": "pc_transpo",
            "Palawan Cancel": "palawan_cancel",
            "Palawan Suki Discounts": "palawan_suki_discounts",
            "Palawan Suki Rebates": "palawan_suki_rebates",
            "OTHERS": "others",
        }
        return mapping.get(field_name, field_name.lower().replace(" ", "_"))

    def get_data(self):
        """Get all data from cash flow tab"""
        debit_values = {}
        for k, v in self.debit_inputs.items():
            value = float(v.text().strip()) if v.text().strip() else 0
            debit_values[self.field_name_to_db_column(k)] = value

        credit_values = {}
        for k, v in self.credit_inputs.items():
            value = float(v.text().strip()) if v.text().strip() else 0
            credit_values[self.field_name_to_db_column(k)] = value

        return {
            'debit': debit_values,
            'credit': credit_values
        }

    def clear_fields(self):
        """Clear all input fields"""
        for field in self.debit_inputs.values():
            field.clear()
        for field in self.credit_inputs.values():
            field.clear()