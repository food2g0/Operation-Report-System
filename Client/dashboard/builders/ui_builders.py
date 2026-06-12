"""UI builders - reusable components for constructing dashboard UI."""

from PyQt5.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QFrame,
    QPushButton
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QDoubleValidator


class BalanceColumnBuilder:
    """Builds balance display columns with input fields."""

    @staticmethod
    def build(brand, bb_input, cc_input, cr_label, vs_label, eb_label, zoom_level=100):
        """Build a balance column layout.

        Args:
            brand: Brand name (A or B)
            bb_input: Beginning balance input widget
            cc_input: Cash count input widget
            cr_label: Cash result label widget
            vs_label: Variance status label widget
            eb_label: Ending balance label widget
            zoom_level: UI zoom level percentage

        Returns:
            QVBoxLayout: Configured layout
        """
        col = QVBoxLayout()
        col.setSpacing(8)
        # Placeholder: actual layout building logic
        return col


class BrandSummaryBuilder:
    """Builds brand summary card layouts."""

    @staticmethod
    def build(brand, debit_label, credit_label, ending_label, variance_label, zoom_level=100):
        """Build a brand summary card.

        Args:
            brand: Brand name
            debit_label: Debit display label
            credit_label: Credit display label
            ending_label: Ending balance label
            variance_label: Variance display label
            zoom_level: UI zoom level percentage

        Returns:
            QFrame: Configured frame
        """
        frame = QFrame()
        # Placeholder: actual frame building logic
        return frame


class StatusBoxBuilder:
    """Builds status display boxes."""

    @staticmethod
    def create_status_box(status_text, status_type="info"):
        """Create a status display box.

        Args:
            status_text: Text to display
            status_type: Type of status (info, success, warning, error)

        Returns:
            QFrame: Status box frame
        """
        box = QFrame()
        # Placeholder
        return box


class InputFieldBuilder:
    """Builds input field widgets with validation."""

    @staticmethod
    def create_money_input(placeholder="0.00", zoom_level=100):
        """Create a money input field.

        Args:
            placeholder: Placeholder text
            zoom_level: UI zoom level percentage

        Returns:
            QLineEdit: Configured input field
        """
        field = QLineEdit()
        field.setPlaceholderText(placeholder)
        field.setValidator(QDoubleValidator(0.0, 1e12, 2))
        # Placeholder: actual styling logic
        return field

    @staticmethod
    def create_display_field(initial_text="0.00"):
        """Create a read-only display field.

        Args:
            initial_text: Initial display text

        Returns:
            QLineEdit: Read-only display field
        """
        field = QLineEdit()
        field.setText(initial_text)
        field.setReadOnly(True)
        # Placeholder: actual styling logic
        return field


class FrameBuilder:
    """Builds frame and separator components."""

    @staticmethod
    def create_separator(orientation="horizontal"):
        """Create a separator line.

        Args:
            orientation: "horizontal" or "vertical"

        Returns:
            QFrame: Separator frame
        """
        frame = QFrame()
        # Placeholder: actual separator logic
        return frame

    @staticmethod
    def create_titled_frame(title, content_layout):
        """Create a titled frame with content.

        Args:
            title: Frame title text
            content_layout: Layout to add inside frame

        Returns:
            QFrame: Configured titled frame
        """
        frame = QFrame()
        # Placeholder
        return frame
