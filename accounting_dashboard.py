"""
Accounting Dashboard — restricted to BIR book access only.

This role is assigned to accounting staff who need read access to BIR reports
but should not see operational data (daily reports, cash flow, etc.).
"""
import logging
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QLabel, QPushButton, QHBoxLayout
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont

logger = logging.getLogger(__name__)


class AccountingDashboard(QMainWindow):

    logout_requested = pyqtSignal()

    def __init__(self, branch: str = "", corporation: str = "", parent=None):
        super().__init__(parent)
        self.branch      = branch
        self.corporation = corporation
        self.setWindowTitle("Operation Report System — Accounting")
        self._build_ui()

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(40, 40, 40, 40)
        root.setSpacing(20)

        title = QLabel("BIR Book")
        title.setFont(QFont("Segoe UI", 22, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        root.addWidget(title)

        info = QLabel(f"Branch: {self.branch}   |   Corporation: {self.corporation}")
        info.setAlignment(Qt.AlignCenter)
        info.setStyleSheet("color: #64748B; font-size: 13px;")
        root.addWidget(info)

        placeholder = QLabel("BIR Book content will appear here.")
        placeholder.setAlignment(Qt.AlignCenter)
        placeholder.setStyleSheet(
            "color: #94A3B8; font-size: 14px; border: 2px dashed #CBD5E1;"
            "border-radius: 12px; padding: 60px 40px;"
        )
        root.addWidget(placeholder, 1)

        btn_row = QHBoxLayout()
        btn_row.addStretch()
        logout_btn = QPushButton("Logout")
        logout_btn.setStyleSheet(
            "QPushButton{background:#EF4444;color:white;border:none;border-radius:6px;"
            "padding:8px 24px;font-weight:700;font-size:13px;}"
            "QPushButton:hover{background:#DC2626;}"
        )
        logout_btn.clicked.connect(self._on_logout)
        btn_row.addWidget(logout_btn)
        root.addLayout(btn_row)

    def _on_logout(self):
        self.logout_requested.emit()
        self.close()

    def closeEvent(self, event):
        event.accept()
