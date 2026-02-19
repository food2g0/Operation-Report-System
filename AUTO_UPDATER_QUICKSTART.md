# Auto-Updater - Quick Start

## Installation

1. **Install dependencies:**
   ```powershell
   pip install requests packaging
   ```

2. **Configure your GitHub repository:**
   - Edit `version.py`
   - Change `GITHUB_REPO = "your-username/Operation-Report-System"`

3. **Done!** The auto-updater is now active.

## For Users

### Automatic Updates
- App checks for updates on startup
- If an update is found, you'll see a dialog with:
  - Version number
  - What's new
  - Download button

### Manual Check
- Click the version button (e.g., "ℹ️ v1.0.0") in the admin dashboard header
- Or it will automatically check on startup

### Installing Updates
1. Click "Download and Install"
2. Wait for download to complete
3. Click "Yes" to install
4. App closes and installer runs
5. Follow installer prompts

## For Developers

### Creating a Release

1. **Update version:**
   ```python
   # version.py
   __version__ = "1.1.0"
   ```

2. **Build application:**
   ```powershell
   .\build_windows.ps1
   ```

3. **Create GitHub release:**
   - Go to GitHub → Releases → New release
   - Tag: `v1.1.0`
   - Title: `Version 1.1.0`
   - Description: List changes
   - **Upload installer .exe file**
   - Publish

4. **Users get notified automatically!**

## Configuration

### Disable Auto-Check on Startup
```python
# version.py
CHECK_ON_STARTUP = False
```

### Change Check Interval
```python
# version.py
AUTO_CHECK_INTERVAL = 86400  # seconds (24 hours)
```

## Troubleshooting

**"Repository not found"**
- Update `GITHUB_REPO` in `version.py`

**"No installer found"**
- Ensure `.exe` file is uploaded to GitHub release
- File should have "setup" or "installer" in name

**Update check fails**
- Check internet connection
- Verify GitHub repo is public

## Need Help?

See detailed guide: [AUTO_UPDATER_GUIDE.md](AUTO_UPDATER_GUIDE.md)
