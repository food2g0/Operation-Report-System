# Auto-Updater Setup Guide

## Overview
The auto-updater system allows your Operation Report System application to automatically check for updates from GitHub releases and install them with a single click.

## Features
✅ Automatic update checking on app startup  
✅ Manual "Check for Updates" option  
✅ Download progress tracking  
✅ One-click installation  
✅ View release notes before updating  
✅ Silent background checks (no interruption if no update)  

## Setup Instructions

### 1. Install Required Dependencies

```powershell
pip install -r Requirements.txt
```

This will install:
- `requests` - For downloading updates from GitHub
- `packaging` - For version comparison

### 2. Configure GitHub Repository

Edit [`version.py`](version.py) and update the GitHub repository:

```python
GITHUB_REPO = "your-username/Operation-Report-System"  # Change this!
```

Replace `your-username` with your actual GitHub username or organization name.

### 3. Create GitHub Releases

When you're ready to release a new version:

#### Step 1: Update Version Number
Edit [`version.py`](version.py):
```python
__version__ = "1.1.0"  # Increment version
__version_info__ = {
    "major": 1,
    "minor": 1,
    "patch": 0,
    "release_date": "2026-02-20",
    "build": 2
}
```

#### Step 2: Build Your Application
```powershell
# Build the executable
.\build_windows.ps1

# This will create the installer in the build directory
```

#### Step 3: Create GitHub Release
1. Go to your GitHub repository
2. Click "Releases" → "Create a new release"
3. Tag version: `v1.1.0` (must start with 'v')
4. Release title: `Version 1.1.0` or descriptive name
5. Description: Add release notes (what's new, bug fixes, etc.)
6. **Attach the installer file**: Upload your `.exe` installer
   - File should contain "setup" or "installer" in the name
   - Example: `OperationReportSystem_v1.1.0_Setup.exe`
7. Click "Publish release"

### 4. Enable/Disable Auto-Updates

#### Disable Updates on Startup
Edit [`version.py`](version.py):
```python
CHECK_ON_STARTUP = False  # Disable automatic check
```

#### Completely Disable Auto-Updater
Comment out the import in [`login.py`](login.py):
```python
# Auto-updater (optional - comment out if not using)
# try:
#     from auto_updater import check_for_updates
#     from version import __version__, CHECK_ON_STARTUP
#     AUTO_UPDATE_ENABLED = True
# except ImportError:
AUTO_UPDATE_ENABLED = False
```

## How It Works

### For End Users
1. **On Startup**: App silently checks for updates in the background
2. **If Update Found**: Dialog shows with:
   - New version number
   - Release notes
   - Options: Download & Install, View Online, Remind Later
3. **Download**: One-click download with progress bar
4. **Install**: Installer runs automatically, app closes
5. **User**: Runs installer, gets the new version

### For Developers
1. Update version in `version.py`
2. Build application with `build_windows.ps1`
3. Create GitHub release with installer attached
4. Users get notified automatically

## Version Numbering

Use semantic versioning: `MAJOR.MINOR.PATCH`
- **MAJOR**: Breaking changes (1.0.0 → 2.0.0)
- **MINOR**: New features (1.0.0 → 1.1.0)
- **PATCH**: Bug fixes (1.0.0 → 1.0.1)

Examples:
- `1.0.0` - Initial release
- `1.0.1` - Bug fix
- `1.1.0` - New feature added
- `2.0.0` - Major redesign

## Testing the Auto-Updater

### Test Without Creating a Release
You can test the updater locally:

```python
# In auto_updater.py, temporarily modify:
if __name__ == "__main__":
    # Simulate update available
    test_update_info = {
        'version': '999.0.0',
        'name': 'Test Version',
        'description': 'This is a test update',
        'download_url': None,
        'release_date': '2026-02-16',
        'html_url': 'https://github.com/your-repo'
    }
    
    from PyQt5.QtWidgets import QApplication
    app = QApplication(sys.argv)
    dialog = UpdateDialog(test_update_info)
    dialog.exec_()
```

```powershell
python auto_updater.py
```

## Building Installer with Inno Setup

Your [`installer.iss`](installer.iss) file should include:

```iss
#define MyAppVersion "1.0.0"
#define MyAppPublisher "Your Company"
#define MyAppURL "https://github.com/your-username/Operation-Report-System"

[Setup]
AppId={{YOUR-UNIQUE-GUID}}
AppName=Operation Report System
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
DefaultDirName={autopf}\Operation Report System
OutputBaseFilename=OperationReportSystem_v{#MyAppVersion}_Setup
```

Build command:
```powershell
iscc installer.iss
```

## Manual Update Check

Add a "Check for Updates" button to your admin dashboard:

```python
# In admin_dashboard.py
from auto_updater import check_for_updates

def add_update_menu(self):
    # Add to menu bar
    help_menu = self.menuBar().addMenu("Help")
    check_updates_action = help_menu.addAction("Check for Updates")
    check_updates_action.triggered.connect(self.manual_update_check)

def manual_update_check(self):
    """Manually check for updates"""
    check_for_updates(parent=self, silent=False)
```

## Troubleshooting

### "Repository not found" Error
- Check `GITHUB_REPO` in `version.py` is correct
- Make sure repository is public (or provide authentication for private repos)

### "No installer found" Error
- Ensure your installer file has "setup" or "installer" in the filename
- Make sure it's uploaded to the GitHub release as an asset
- File must be `.exe` format

### Update Check Takes Too Long
- Normal for first check (GitHub API call)
- Subsequent checks are faster
- Check runs in background thread (non-blocking)

### Users Not Getting Update Notifications
- Check `CHECK_ON_STARTUP = True` in `version.py`
- Ensure users have internet connection
- Verify GitHub release is published (not draft)

## Security Considerations

1. **HTTPS Only**: All downloads use HTTPS
2. **GitHub Releases**: Updates only from your official GitHub repository
3. **User Confirmation**: User must approve download and installation
4. **No Auto-Install**: Updates never install without user consent

## Example Release Workflow

```powershell
# 1. Update version
# Edit version.py: __version__ = "1.2.0"

# 2. Commit changes
git add version.py
git commit -m "Bump version to 1.2.0"
git push

# 3. Build application
.\build_windows.ps1

# 4. Create release on GitHub
# - Tag: v1.2.0
# - Title: Version 1.2.0 - Enhanced Reports
# - Description: 
#   - Added new export feature
#   - Fixed date picker bug
#   - Improved performance
# - Attach: dist/OperationReportSystem_v1.2.0_Setup.exe

# 5. Publish release

# Users will be notified on next app startup!
```

## Support

For issues with the auto-updater:
1. Check GitHub repository configuration
2. Verify internet connectivity
3. Check `database.log` for error messages
4. Test with manual check: `python auto_updater.py`
