"""
Auto Updater Module
Checks for application updates from GitHub releases and manages the update process.
Supports both interactive and silent (automatic) updates.
"""

import os
import sys
import json
import requests
import tempfile
import subprocess
import shutil
import logging
from pathlib import Path
from packaging import version
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QProgressBar, QTextEdit, QMessageBox)
from PyQt5.QtCore import QThread, pyqtSignal, Qt
from PyQt5.QtGui import QFont

# Import version from version.py (single source of truth)
try:
    from version import __version__ as CURRENT_VERSION, GITHUB_REPO
except ImportError:
    CURRENT_VERSION = "1.0.0"
    GITHUB_REPO = "food2g0/Operation-Report-System"

CHECK_UPDATE_ON_STARTUP = True
UPDATE_CHECK_INTERVAL = 86400  # 24 hours in seconds

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("AutoUpdater")

# Version tracking file path (to detect successful updates)
def _get_version_file_path():
    """Get the path to the version tracking file"""
    if sys.platform == 'win32':
        app_data = os.environ.get('APPDATA', os.path.expanduser('~'))
        return os.path.join(app_data, 'OperationReportSystem', 'last_version.json')
    else:
        return os.path.join(os.path.expanduser('~'), '.ors_last_version.json')


def _save_pre_update_version():
    """Save the current version before updating (called before installer runs)"""
    try:
        version_file = _get_version_file_path()
        os.makedirs(os.path.dirname(version_file), exist_ok=True)
        data = {
            'pre_update_version': CURRENT_VERSION,
            'updating': True
        }
        with open(version_file, 'w') as f:
            json.dump(data, f)
        logger.info(f"Saved pre-update version: {CURRENT_VERSION}")
    except Exception as e:
        logger.error(f"Failed to save pre-update version: {e}")


def check_update_success(parent=None):
    """
    Check if the app was just updated and show a success message.
    Call this on app startup.
    
    Args:
        parent: Parent widget for the message box
    
    Returns:
        Tuple (was_updated: bool, from_version: str or None)
    """
    try:
        version_file = _get_version_file_path()
        
        if not os.path.exists(version_file):
            # First run or no update tracking - save current version
            os.makedirs(os.path.dirname(version_file), exist_ok=True)
            data = {'last_version': CURRENT_VERSION, 'updating': False}
            with open(version_file, 'w') as f:
                json.dump(data, f)
            return (False, None)
        
        with open(version_file, 'r') as f:
            data = json.load(f)
        
        pre_update_version = data.get('pre_update_version')
        was_updating = data.get('updating', False)
        last_version = data.get('last_version')
        
        # Check if we just completed an update
        if was_updating and pre_update_version:
            # Compare versions - if current is newer, update was successful
            if version.parse(CURRENT_VERSION) > version.parse(pre_update_version):
                logger.info(f"Update successful: {pre_update_version} -> {CURRENT_VERSION}")
                
                # Clear the updating flag and save new version
                data = {'last_version': CURRENT_VERSION, 'updating': False}
                with open(version_file, 'w') as f:
                    json.dump(data, f)
                
                # Show success message
                if parent is not None:
                    QMessageBox.information(
                        parent,
                        "Update Successful",
                        f"The application has been updated successfully!\n\n"
                        f"Previous version: {pre_update_version}\n"
                        f"Current version: {CURRENT_VERSION}\n\n"
                        f"Thank you for updating!"
                    )
                
                return (True, pre_update_version)
            else:
                # Update was cancelled or failed - reset flag
                data = {'last_version': CURRENT_VERSION, 'updating': False}
                with open(version_file, 'w') as f:
                    json.dump(data, f)
        
        # Update last_version if it changed (manual install, etc.)
        if last_version and version.parse(CURRENT_VERSION) != version.parse(last_version):
            data = {'last_version': CURRENT_VERSION, 'updating': False}
            with open(version_file, 'w') as f:
                json.dump(data, f)
        
        return (False, None)
        
    except Exception as e:
        logger.error(f"Error checking update success: {e}")
        return (False, None)


