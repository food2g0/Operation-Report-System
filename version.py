"""
Version Configuration for Operation Report System
Update this file with each new release.
"""

__version__ = "2.0.2"
__version_info__ = {
    "major": 2,
    "minor": 0,
    "patch": 2,
    "release_date": "2026-06-22",
    "build": 4
}

# Auto-updater configuration
GITHUB_REPO = "food2g0/Operation-Report-System"
CHECK_ON_STARTUP = True  # Check for updates when app starts
AUTO_CHECK_INTERVAL = 86400  # Check every 24 hours (in seconds)
SILENT_UPDATE = True  # If True: auto-download and auto-install without prompts
