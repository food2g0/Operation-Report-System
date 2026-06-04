from PyQt5.QtWidgets import (
    QWidget, QLabel, QFrame, QVBoxLayout, QProgressBar,
    QDateEdit, QApplication
)
from PyQt5.QtGui import QFont
from PyQt5.QtCore import Qt

__all__ = [
    'LoadingOverlay',
    'NoWheelDateEdit',
]


class LoadingOverlay(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setStyleSheet("background-color: transparent;")

        container = QFrame(self)
        container.setAttribute(Qt.WA_TransparentForMouseEvents, False)
        container.setFixedSize(280, 140)
        container.setStyleSheet("""
            QFrame {
                background-color: white;
                border-radius: 12px;
                border: none;
            }
        """)

        layout = QVBoxLayout(container)
        layout.setAlignment(Qt.AlignCenter)
        layout.setSpacing(15)

        self.spinner = QLabel("⏳")
        self.spinner.setAlignment(Qt.AlignCenter)
        self.spinner.setStyleSheet("""
            QLabel {
                font-size: 28px;
                background: transparent;
            }
        """)

        self.status_label = QLabel("Posting report...")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setStyleSheet("""
            QLabel {
                color: #333333;
                font-size: 14px;
                font-weight: bold;
                font-family: 'Segoe UI', Arial;
                background: transparent;
            }
        """)

        self.progress = QProgressBar()
        self.progress.setRange(0, 0)
        self.progress.setTextVisible(False)
        self.progress.setFixedHeight(6)
        self.progress.setStyleSheet("""
            QProgressBar {
                background-color: #f0f0f0;
                border: none;
                border-radius: 3px;
            }
            QProgressBar::chunk {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #667eea, stop:1 #764ba2);
                border-radius: 3px;
            }
        """)

        self.subtitle_label = QLabel("Please wait...")
        self.subtitle_label.setAlignment(Qt.AlignCenter)
        self.subtitle_label.setStyleSheet("""
            QLabel {
                color: #888888;
                font-size: 11px;
                font-family: 'Segoe UI', Arial;
                background: transparent;
            }
        """)

        layout.addWidget(self.spinner)
        layout.addWidget(self.status_label)
        layout.addWidget(self.progress)
        layout.addWidget(self.subtitle_label)

        self.container = container
        self.hide()

    def showEvent(self, event):
        super().showEvent(event)
        if self.parent():
            self.setGeometry(self.parent().rect())
            self.container.move(
                (self.width() - self.container.width()) // 2,
                (self.height() - self.container.height()) // 2
            )

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.container.move(
            (self.width() - self.container.width()) // 2,
            (self.height() - self.container.height()) // 2
        )

    def set_status(self, text, subtitle="Please wait..."):
        self.status_label.setText(text)
        self.subtitle_label.setText(subtitle)
        QApplication.processEvents()


class NoWheelDateEdit(QDateEdit):
    """QDateEdit that ignores mouse wheel events to prevent accidental date changes."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Apply standardized calendar styling to all instances
        self.setStyleSheet(self._get_calendar_style())

    @staticmethod
    def _get_calendar_style():
        """Standardized calendar style matching DateRangeWidget."""
        return (
            "QDateEdit {padding:8px 32px 8px 8px;border:2px solid #dee2e6;border-radius:6px;"
            "background:white;font-size:13px;}"
            "QDateEdit:focus{border-color:#007bff;}"
            "QDateEdit::drop-down{subcontrol-origin:border;subcontrol-position:center right;"
            "width:28px;border-left:1px solid #dee2e6;background:#f0f2f5;"
            "border-top-right-radius:6px;border-bottom-right-radius:6px;}"
            "QDateEdit::drop-down:hover{background:#dde1e7;}"
            "QDateEdit::down-arrow{width:10px;height:10px;}"
            "QCalendarWidget{min-width:340px;min-height:280px;background:white;border:1px solid #dee2e6;border-radius:6px;}"
            "QCalendarWidget QWidget#qt_calendar_navigationbar{background-color:#343a40;min-height:42px;padding:4px 6px;border-radius:4px 4px 0 0;}"
            "QCalendarWidget QToolButton{color:#ecf0f1;font-size:14px;font-weight:bold;"
            "background-color:transparent;padding:6px 10px;border-radius:4px;margin:2px;}"
            "QCalendarWidget QToolButton:hover{background-color:#007bff;color:white;}"
            "QCalendarWidget QToolButton:pressed{background-color:#0056b3;color:white;}"
            "QCalendarWidget QSpinBox{color:#2c3e50;background-color:#ecf0f1;font-size:13px;"
            "font-weight:bold;border:1px solid #bdc3c7;border-radius:4px;padding:4px 8px;"
            "selection-background-color:#007bff;selection-color:white;}"
            "QCalendarWidget QAbstractItemView{background:white;selection-background-color:#007bff;"
            "selection-color:white;font-size:12px;alternate-background-color:#f8f9fa;}"
            "QCalendarWidget QAbstractItemView::item{padding:6px;border-radius:4px;}"
            "QCalendarWidget QAbstractItemView::item:alternate{background-color:#f8f9fa;}"
            "QCalendarWidget QAbstractItemView::item:selected{background-color:#007bff;color:white;font-weight:bold;}"
        )

    def wheelEvent(self, event):
        event.ignore()

    def open_calendar(self):
        try:
            self.showCalendarPopup()
            return
        except Exception:
            pass
        try:
            self.showPopup()
            return
        except Exception:
            pass
        try:
            w = self.calendarWidget()
            if w:
                w.show()
        except Exception:
            pass