class UpdateChecker(QThread):
    """Background thread to check for updates"""
    update_available = pyqtSignal(dict)  # Emits update info
    no_update = pyqtSignal()
    error_occurred = pyqtSignal(str)
    finished_check = pyqtSignal()  # Emitted when check completes (success or failure)
    
    def __init__(self, current_version=CURRENT_VERSION):
        super().__init__()
        self.current_version = current_version
        self._is_running = False
    
    def run(self):
        """Check for updates from GitHub releases"""
        self._is_running = True
        try:
            # Get latest release from GitHub API
            api_url = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"
            response = requests.get(api_url, timeout=10)
            
            if response.status_code == 404:
                self.error_occurred.emit("Repository not found. Please check GITHUB_REPO configuration.")
                return
            
            if response.status_code != 200:
                self.error_occurred.emit(f"Failed to check for updates: HTTP {response.status_code}")
                return
            
            release_data = response.json()
            latest_version = release_data.get('tag_name', '').lstrip('v')
            
            if not latest_version:
                self.error_occurred.emit("Invalid release data received")
                return
            
            # Compare versions
            if version.parse(latest_version) > version.parse(self.current_version):
                update_info = {
                    'version': latest_version,
                    'name': release_data.get('name', f'Version {latest_version}'),
                    'description': release_data.get('body', 'No description available'),
                    'download_url': self._get_download_url(release_data),
                    'release_date': release_data.get('published_at', ''),
                    'html_url': release_data.get('html_url', '')
                }
                self.update_available.emit(update_info)
            else:
                self.no_update.emit()
                
        except requests.exceptions.RequestException as e:
            self.error_occurred.emit(f"Network error: {str(e)}")
        except Exception as e:
            self.error_occurred.emit(f"Unexpected error: {str(e)}")
        finally:
            self._is_running = False
            self.finished_check.emit()
    
    def _get_download_url(self, release_data):
        """Extract download URL for Windows installer from release assets"""
        assets = release_data.get('assets', [])
        
        # Look for .exe installer first
        for asset in assets:
            name = asset.get('name', '').lower()
            if name.endswith('.exe') and 'setup' in name or 'installer' in name:
                return asset.get('browser_download_url')
        
        # Fall back to first .exe file
        for asset in assets:
            if asset.get('name', '').lower().endswith('.exe'):
                return asset.get('browser_download_url')
        
        # No suitable asset found
        return None


