"""
Version Configuration for Operation Report System
Update this file with each new release.
"""

__version__ = "1.0.0"
__version_info__ = {
    "major": 1,
    "minor": 0,
    "patch": 1,
    "release_date": "2026-02-17",
    "build": 1
}

# Auto-updater configuration
GITHUB_REPO = "food2g0/Operation-Report-System"  # Your GitHub repository
CHECK_ON_STARTUP = True  # Check for updates when app starts
AUTO_CHECK_INTERVAL = 86400  # Check every 24 hours (in seconds)
SILENT_UPDATE = True  # If True: auto-download and auto-install without prompts
