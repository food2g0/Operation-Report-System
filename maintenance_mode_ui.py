"""
Maintenance Mode UI Components
================================
Professional UI components for displaying maintenance notifications.
"""

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QWidget, QFrame
)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal
from PyQt5.QtGui import QFont, QPixmap, QIcon
from PyQt5.QtSvg import QSvgWidget
import datetime


class MaintenanceNotificationBar(QWidget):
    """Non-blocking maintenance banner shown at top of dashboards."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.maintenance_info = None
        self._init_ui()
        self._check_maintenance()
        
        # Check every 5 seconds for changes
        self._timer = QTimer()
        self._timer.timeout.connect(self._check_maintenance)
        self._timer.start(5000)
    
    def _init_ui(self):
        """Build the banner UI (initially hidden)."""
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)
        
        self.banner = QFrame()
        self.banner.setStyleSheet("""
            QFrame {
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:0,
                    stop:0 #FFA500, stop:1 #FF8C00
                );
                border: none;
                border-bottom: 3px solid #E67E22;
            }
        """)
        self.banner.setFixedHeight(0)  # Hidden by default
        
        banner_layout = QHBoxLayout(self.banner)
        banner_layout.setContentsMargins(16, 12, 16, 12)
        banner_layout.setSpacing(12)
        
        # Icon
        self.icon_label = QLabel("⚠️")
        self.icon_label.setStyleSheet("font-size: 24px; background: transparent;")
        self.icon_label.setFixedWidth(32)
        banner_layout.addWidget(self.icon_label)
        
        # Content area
        content = QVBoxLayout()
        content.setSpacing(4)
        
        self.title_label = QLabel()
        self.title_label.setStyleSheet("""
            QLabel {
                color: white;
                font-weight: bold;
                font-size: 14px;
                background: transparent;
            }
        """)
        content.addWidget(self.title_label)
        
        self.message_label = QLabel()
        self.message_label.setStyleSheet("""
            QLabel {
                color: rgba(255, 255, 255, 0.9);
                font-size: 12px;
                background: transparent;
            }
        """)
        self.message_label.setWordWrap(True)
        content.addWidget(self.message_label)
        
        self.timer_label = QLabel()
        self.timer_label.setStyleSheet("""
            QLabel {
                color: rgba(255, 255, 255, 0.8);
                font-size: 11px;
                background: transparent;
                font-style: italic;
            }
        """)
        content.addWidget(self.timer_label)
        
        banner_layout.addLayout(content, 1)
        
        self.layout.addWidget(self.banner)
    
    def _check_maintenance(self):
        """Check if maintenance is active and update banner."""
        from maintenance_mode import get_maintenance_info, is_maintenance_blocking
        
        info = get_maintenance_info()
        
        if info and info != self.maintenance_info:
            self.maintenance_info = info
            self.show_banner()
            self._update_timer_display()
        elif not info and self.maintenance_info:
            self.maintenance_info = None
            self.hide_banner()
        
        # If blocking mode, show the full-screen dialog instead
        if is_maintenance_blocking() and info:
            self.hide_banner()
            if not hasattr(self, '_blocking_dialog'):
                self._blocking_dialog = MaintenanceDialog(self.parent())
            self._blocking_dialog.show_maintenance(info)
            self._blocking_dialog.showFullScreen()
    
    def show_banner(self):
        """Display the maintenance banner."""
        if self.maintenance_info:
            self.title_label.setText(self.maintenance_info.get('title', 'System Maintenance'))
            self.message_label.setText(self.maintenance_info.get('message', 'We are performing maintenance.'))
            self.banner.setFixedHeight(90)
            self._timer_display = QTimer()
            self._timer_display.timeout.connect(self._update_timer_display)
            self._timer_display.start(1000)
    
    def hide_banner(self):
        """Hide the maintenance banner."""
        self.banner.setFixedHeight(0)
        if hasattr(self, '_timer_display'):
            self._timer_display.stop()
    
    def _update_timer_display(self):
        """Update the countdown timer in the banner."""
        if not self.maintenance_info:
            return
        
        try:
            ends_at = self.maintenance_info.get('ends_at')
            if isinstance(ends_at, str):
                ends_at = datetime.datetime.fromisoformat(ends_at)
            
            remaining = ends_at - datetime.datetime.now()
            if remaining.total_seconds() > 0:
                mins, secs = divmod(int(remaining.total_seconds()), 60)
                self.timer_label.setText(f"Estimated time remaining: {mins}m {secs}s")
            else:
                self.timer_label.setText("Maintenance should complete shortly...")
        except Exception:
            pass


class MaintenanceDialog(QDialog):
    """Full-screen maintenance mode dialog blocking user interaction."""
    
    def __init__(self, parent=None):
        super().__init__(parent, Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.maintenance_info = None
        self.setStyleSheet("background: transparent;")
        self.setAttribute(Qt.WA_TranslucentBackground)
        self._build_ui()
    
    def _build_ui(self):
        """Build the full-screen maintenance dialog."""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        # Semi-transparent background overlay
        overlay = QFrame()
        overlay.setStyleSheet("""
            QFrame {
                background-color: rgba(0, 0, 0, 0.85);
                border: none;
            }
        """)
        
        overlay_layout = QVBoxLayout(overlay)
        overlay_layout.setAlignment(Qt.AlignCenter)
        
        # Centered card
        card = QFrame()
        card.setStyleSheet("""
            QFrame {
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:1,
                    stop:0 #F8F9FA, stop:1 #E8EAED
                );
                border-radius: 20px;
                border: 2px solid #E67E22;
                padding: 0px;
            }
        """)
        card.setFixedSize(500, 400)
        
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(40, 40, 40, 40)
        card_layout.setSpacing(20)
        
        # Header with icon
        header = QHBoxLayout()
        header.setSpacing(15)
        
        icon_label = QLabel("🔧")
        icon_label.setStyleSheet("font-size: 48px; background: transparent;")
        icon_label.setFixedWidth(64)
        icon_label.setAlignment(Qt.AlignCenter)
        header.addWidget(icon_label)
        
        title = QLabel("System Maintenance")
        title.setStyleSheet("""
            QLabel {
                color: #E67E22;
                font-size: 28px;
                font-weight: bold;
                background: transparent;
            }
        """)
        title.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        header.addWidget(title, 1)
        
        card_layout.addLayout(header)
        
        # Message
        self.message = QLabel(
            "We are performing scheduled maintenance to improve your experience.\n"
            "We apologize for any inconvenience."
        )
        self.message.setStyleSheet("""
            QLabel {
                color: #555;
                font-size: 14px;
                background: transparent;
                line-height: 1.6;
            }
        """)
        self.message.setWordWrap(True)
        self.message.setAlignment(Qt.AlignCenter)
        card_layout.addWidget(self.message)
        
        # Timer
        self.timer_info = QLabel()
        self.timer_info.setStyleSheet("""
            QLabel {
                color: #E67E22;
                font-size: 18px;
                font-weight: bold;
                background: transparent;
            }
        """)
        self.timer_info.setAlignment(Qt.AlignCenter)
        card_layout.addWidget(self.timer_info)
        
        # Additional info
        self.details = QLabel()
        self.details.setStyleSheet("""
            QLabel {
                color: #888;
                font-size: 12px;
                background: transparent;
                line-height: 1.5;
            }
        """)
        self.details.setAlignment(Qt.AlignCenter)
        self.details.setWordWrap(True)
        card_layout.addWidget(self.details)
        
        card_layout.addStretch()
        
        # Refresh button
        refresh_btn = QPushButton("↻ Check Status")
        refresh_btn.setFixedSize(150, 40)
        refresh_btn.setStyleSheet("""
            QPushButton {
                background: #E67E22;
                color: white;
                border: none;
                border-radius: 8px;
                font-weight: bold;
                font-size: 12px;
            }
            QPushButton:hover {
                background: #D35400;
            }
            QPushButton:pressed {
                background: #BA4A00;
            }
        """)
        refresh_btn.clicked.connect(self._refresh_status)
        
        # Offline mode button (if offline support available)
        offline_btn = QPushButton("💾 Work Offline")
        offline_btn.setFixedSize(150, 40)
        offline_btn.setStyleSheet("""
            QPushButton {
                background: #3B82F6;
                color: white;
                border: none;
                border-radius: 8px;
                font-weight: bold;
                font-size: 12px;
            }
            QPushButton:hover {
                background: #2563EB;
            }
            QPushButton:pressed {
                background: #1D4ED8;
            }
        """)
        offline_btn.clicked.connect(self._enable_offline_mode)
        
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_layout.addWidget(offline_btn)
        btn_layout.addSpacing(10)
        btn_layout.addWidget(refresh_btn)
        btn_layout.addStretch()
        card_layout.addLayout(btn_layout)
        
        overlay_layout.addWidget(card)
        main_layout.addWidget(overlay)
        
        # Update timer every second
        self._update_timer = QTimer()
        self._update_timer.timeout.connect(self._update_countdown)
        self._update_timer.start(1000)
    
    def show_maintenance(self, info):
        """Display maintenance with given info."""
        self.maintenance_info = info
        if info:
            self.message.setText(info.get('message', 'System Maintenance'))
            self.details.setText(
                f"Started: {info.get('started_at', 'N/A')}\n"
                f"Started by: {info.get('started_by', 'System')}"
            )
            self._update_countdown()
            self.showFullScreen()
    
    def _update_countdown(self):
        """Update countdown timer."""
        if not self.maintenance_info:
            self.hide()
            return
        
        try:
            from maintenance_mode import get_maintenance_info
            info = get_maintenance_info()
            
            if not info:
                self.hide()
                return
            
            self.maintenance_info = info
            ends_at = info.get('ends_at')
            if isinstance(ends_at, str):
                ends_at = datetime.datetime.fromisoformat(ends_at)
            
            remaining = ends_at - datetime.datetime.now()
            if remaining.total_seconds() > 0:
                mins, secs = divmod(int(remaining.total_seconds()), 60)
                hours = mins // 60
                mins = mins % 60
                
                if hours > 0:
                    self.timer_info.setText(f"⏱️ {hours}h {mins}m {secs}s remaining")
                else:
                    self.timer_info.setText(f"⏱️ {mins}m {secs}s remaining")
            else:
                self.hide()
        except Exception as e:
            print(f"Error updating countdown: {e}")
    
    def _refresh_status(self):
        """Manually check if maintenance is still active."""
        from maintenance_mode import get_maintenance_info
        
        info = get_maintenance_info()
        if info:
            self.show_maintenance(info)
        else:
            self.hide()
    
    def _enable_offline_mode(self):
        """Enable offline mode so user can continue working."""
        try:
            from offline_manager import offline_manager
            if offline_manager:
                offline_manager.set_offline(True)
                self.hide()
                # Notify user
                from PyQt5.QtWidgets import QMessageBox
                QMessageBox.information(
                    self.parent(),
                    "Offline Mode Enabled",
                    "You are now in offline mode.\n\n"
                    "Your entries will be saved locally and synced when maintenance ends."
                )
        except Exception as e:
            print(f"Could not enable offline mode: {e}")