class SilentUpdater(QThread):
    """
    Silent Auto Updater - Downloads and installs updates without user interaction.
    Perfect for automatic background updates.
    """
    update_ready = pyqtSignal(str)  # Emits installer path when ready
    update_applied = pyqtSignal()  # Emitted when update is being applied
    request_exit = pyqtSignal()  # Request app exit from main thread (safe)
    error_occurred = pyqtSignal(str)
    status_changed = pyqtSignal(str)  # For optional status logging
    
    def __init__(self, current_version=CURRENT_VERSION, auto_install=True):
        super().__init__()
        self.current_version = current_version
        self.auto_install = auto_install
        self.installer_path = None
        self._is_running = False
    
    def run(self):
        """Check, download, and optionally install update silently"""
        self._is_running = True
        try:
            # Step 1: Check for updates
            self.status_changed.emit("Checking for updates...")
            logger.info("Silent updater: Checking for updates...")
            
            api_url = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"
            response = requests.get(api_url, timeout=10)
            
            if response.status_code != 200:
                logger.warning(f"Update check failed: HTTP {response.status_code}")
                return
            
            release_data = response.json()
            latest_version = release_data.get('tag_name', '').lstrip('v')
            
            if not latest_version:
                return
            
            # Compare versions
            if version.parse(latest_version) <= version.parse(self.current_version):
                self.status_changed.emit("Already up to date")
                logger.info(f"Silent updater: Already on latest version ({self.current_version})")
                return
            
            logger.info(f"Silent updater: New version available: {latest_version}")
            
            # Step 2: Get download URL
            download_url = self._get_download_url(release_data)
            if not download_url:
                logger.warning("No installer found in release assets")
                return
            
            # Step 3: Download update
            self.status_changed.emit(f"Downloading v{latest_version}...")
            logger.info(f"Silent updater: Downloading from {download_url}")
            
            temp_dir = tempfile.gettempdir()
            filename = f"ORS_Update_v{latest_version}.exe"
            self.installer_path = os.path.join(temp_dir, filename)
            
            response = requests.get(download_url, stream=True, timeout=60)
            response.raise_for_status()
            
            with open(self.installer_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            
            logger.info(f"Silent updater: Downloaded to {self.installer_path}")
            self.update_ready.emit(self.installer_path)
            
            # Step 4: Auto-install if enabled
            if self.auto_install:
                self.status_changed.emit("Installing update...")
                self._install_silent()
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Silent updater network error: {e}")
            self.error_occurred.emit(f"Network error: {str(e)}")
        except Exception as e:
            logger.error(f"Silent updater error: {e}")
            self.error_occurred.emit(f"Update error: {str(e)}")
        finally:
            self._is_running = False
    
    def _get_download_url(self, release_data):
        """Extract download URL for Windows installer from release assets"""
        assets = release_data.get('assets', [])
        
        # Look for .exe installer
        for asset in assets:
            name = asset.get('name', '').lower()
            if name.endswith('.exe') and ('setup' in name or 'installer' in name or 'ors' in name):
                return asset.get('browser_download_url')
        
        # Fall back to first .exe file
        for asset in assets:
            if asset.get('name', '').lower().endswith('.exe'):
                return asset.get('browser_download_url')
        
        return None
    
    def _install_silent(self):
        """Install the update silently using Inno Setup silent flags"""
        if not self.installer_path or not os.path.exists(self.installer_path):
            self.error_occurred.emit("Installer not found")
            return
        
        try:
            # Save pre-update version so we can show success message after restart
            _save_pre_update_version()
            
            logger.info("Silent updater: Starting silent installation...")
            
            # Inno Setup silent install flags:
            # /VERYSILENT - No UI at all
            # /SUPPRESSMSGBOXES - Suppress message boxes
            # /NORESTART - Don't restart automatically
            # /CLOSEAPPLICATIONS - Close running apps
            # /RESTARTAPPLICATIONS - Restart apps after install
            
            if sys.platform == 'win32':
                # Use subprocess to run installer with silent flags
                cmd = [
                    self.installer_path,
                    '/VERYSILENT',
                    '/SUPPRESSMSGBOXES',
                    '/NORESTART',
                    '/CLOSEAPPLICATIONS',
                    '/RESTARTAPPLICATIONS'
                ]
                
                # Start installer
                subprocess.Popen(cmd, shell=False, creationflags=subprocess.CREATE_NO_WINDOW)
                
                self.update_applied.emit()
                logger.info("Silent updater: Installer launched, requesting app exit...")
                
                # Give installer time to start, then request exit via signal (safe for QThread)
                import time
                time.sleep(1)
                self.request_exit.emit()  # Signal main thread to exit safely
            else:
                # Non-Windows: just mark as ready
                self.update_ready.emit(self.installer_path)
                
        except Exception as e:
            logger.error(f"Silent install failed: {e}")
            self.error_occurred.emit(f"Install failed: {str(e)}")
    
    def install_on_exit(self):
        """Schedule update to install when app exits (alternative to immediate install)"""
        if not self.installer_path or not os.path.exists(self.installer_path):
            return False
        
        # Create a batch script to run after app closes
        batch_path = os.path.join(tempfile.gettempdir(), "ors_update.bat")
        batch_content = f'''@echo off
timeout /t 2 /nobreak > nul
"{self.installer_path}" /VERYSILENT /SUPPRESSMSGBOXES /NORESTART
del "%~f0"
'''
        with open(batch_path, 'w') as f:
            f.write(batch_content)
        
        # Schedule batch to run
        subprocess.Popen(['cmd', '/c', batch_path], 
                        shell=False, 
                        creationflags=subprocess.CREATE_NO_WINDOW)
        return True


class UpdateDownloader(QThread):
    """Background thread to download updates"""
    progress = pyqtSignal(int)  # Download progress percentage
    finished = pyqtSignal(str)  # Download complete, emits file path
    error_occurred = pyqtSignal(str)
    
    def __init__(self, download_url, filename):
        super().__init__()
        self.download_url = download_url
        self.filename = filename
        self.download_path = None
    
    def run(self):
        """Download the update file"""
        try:
            # Create temp directory for download
            temp_dir = tempfile.gettempdir()
            self.download_path = os.path.join(temp_dir, self.filename)
            
            # Download with progress tracking
            response = requests.get(self.download_url, stream=True, timeout=30)
            response.raise_for_status()
            
            total_size = int(response.headers.get('content-length', 0))
            downloaded = 0
            
            with open(self.download_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        
                        if total_size > 0:
                            progress_percent = int((downloaded / total_size) * 100)
                            self.progress.emit(progress_percent)
            
            self.finished.emit(self.download_path)
            
        except requests.exceptions.RequestException as e:
            self.error_occurred.emit(f"Download failed: {str(e)}")
        except Exception as e:
            self.error_occurred.emit(f"Unexpected error during download: {str(e)}")


class UpdateDialog(QDialog):
    """Dialog to show update information and manage the update process"""
    
    def __init__(self, update_info, parent=None):
        super().__init__(parent)
        self.update_info = update_info
        self.download_thread = None
        self.installer_path = None
        
        self.setWindowTitle("Update Available")
        self.setMinimumWidth(500)
        self.setMinimumHeight(400)
        
        self.init_ui()
    
    def init_ui(self):
        """Initialize the user interface"""
        layout = QVBoxLayout()
        
        # Title
        title = QLabel(f"New Version Available: {self.update_info['version']}")
        title_font = QFont()
        title_font.setPointSize(12)
        title_font.setBold(True)
        title.setFont(title_font)
        layout.addWidget(title)
        
        # Current version
        current_label = QLabel(f"Current Version: {CURRENT_VERSION}")
        layout.addWidget(current_label)
        
        layout.addSpacing(10)
        
        # Release notes
        notes_label = QLabel("What's New:")
        notes_label.setFont(QFont("Arial", 10, QFont.Bold))
        layout.addWidget(notes_label)
        
        self.notes_text = QTextEdit()
        self.notes_text.setReadOnly(True)
        self.notes_text.setMaximumHeight(200)
        self.notes_text.setPlainText(self.update_info['description'])
        layout.addWidget(self.notes_text)
        
        layout.addSpacing(10)
        
        # Progress bar (hidden initially)
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
        
        # Status label
        self.status_label = QLabel("")
        self.status_label.setVisible(False)
        layout.addWidget(self.status_label)
        
        layout.addStretch()
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.view_release_btn = QPushButton("View Release Notes")
        self.view_release_btn.clicked.connect(self.view_release_online)
        button_layout.addWidget(self.view_release_btn)
        
        button_layout.addStretch()
        
        self.download_btn = QPushButton("Download and Install")
        self.download_btn.setDefault(True)
        self.download_btn.clicked.connect(self.start_download)
        button_layout.addWidget(self.download_btn)
        
        self.later_btn = QPushButton("Remind Me Later")
        self.later_btn.clicked.connect(self.reject)
        button_layout.addWidget(self.later_btn)
        
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
    
    def view_release_online(self):
        """Open the release page in a browser"""
        import webbrowser
        webbrowser.open(self.update_info['html_url'])
    
    def start_download(self):
        """Start downloading the update"""
        download_url = self.update_info.get('download_url')
        
        if not download_url:
            QMessageBox.warning(
                self,
                "No Installer Available",
                "No installer file found in the release.\n"
                "Please download manually from the release page."
            )
            self.view_release_online()
            return
        
        # Disable buttons
        self.download_btn.setEnabled(False)
        self.later_btn.setEnabled(False)
        self.view_release_btn.setEnabled(False)
        
        # Show progress
        self.progress_bar.setVisible(True)
        self.status_label.setVisible(True)
        self.status_label.setText("Downloading update...")
        
        # Start download
        filename = f"OperationReportSystem_v{self.update_info['version']}_Setup.exe"
        self.download_thread = UpdateDownloader(download_url, filename)
        self.download_thread.progress.connect(self.update_progress)
        self.download_thread.finished.connect(self.download_finished)
        self.download_thread.error_occurred.connect(self.download_error)
        self.download_thread.start()
    
    def update_progress(self, percent):
        """Update the progress bar"""
        self.progress_bar.setValue(percent)
    
    def download_finished(self, file_path):
        """Handle download completion"""
        self.installer_path = file_path
        self.status_label.setText("Download complete!")
        
        reply = QMessageBox.question(
            self,
            "Install Update",
            "Update downloaded successfully!\n\n"
            "Do you want to install it now?\n"
            "(The application will close and the installer will run)",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.Yes
        )
        
        if reply == QMessageBox.Yes:
            self.install_update()
        else:
            QMessageBox.information(
                self,
                "Update Ready",
                f"The installer has been downloaded to:\n{file_path}\n\n"
                "You can run it manually when you're ready."
            )
            self.accept()
    
    def download_error(self, error_msg):
        """Handle download errors"""
        self.status_label.setText("Download failed!")
        QMessageBox.critical(self, "Download Error", error_msg)
        
        # Re-enable buttons
        self.download_btn.setEnabled(True)
        self.later_btn.setEnabled(True)
        self.view_release_btn.setEnabled(True)
        self.progress_bar.setVisible(False)
    
    def install_update(self):
        """Run the installer and close the application"""
        if not self.installer_path or not os.path.exists(self.installer_path):
            QMessageBox.critical(
                self,
                "Error",
                "Installer file not found!"
            )
            return
        
        try:
            # Save pre-update version so we can show success message after restart
            _save_pre_update_version()
            
            # Launch the installer
            if sys.platform == 'win32':
                os.startfile(self.installer_path)
            else:
                subprocess.Popen([self.installer_path])
            
            # Close the application
            QMessageBox.information(
                self,
                "Installing Update",
                "The installer will now run.\n"
                "The application will close."
            )
            
            # Exit the application safely via QApplication
            from PyQt5.QtWidgets import QApplication
            app = QApplication.instance()
            if app:
                app.quit()
            else:
                sys.exit(0)
            
        except Exception as e:
            QMessageBox.critical(
                self,
                "Error",
                f"Failed to launch installer:\n{str(e)}"
            )


def check_for_updates(parent=None, silent=False):
    """
    Check for updates and show update dialog if available (INTERACTIVE mode)
    
    Args:
        parent: Parent widget for dialogs
        silent: If True, don't show "no updates" message
    
    Returns:
        UpdateChecker thread (connect to signals for custom handling)
    """
    checker = UpdateChecker()
    
    def on_update_available(update_info):
        dialog = UpdateDialog(update_info, parent)
        dialog.exec_()
    
    def on_no_update():
        if not silent:
            QMessageBox.information(
                parent,
                "No Updates",
                f"You are running the latest version ({CURRENT_VERSION})"
            )
    
    def on_error(error_msg):
        if not silent:
            QMessageBox.warning(
                parent,
                "Update Check Failed",
                f"Could not check for updates:\n{error_msg}"
            )
    
    def on_finished():
        # Clean up when check completes
        if hasattr(parent, '_update_checker_threads'):
            if checker in parent._update_checker_threads:
                parent._update_checker_threads.remove(checker)
    
    checker.update_available.connect(on_update_available)
    checker.no_update.connect(on_no_update)
    checker.error_occurred.connect(on_error)
    checker.finished_check.connect(on_finished)
    
    # Store reference in parent to prevent garbage collection
    if parent is not None:
        if not hasattr(parent, '_update_checker_threads'):
            parent._update_checker_threads = []
        parent._update_checker_threads.append(checker)
    
    checker.start()
    return checker


def check_for_updates_silent(parent=None, auto_install=True):
    """
    Check and apply updates SILENTLY in the background.
    No user interaction required - downloads and installs automatically.
    
    Args:
        parent: Parent widget (for thread reference)
        auto_install: If True, install immediately when downloaded
                      If False, just download (call install_on_exit later)
    
    Returns:
        SilentUpdater thread
    
    Usage:
        # In your app startup:
        updater = check_for_updates_silent(self)
        
        # Optional: connect to signals for logging/UI updates
        updater.status_changed.connect(lambda s: print(f"Update: {s}"))
    """
    from PyQt5.QtWidgets import QApplication
    
    updater = SilentUpdater(auto_install=auto_install)
    
    def on_status(status):
        logger.info(f"Silent update status: {status}")
    
    def on_error(error):
        logger.error(f"Silent update error: {error}")
    
    def on_ready(path):
        logger.info(f"Update ready at: {path}")
    
    def on_request_exit():
        """Safely exit application from main thread"""
        logger.info("Exiting application for update...")
        app = QApplication.instance()
        if app:
            app.quit()
        else:
            sys.exit(0)
    
    def on_finished():
        if hasattr(parent, '_update_checker_threads'):
            if updater in parent._update_checker_threads:
                parent._update_checker_threads.remove(updater)
    
    updater.status_changed.connect(on_status)
    updater.error_occurred.connect(on_error)
    updater.update_ready.connect(on_ready)
    updater.request_exit.connect(on_request_exit)
    updater.finished.connect(on_finished)
    
    # Store reference to prevent garbage collection
    if parent is not None:
        if not hasattr(parent, '_update_checker_threads'):
            parent._update_checker_threads = []
        parent._update_checker_threads.append(updater)
    
    updater.start()
    return updater


if __name__ == "__main__":
    # Test the updater
    from PyQt5.QtWidgets import QApplication
    
    app = QApplication(sys.argv)
    check_for_updates(silent=False)
    sys.exit(app.exec_())
