"""UI builders - reusable components for constructing dashboard UI."""

from PyQt5.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QFrame,
    QPushButton
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QDoubleValidator, QFont


# ── Color Constants ──────────────────────────────────────────────────────────
_PRIMARY = "#3B82F6"        # Blue
_PRIMARY_DARK = "#2563EB"   # Dark Blue
_PURPLE = "#8B5CF6"         # Purple
_PURPLE_DARK = "#7C3AED"    # Dark Purple
_RED = "#EF4444"            # Red
_RED_DARK = "#DC2626"       # Dark Red
_RED_LIGHT = "#FEE2E2"      # Light Red
_WHITE = "#FFFFFF"
_TEXT_MUTED = "#6B7280"


class ButtonBuilder:
   

    @staticmethod
    def create_primary_button(text, callback=None):

        btn = QPushButton(text)
        btn.setStyleSheet(f"""
            QPushButton {{ background: {_PRIMARY}; color: {_WHITE}; border: none;
                          border-radius: 6px; padding: 7px 18px;
                          font-weight: 700; font-size: 12px; }}
            QPushButton:hover {{ background: {_PRIMARY_DARK}; }}
        """)
        if callback:
            btn.clicked.connect(callback)
        return btn

    @staticmethod
    def create_purple_button(text, callback=None):

        btn = QPushButton(text)
        btn.setStyleSheet(f"""
            QPushButton {{ background: {_PURPLE}; color: {_WHITE}; border: none;
                          border-radius: 6px; padding: 7px 18px;
                          font-weight: 700; font-size: 12px; }}
            QPushButton:hover {{ background: {_PURPLE_DARK}; }}
        """)
        if callback:
            btn.clicked.connect(callback)
        return btn

    @staticmethod
    def create_danger_button(text, callback=None):
        """Create red danger button for delete/remove.

        Args:
            text: Button text
            callback: Optional click callback

        Returns:
            QPushButton: Styled button
        """
        btn = QPushButton(text)
        btn.setStyleSheet(f"""
            QPushButton {{ color: {_RED}; font-weight: 900; border: none;
                          font-size: 13px; }}
            QPushButton:hover {{ color: {_RED_DARK}; }}
        """)
        if callback:
            btn.clicked.connect(callback)
        return btn

    @staticmethod
    def create_danger_button_filled(text, callback=None):

        btn = QPushButton(text)
        btn.setStyleSheet(f"""
            QPushButton {{ background: {_RED_LIGHT}; color: {_RED_DARK};
                          border: none; border-radius: 6px; padding: 6px 12px;
                          font-weight: 600; }}
            QPushButton:hover {{ background: #FECACA; }}
        """)
        if callback:
            btn.clicked.connect(callback)
        return btn


