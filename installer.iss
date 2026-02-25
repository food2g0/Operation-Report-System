[Setup]
AppName=ORS
AppVersion=1.0.0
AppId={{A1B2C3D4-E5F6-7890-ABCD-EF1234567890}
DefaultDirName={autopf}\ORS
DefaultGroupName=ORS
OutputDir=installer
OutputBaseFilename=ORS_Setup
Compression=lzma
SolidCompression=yes
SetupIconFile=assets\logo.ico
DisableProgramGroupPage=yes
; Allow running in silent mode
AllowNoIcons=yes
; Close running application before install
CloseApplications=force
CloseApplicationsFilter=main.exe
RestartApplications=yes
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
; Only run app if NOT in silent mode (silent updates should restart automatically)
Filename: "{app}\main.exe"; Description: "Launch ORS"; Flags: nowait postinstall skipifsilent
