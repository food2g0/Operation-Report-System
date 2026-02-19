# Building a production Windows executable

Prerequisites:

- Python 3.8+ installed and on PATH
- Optional: Inno Setup (for .exe installer) available as `iscc` on PATH
- Optional: Code signing certificate for signing the executable

Quick build steps:

1. Open PowerShell in repository root.
2. Run the build script (creates a venv, installs deps, builds with PyInstaller):

```powershell
.\build_windows.ps1
```

3. If Inno Setup is installed the script will run `iscc installer.iss` to build an installer.

Notes and recommendations:

- The project already includes `main.spec` used by PyInstaller. The resulting exe will be in `dist\`.
- After building, sign the executable with your code-signing cert to reduce antivirus false positives.
- Test the installer on a clean Windows VM before distribution.
- Consider using `--onefile` vs `--onedir` depending on update strategy. Onefile is simpler but larger and extracts to temp at runtime.
- Update `AppVersion` in `installer.iss` and add release notes for installers.
