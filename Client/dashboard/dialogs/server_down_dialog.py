"""Server down error dialog with offline mode support."""

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QMessageBox
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont, QPixmap
from PyQt5.QtSvg import QSvgWidget
import os


class ServerDownDialog(QDialog):
    """Dialog shown when server is down/unreachable.

    Offers user options to:
    - Retry (reconnect to server)
    - Proceed Offline (use offline mode)
    - Exit (close application)
    """

    retry_clicked = pyqtSignal()
    offline_clicked = pyqtSignal()
    exit_clicked = pyqtSignal()

    def __init__(self, parent=None, show_offline_option=True):
        """Initialize server down dialog.

        Args:
            parent: Parent widget
            show_offline_option: Whether to show "Proceed Offline" button
        """
        super().__init__(parent)
        self.setWindowTitle("Server Connection Error")
        self.setModal(True)
        self.setStyleSheet("""
            QDialog {
                background-color: #FFFFFF;
                border-radius: 12px;
            }
            QLabel {
                color: #1F2937;
            }
            QPushButton {
                border-radius: 6px;
                padding: 8px 16px;
                font-weight: 600;
                border: none;
            }
            QPushButton#retryBtn {
                background-color: #3B82F6;
                color: white;
            }
            QPushButton#retryBtn:hover {
                background-color: #2563EB;
            }
            QPushButton#offlineBtn {
                background-color: #10B981;
                color: white;
            }
            QPushButton#offlineBtn:hover {
                background-color: #059669;
            }
            QPushButton#exitBtn {
                background-color: #EF4444;
                color: white;
            }
            QPushButton#exitBtn:hover {
                background-color: #DC2626;
            }
        """)
        self.show_offline = show_offline_option
        self._init_ui()

    def _init_ui(self):
        """Initialize UI components."""
        layout = QVBoxLayout()
        layout.setSpacing(20)
        layout.setContentsMargins(40, 40, 40, 40)

        # Icon/Image
        icon_label = QLabel()
        icon_label.setText("🔌")
        icon_label.setFont(QFont("Arial", 64))
        icon_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(icon_label)

        # Title
        title = QLabel("Something went wrong.")
        title_font = QFont()
        title_font.setPointSize(20)
        title_font.setBold(True)
        title.setFont(title_font)
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        # Message
        message = QLabel(
            "It's not you, it's us.\n\n"
            "The server is currently down, but we'll have things\n"
            "back to normal soon."
        )
        message_font = QFont()
        message_font.setPointSize(12)
        message.setFont(message_font)
        message.setAlignment(Qt.AlignCenter)
        message.setStyleSheet("color: #6B7280; line-height: 1.6;")
        layout.addWidget(message)

        layout.addSpacing(20)

        # Buttons
        button_layout = QHBoxLayout()
        button_layout.setSpacing(12)
        button_layout.setContentsMargins(0, 0, 0, 0)

        # Retry button
        retry_btn = QPushButton("Retry Connection")
        retry_btn.setObjectName("retryBtn")
        retry_btn.setMinimumWidth(120)
        retry_btn.clicked.connect(self._on_retry)
        button_layout.addWidget(retry_btn)

        # Proceed Offline button (if offline mode available)
        if self.show_offline:
            offline_btn = QPushButton("Proceed Offline")
            offline_btn.setObjectName("offlineBtn")
            offline_btn.setMinimumWidth(120)
            offline_btn.clicked.connect(self._on_offline)
            button_layout.addWidget(offline_btn)

        # Exit button
        exit_btn = QPushButton("Exit Application")
        exit_btn.setObjectName("exitBtn")
        exit_btn.setMinimumWidth(120)
        exit_btn.clicked.connect(self._on_exit)
        button_layout.addWidget(exit_btn)

        layout.addLayout(button_layout)

        self.setLayout(layout)
        self.setMinimumWidth(500)
        self.setMinimumHeight(400)

    def _on_retry(self):
        """Handle retry button click."""
        self.retry_clicked.emit()
        self.accept()

    def _on_offline(self):
        """Handle proceed offline button click."""
        self.offline_clicked.emit()
        self.accept()

    def _on_exit(self):
        """Handle exit button click."""
        self.exit_clicked.emit()
        self.reject()

    @staticmethod
    def show_and_get_action(parent=None, show_offline=True):
        """Show dialog and return user's choice.

        Args:
            parent: Parent widget
            show_offline: Whether to show offline option

        Returns:
            str: "retry", "offline", or "exit"
        """
        dialog = ServerDownDialog(parent, show_offline)

        choice = {"result": "exit"}

        def on_retry():
            choice["result"] = "retry"

        def on_offline():
            choice["result"] = "offline"

        dialog.retry_clicked.connect(on_retry)
        dialog.offline_clicked.connect(on_offline)

        dialog.exec_()
        return choice["result"]
