[Setup]
AppName=Operation Report System
AppVersion=2.0.2
AppId={{A1B2C3D4-E5F6-7890-ABCD-EF1234567890}

; Install to D:\OperationReportSystem (main app on fast disk)
; AppData\OperationReportSystem is used for cache/logs/updates only
DefaultDirName=D:\OperationReportSystem
DefaultGroupName=Operation Report System
OutputDir=installer
OutputBaseFilename=ORS_Setup_v2.0.2
Compression=lzma
SolidCompression=yes
SetupIconFile=assets\logo.ico
DisableProgramGroupPage=yes
AllowNoIcons=yes

; No elevation needed — users can update without admin
PrivilegesRequired=lowest

; Close running application before install
CloseApplications=no

; Uninstaller settings
UninstallDisplayIcon={app}\main.exe
UninstallDisplayName=Operation Report System
CreateUninstallRegKey=yes

; Allow user to choose installation directory during setup
AllowUNCPath=no
WizardStyle=modern

[Files]
; Include the single .exe - NO .env file (credentials are embedded in the exe)
Source: "dist\main.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "assets\*"; DestDir: "{app}\assets"; Flags: recursesubdirs createallsubdirs ignoreversion
Source: "field_config.json"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{autoprograms}\Operation Report System\ORS"; Filename: "{app}\main.exe"
Name: "{autodesktop}\ORS"; Filename: "{app}\main.exe"; Tasks: desktopicon

[Tasks]
Name: "desktopicon"; Description: "Create desktop shortcut"; GroupDescription: "Additional icons:"; Flags: checkedonce

[Run]
; Non-silent install — show "Launch ORS" checkbox at the end of the wizard
Filename: "{app}\main.exe"; Description: "Launch ORS"; Flags: nowait postinstall skipifsilent
; Silent install (auto-update) — always relaunch the app automatically
Filename: "{app}\main.exe"; Flags: nowait runasoriginaluser; Check: WizardSilent
