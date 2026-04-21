from PyQt5.QtWidgets import (
    QWidget, QLabel, QLineEdit, QVBoxLayout, QHBoxLayout,
    QGroupBox, QFormLayout, QScrollArea, QFrame, QGridLayout
)
from PyQt5.QtGui import QDoubleValidator
from PyQt5.QtCore import Qt

from Client.ui_scaling import _sz


class PalawanDetailsTab(QWidget):
    def set_enabled(self, enabled):
        """Enable or disable all Palawan input fields for editability control."""
        for group in [getattr(self, 'sendout_inputs', {}), getattr(self, 'payout_inputs', {}), getattr(self, 'international_inputs', {}), getattr(self, 'lotes_inputs', {}), getattr(self, 'adjustments_inputs', {})]:
            for field in group.values():
                field.setReadOnly(not enabled)
                field.setEnabled(enabled)
    
    def __init__(self, parent):
        super().__init__()
        self.parent = parent
        self.setup_ui()

    def setup_ui(self):

        palawan_scroll = QScrollArea()
        palawan_scroll.setWidgetResizable(True)

        palawan_widget = QWidget()
        palawan_scroll.setWidget(palawan_widget)

        palawan_layout = QVBoxLayout(palawan_widget)

    

        # Create main sections
        main_sections_frame = QFrame()
        main_sections_layout = QGridLayout(main_sections_frame)
        main_sections_layout.setSpacing(_sz(15))

        sendout_group = self.create_palawan_section_group(
            "PALAWAN SEND-OUT",
            "sendout",
            "#1b75bc"
        )


        payout_group = self.create_palawan_section_group(
            "PALAWAN PAY-OUT",
            "payout",
            "#1b75bc"
        )

        international_group = self.create_palawan_section_group(
            "PALAWAN INTERNATIONAL",
            "international",
            "#1b75bc"
        )

        main_sections_layout.addWidget(sendout_group, 0, 0)
        main_sections_layout.addWidget(payout_group, 0, 1)
        main_sections_layout.addWidget(international_group, 1, 0, 1, 2)

        palawan_layout.addWidget(main_sections_frame)

        adjustments_section = self.create_adjustments_section()
        palawan_layout.addWidget(adjustments_section)

        lotes_section = self.create_lotes_section()
        palawan_layout.addWidget(lotes_section)

        palawan_layout.addStretch()

        container_layout = QVBoxLayout(self)
        container_layout.addWidget(palawan_scroll)

    def create_palawan_section_group(self, title, section_type, color):
        """Create a Palawan section group with improved styling"""
        group = QGroupBox(title)
        group.setStyleSheet(f"""
            QGroupBox {{
                border: 1px solid #E2E8F0;
                border-radius: {_sz(6)}px;
                margin-top: {_sz(22)}px;
                padding: {_sz(18)}px {_sz(16)}px {_sz(16)}px {_sz(16)}px;
                background-color: #FFFFFF;
            }}
            QGroupBox::title {{
                color: {color};
                font-weight: 800;
                font-size: {_sz(13)}px;
                letter-spacing: 1.2px;
                padding: 1px {_sz(8)}px;
                background-color: #FFFFFF;
                border-radius: {_sz(4)}px;
            }}
        """)

        form = QFormLayout()
        form.setSpacing(_sz(10))
        form.setContentsMargins(_sz(16), _sz(24), _sz(16), _sz(16))

        inputs = {}

        fields = [("Principal", "Enter Principal"), ("SC", "Enter SC"), ("Commission", "Enter Commission")]

        for label_text, placeholder in fields:
            field = self.create_money_input(placeholder)
            field.textChanged.connect(self.calculate_palawan_totals)
            label = QLabel(label_text + ":")
            label.setStyleSheet(f"font-size: {_sz(14)}px; font-weight: 600; color: #334155;")
            form.addRow(label, field)
            inputs[label_text] = field

        total_display = self.parent.create_display_field("0.00")
        total_display.setStyleSheet(
            f"font-weight: 800; font-size: {_sz(14)}px; color: {color}; "
            f"background-color: #F0F9FF; border: 1px solid #BAE6FD; "
            f"border-radius: {_sz(6)}px; padding: {_sz(7)}px {_sz(14)}px;"
        )
        total_lbl = QLabel("TOTAL:")
        total_lbl.setStyleSheet(f"font-weight: 700; color: {color}; font-size: {_sz(14)}px;")
        form.addRow(total_lbl, total_display)

        group.setLayout(form)

        setattr(self, f"{section_type}_inputs", inputs)
        setattr(self, f"{section_type}_total_display", total_display)

        return group

    def create_adjustments_section(self):
   
        group = QGroupBox("PALAWAN ADJUSTMENTS (Auto-carries to Brand B Cash Flow)")
        group.setStyleSheet(f"""
            QGroupBox {{
                border: 2px solid #F59E0B;
                border-radius: {_sz(6)}px;
                margin-top: {_sz(22)}px;
                padding: {_sz(18)}px {_sz(16)}px {_sz(16)}px {_sz(16)}px;
                background-color: #FFFBEB;
            }}
            QGroupBox::title {{
                color: #D97706;
                font-weight: 800;
                font-size: {_sz(13)}px;
                letter-spacing: 1.2px;
                padding: 1px {_sz(8)}px;
                background-color: #FFFBEB;
                border-radius: {_sz(4)}px;
            }}
        """)

        form = QFormLayout()
        form.setSpacing(_sz(10))
        form.setContentsMargins(_sz(16), _sz(24), _sz(16), _sz(16))

        self.adjustments_inputs = {}

        adjustment_fields = [
            ("Palawan Pay Out Incentives", "Enter Incentives Amount", "palawan_pay_out_incentives"),
            ("Palawan Suki Discounts", "Enter Suki Discounts", "palawan_suki_discounts"),
            ("Palawan Suki Rebates", "Enter Suki Rebates", "palawan_suki_rebates"),
            ("Palawan Cancel", "Enter Cancellation Amount", "palawan_cancel"),
        ]

        for label_text, placeholder, db_column in adjustment_fields:
            field = self.create_money_input(placeholder)
            field.textChanged.connect(self.calculate_adjustments_total)
            # Store db_column as property for easy mapping
            field.setProperty("db_column", db_column)
            label = QLabel(label_text + ":")
            label.setStyleSheet(f"font-size: {_sz(14)}px; font-weight: 600; color: #92400E;")
            form.addRow(label, field)
            self.adjustments_inputs[label_text] = field

        # Adjustments total
        self.adjustments_total_display = self.parent.create_display_field("0.00")
        self.adjustments_total_display.setStyleSheet(
            f"font-weight: 800; font-size: {_sz(14)}px; color: #D97706; "
            f"background-color: #FEF3C7; border: 1px solid #FCD34D; "
            f"border-radius: {_sz(6)}px; padding: {_sz(7)}px {_sz(14)}px;"
        )
        total_lbl = QLabel("ADJUSTMENTS TOTAL:")
        total_lbl.setStyleSheet(f"font-weight: 700; color: #D97706; font-size: {_sz(14)}px;")
        form.addRow(total_lbl, self.adjustments_total_display)

        # Info label
        info_label = QLabel("Values entered here automatically populate Brand B Cash Flow fields")
        info_label.setStyleSheet(f"font-size: {_sz(12)}px; color: #92400E; font-style: italic;")
        form.addRow(info_label)

        group.setLayout(form)
        return group

    def calculate_adjustments_total(self):
        adjustments_total = self.parent.get_total_amount(self.adjustments_inputs)
        self.adjustments_total_display.setText(f"{adjustments_total:.2f}")

    def create_lotes_section(self):
        lotes_group = QGroupBox("LOTES TRANSACTIONS")
        lotes_group.setStyleSheet(f"""
            QGroupBox {{
                border: 1px solid #E2E8F0;
                border-radius: {_sz(6)}px;
                margin-top: {_sz(22)}px;
                padding: {_sz(18)}px {_sz(16)}px {_sz(16)}px {_sz(16)}px;
                background-color: #FFFFFF;
            }}
            QGroupBox::title {{
                color: #8B5CF6;
                font-weight: 800;
                font-size: {_sz(13)}px;
                letter-spacing: 1.2px;
                padding: 1px {_sz(8)}px;
                background-color: #FFFFFF;
                border-radius: {_sz(4)}px;
            }}
        """)

        form = QFormLayout()
        form.setSpacing(_sz(10))
        form.setContentsMargins(_sz(16), _sz(24), _sz(16), _sz(16))

        self.lotes_inputs = {}

        lotes_fields = [
            ("Lotes Send-Out", "Enter Lotes Send-Out Amount"),
            ("Lotes Pay-Out", "Enter Lotes Pay-Out Amount"),
            ("Lotes International", "Enter Lotes International Amount")
        ]

        for label_text, placeholder in lotes_fields:
            field = self.create_money_input(placeholder)
            field.textChanged.connect(self.calculate_lotes_total)
            label = QLabel(label_text + ":")
            label.setStyleSheet(f"font-size: {_sz(14)}px; font-weight: 600; color: #334155;")
            form.addRow(label, field)
            self.lotes_inputs[label_text] = field

        self.lotes_total_display = self.parent.create_display_field("0.00")
        self.lotes_total_display.setStyleSheet(
            f"font-weight: 800; font-size: {_sz(14)}px; color: #8B5CF6; "
            f"background-color: #F5F3FF; border: 1px solid #DDD6FE; "
            f"border-radius: {_sz(6)}px; padding: {_sz(7)}px {_sz(14)}px;"
        )
        total_lbl = QLabel("LOTES TOTAL:")
        total_lbl.setStyleSheet(f"font-weight: 700; color: #8B5CF6; font-size: {_sz(14)}px;")
        form.addRow(total_lbl, self.lotes_total_display)

        lotes_group.setLayout(form)
        return lotes_group

    def create_money_input(self, placeholder=""):
        field = QLineEdit()
        field.setValidator(QDoubleValidator(0.0, 1e12, 2))
        field.setPlaceholderText(placeholder)
        field.textChanged.connect(self.parent.recalculate_all)
        return field

    def calculate_palawan_totals(self):
        sections = ['sendout', 'payout', 'international']

        for section in sections:
            inputs = getattr(self, f"{section}_inputs", {})
            total = self.parent.get_total_amount(inputs)
            display = getattr(self, f"{section}_total_display", None)
            if display:
                display.setText(f"{total:.2f}")

    def calculate_lotes_total(self):

        lotes_total = self.parent.get_total_amount(self.lotes_inputs)
        self.lotes_total_display.setText(f"{lotes_total:.2f}")

    def get_data(self):
     
        palawan_values = {}


        for k, v in self.sendout_inputs.items():
            value = float(v.text().strip()) if v.text().strip() else 0
            palawan_values[f"palawan_sendout_{k.lower()}"] = value
        palawan_values["palawan_sendout_regular_total"] = float(
            self.sendout_total_display.text().strip()) if self.sendout_total_display.text().strip() else 0

        for k, v in self.payout_inputs.items():
            value = float(v.text().strip()) if v.text().strip() else 0
            palawan_values[f"palawan_payout_{k.lower()}"] = value
        palawan_values["palawan_payout_regular_total"] = float(
            self.payout_total_display.text().strip()) if self.payout_total_display.text().strip() else 0

        for k, v in self.international_inputs.items():
            value = float(v.text().strip()) if v.text().strip() else 0
            palawan_values[f"palawan_international_{k.lower()}"] = value
        palawan_values["palawan_international_regular_total"] = float(
            self.international_total_display.text().strip()) if self.international_total_display.text().strip() else 0


        lotes_mapping = {
            "Lotes Send-Out": "palawan_sendout_lotes_total",
            "Lotes Pay-Out": "palawan_payout_lotes_total",
            "Lotes International": "palawan_international_lotes_total"
        }

        for k, v in self.lotes_inputs.items():
            value = float(v.text().strip()) if v.text().strip() else 0
            if k in lotes_mapping:
                palawan_values[lotes_mapping[k]] = value

        for label, field in getattr(self, 'adjustments_inputs', {}).items():
            db_column = field.property("db_column")
            if db_column:
                value = float(field.text().strip()) if field.text().strip() else 0
                palawan_values[db_column] = value

        return palawan_values

    def clear_fields(self):

        for field in getattr(self, 'sendout_inputs', {}).values():
            field.clear()

        for field in getattr(self, 'payout_inputs', {}).values():
            field.clear()

        for field in getattr(self, 'international_inputs', {}).values():
            field.clear()

        for field in getattr(self, 'lotes_inputs', {}).values():
            field.clear()

        for field in getattr(self, 'adjustments_inputs', {}).values():
            field.clear()