import re

from PyQt5.QtWidgets import (
    QWidget, QLabel, QLineEdit, QVBoxLayout, QHBoxLayout,
    QGroupBox, QFormLayout, QScrollArea, QFrame
)
from PyQt5.QtGui import QDoubleValidator, QIntValidator
from PyQt5.QtCore import Qt


class CashFlowTab(QWidget):
    def __init__(self, parent):
        super().__init__()
        self.parent = parent
        self.current_brand = "Brand A"  # Default to Brand A
        
        # Connect to brand change signal from parent
        self.parent.brand_changed.connect(self.on_brand_changed)
        
        # Storage for inputs
        self.debit_inputs = {}
        self.credit_inputs = {}
        self.debit_lotes_inputs = {}
        self.credit_lotes_inputs = {}
        
        # Main layout
        self.main_layout = QHBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(10)
        
        # Build initial UI for Brand A
        self.setup_ui()

    def on_brand_changed(self, brand_name):
        """Handle brand switching"""
        if brand_name == self.current_brand:
            return
        self.current_brand = brand_name
        self.rebuild_ui()

    def rebuild_ui(self):
        """Clear and rebuild entire UI for current brand"""
        while self.main_layout.count():
            item = self.main_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self.debit_inputs.clear()
        self.credit_inputs.clear()
        self.debit_lotes_inputs.clear()
        self.credit_lotes_inputs.clear()
        self.setup_ui()

    def setup_ui(self):
        """Setup UI based on current brand"""
        # === Debit Section (Cash Outflow) ===
        debit_scroll = QScrollArea()
        debit_scroll.setWidgetResizable(True)
        debit_scroll.setMaximumHeight(600)

        debit_box = QGroupBox("Cash Outflow")
        debit_form = QFormLayout()
        debit_form.setSpacing(8)
        debit_form.setContentsMargins(15, 20, 15, 15)

        debit_fields = self.get_debit_fields()
        self.debit_inputs = self.build_input_group(debit_form, debit_fields, is_debit=True)

        debit_form.addRow(self.parent.create_separator(), QLabel(""))
        self.debit_total_display = self.parent.create_display_field("0.00")
        total_label = QLabel("Total Cash In:")
        total_label.setStyleSheet("font-weight: bold; color: #c0392b; font-size: 12px;")
        debit_form.addRow(total_label, self.debit_total_display)

        debit_box.setLayout(debit_form)
        debit_scroll.setWidget(debit_box)

        # === Credit Section (Cash Inflow) ===
        credit_scroll = QScrollArea()
        credit_scroll.setWidgetResizable(True)
        credit_scroll.setMaximumHeight(600)

        credit_box = QGroupBox("Cash Inflow")
        credit_form = QFormLayout()
        credit_form.setSpacing(8)
        credit_form.setContentsMargins(15, 20, 15, 15)

        credit_fields = self.get_credit_fields()
        self.credit_inputs = self.build_input_group(credit_form, credit_fields, is_debit=False)

        credit_form.addRow(self.parent.create_separator(), QLabel(""))
        self.credit_total_display = self.parent.create_display_field("0.00")
        total_label = QLabel("Total Cash Out:")
        total_label.setStyleSheet("font-weight: bold; color: #27ae60; font-size: 12px;")
        credit_form.addRow(total_label, self.credit_total_display)

        credit_box.setLayout(credit_form)
        credit_scroll.setWidget(credit_box)

        self.main_layout.addWidget(debit_scroll)
        self.main_layout.addWidget(credit_scroll)

    def get_debit_fields(self):
        """Get debit fields based on current brand"""
        if self.current_brand == "Brand A":
            return [
                ("Rescate Jewelry", "Enter Rescate Jewelry"),
                ("Interest", "Enter Interest"),
                ("Penalty", "Enter Penalty"),
                ("Stamp", "Enter Stamp"),
                ("Rescuardo/Affidavit", "Enter Rescuardo/Affidavit"),
                ("HABOL Renew/Tubos", "Enter HABOL Renew/Tubos"),
                ("Habol R/T Interest&Stamp", "Enter Habol R/T Interest&Stamp"),
                ("CR STORAGE", "Enter CR STORAGE"),
                ("CR Storage Int/Penalty", "Enter CR Storage Int/Penalty"),
                ("Rescate Silver", "Enter Rescate Silver"),
                ("Silver int.", "Enter Silver int."),
                ("Res Storage", "Enter Res Storage"),
                ("Res. Storage Int./Penalty", "Enter Res. Storage Int./Penalty"),
                ("Res. Motor", "Enter Res. Motor"),
                ("Penalty Motor", "Enter Penalty Motor"),
                ("Jew. A.I", "Enter Jew. A.I"),
                ("S.C", "Enter S.C"),
                ("O.s.f Sto.", "Enter O.s.f Sto."),
                ("Sto. A.I", "Enter Sto. A.I"),
                ("Silver A.I", "Enter Silver A.I"),
                ("O.s.f Silver", "Enter O.s.f Silver"),
                ("Motor A.I", "Enter Motor A.I"),
                ("O.s.f Motor", "Enter O.s.f Motor"),
                ("Miscellaneous Fee", "Enter Miscellaneous Fee"),
                ("Insurance(20)", "Enter Insurance(20)"),
                ("Insurance PHILAM(php 30)", "Enter Insurance PHILAM(php 30)"),
                ("Insurance PHILAM(php 60)", "Enter Insurance PHILAM(php 60)"),
                ("Insurance PHILAM(php 90)", "Enter Insurance PHILAM(php 90)"),
                ("Fund Transfer from BRANCH", "Enter Fund Transfer from BRANCH"),
                ("AYANAH + SC", "Enter AYANAH + SC"),
                ("Sendah Load + SC", "Enter Sendah Load + SC"),
                ("Smart Money + SC", "Enter Smart Money + SC"),
                ("G-Cash In", "Enter G-Cash In"),
                ("Gcash Out S.C", "Enter Gcash Out S.C"),
                ("Abra S.O + S.C", "Enter Abra S.O + S.C"),
                ("BDO S.C", "Enter BDO S.C"),
                ("Palawan Pay Cash Out SC", "Enter Palawan Pay Cash Out SC"),
                ("Ria In + S.C", "Enter Ria In + S.C"),
                ("Paymaya In", "Enter Paymaya In"),
                ("I2I Remittance In", "Enter I2I Remittance In"),
                ("I2I Bills Payment", "Enter I2I Bills Payment"),
                ("I2I Bank Transfer", "Enter I2I Bank Transfer"),
                ("I2I Pesonet", "Enter I2I Pesonet"),
                ("I2I Instapay", "Enter I2I Instapay"),
                ("Sendah Bills + SC", "Enter Sendah Bills + SC"),
                ("Palawan Send Out", "Enter Palawan Send Out"),
                ("Palawan S.C", "Enter Palawan S.C"),
                ("Palawan Suki Card", "Enter Palawan Suki Card"),
                ("Palawan Pay Cash-In +SC", "Enter Palawan Pay Cash-In +SC"),
                ("Palawan Load + SC", "Enter Palawan Load + SC"),
                ("Palawan Pay Bills + SC", "Enter Palawan Pay Bills + SC"),
                ("Palawan Change Receiver", "Enter Palawan Change Receiver"),
                ("MC In", "Enter MC In"),
                ("Handling fee", "Enter Handling fee"),
                ("Other Penalty", "Enter Other Penalty"),
                ("Cash Overage", "Enter Cash Overage"),
            ]
        else:  # Brand B
            return [
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
                ("Cash Overage", "Enter Cash Overage"),
            ]

    def get_credit_fields(self):
        """Get credit fields based on current brand"""
        if self.current_brand == "Brand A":
            return [
                ("Empeno JEW. (NEW)", "Enter Empeno Jew"),
                ("Empeno JEW (RENEW)", "Enter Empeno Jew"),
                ("Empeno STO. (NEW)", "Enter Empeno STO. (NEW)"),
                ("Fund Empeno STO. (RENEW)", "Enter Empeno STO. (RENEW)"),
                ("Empeno Motor/Car", "Enter Empeno Motor/Car"),
                ("Empeno silver", "Enter Empeno silver"),
                ("G-Cash Out", "Enter G-Cash Out"),
                ("G-Cash Padala (SENDAH)", "Enter G-Cash Padala (SENDAH)"),
                ("Abra P.o", "Enter Abra P.o"),
                ("BDO P.o", "Enter BDO P.o"),
                ("I2I Remittance Out", "Enter I2I Remittance Out"),
                ("Remitly", "Enter Remitly"),
                ("Smart Money P.O.", "Enter Smart Money P.O."),
                ("Fund Transfer to HEAD OFFICE", "Enter Fund Transfer to HEAD OFFICE"),
                ("Fund Transfer to BRANCH", "Enter Fund Transfer to BRANCH"),
                ("AYANAH OUT", "Enter AYANAH OUT"),
                ("Palawan Pay Out", "Enter Palawan Pay Out"),
                ("Palawan Pay Out (incentives)", "Enter Palawan Pay Out (incentives)"),
                ("Palawan Pay Cash Out", "Enter Palawan Pay Cash Out"),
                ("MC Out", "Enter MC Out"),
                ("PC-Inc. Emp", "Enter PC-Inc. Emp"),
                ("PC-Inc. Motor", "Enter PC-Inc. Motor"),
                ("PC-Inc. Suki Card", "Enter PC-Inc. Suki Card"),
                ("PC-Inc. Insurance", "Enter PC-Inc. Insurance"),
                ("PC-Inc. MC", "Enter PC-Inc. MC"),
                ("PC-Salary", "Enter PC-Salary"),
                ("PC-Rental", "Enter PC-Rental"),
                ("PC-Electric", "Enter PC-Electric"),
                ("PC-Water", "Enter PC-Water"),
                ("PC-Internet", "Enter PC-Internet"),
                ("PC-Lbc/Jrs/Jnt", "Enter PC-Lbc/Jrs/Jnt"),
                ("PC-Permits/BIR Payments", "Enter PC-Permits/BIR Payments"),
                ("PC-Supplies/Xerox/Maintenance", "Enter PC-Supplies/Xerox/Maintenance"),
                ("PC-Transpo", "Enter PC-Transpo"),
                ("Transfast", "Enter Transfast"),
                ("Paymaya Out", "Enter Paymaya Out"),
                ("Ria Out", "Enter Ria Out"),
                ("FIXCO", "Enter FIXCO"),
                ("Moneygram", "Enter Moneygram"),
                ("Palawan Cancel", "Enter Palawan Cancel"),
                ("Palawan Suki Discounts", "Enter Palawan Suki Discounts"),
                ("Palawan Suki Rebates", "Enter Palawan Suki Rebates"),
                ("Storage Rebates", "Enter Storage Rebates"),
                ("Silver Rebates", "Enter Silver Rebates"),
                ("OTHERS", "Enter Others"),
                ("Cash Shortage", "Enter Cash Shortage"),
            ]
        else:  # Brand B
            return [
                ("Empeno JEW. (NEW)", "Enter Empeno Jew"),
                ("Empeno JEW (RENEW)", "Enter Empeno Jew"),
                ("Fund Transfer to HEAD OFFICE", "Enter Fund Transfer to HEAD OFFICE"),
                ("Fund Transfer to BRANCH", "Enter Fund Transfer to BRANCH"),
                ("Palawan Pay Out", "Enter Palawan Pay Out"),
                ("Palawan Pay Out (incentives)", "Enter Palawan Pay Out (incentives)"),
                ("Palawan Pay Cash Out", "Enter Palawan Pay Cash Out"),
                ("PC-Inc. Emp", "Enter PC-Inc. Emp"),
                ("PC-Inc. Suki Card", "Enter PC-Inc. Suki Card"),
                ("PC-Inc. Insurance", "Enter PC-Inc. Insurance"),
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
                ("Cash Shortage", "Enter Cash Shortage"),
            ]

    def build_input_group(self, form_layout, fields, is_debit=True):
        """Build input group for fields with lotes input"""
        inputs = {}
        lotes_inputs = self.debit_lotes_inputs if is_debit else self.credit_lotes_inputs

        for label_text, placeholder in fields:
            amount_field = self.create_money_input(placeholder)
            lotes_field = self.create_lotes_input()

            container = QWidget()
            container.setContentsMargins(0, 0, 0, 0)
            row_layout = QHBoxLayout(container)
            row_layout.setContentsMargins(0, 0, 0, 0)
            row_layout.setSpacing(6)
            row_layout.addWidget(amount_field, 1)
            row_layout.addWidget(QLabel("Lotes:"), 0)
            row_layout.addWidget(lotes_field, 0)

            label = QLabel(label_text + ":")
            form_layout.addRow(label, container)

            inputs[label_text] = amount_field
            lotes_inputs[label_text] = lotes_field

        return inputs

    def create_money_input(self, placeholder=""):
        """Create money input field"""
        field = QLineEdit()
        field.setValidator(QDoubleValidator(0.0, 1e12, 2))
        field.setPlaceholderText(placeholder)
        field.textChanged.connect(self.parent.recalculate_all)
        return field

    def create_lotes_input(self, placeholder="0"):
        """Create lotes (transaction count) input field"""
        field = QLineEdit()
        field.setValidator(QIntValidator(0, 999999))
        field.setPlaceholderText(placeholder)
        field.setMaximumWidth(70)
        field.textChanged.connect(self.parent.recalculate_all)
        return field

    def get_debit_total(self):
        return self.parent.get_total_amount(self.debit_inputs)

    def get_credit_total(self):
        return self.parent.get_total_amount(self.credit_inputs)

    def update_totals(self, beginning, debit_total, credit_total):
        self.total_cash_in = beginning + debit_total
        self.debit_total_display.setText(f"{self.total_cash_in:.2f}")
        self.credit_total_display.setText(f"{credit_total:.2f}")

    @staticmethod
    def _sanitize_column(name: str) -> str:
        """
        Safe SQL column name fallback.
        Replaces every run of non-alphanumeric characters with a single
        underscore, then strips leading/trailing underscores.
        e.g. "Empeno STO. (NEW)" -> "empeno_sto_new"
        """
        col = name.lower()
        col = re.sub(r'[^a-z0-9]+', '_', col)
        col = col.strip('_')
        return col

    def field_name_to_db_column(self, field_name):
        """Convert field label to DB column name via explicit map, then safe fallback."""

        # ── Brand A ───────────────────────────────────────────────────────────
        brand_a_mapping = {
            # Debit
            "Rescate Jewelry":               "rescate_jewelry",
            "Interest":                      "interest",
            "Penalty":                       "penalty",
            "Stamp":                         "stamp",
            "Rescuardo/Affidavit":           "rescuardo_affidavit",
            "HABOL Renew/Tubos":             "habol_renew_tubos",
            "Habol R/T Interest&Stamp":      "habol_rt_interest_stamp",
            "CR STORAGE":                    "cr_storage",
            "CR Storage Int/Penalty":        "cr_storage_int_penalty",
            "Rescate Silver":                "rescate_silver",
            "Silver int.":                   "silver_interest",
            "Res Storage":                   "res_storage",
            "Res. Storage Int./Penalty":     "res_storage_int_penalty",
            "Res. Motor":                    "res_motor",
            "Penalty Motor":                 "penalty_motor",
            "Jew. A.I":                      "jew_ai",
            "S.C":                           "service_charge",
            "O.s.f Sto.":                    "osf_storage",
            "Sto. A.I":                      "storage_ai",
            "Silver A.I":                    "silver_ai",
            "O.s.f Silver":                  "osf_silver",
            "Motor A.I":                     "motor_ai",
            "O.s.f Motor":                   "osf_motor",
            "Miscellaneous Fee":             "miscellaneous_fee",
            "Insurance(20)":                 "insurance_20",
            "Insurance PHILAM(php 30)":      "insurance_philam_30",
            "Insurance PHILAM(php 60)":      "insurance_philam_60",
            "Insurance PHILAM(php 90)":      "insurance_philam_90",
            "Fund Transfer from BRANCH":     "fund_transfer_from_branch",
            "AYANAH + SC":                   "ayanah_sc",
            "Sendah Load + SC":              "sendah_load_sc",
            "Smart Money + SC":              "smart_money_sc",
            "G-Cash In":                     "gcash_in",
            "Gcash Out S.C":                 "gcash_out_sc",
            "Abra S.O + S.C":               "abra_so_sc",
            "BDO S.C":                       "bdo_sc",
            "Palawan Pay Cash Out SC":       "palawan_pay_cash_out_sc",
            "Ria In + S.C":                  "ria_in_sc",
            "Paymaya In":                    "paymaya_in",
            "I2I Remittance In":             "i2i_remittance_in",
            "I2I Bills Payment":             "i2i_bills_payment",
            "I2I Bank Transfer":             "i2i_bank_transfer",
            "I2I Pesonet":                   "i2i_pesonet",
            "I2I Instapay":                  "i2i_instapay",
            "Sendah Bills + SC":             "sendah_bills_sc",
            "Palawan Send Out":              "palawan_send_out",
            "Palawan S.C":                   "palawan_sc",
            "Palawan Suki Card":             "palawan_suki_card",
            "Palawan Pay Cash-In +SC":       "palawan_pay_cash_in_sc",
            "Palawan Load + SC":             "palawan_load_sc",
            "Palawan Pay Bills + SC":        "palawan_pay_bills_sc",
            "Palawan Change Receiver":       "palawan_change_receiver",
            "MC In":                         "mc_in",
            "Handling fee":                  "handling_fee",
            "Other Penalty":                 "other_penalty",
            "Cash Overage":                  "cash_overage",
            # Credit
            "Empeno JEW. (NEW)":             "empeno_jew_new",
            "Empeno JEW (RENEW)":            "empeno_jew_renew",
            "Empeno STO. (NEW)":             "empeno_sto_new",
            "Fund Empeno STO. (RENEW)":      "fund_empeno_sto_renew",
            "Empeno Motor/Car":              "empeno_motor_car",
            "Empeno silver":                 "empeno_silver",
            "G-Cash Out":                    "gcash_out",
            "G-Cash Padala (SENDAH)":        "gcash_padala_sendah",
            "Abra P.o":                      "abra_po",
            "BDO P.o":                       "bdo_po",
            "I2I Remittance Out":            "i2i_remittance_out",
            "Remitly":                       "remitly",
            "Smart Money P.O.":              "smart_money_po",
            "Fund Transfer to HEAD OFFICE":  "fund_transfer_to_head_office",
            "Fund Transfer to BRANCH":       "fund_transfer_to_branch",
            "AYANAH OUT":                    "ayanah_out",
            "Palawan Pay Out":               "palawan_pay_out",
            "Palawan Pay Out (incentives)":  "palawan_pay_out_incentives",
            "Palawan Pay Cash Out":          "palawan_pay_cash_out",
            "MC Out":                        "mc_out",
            "PC-Inc. Emp":                   "pc_inc_emp",
            "PC-Inc. Motor":                 "pc_inc_motor",
            "PC-Inc. Suki Card":             "pc_inc_suki_card",
            "PC-Inc. Insurance":             "pc_inc_insurance",
            "PC-Inc. MC":                    "pc_inc_mc",
            "PC-Salary":                     "pc_salary",
            "PC-Rental":                     "pc_rental",
            "PC-Electric":                   "pc_electric",
            "PC-Water":                      "pc_water",
            "PC-Internet":                   "pc_internet",
            "PC-Lbc/Jrs/Jnt":               "pc_lbc_jrs_jnt",
            "PC-Permits/BIR Payments":       "pc_permits_bir_payments",
            "PC-Supplies/Xerox/Maintenance": "pc_supplies_xerox_maintenance",
            "PC-Transpo":                    "pc_transpo",
            "Transfast":                     "transfast",
            "Paymaya Out":                   "paymaya_out",
            "Ria Out":                       "ria_out",
            "FIXCO":                         "fixco",
            "Moneygram":                     "moneygram",
            "Palawan Cancel":                "palawan_cancel",
            "Palawan Suki Discounts":        "palawan_suki_discounts",
            "Palawan Suki Rebates":          "palawan_suki_rebates",
            "Storage Rebates":               "storage_rebates",
            "Silver Rebates":                "silver_rebates",
            "OTHERS":                        "others",
            "Cash Shortage":                 "cash_shortage",
        }

        # ── Brand B ───────────────────────────────────────────────────────────
        brand_b_mapping = {
            # Debit
            "Rescate Jewelry":               "rescate_jewelry",
            "Interest":                      "interest",
            "Penalty":                       "penalty",
            "Stamp":                         "stamp",
            "Resguardo/Affidavit":           "resguardo_affidavit",
            "HABOL Renew/Tubos":             "habol_renew_tubos",
            "Habol R/T Interest&Stamp":      "habol_rt_interest_stamp",
            "Jew. A.I":                      "jew_ai",
            "S.C":                           "sc",
            "Fund Transfer from BRANCH":     "fund_transfer_from_branch",
            "Sendah Load + SC":              "sendah_load_sc",
            "PPAY CO SC":                    "ppay_co_sc",
            "Palawan Send Out":              "palawan_send_out",
            "Palawan S.C":                   "palawan_sc",
            "Palawan Suki Card":             "palawan_suki_card",
            "Palawan Pay Cash-In + SC":      "palawan_pay_cash_in_sc",
            "Palawan Pay Bills + SC":        "palawan_pay_bills_sc",
            "Palawan Load":                  "palawan_load",
            "Palawan Change Receiver":       "palawan_change_receiver",
            "MC In":                         "mc_in",
            "Handling fee":                  "handling_fee",
            "Other Penalty":                 "other_penalty",
            "Cash Overage":                  "cash_overage",
            # Credit
            "Empeno JEW. (NEW)":             "empeno_jew_new",
            "Empeno JEW (RENEW)":            "empeno_jew_renew",
            "Fund Transfer to HEAD OFFICE":  "fund_transfer_to_head_office",
            "Fund Transfer to BRANCH":       "fund_transfer_to_branch",
            "Palawan Pay Out":               "palawan_pay_out",
            "Palawan Pay Out (incentives)":  "palawan_pay_out_incentives",
            "Palawan Pay Cash Out":          "palawan_pay_cash_out",
            "PC-Inc. Emp":                   "pc_inc_emp",
            "PC-Inc. Suki Card":             "pc_inc_suki_card",
            "PC-Inc. Insurance":             "pc_inc_insurance",
            "PC-Salary":                     "pc_salary",
            "PC-Rental":                     "pc_rental",
            "PC-Electric":                   "pc_electric",
            "PC-Water":                      "pc_water",
            "PC-Internet":                   "pc_internet",
            "PC-Lbc/Jrs/Jnt":               "pc_lbc_jrs_jnt",
            "PC-Permits/BIR Payments":       "pc_permits_bir_payments",
            "PC-Supplies/Xerox/Maintenance": "pc_supplies_xerox_maintenance",
            "PC-Transpo":                    "pc_transpo",
            "Palawan Cancel":                "palawan_cancel",
            "Palawan Suki Discounts":        "palawan_suki_discounts",
            "Palawan Suki Rebates":          "palawan_suki_rebates",
            "OTHERS":                        "others",
            "Cash Shortage":                 "cash_shortage",
        }

        mapping = brand_a_mapping if self.current_brand == "Brand A" else brand_b_mapping

        if field_name in mapping:
            return mapping[field_name]

        # Safe fallback — no dots, parens, or special chars will reach SQL
        col = self._sanitize_column(field_name)
        print(f"[WARN] field_name_to_db_column: '{field_name}' not in mapping, "
              f"using sanitized fallback '{col}'")
        return col

    def get_data(self):
        """Get all data from cash flow tab"""
        debit_values = {}
        for k, v in self.debit_inputs.items():
            value = float(v.text().strip()) if v.text().strip() else 0
            db_column = self.field_name_to_db_column(k)
            debit_values[db_column] = value
            lotes_text = self.debit_lotes_inputs[k].text().strip()
            debit_values[db_column + "_lotes"] = int(lotes_text) if lotes_text else 0

        credit_values = {}
        for k, v in self.credit_inputs.items():
            value = float(v.text().strip()) if v.text().strip() else 0
            db_column = self.field_name_to_db_column(k)
            credit_values[db_column] = value
            lotes_text = self.credit_lotes_inputs[k].text().strip()
            credit_values[db_column + "_lotes"] = int(lotes_text) if lotes_text else 0

        return {'debit': debit_values, 'credit': credit_values}

    def clear_fields(self):
        """Clear all input fields"""
        for field in list(self.debit_inputs.values()) + list(self.debit_lotes_inputs.values()) \
                     + list(self.credit_inputs.values()) + list(self.credit_lotes_inputs.values()):
            field.clear()

    def set_enabled(self, enabled):
        """Enable or disable all inputs"""
        for field in list(self.debit_inputs.values()) + list(self.debit_lotes_inputs.values()) \
                     + list(self.credit_inputs.values()) + list(self.credit_lotes_inputs.values()):
            field.setEnabled(enabled)