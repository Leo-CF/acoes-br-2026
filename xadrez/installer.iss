[Setup]
AppName=Xadrez
AppVersion=1.0
AppPublisher=Leo
DefaultDirName={autopf}\Xadrez
DefaultGroupName=Xadrez
OutputDir=dist_installer
OutputBaseFilename=Xadrez_Setup
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=lowest

[Languages]
Name: "portuguese"; MessagesFile: "compiler:Languages\Portuguese.isl"

[Tasks]
Name: "desktopicon"; Description: "Criar atalho na &Área de Trabalho"; GroupDescription: "Ícones adicionais:"

[Files]
Source: "dist\Xadrez\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\Xadrez"; Filename: "{app}\Xadrez.exe"
Name: "{group}\Desinstalar Xadrez"; Filename: "{uninstallexe}"
Name: "{commondesktop}\Xadrez"; Filename: "{app}\Xadrez.exe"; Tasks: desktopicon

[Run]
Filename: "{app}\Xadrez.exe"; Description: "Iniciar Xadrez"; Flags: nowait postinstall skipifsilent
