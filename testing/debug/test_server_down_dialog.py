"""Test script to demonstrate ServerDownDialog.

Run this to see the dialog in action:
    python test_server_down_dialog.py
"""

import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QPushButton, QVBoxLayout, QWidget, QLabel
from PyQt5.QtCore import Qt

# Add project to path
sys.path.insert(0, '/c/Users/Admin/Operation-Report-System')

from Client.dashboard.dialogs import ServerDownDialog
from Client.dashboard.handlers import ServerErrorHandler


class TestWindow(QMainWindow):
    """Test window for ServerDownDialog."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Server Down Dialog Test")
        self.setGeometry(100, 100, 500, 300)

        # Create central widget
        central = QWidget()
        self.setCentralWidget(central)

        layout = QVBoxLayout(central)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)

        # Title
        title = QLabel("ServerDownDialog Test Suite")
        title.setStyleSheet("font-size: 16px; font-weight: bold; margin-bottom: 10px;")
        layout.addWidget(title)

        # Test buttons
        btn1 = QPushButton("Test 1: Show Dialog (with offline option)")
        btn1.clicked.connect(self._test_dialog_with_offline)
        layout.addWidget(btn1)

        btn2 = QPushButton("Test 2: Show Dialog (without offline option)")
        btn2.clicked.connect(self._test_dialog_without_offline)
        layout.addWidget(btn2)

        btn3 = QPushButton("Test 3: Test Error Handler")
        btn3.clicked.connect(self._test_error_handler)
        layout.addWidget(btn3)

        btn4 = QPushButton("Test 4: Test Error Detection")
        btn4.clicked.connect(self._test_error_detection)
        layout.addWidget(btn4)

        # Result label
        self.result_label = QLabel("Click a button to test")
        self.result_label.setStyleSheet(
            "background-color: #F3F4F6; padding: 10px; border-radius: 4px; "
            "color: #1F2937; margin-top: 20px;"
        )
        self.result_label.setWordWrap(True)
        layout.addWidget(self.result_label)

        layout.addStretch()

    def _test_dialog_with_offline(self):
        """Test dialog with offline option."""
        dialog = ServerDownDialog(self, show_offline_option=True)

        # Connect signals
        dialog.retry_clicked.connect(lambda: self._update_result("✅ User clicked: Retry"))
        dialog.offline_clicked.connect(lambda: self._update_result("✅ User clicked: Proceed Offline"))
        dialog.exit_clicked.connect(lambda: self._update_result("✅ User clicked: Exit"))

        dialog.exec_()

    def _test_dialog_without_offline(self):
        """Test dialog without offline option."""
        dialog = ServerDownDialog(self, show_offline_option=False)

        # Connect signals
        dialog.retry_clicked.connect(lambda: self._update_result("✅ User clicked: Retry (no offline)"))
        dialog.exit_clicked.connect(lambda: self._update_result("✅ User clicked: Exit (no offline)"))

        dialog.exec_()

    def _test_error_handler(self):
        """Test error handler."""
        error_handler = ServerErrorHandler(self, offline_manager=None)

        # Simulate a server error
        test_errors = [
            "Connection refused: Unable to reach server",
            "HTTP 503: Service Unavailable",
            "Network timeout: Connection timeout after 30s",
        ]

        results = []
        for error in test_errors:
            if error_handler.is_server_down_error(error):
                results.append(f"✅ Detected: {error}")
            else:
                results.append(f"❌ Failed to detect: {error}")

        self._update_result("\n".join(results))

    def _test_error_detection(self):
        """Test error detection logic."""
        error_handler = ServerErrorHandler(self, offline_manager=None)

        test_cases = [
            ("Connection refused", True),
            ("Connection reset by peer", True),
            ("Unable to connect to server", True),
            ("HTTP 502 Bad Gateway", True),
            ("HTTP 503 Service Unavailable", True),
            ("Server down for maintenance", True),
            ("Database connection timeout", True),
            ("Invalid username", False),
            ("Access denied", False),
            ("File not found", False),
        ]

        results = []
        for error_msg, expected in test_cases:
            detected = error_handler.is_server_down_error(error_msg)
            status = "✅" if detected == expected else "❌"
            results.append(f"{status} '{error_msg}' → {detected} (expected {expected})")

        self._update_result("\n".join(results))

    def _update_result(self, text):
        """Update result label."""
        self.result_label.setText(text)


def main():
    """Run the test application."""
    app = QApplication(sys.argv)

    window = TestWindow()
    window.show()

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