class InputFieldBuilder:
    """Builds input field widgets with validation."""

    @staticmethod
    def create_money_input(placeholder="0.00"):
        """Create money input field with decimal validation.

        Args:
            placeholder: Placeholder text

        Returns:
            QLineEdit: Configured money input field
        """
        field = QLineEdit()
        field.setPlaceholderText(placeholder)
        field.setValidator(QDoubleValidator(0.0, 1e12, 2))
        field.setStyleSheet("""
            QLineEdit {
                background: white;
                border: 1px solid #E5E7EB;
                border-radius: 6px;
                padding: 8px 12px;
                font-size: 13px;
            }
            QLineEdit:focus {
                border: 1px solid #3B82F6;
            }
        """)
        return field

    @staticmethod
    def create_display_field(initial_text="0.00", read_only=True):
        """Create read-only display field for amounts.

        Args:
            initial_text: Initial display text
            read_only: Whether field is read-only

        Returns:
            QLineEdit: Display field
        """
        field = QLineEdit()
        field.setText(initial_text)
        if read_only:
            field.setReadOnly(True)
        field.setStyleSheet("""
            QLineEdit {
                background: #F3F4F6;
                border: 1px solid #E5E7EB;
                border-radius: 6px;
                padding: 8px 12px;
                font-size: 13px;
                color: #374151;
            }
        """)
        return field

    @staticmethod
    def create_text_input(placeholder="", max_length=None):
        """Create generic text input field.

        Args:
            placeholder: Placeholder text
            max_length: Optional max character length

        Returns:
            QLineEdit: Text input field
        """
        field = QLineEdit()
        field.setPlaceholderText(placeholder)
        if max_length:
            field.setMaxLength(max_length)
        field.setStyleSheet("""
            QLineEdit {
                background: white;
                border: 1px solid #E5E7EB;
                border-radius: 6px;
                padding: 8px 12px;
                font-size: 13px;
            }
            QLineEdit:focus {
                border: 1px solid #3B82F6;
            }
        """)
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
        if orientation == "horizontal":
            frame.setFrameShape(QFrame.HLine)
            frame.setFrameShadow(QFrame.Sunken)
            frame.setStyleSheet("border: none; background: #E5E7EB;")
            frame.setFixedHeight(1)
        else:
            frame.setFrameShape(QFrame.VLine)
            frame.setFrameShadow(QFrame.Sunken)
            frame.setStyleSheet("border: none; background: #E5E7EB;")
            frame.setFixedWidth(1)
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
        main_layout = QVBoxLayout()

        # Create title label
        title_label = QLabel(title)
        title_font = QFont()
        title_font.setBold(True)
        title_font.setPointSize(11)
        title_label.setFont(title_font)

        main_layout.addWidget(title_label)
        main_layout.addLayout(content_layout)

        frame = QFrame()
        frame.setStyleSheet("""
            background: #FFFFFF;
            border: 1px solid #E5E7EB;
            border-radius: 8px;
            padding: 12px;
        """)
        frame.setLayout(main_layout)
        return frame

    @staticmethod
    def create_card_frame(content_layout, background="#F9FAFB"):
        """Create a card-style frame.

        Args:
            content_layout: Layout to add inside frame
            background: Background color

        Returns:
            QFrame: Card frame
        """
        frame = QFrame()
        frame.setStyleSheet(f"""
            background: {background};
            border: 1px solid #E5E7EB;
            border-radius: 8px;
            padding: 12px;
        """)
        frame.setLayout(content_layout)
        return frame


class LabelBuilder:
    """Builds label widgets."""

    @staticmethod
    def create_label(text, bold=False, color="#000000", size=11):
        """Create a styled label.

        Args:
            text: Label text
            bold: Whether text is bold
            color: Text color
            size: Font size in points

        Returns:
            QLabel: Styled label
        """
        label = QLabel(text)
        font = QFont()
        font.setBold(bold)
        font.setPointSize(size)
        label.setFont(font)
        label.setStyleSheet(f"color: {color};")
        return label

    @staticmethod
    def create_title_label(text):
        """Create a title-style label.

        Args:
            text: Title text

        Returns:
            QLabel: Title label
        """
        return LabelBuilder.create_label(text, bold=True, size=13)

    @staticmethod
    def create_muted_label(text, size=10):
        """Create a muted/secondary label.

        Args:
            text: Label text
            size: Font size in points

        Returns:
            QLabel: Muted label
        """
        return LabelBuilder.create_label(text, color=_TEXT_MUTED, size=size)


class LayoutBuilder:
    """Builds common layout patterns."""

    @staticmethod
    def create_row_layout(*widgets):
        """Create a horizontal row with widgets.

        Args:
            *widgets: Widgets to add to row

        Returns:
            QHBoxLayout: Configured row layout
        """
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)
        for widget in widgets:
            layout.addWidget(widget)
        return layout

    @staticmethod
    def create_column_layout(*widgets):
        """Create a vertical column with widgets.

        Args:
            *widgets: Widgets to add to column

        Returns:
            QVBoxLayout: Configured column layout
        """
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)
        for widget in widgets:
            layout.addWidget(widget)
        return layout

    @staticmethod
    def create_form_row(label_text, widget):
        """Create a form row with label and widget.

        Args:
            label_text: Label text
            widget: Widget for input

        Returns:
            QHBoxLayout: Form row layout
        """
        layout = QHBoxLayout()
        label = LabelBuilder.create_label(label_text)
        label.setFixedWidth(150)
        layout.addWidget(label)
        layout.addWidget(widget)
        return layout
