[Setup]
AppName=ORS
AppVersion=1.0.0
AppId={{A1B2C3D4-E5F6-7890-ABCD-EF1234567890}
; Install to AppData\Local — no admin rights needed, no UAC prompt
DefaultDirName={localappdata}\ORS
DefaultGroupName=ORS
OutputDir=installer
OutputBaseFilename=ORS_Setup
Compression=lzma
SolidCompression=yes
SetupIconFile=assets\logo.ico
DisableProgramGroupPage=yes
AllowNoIcons=yes
; Run without requesting elevation — this is the key to silent UAC-free install
PrivilegesRequired=lowest
; Close running application before install
; main.exe is already exited before the installer runs (batch relay handles timing)
CloseApplications=no
; Uninstaller settings
UninstallDisplayIcon={app}\main.exe
UninstallDisplayName=ORS
CreateUninstallRegKey=yes

[Files]
; Include the single .exe - NO .env file (credentials are embedded in the exe)
Source: "dist\main.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "assets\*"; DestDir: "{app}\assets"; Flags: recursesubdirs createallsubdirs ignoreversion
Source: "field_config.json"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\ORS"; Filename: "{app}\main.exe"
Name: "{commondesktop}\ORS"; Filename: "{app}\main.exe"; Tasks: desktopicon

[Tasks]
Name: "desktopicon"; Description: "Create desktop shortcut"; GroupDescription: "Additional icons:"; Flags: checkedonce

[Run]
; Non-silent install — show "Launch ORS" checkbox at the end of the wizard
Filename: "{app}\main.exe"; Description: "Launch ORS"; Flags: nowait postinstall skipifsilent
; Silent install (auto-update) — always relaunch the app automatically
Filename: "{app}\main.exe"; Flags: nowait runasoriginaluser; Check: WizardSilent
