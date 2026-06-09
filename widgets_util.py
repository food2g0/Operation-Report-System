"""
Reusable widget components for the admin dashboard.
Extracted to promote code reuse and maintainability.
"""

from PyQt5.QtWidgets import (
    QWidget, QHBoxLayout, QLineEdit, QDoubleSpinBox, QSpinBox, QLabel
)
from PyQt5.QtGui import QDoubleValidator, QIntValidator, QFont
from PyQt5.QtCore import Qt, pyqtSignal


class MoneyInput(QWidget):
    """Currency input with comma separators and validation."""

    valueChanged = pyqtSignal(float)

    def __init__(self, placeholder="0.00", parent=None):
        super().__init__(parent)
        self.input = QLineEdit()
        self.input.setPlaceholderText(placeholder)
        self.input.setValidator(QDoubleValidator(0.0, 999999999.99, 2))
        self.input.setStyleSheet("""
            QLineEdit {
                padding: 6px;
                border: 1px solid #bdc3c7;
                border-radius: 3px;
                font-size: 11px;
            }
            QLineEdit:focus {
                border: 2px solid #3498db;
                outline: none;
            }
        """)
        self.input.textChanged.connect(self._on_text_changed)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.input)
        self.setLayout(layout)

    @property
    def textChanged(self):
        """Expose the underlying QLineEdit's textChanged signal."""
        return self.input.textChanged

    def _on_text_changed(self):
        try:
            value = float(self.input.text() or 0)
            self.valueChanged.emit(value)
        except ValueError:
            pass

    def value(self):
        try:
            return float(self.input.text() or 0)
        except ValueError:
            return 0.0

    def setValue(self, val):
        self.input.setText(f"{val:.2f}" if val else "0.00")

    def setText(self, text):
        self.input.setText(text)

    def text(self):
        return self.input.text()

    def setReadOnly(self, readonly):
        self.input.setReadOnly(readonly)

    def isReadOnly(self):
        return self.input.isReadOnly()

    def setPlaceholderText(self, text):
        self.input.setPlaceholderText(text)

    def clear(self):
        self.input.clear()

    def setValidator(self, validator):
        self.input.setValidator(validator)

    def validator(self):
        return self.input.validator()

    def setStyleSheet(self, stylesheet):
        self.input.setStyleSheet(stylesheet)

    def setProperty(self, name, value):
        self.input.setProperty(name, value)

    def property(self, name):
        return self.input.property(name)

    def setFocus(self):
        self.input.setFocus()

    def hasFocus(self):
        return self.input.hasFocus()

    def selectAll(self):
        self.input.selectAll()

    def hasAcceptableInput(self):
        return self.input.hasAcceptableInput()

    def font(self):
        return self.input.font()

    def setFont(self, font):
        self.input.setFont(font)


class LotesInput(QSpinBox):
    """Integer input for lote counts with styling."""

    def __init__(self, read_only=False, parent=None):
        super().__init__(parent)
        self.setRange(0, 999999)
        self.setReadOnly(read_only)
        self.setStyleSheet("""
            QSpinBox {
                padding: 6px;
                border: 1px solid #bdc3c7;
                border-radius: 3px;
                font-size: 11px;
            }
            QSpinBox:focus {
                border: 2px solid #3498db;
                outline: none;
            }
        """)

    def setText(self, text):
        """Set value from text (for QLineEdit compatibility)."""
        try:
            val = int(text or 0)
            self.setValue(val)
        except (ValueError, TypeError):
            self.setValue(0)

    def text(self):
        """Get text representation of value (for QLineEdit compatibility)."""
        return str(self.value())

    def setMaximumWidth(self, width):
        """Set maximum width (for consistent API)."""
        super().setMaximumWidth(width)


class DisplayField(QLineEdit):
    """Read-only display field with styling."""

    def __init__(self, text="", parent=None):
        super().__init__(text, parent)
        self.setReadOnly(True)
        self.setStyleSheet("""
            QLineEdit {
                background-color: #f8f9fa;
                padding: 6px;
                border: 1px solid #e0e0e0;
                border-radius: 3px;
                color: #333;
                font-size: 11px;
            }
        """)


class CurrencySpinBox(QDoubleSpinBox):
    """Double spin box with currency formatting."""

    def __init__(self, min_val=0, max_val=999999.99, parent=None):
        super().__init__(parent)
        self.setRange(min_val, max_val)
        self.setDecimals(2)
        self.setPrefix("₱ ")
        self.setStyleSheet("""
            QDoubleSpinBox {
                padding: 6px;
                border: 1px solid #bdc3c7;
                border-radius: 3px;
                font-size: 11px;
            }
            QDoubleSpinBox:focus {
                border: 2px solid #3498db;
                outline: none;
            }
        """)


class IntegerSpinBox(QSpinBox):
    """Integer spin box with styling."""

    def __init__(self, min_val=0, max_val=999999, parent=None):
        super().__init__(parent)
        self.setRange(min_val, max_val)
        self.setStyleSheet("""
            QSpinBox {
                padding: 6px;
                border: 1px solid #bdc3c7;
                border-radius: 3px;
                font-size: 11px;
            }
            QSpinBox:focus {
                border: 2px solid #3498db;
                outline: none;
            }
        """)
