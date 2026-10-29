#define MyAppName "MotorDesk"
#ifndef MyAppVersion
  #define MyAppVersion "1.0.30"
#endif
#define MyAppPublisher "MotorDesk"
#define MyAppExeName "MotorDesk.exe"

[Setup]
AppId={{8C89758B-77CB-4B7B-89C2-7D37C26AF947}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}

DefaultDirName={autopf}\MotorDesk
DefaultGroupName=MotorDesk
DisableProgramGroupPage=yes

PrivilegesRequired=admin
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible

OutputDir=output
OutputBaseFilename=MotorDesk-Setup-{#MyAppVersion}

Compression=lzma2
SolidCompression=yes
WizardStyle=modern

UninstallDisplayName=MotorDesk
UninstallDisplayIcon={app}\MotorDesk.exe

SetupLogging=yes
SetupIconFile=assets\MotorDesk.ico

[Languages]
Name: "spanish"; MessagesFile: "compiler:Languages\Spanish.isl"

[Dirs]
Name: "{commonappdata}\MotorDesk"
Name: "{commonappdata}\MotorDesk\uploads"
Name: "{commonappdata}\MotorDesk\backups"
Name: "{commonappdata}\MotorDesk\logs"

[UninstallDelete]
; PostgreSQL se instala por fuera de los ficheros gestionados por Inno Setup.
; Estas dos entradas eliminan únicamente la instancia aislada de MotorDesk:
; binarios y cluster de datos. No afectan a ningún PostgreSQL ajeno.
Name: "{app}\PostgreSQL"; Type: filesandordirs
Name: "{commonappdata}\MotorDesk\PostgreSQL"; Type: filesandordirs

[Files]
; =========================================================
; APLICACION MOTORDesk
; =========================================================

Source: "..\dist\MotorDesk\*"; \
    DestDir: "{app}"; \
    Flags: ignoreversion recursesubdirs createallsubdirs

Source: "..\backend\dist\MotorDeskBackend\*"; \
    DestDir: "{app}\Backend"; \
    Flags: ignoreversion recursesubdirs createallsubdirs

Source: "..\frontend\dist\frontend\browser\*"; \
    DestDir: "{app}\Backend\frontend"; \
    Flags: ignoreversion recursesubdirs createallsubdirs


; =========================================================
; DEPENDENCIAS INTERNAS DEL SETUP
;
; No se copian automáticamente.
; PrepareToInstall las extrae a {tmp} antes de instalar.
; =========================================================

Source: "dependencies\postgresql-17.11-1-windows-x64-binaries.zip"; \
    Flags: dontcopy

; Runtime requerido por PostgreSQL y por los binarios de MotorDesk en un
; Windows limpio. Se instala de forma silenciosa antes de inicializar la BD.
Source: "dependencies\vc_redist.x64.exe"; \
    Flags: dontcopy

Source: "scripts\install-postgresql.ps1"; \
    Flags: dontcopy

Source: "scripts\update-whatsapp-config.ps1"; \
    Flags: dontcopy

; Configurador gráfico descargable desde el servidor para preparar una vez
; cada puesto cliente. Solo descarga la CA pública por la LAN.
Source: "..\dist\MotorDesk-Configurar-Cliente.exe"; \
    DestDir: "{app}\Backend\frontend"; \
    DestName: "MotorDesk-Configurar-Cliente.exe"; \
    Flags: ignoreversion

Source: "generated\installer-integrations.env"; \
    DestName: "installer-integrations.env"; \
    Flags: dontcopy


[Icons]
Name: "{autoprograms}\MotorDesk"; \
    Filename: "{app}\MotorDesk.exe"; \
    IconFilename: "{app}\MotorDesk.exe"; \
    WorkingDir: "{app}"

Name: "{autodesktop}\MotorDesk"; \
    Filename: "{app}\MotorDesk.exe"; \
    IconFilename: "{app}\MotorDesk.exe"; \
    WorkingDir: "{app}"


[Run]
Filename: "{app}\Backend\MotorDeskBackend.exe"; \
    Parameters: "--migrate-only"; \
    Flags: runhidden waituntilterminated; \
    StatusMsg: "Actualizando de forma segura la base de datos existente..."

Filename: "{app}\Backend\MotorDeskBackend.exe"; \
    Parameters: "--generate-local-tls-certificate"; \
    Flags: runhidden waituntilterminated; \
    StatusMsg: "Preparando conexión segura para WhatsApp..."

Filename: "{sys}\certutil.exe"; \
    Parameters: "-addstore -f Root ""{commonappdata}\MotorDesk\tls\motordesk-local-ca.cer"""; \
    Flags: runhidden waituntilterminated; \
    StatusMsg: "Registrando la autoridad segura local..."

Filename: "{app}\MotorDesk.exe"; \
    Description: "Ejecutar MotorDesk"; \
    Flags: nowait postinstall skipifsilent; \
    Check: PostgreSQLReady


[Code]

var
  PostgreSQLReadyFlag: Boolean;
  VisualCppRestartRequired: Boolean;
  InstallProgressPage: TOutputProgressWizardPage;


procedure SetInstallProgress(const Percent: Integer; const Detail: String);
begin
  InstallProgressPage.SetText(
    'MotorDesk se esta preparando. No cierres este asistente.',
    Detail
  );
  InstallProgressPage.SetProgress(Percent, 100);
end;


procedure InitializeWizard();
begin
  InstallProgressPage := CreateOutputProgressPage(
    'Instalando MotorDesk',
    'Configuracion del sistema'
  );
  InstallProgressPage.SetProgress(0, 100);
end;


function PostgreSQLReady(): Boolean;
begin
  Result := PostgreSQLReadyFlag;
end;


function InitializeUninstall(): Boolean;
begin
  Result := MsgBox(
    'La desinstalacion eliminara PostgreSQL propio de MotorDesk y la base de datos local.' +
    Chr(13) + Chr(10) + Chr(13) + Chr(10) +
    'Las copias de seguridad de C:\ProgramData\MotorDesk\backups se conservaran.' +
    Chr(13) + Chr(10) +
    'No se modificara ningun PostgreSQL instalado fuera de MotorDesk.' +
    Chr(13) + Chr(10) + Chr(13) + Chr(10) +
    '¿Deseas continuar con la desinstalacion?',
    mbConfirmation,
    MB_YESNO
  ) = IDYES;
end;


procedure DetenerYEliminarPostgreSQLMotorDesk();
var
  ResultCode: Integer;
  Intento: Integer;
begin
  // El servicio pertenece exclusivamente a la instancia aislada instalada
  // por MotorDesk. Pararlo antes de borrar sus carpetas evita archivos
  // bloqueados y no interactúa con servicios PostgreSQL de terceros.
  Exec(
    ExpandConstant('{sys}\sc.exe'),
    'stop "MotorDeskPostgreSQL"',
    '',
    SW_HIDE,
    ewWaitUntilTerminated,
    ResultCode
  );

  // PostgreSQL puede necesitar unos segundos para cerrar el cluster.
  for Intento := 1 to 15 do
  begin
    Sleep(1000);
  end;

  Exec(
    ExpandConstant('{sys}\sc.exe'),
    'delete "MotorDeskPostgreSQL"',
    '',
    SW_HIDE,
    ewWaitUntilTerminated,
    ResultCode
  );
end;


procedure CurUninstallStepChanged(CurUninstallStep: TUninstallStep);
begin
  if CurUninstallStep = usUninstall then
  begin
    DetenerYEliminarPostgreSQLMotorDesk();
  end;
end;


function ServiceExists(const ServiceName: String): Boolean;
var
  ResultCode: Integer;
begin
  Result := False;

  if Exec(
    ExpandConstant('{sys}\sc.exe'),
    'query "' + ServiceName + '"',
    '',
    SW_HIDE,
    ewWaitUntilTerminated,
    ResultCode
  ) then
  begin
    Result := ResultCode = 0;
  end;
end;


function PostgreSQLResponde(): Boolean;
var
  PgIsReady: String;
  ResultCode: Integer;
begin
  Result := False;
  PgIsReady := ExpandConstant('{app}\PostgreSQL\bin\pg_isready.exe');

  if not FileExists(PgIsReady) then
    Exit;

  if Exec(
    PgIsReady,
    '-h 127.0.0.1 -p 55432 -q',
    '',
    SW_HIDE,
    ewWaitUntilTerminated,
    ResultCode
  ) then
  begin
    Result := ResultCode = 0;
  end;
end;


procedure DetenerBackendMotorDesk();
var
  ResultCode: Integer;
begin
  // Durante una actualizacion puede permanecer activo un backend anterior.
  // Solo se detienen componentes identificados como MotorDesk; PostgreSQL y
  // los datos de la empresa no se modifican.
  Exec(
    ExpandConstant('{sys}\sc.exe'),
    'stop "MotorDeskBackend"',
    '',
    SW_HIDE,
    ewWaitUntilTerminated,
    ResultCode
  );

  Exec(
    ExpandConstant('{sys}\taskkill.exe'),
    '/F /T /IM "MotorDeskBackend.exe"',
    '',
    SW_HIDE,
    ewWaitUntilTerminated,
    ResultCode
  );

  Sleep(1500);
end;


function AsegurarPostgreSQLExistente(): Boolean;
var
  ResultCode: Integer;
  Intento: Integer;
begin
  if PostgreSQLResponde() then
  begin
    Result := True;
    Exit;
  end;

  // Una actualizacion nunca reemplaza un cluster existente. Intentamos
  // arrancar su servicio y exigimos que responda antes de continuar.
  Exec(
    ExpandConstant('{sys}\sc.exe'),
    'start "MotorDeskPostgreSQL"',
    '',
    SW_HIDE,
    ewWaitUntilTerminated,
    ResultCode
  );

  for Intento := 1 to 30 do
  begin
    Sleep(1000);

    if PostgreSQLResponde() then
    begin
      Result := True;
      Exit;
    end;
  end;

  Result := False;
end;


function ConfigurarAccesoRedLocal(): Boolean;
var
  ResultCode: Integer;
begin
  // Solo abrimos la API web en redes privadas. PostgreSQL continua escuchando
  // exclusivamente en localhost:55432, por lo que no queda accesible desde
  // ningún equipo de la red.
  Exec(
    ExpandConstant('{sys}\netsh.exe'),
    'advfirewall firewall delete rule name="MotorDesk - Acceso red local"',
    '',
    SW_HIDE,
    ewWaitUntilTerminated,
    ResultCode
  );

  Result := Exec(
    ExpandConstant('{sys}\netsh.exe'),
    'advfirewall firewall add rule name="MotorDesk - Acceso red local" ' +
    // 8000 mantiene compatibilidad con los equipos LAN ya configurados y
    // 8443 es el punto HTTPS que abre el lanzador local y requiere Meta.
    'dir=in action=allow protocol=TCP localport=8000,8443 profile=private',
    '',
    SW_HIDE,
    ewWaitUntilTerminated,
    ResultCode
  ) and (ResultCode = 0);
end;


function InstallVisualCppRuntime(): Boolean; forward;


function RunPostgreSQLInstaller(): Boolean;
var
  PowerShellExe: String;
  ScriptPath: String;
  ArchivePath: String;
  Parameters: String;
  ResultCode: Integer;
begin
  Result := False;

  PowerShellExe :=
    ExpandConstant(
      '{sys}\WindowsPowerShell\v1.0\powershell.exe'
    );

  ScriptPath :=
    ExpandConstant('{tmp}\install-postgresql.ps1');

  ArchivePath :=
    ExpandConstant(
      '{tmp}\postgresql-17.11-1-windows-x64-binaries.zip'
    );

  if not FileExists(PowerShellExe) then
  begin
    MsgBox(
      'MotorDesk no encuentra Windows PowerShell.' +
      Chr(13) + Chr(10) + Chr(13) + Chr(10) +
      'No es posible configurar la base de datos.',
      mbError,
      MB_OK
    );

    Exit;
  end;

  if not FileExists(ScriptPath) then
  begin
    MsgBox(
      'No se ha podido extraer el instalador interno de PostgreSQL.' +
      Chr(13) + Chr(10) + Chr(13) + Chr(10) +
      ScriptPath,
      mbError,
      MB_OK
    );

    Exit;
  end;

  if not FileExists(ArchivePath) then
  begin
    MsgBox(
      'No se ha podido extraer PostgreSQL.' +
      Chr(13) + Chr(10) + Chr(13) + Chr(10) +
      ArchivePath,
      mbError,
      MB_OK
    );

    Exit;
  end;

  Parameters :=
    '-NoProfile -NonInteractive -ExecutionPolicy Bypass ' +
    '-File "' + ScriptPath + '" ' +
    '-ArchivePath "' + ArchivePath + '" ' +
    '-InstallDir "' + ExpandConstant('{app}\PostgreSQL') + '" ' +
    '-IntegrationConfigPath "' +
      ExpandConstant('{tmp}\installer-integrations.env') + '" ' +
    '-StatusFile "' +
      ExpandConstant(
        '{commonappdata}\MotorDesk\logs\install-status.txt'
      ) + '"';

  SetInstallProgress(
    25,
    'Instalando PostgreSQL aislado y creando la base de datos...'
  );

  if not Exec(
    PowerShellExe,
    Parameters,
    '',
    SW_HIDE,
    ewWaitUntilTerminated,
    ResultCode
  ) then
  begin
    MsgBox(
      'No se ha podido iniciar la configuración de PostgreSQL.' +
      Chr(13) + Chr(10) + Chr(13) + Chr(10) +
      'MotorDesk no se instalará.',
      mbError,
      MB_OK
    );

    Exit;
  end;

  if ResultCode <> 0 then
  begin
    MsgBox(
      'No se ha podido preparar la base de datos de MotorDesk.' +
      Chr(13) + Chr(10) + Chr(13) + Chr(10) +
      'Código de error: ' + IntToStr(ResultCode) +
      Chr(13) + Chr(10) + Chr(13) + Chr(10) +
      'Consulta el registro:' +
      Chr(13) + Chr(10) +
      'C:\ProgramData\MotorDesk\logs\install-postgresql.log',
      mbError,
      MB_OK
    );

    Exit;
  end;

  Result := True;
end;


function ActualizarConfiguracionWhatsAppExistente(): Boolean;
var
  PowerShellExe: String;
  ScriptPath: String;
  Parameters: String;
  ResultCode: Integer;
begin
  Result := False;
  PowerShellExe := ExpandConstant('{sys}\WindowsPowerShell\v1.0\powershell.exe');
  ScriptPath := ExpandConstant('{tmp}\update-whatsapp-config.ps1');

  if not FileExists(PowerShellExe) or not FileExists(ScriptPath) then
    Exit;

  Parameters :=
    '-NoProfile -NonInteractive -ExecutionPolicy Bypass ' +
    '-File "' + ScriptPath + '" ' +
    '-ConfigPath "' + ExpandConstant('{commonappdata}\MotorDesk\.env') + '" ' +
    '-IntegrationConfigPath "' +
      ExpandConstant('{tmp}\installer-integrations.env') + '"';

  if Exec(
    PowerShellExe,
    Parameters,
    '',
    SW_HIDE,
    ewWaitUntilTerminated,
    ResultCode
  ) then
  begin
    Result := ResultCode = 0;
  end;
end;


function PrepareToInstall(var NeedsRestart: Boolean): String;
begin
  Result := '';
  PostgreSQLReadyFlag := False;
  VisualCppRestartRequired := False;
  InstallProgressPage.Show;
  SetInstallProgress(5, 'Comprobando el sistema...');

  WizardForm.StatusLabel.Caption :=
    'Comprobando la instalación de MotorDesk...';

  // Si ya existe la BD de MotorDesk, estamos ante una actualización.
  // No se toca PostgreSQL ni los datos existentes.
  DetenerBackendMotorDesk();

  if ServiceExists('MotorDeskPostgreSQL') then
  begin
    SetInstallProgress(70, 'Comprobando la base de datos existente...');

    if not AsegurarPostgreSQLExistente() then
    begin
      InstallProgressPage.Hide;
      Result :=
        'Se ha detectado una instalacion existente de PostgreSQL, ' +
        'pero no responde en el puerto local 55432.' +
        Chr(13) + Chr(10) + Chr(13) + Chr(10) +
        'Para proteger los datos existentes, MotorDesk no la ' +
        'reemplazara automaticamente.' +
        Chr(13) + Chr(10) +
        'Consulta: C:\ProgramData\MotorDesk\logs\install-postgresql.log';
      Exit;
    end;

    // La actualización mantiene intactos PostgreSQL y los datos. Solo añade
    // las credenciales Meta a la configuración privada existente.
    SetInstallProgress(85, 'Actualizando la integración local de WhatsApp...');
    ExtractTemporaryFile('update-whatsapp-config.ps1');
    ExtractTemporaryFile('installer-integrations.env');

    // WhatsApp es opcional: si por algún motivo no se puede actualizar, el
    // instalador no bloquea la aplicación ni toca datos. El script registra
    // el motivo para soporte en ProgramData\MotorDesk\logs.
    ActualizarConfiguracionWhatsAppExistente();

    PostgreSQLReadyFlag := True;
    if not ConfigurarAccesoRedLocal() then
    begin
      InstallProgressPage.Hide;
      Result := 'No se ha podido configurar el acceso desde la red local.';
      Exit;
    end;
    SetInstallProgress(100, 'MotorDesk esta listo para continuar.');
    InstallProgressPage.Hide;
    Exit;
  end;

  try
    SetInstallProgress(12, 'Extrayendo componentes de PostgreSQL...');
    WizardForm.StatusLabel.Caption :=
      'Preparando componentes de PostgreSQL...';

    ExtractTemporaryFile(
      'install-postgresql.ps1'
    );

    ExtractTemporaryFile(
      'installer-integrations.env'
    );

    ExtractTemporaryFile(
      'vc_redist.x64.exe'
    );

    ExtractTemporaryFile(
      'postgresql-17.11-1-windows-x64-binaries.zip'
    );
  except
    InstallProgressPage.Hide;
    Result :=
      'MotorDesk no ha podido preparar los archivos necesarios ' +
      'para instalar PostgreSQL.' +
      Chr(13) + Chr(10) +
      GetExceptionMessage;

    Exit;
  end;

  if not InstallVisualCppRuntime() then
  begin
    InstallProgressPage.Hide;
    Result :=
      'No se han podido instalar los componentes de Windows ' +
      'necesarios para MotorDesk.';
    Exit;
  end;

  if not RunPostgreSQLInstaller() then
  begin
    InstallProgressPage.Hide;
    Result :=
      'No se ha podido preparar la base de datos de MotorDesk.' +
      Chr(13) + Chr(10) +
      'La instalación se ha detenido.';

    Exit;
  end;

  if not ServiceExists('MotorDeskPostgreSQL') then
  begin
    InstallProgressPage.Hide;
    Result :=
      'PostgreSQL terminó el proceso de instalación, pero ' +
      'el servicio MotorDeskPostgreSQL no está disponible.';

    Exit;
  end;

  if not AsegurarPostgreSQLExistente() then
  begin
    InstallProgressPage.Hide;
    Result :=
      'PostgreSQL se ha registrado, pero no responde tras la instalacion.' +
      Chr(13) + Chr(10) + Chr(13) + Chr(10) +
      'Consulta: C:\ProgramData\MotorDesk\logs\install-postgresql.log';
    Exit;
  end;

  PostgreSQLReadyFlag := True;
  if not ConfigurarAccesoRedLocal() then
  begin
    InstallProgressPage.Hide;
    Result := 'No se ha podido configurar el acceso desde la red local.';
    Exit;
  end;
  NeedsRestart := VisualCppRestartRequired;
  SetInstallProgress(100, 'Base de datos preparada correctamente.');
  InstallProgressPage.Hide;
end;


function InstallVisualCppRuntime(): Boolean;
var
  RuntimePath: String;
  RuntimeLogPath: String;
  ResultCode: Integer;
begin
  Result := False;
  RuntimePath := ExpandConstant('{tmp}\vc_redist.x64.exe');
  RuntimeLogPath := ExpandConstant(
    '{commonappdata}\MotorDesk\logs\vc_redist.log'
  );

  if not FileExists(RuntimePath) then
  begin
    MsgBox(
      'No se ha podido extraer el componente Visual C++ requerido ' +
      'por MotorDesk.',
      mbError,
      MB_OK
    );
    Exit;
  end;

  SetInstallProgress(8, 'Instalando componentes de Windows necesarios...');

  // El redistribuible se ejecuta sin interfaz; conservamos su log para
  // poder diagnosticar de forma fiable cualquier PC limpio.
  ForceDirectories(ExtractFileDir(RuntimeLogPath));

  if not Exec(
    RuntimePath,
    '/install /quiet /norestart /log "' + RuntimeLogPath + '"',
    '',
    SW_HIDE,
    ewWaitUntilTerminated,
    ResultCode
  ) then
  begin
    MsgBox(
      'No se ha podido iniciar la instalacion de Visual C++.',
      mbError,
      MB_OK
    );
    Exit;
  end;

  // 1638: ya existe una versi\u00f3n del redistribuible; el requisito ya
  // est\u00e1 cubierto. 3010 y 1641 indican instalaci\u00f3n correcta que pide
  // reiniciar Windows, no un fallo.
  if (ResultCode = 0) or (ResultCode = 1638) then
  begin
    Result := True;
    Exit;
  end;

  if (ResultCode = 3010) or (ResultCode = 1641) then
  begin
    VisualCppRestartRequired := True;
    Result := True;
    Exit;
  end;

  if ResultCode <> 0 then
  begin
    MsgBox(
      'Visual C++ no se ha instalado correctamente. ' +
      'Codigo de error: ' + IntToStr(ResultCode) +
      Chr(13) + Chr(10) + Chr(13) + Chr(10) +
      'Consulta el registro:' + Chr(13) + Chr(10) +
      RuntimeLogPath,
      mbError,
      MB_OK
    );
    Exit;
  end;
end;
