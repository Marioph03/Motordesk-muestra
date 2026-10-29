param(
    [Parameter(Mandatory = $true)]
    [string]$ArchivePath,

    [string]$InstallDir = "$env:ProgramFiles\MotorDesk\PostgreSQL",

    [string]$DataDir = "$env:ProgramData\MotorDesk\PostgreSQL\data",

    [string]$ConfigDir = "$env:ProgramData\MotorDesk",

    [string]$ServiceName = "MotorDeskPostgreSQL",

    [string]$DatabaseName = "motordesk",

    [string]$DatabaseUser = "motordesk_app",

    [int]$Port = 55432,

    # El Setup actual entrega credenciales mediante un fichero temporal. Esto
    # evita que caracteres especiales se alteren al pasarlos por argumentos.
    [string]$IntegrationConfigPath = "",

    # Compatibilidad con ejecuciones manuales antiguas.
    [string]$MetaAppId = "",

    [string]$MetaAppSecret = "",

    [string]$MetaConfigId = "",

    # Se conserva exclusivamente en el .env privado de cada instalacion.
    # Nunca se escribe en logs ni se muestra al usuario.
    [string]$GroqApiKey = "",

    [string]$GoogleOAuthClientSecret = "",

    # Archivo que el instalador visual consulta para mostrar el progreso real
    # del componente que esta ejecutando PowerShell.
    [string]$StatusFile = "$env:ProgramData\MotorDesk\logs\install-status.txt"
)

$ErrorActionPreference = "Stop"


function Import-IntegrationConfig {
    <# Carga exclusivamente los ajustes permitidos del fichero temporal.
       El contenido no se muestra ni se registra. #>
    if ([string]::IsNullOrWhiteSpace($IntegrationConfigPath)) {
        return
    }

    if (-not (Test-Path -LiteralPath $IntegrationConfigPath -PathType Leaf)) {
        throw "No se encuentra la configuración interna de integraciones."
    }

    $permitidos = @{
        "META_APP_ID" = "MetaAppId"
        "META_APP_SECRET" = "MetaAppSecret"
        "META_CONFIG_ID" = "MetaConfigId"
        "GROQ_API_KEY" = "GroqApiKey"
        "GOOGLE_OAUTH_CLIENT_SECRET" = "GoogleOAuthClientSecret"
    }

    foreach ($linea in Get-Content -LiteralPath $IntegrationConfigPath) {
        if ($linea -match '^(?<clave>[A-Z0-9_]+)=(?<valor>.*)$') {
            $destino = $permitidos[$Matches.clave]
            if ($destino) {
                Set-Variable -Name $destino -Value $Matches.valor -Scope Script
            }
        }
    }
}


Import-IntegrationConfig

# ============================================================
# LOG
# ============================================================

$LogDir = Join-Path $ConfigDir "logs"
$LogFile = Join-Path $LogDir "install-postgresql.log"

New-Item `
    -ItemType Directory `
    -Path $LogDir `
    -Force | Out-Null

$transcriptStarted = $false
$serviceRegistered = $false
$installDirCreated = $false
$dataDirCreated = $false
$configCreated = $false


function Write-InstallStatus {
    param(
        [Parameter(Mandatory = $true)]
        [int]$Percent,

        [Parameter(Mandatory = $true)]
        [string]$Message
    )

    # Una sola linea facilita que el instalador pueda leerla incluso mientras
    # PowerShell continua trabajando. No se escriben secretos en este archivo.
    $line = "$Percent|$Message|$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"
    [IO.File]::WriteAllText(
        $StatusFile,
        $line + [Environment]::NewLine,
        [System.Text.UTF8Encoding]::new($false)
    )
    Write-Host "[$Percent%] $Message"
}


# ============================================================
# FUNCIONES
# ============================================================

function Assert-Administrator {

    $identity = [Security.Principal.WindowsIdentity]::GetCurrent()

    $principal = New-Object `
        Security.Principal.WindowsPrincipal($identity)

    if (
        -not $principal.IsInRole(
            [Security.Principal.WindowsBuiltInRole]::Administrator
        )
    ) {
        throw "Este script debe ejecutarse como administrador."
    }
}


function New-RandomBytes {
    param(
        [Parameter(Mandatory = $true)]
        [int]$ByteCount
    )

    $bytes = New-Object byte[] $ByteCount
    $rng = [Security.Cryptography.RandomNumberGenerator]::Create()

    try {
        $rng.GetBytes($bytes)
    }
    finally {
        $rng.Dispose()
    }

    return $bytes
}


function New-RandomSecret {
    param(
        [int]$ByteCount = 48
    )

    $bytes = New-RandomBytes -ByteCount $ByteCount

    return [Convert]::ToBase64String($bytes).
        TrimEnd("=").
        Replace("+", "-").
        Replace("/", "_")
}


function New-FernetKey {

    $bytes = New-RandomBytes -ByteCount 32

    # Fernet utiliza Base64 URL-safe de exactamente 32 bytes.
    return [Convert]::ToBase64String($bytes).
        Replace("+", "-").
        Replace("/", "_")
}


function Assert-SafeName {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Name,

        [Parameter(Mandatory = $true)]
        [string]$Label
    )

    if ($Name -notmatch "^[A-Za-z_][A-Za-z0-9_]{0,62}$") {
        throw "$Label no es un identificador PostgreSQL valido."
    }
}


function Wait-PostgreSql {
    param(
        [Parameter(Mandatory = $true)]
        [string]$PgIsReady,

        [Parameter(Mandatory = $true)]
        [int]$ServerPort
    )

    Write-Host "Esperando a que PostgreSQL acepte conexiones..."

    for ($intento = 1; $intento -le 60; $intento++) {

        & $PgIsReady `
            -h "127.0.0.1" `
            -p "$ServerPort" `
            -q

        if ($LASTEXITCODE -eq 0) {
            Write-Host "PostgreSQL acepta conexiones."
            return
        }

        Start-Sleep -Seconds 1
    }

    throw (
        "MotorDeskPostgreSQL no ha empezado a aceptar " +
        "conexiones en el plazo previsto."
    )
}


function Invoke-Icacls {
    param(
        [Parameter(Mandatory = $true)]
        [string[]]$Arguments,

        [Parameter(Mandatory = $true)]
        [string]$ErrorMessage
    )

    & icacls.exe @Arguments | Out-Null

    if ($LASTEXITCODE -ne 0) {
        throw "$ErrorMessage (icacls $LASTEXITCODE)."
    }
}


function Get-LocalSystemAccount {
    # El SID de LocalSystem es invariable; traducirlo evita asumir el idioma
    # del sistema en Task Scheduler (SYSTEM / SISTEMA / etc.).
    return (
        [Security.Principal.SecurityIdentifier]::new("S-1-5-18")
    ).Translate(
        [Security.Principal.NTAccount]
    ).Value
}


function Initialize-ClusterAsLocalSystem {
    param(
        [Parameter(Mandatory = $true)]
        [string]$InitDb,

        [Parameter(Mandatory = $true)]
        [string]$ClusterDataDir,

        [Parameter(Mandatory = $true)]
        [string]$SuperUser,

        [Parameter(Mandatory = $true)]
        [string]$PasswordFile,

        [Parameter(Mandatory = $true)]
        [string]$WorkingDirectory,

        [Parameter(Mandatory = $true)]
        [string]$InitLogFile
    )

    # PostgreSQL exige que initdb y el proceso servidor se ejecuten bajo la
    # misma cuenta de Windows. Usamos LocalSystem para el servicio local y
    # una tarea temporal con esa misma identidad. Esto evita que ACL locales
    # distintas impidan a una cuenta limitada leer postgresql.conf.
    $taskName = "MotorDesk-PostgreSQL-Init-" +
        [Guid]::NewGuid().ToString("N")

    $bootstrapScript = Join-Path `
        $WorkingDirectory `
        ("initdb-" + [Guid]::NewGuid().ToString("N") + ".ps1")

    try {
        New-Item `
            -ItemType Directory `
            -Path $WorkingDirectory `
            -Force | Out-Null

        $bootstrapContent = @'
param(
    [string]$InitDb,
    [string]$DataDir,
    [string]$SuperUser,
    [string]$PasswordFile,
    [string]$LogFile
)

$ErrorActionPreference = "Stop"

try {
    & $InitDb `
        -D $DataDir `
        -U $SuperUser `
        "--pwfile=$PasswordFile" `
        "--auth=scram-sha-256" `
        "--encoding=UTF8" *>> $LogFile

    exit $LASTEXITCODE
}


catch {
    $_ | Out-File -LiteralPath $LogFile -Append -Encoding utf8
    exit 1
}
'@

        [IO.File]::WriteAllText(
            $bootstrapScript,
            $bootstrapContent,
            [System.Text.UTF8Encoding]::new($false)
        )

        # La cuenta del servicio necesita leer el script y la contrasena
        # temporal, y debe poder crear todos los ficheros del cluster.
        Invoke-Icacls `
            -Arguments @(
                $ClusterDataDir,
                "/grant",
                "*S-1-5-18:(OI)(CI)F",
                "/T",
                "/C"
            ) `
            -ErrorMessage (
                "No se han podido preparar permisos para LocalSystem"
            )

        foreach ($temporaryFile in @($bootstrapScript, $PasswordFile)) {
            Invoke-Icacls `
                -Arguments @(
                    $temporaryFile,
                    "/grant:r",
                    "*S-1-5-18:(F)",
                    "*S-1-5-32-544:(F)",
                    "*S-1-5-18:(R)",
                    "/C"
                ) `
                -ErrorMessage (
                    "No se han podido proteger los archivos temporales"
                )
        }

        $powershellExe = Join-Path `
            $env:WINDIR `
            "System32\\WindowsPowerShell\\v1.0\\powershell.exe"

        $arguments = (
            "-NoProfile -NonInteractive -ExecutionPolicy Bypass " +
            "-File `"$bootstrapScript`" " +
            "-InitDb `"$InitDb`" " +
            "-DataDir `"$ClusterDataDir`" " +
            "-SuperUser `"$SuperUser`" " +
            "-PasswordFile `"$PasswordFile`" " +
            "-LogFile `"$InitLogFile`""
        )

        $action = New-ScheduledTaskAction `
            -Execute $powershellExe `
            -Argument $arguments

        # Task Scheduler necesita el nombre localizado de la cuenta integrada.
        $localSystemAccount = Get-LocalSystemAccount

        $principal = New-ScheduledTaskPrincipal `
            -UserId $localSystemAccount `
            -LogonType ServiceAccount

        $settings = New-ScheduledTaskSettingsSet `
            -ExecutionTimeLimit (New-TimeSpan -Minutes 3) `
            -AllowStartIfOnBatteries `
            -DontStopIfGoingOnBatteries

        Register-ScheduledTask `
            -TaskName $taskName `
            -Action $action `
            -Principal $principal `
            -Settings $settings `
            -Force | Out-Null

        Start-ScheduledTask -TaskName $taskName
        $startedAt = Get-Date

        # 0x41301 (267009) es SCHED_S_TASK_RUNNING. PG_VERSION se crea al
        # principio de initdb, por lo que no puede utilizarse como senal de
        # finalizacion: esperar solo a ese archivo cancelaria el proceso a
        # mitad de la inicializacion.
        $taskStillRunning = 267009

        for ($attempt = 1; $attempt -le 180; $attempt++) {
            Start-Sleep -Seconds 1

            $taskInfo = Get-ScheduledTaskInfo -TaskName $taskName

            if (
                ($taskInfo.LastRunTime -ge $startedAt.AddSeconds(-5))
            ) {
                if ($taskInfo.LastTaskResult -eq $taskStillRunning) {
                    continue
                }

                if ($taskInfo.LastTaskResult -eq 0) {
                    if (
                        Test-Path -LiteralPath (
                            Join-Path $ClusterDataDir "PG_VERSION"
                        )
                    ) {
                        return
                    }

                    throw (
                        "initdb termino sin crear PG_VERSION. Consulta: " +
                        $InitLogFile
                    )
                }

                throw (
                    "initdb bajo LocalSystem fallo con codigo " +
                    "$($taskInfo.LastTaskResult). Consulta: $InitLogFile"
                )
            }
        }

        throw (
            "initdb no termino en el plazo previsto. Consulta: " +
            $InitLogFile
        )
    }
    finally {
        Unregister-ScheduledTask `
            -TaskName $taskName `
            -Confirm:$false `
            -ErrorAction SilentlyContinue

        Remove-Item `
            -LiteralPath $bootstrapScript `
            -Force `
            -ErrorAction SilentlyContinue
    }
}


function Test-PostgreSqlStartAsLocalSystem {
    param(
        [Parameter(Mandatory = $true)] [string]$PgCtl,
        [Parameter(Mandatory = $true)] [string]$ClusterDataDir,
        [Parameter(Mandatory = $true)] [string]$WorkingDirectory,
        [Parameter(Mandatory = $true)] [string]$StartupLogFile
    )

    # Verifica el arranque real con la identidad del servicio antes de
    # registrarlo en SCM. Asi los problemas de ACL, DLL o configuracion se
    # guardan en un log de PostgreSQL util para soporte.
    $taskName = "MotorDesk-PostgreSQL-StartTest-" +
        [Guid]::NewGuid().ToString("N")
    $testScript = Join-Path $WorkingDirectory (
        "postgresql-start-test-" + [Guid]::NewGuid().ToString("N") + ".ps1"
    )

    try {
        $testContent = @'
param([string]$PgCtl, [string]$DataDir, [string]$StartupLog)
$ErrorActionPreference = "Stop"
try {
    & $PgCtl start -D $DataDir -l $StartupLog -w -t 45
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
    & $PgCtl stop -D $DataDir -m fast -w -t 45
    exit $LASTEXITCODE
}
catch {
    $_ | Out-File -LiteralPath $StartupLog -Append -Encoding utf8
    exit 1
}
'@

        [IO.File]::WriteAllText(
            $testScript, $testContent,
            [System.Text.UTF8Encoding]::new($false)
        )

        Invoke-Icacls `
            -Arguments @(
                $testScript, "/grant:r",
                "*S-1-5-18:(F)", "*S-1-5-32-544:(F)",
                "*S-1-5-18:(R)", "/C"
            ) `
            -ErrorMessage "No se ha podido preparar la prueba de PostgreSQL"

        $powershellExe = Join-Path $env:WINDIR `
            "System32\\WindowsPowerShell\\v1.0\\powershell.exe"
        $arguments = (
            "-NoProfile -NonInteractive -ExecutionPolicy Bypass " +
            "-File `"$testScript`" -PgCtl `"$PgCtl`" " +
            "-DataDir `"$ClusterDataDir`" -StartupLog `"$StartupLogFile`""
        )

        Register-ScheduledTask `
            -TaskName $taskName `
            -Action (New-ScheduledTaskAction -Execute $powershellExe -Argument $arguments) `
            -Principal (New-ScheduledTaskPrincipal -UserId (Get-LocalSystemAccount) -LogonType ServiceAccount) `
            -Settings (New-ScheduledTaskSettingsSet -ExecutionTimeLimit (New-TimeSpan -Minutes 3)) `
            -Force | Out-Null

        Start-ScheduledTask -TaskName $taskName
        $startedAt = Get-Date

        for ($attempt = 1; $attempt -le 180; $attempt++) {
            Start-Sleep -Seconds 1
            $taskInfo = Get-ScheduledTaskInfo -TaskName $taskName

            if ($taskInfo.LastRunTime -lt $startedAt.AddSeconds(-5)) {
                continue
            }
            if ($taskInfo.LastTaskResult -eq 267009) { continue }
            if ($taskInfo.LastTaskResult -eq 0) { return }

            throw (
                "La prueba de arranque de PostgreSQL bajo LocalSystem " +
                "fallo con codigo $($taskInfo.LastTaskResult). Consulta: " +
                $StartupLogFile
            )
        }

        throw "La prueba de arranque de PostgreSQL no termino a tiempo. Consulta: $StartupLogFile"
    }
    finally {
        Unregister-ScheduledTask -TaskName $taskName -Confirm:$false -ErrorAction SilentlyContinue
        Remove-Item -LiteralPath $testScript -Force -ErrorAction SilentlyContinue
    }
}


function Archive-PartialInstallation {
    param(
        [Parameter(Mandatory = $true)]
        [string]$PreviousInstallDir,

        [Parameter(Mandatory = $true)]
        [string]$PreviousDataDir,

        [Parameter(Mandatory = $true)]
        [string]$PreviousConfigPath
    )

    $hasPartialFiles =
        (Test-Path -LiteralPath $PreviousInstallDir) -or
        (Test-Path -LiteralPath $PreviousDataDir) -or
        (Test-Path -LiteralPath $PreviousConfigPath)

    if (-not $hasPartialFiles) {
        return
    }

    # Solo llegamos aqui si el servicio MotorDeskPostgreSQL no existe y el
    # puerto esta libre. No se toca por tanto una instalacion funcional.
    $recoveryRoot = Join-Path `
        $env:ProgramData `
        (
            "MotorDesk\\failed-installations\\" +
            (Get-Date -Format "yyyyMMdd-HHmmss")
        )

    New-Item -ItemType Directory -Path $recoveryRoot -Force | Out-Null

    Write-Host (
        "Se han detectado restos de una instalacion anterior. " +
        "Se conservaran en: $recoveryRoot"
    )

    if (Test-Path -LiteralPath $PreviousInstallDir) {
        Move-Item `
            -LiteralPath $PreviousInstallDir `
            -Destination (Join-Path $recoveryRoot "PostgreSQL") `
            -Force
    }

    if (Test-Path -LiteralPath $PreviousDataDir) {
        Move-Item `
            -LiteralPath $PreviousDataDir `
            -Destination (Join-Path $recoveryRoot "data") `
            -Force
    }

    if (Test-Path -LiteralPath $PreviousConfigPath) {
        Move-Item `
            -LiteralPath $PreviousConfigPath `
            -Destination (Join-Path $recoveryRoot "config.env") `
            -Force
    }
}


# ============================================================
# INSTALACION
# ============================================================

try {

    Start-Transcript `
        -Path $LogFile `
        -Append `
        -Force | Out-Null

    $transcriptStarted = $true

    Write-Host ""
    Write-Host "============================================"
    Write-Host " MotorDesk - PostgreSQL aislado"
    Write-Host "============================================"
    Write-Host ""
    Write-Host "Fecha: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"
    Write-Host "Archivo PostgreSQL: $ArchivePath"
    Write-Host "Instalacion: $InstallDir"
    Write-Host "Datos: $DataDir"
    Write-Host "Configuracion: $ConfigDir"
    Write-Host "Servicio: $ServiceName"
    Write-Host "Puerto: $Port"
    Write-Host ""

    # --------------------------------------------------------
    # 5% - COMPROBACIONES
    # --------------------------------------------------------

    Write-InstallStatus -Percent 5 -Message "Comprobando requisitos del sistema"

    Assert-Administrator

    if (-not (Test-Path -LiteralPath $ArchivePath -PathType Leaf)) {
        throw (
            "No se encuentra el archivo de binarios PostgreSQL: " +
            $ArchivePath
        )
    }

    if (
        [IO.Path]::GetExtension($ArchivePath).ToLowerInvariant() -ne ".zip"
    ) {
        throw "El paquete PostgreSQL debe ser un archivo .zip."
    }

    if ($Port -lt 1024 -or $Port -gt 65535) {
        throw "Puerto PostgreSQL no valido: $Port"
    }

    Assert-SafeName `
        -Name $DatabaseName `
        -Label "El nombre de base de datos"

    Assert-SafeName `
        -Name $DatabaseUser `
        -Label "El usuario de base de datos"

    if (
        Get-Service `
            -Name $ServiceName `
            -ErrorAction SilentlyContinue
    ) {
        throw (
            "Ya existe el servicio '$ServiceName'. " +
            "No se sobrescribira."
        )
    }

    if (
        Get-NetTCPConnection `
            -State Listen `
            -LocalPort $Port `
            -ErrorAction SilentlyContinue
    ) {
        throw "El puerto $Port ya esta en uso."
    }

    $configPath = Join-Path $ConfigDir ".env"

    Archive-PartialInstallation `
        -PreviousInstallDir $InstallDir `
        -PreviousDataDir $DataDir `
        -PreviousConfigPath $configPath


    # --------------------------------------------------------
    # 15% - EXTRAER POSTGRESQL
    # --------------------------------------------------------

    Write-InstallStatus -Percent 15 -Message "Extrayendo PostgreSQL aislado"

    $tar = Join-Path `
        $env:SystemRoot `
        "System32\tar.exe"

    if (-not (Test-Path -LiteralPath $tar -PathType Leaf)) {
        throw (
            "Windows no dispone de tar.exe para extraer " +
            "el paquete PostgreSQL."
        )
    }

    New-Item `
        -ItemType Directory `
        -Path $InstallDir `
        -Force | Out-Null

    $installDirCreated = $true

    & $tar `
        -xf $ArchivePath `
        -C $InstallDir

    if ($LASTEXITCODE -ne 0) {
        throw (
            "No se ha podido extraer el paquete PostgreSQL " +
            "(codigo $LASTEXITCODE)."
        )
    }

    # Los ZIP oficiales contienen normalmente una carpeta pgsql.
    $extractedRoot = Join-Path $InstallDir "pgsql"

    if (
        Test-Path `
            -LiteralPath (Join-Path $extractedRoot "bin") `
            -PathType Container
    ) {

        Get-ChildItem `
            -LiteralPath $extractedRoot `
            -Force |
        Move-Item `
            -Destination $InstallDir `
            -Force

        Remove-Item `
            -LiteralPath $extractedRoot `
            -Force
    }


    # --------------------------------------------------------
    # 30% - COMPROBAR BINARIOS
    # --------------------------------------------------------

    Write-InstallStatus -Percent 30 -Message "Verificando binarios de PostgreSQL"

    $binDir = Join-Path $InstallDir "bin"

    $initDb = Join-Path $binDir "initdb.exe"
    $pgCtl = Join-Path $binDir "pg_ctl.exe"
    $pgIsReady = Join-Path $binDir "pg_isready.exe"
    $psql = Join-Path $binDir "psql.exe"
    $pgDump = Join-Path $binDir "pg_dump.exe"

    foreach (
        $requiredBinary in @(
            $initDb,
            $pgCtl,
            $pgIsReady,
            $psql,
            $pgDump
        )
    ) {

        if (
            -not (
                Test-Path `
                    -LiteralPath $requiredBinary `
                    -PathType Leaf
            )
        ) {
            throw (
                "La extraccion no ha incluido el binario " +
                "requerido: $requiredBinary"
            )
        }
    }

    # El servicio se ejecuta como LocalSystem. No dependemos de las ACL
    # heredadas de Program Files: concedemos expresamente lectura y ejecucion
    # sobre los binarios que el SCM debe poder iniciar tras un reinicio.
    Invoke-Icacls `
        -Arguments @(
            $InstallDir,
            "/grant",
            "*S-1-5-20:(OI)(CI)RX",
            "/T",
            "/C"
        ) `
        -ErrorMessage (
            "No se han podido preparar los binarios de PostgreSQL " +
            "para el servicio"
        )


    # --------------------------------------------------------
    # SECRETOS
    # --------------------------------------------------------

    $superUser = "motordesk_admin"

    $superPassword = New-RandomSecret

    $applicationPassword = New-RandomSecret

    $secretKey = New-RandomSecret -ByteCount 64

    $encryptionKey = New-FernetKey

    # No usamos el TEMP del usuario: NetworkService no tiene por que poder
    # recorrer ese perfil. ProgramData pertenece a la instalacion y ya tiene
    # un directorio de logs creado desde el inicio.
    $passwordFile = Join-Path `
        $LogDir `
        (
            "motordesk-initdb-" +
            [Guid]::NewGuid().ToString("N") +
            ".txt"
        )


    # --------------------------------------------------------
    # 45% - INITDB
    # --------------------------------------------------------

    Write-InstallStatus -Percent 45 -Message "Inicializando la base de datos local"

    try {

        New-Item `
            -ItemType Directory `
            -Path $DataDir `
            -Force | Out-Null

        $dataDirCreated = $true

        $utf8WithoutBom = New-Object `
            System.Text.UTF8Encoding($false)

        [IO.File]::WriteAllText(
            $passwordFile,
            $superPassword,
            $utf8WithoutBom
        )

        Initialize-ClusterAsLocalSystem `
            -InitDb $initDb `
            -ClusterDataDir $DataDir `
            -SuperUser $superUser `
            -PasswordFile $passwordFile `
            -WorkingDirectory $LogDir `
            -InitLogFile (Join-Path $LogDir "initdb.log")
    }
    finally {

        Remove-Item `
            -LiteralPath $passwordFile `
            -Force `
            -ErrorAction SilentlyContinue
    }


    # --------------------------------------------------------
    # CONFIGURACION POSTGRESQL
    # --------------------------------------------------------

    Write-InstallStatus -Percent 55 -Message "Configurando PostgreSQL"

    $postgresqlConf = Join-Path `
        $DataDir `
        "postgresql.conf"

    Add-Content `
        -LiteralPath $postgresqlConf `
        -Value @(
            "",
            "# MotorDesk: instancia local aislada.",
            "listen_addresses = '127.0.0.1'",
            "port = $Port",
            "password_encryption = 'scram-sha-256'"
        )


    # --------------------------------------------------------
    # PERMISOS DEL CLUSTER
    # --------------------------------------------------------

    Write-InstallStatus -Percent 60 -Message "Protegiendo los datos de PostgreSQL"

    # SYSTEM. Este permiso debe ser directo sobre cada archivo existente,
    # no solo heredable: postgresql.conf ya existe al llegar aqui y el
    # servidor se ejecuta como LocalSystem.
    Invoke-Icacls `
        -Arguments @(
            $DataDir,
            "/grant:r",
            "*S-1-5-18:(F)",
            "/T",
            "/C"
        ) `
        -ErrorMessage "No se han podido conceder permisos a SYSTEM"

    # Administradores
    Invoke-Icacls `
        -Arguments @(
            $DataDir,
            "/grant:r",
            "*S-1-5-32-544:(F)",
            "/T",
            "/C"
        ) `
        -ErrorMessage "No se han podido conceder permisos a Administradores"

    # LocalSystem, cuenta de MotorDeskPostgreSQL. Reafirmamos el permiso
    # directo despues de aplicar los de Administradores para evitar que una
    # politica ACL particular de Windows deje fuera al proceso del servidor.
    Invoke-Icacls `
        -Arguments @(
            $DataDir,
            "/grant",
            "*S-1-5-18:(F)",
            "/T",
            "/C"
        ) `
        -ErrorMessage "No se han podido conceder permisos a LocalSystem"

    Invoke-Icacls `
        -Arguments @(
            $DataDir,
            "/inheritance:r",
            "/T",
            "/C"
        ) `
        -ErrorMessage "No se ha podido desactivar la herencia del cluster"


    # --------------------------------------------------------
    # 65% - PRUEBA DE ARRANQUE CON LA CUENTA DEL SERVICIO
    # --------------------------------------------------------

    Write-InstallStatus `
        -Percent 65 `
        -Message "Comprobando el arranque seguro de PostgreSQL"

    Test-PostgreSqlStartAsLocalSystem `
        -PgCtl $pgCtl `
        -ClusterDataDir $DataDir `
        -WorkingDirectory $LogDir `
        -StartupLogFile (Join-Path $LogDir "postgresql-startup.log")


    # --------------------------------------------------------
    # 70% - SERVICIO WINDOWS
    # --------------------------------------------------------

    Write-InstallStatus -Percent 70 -Message "Registrando el servicio de base de datos"

    # Sin -U, pg_ctl registra el servicio como LocalSystem. Es exactamente la
    # misma identidad usada para initdb y la prueba de arranque anterior.
    & $pgCtl `
        register `
        -N $ServiceName `
        -D $DataDir

    if ($LASTEXITCODE -ne 0) {
        throw (
            "No se ha podido registrar el servicio " +
            "'$ServiceName' (codigo $LASTEXITCODE)."
        )
    }

    $serviceRegistered = $true

    Set-Service `
        -Name $ServiceName `
        -StartupType Automatic

    try {
        Start-Service `
            -Name $ServiceName
    }
    catch {
        # El Service Control Manager puede tardar un instante en publicar su
        # evento. Esperamos antes de consultarlo para no perder el motivo
        # exacto de un fallo anterior al inicio del propio PostgreSQL.
        Start-Sleep -Seconds 2

        $eventDetail = ""

        # Algunos Windows publican el evento del servidor algunos segundos
        # despues de que SCM devuelva el error. Reintentamos y consultamos
        # tambien Application: PostgreSQL puede registrar ahi el motivo sin
        # incluir el nombre del servicio en el texto.
        for ($diagnosticAttempt = 1; $diagnosticAttempt -le 5; $diagnosticAttempt++) {
            foreach ($eventLogName in @("System", "Application")) {
                try {
                    $serviceEvent = (
                        Get-WinEvent `
                            -FilterHashtable @{
                                LogName = $eventLogName
                                StartTime = (Get-Date).AddMinutes(-2)
                            } `
                            -ErrorAction SilentlyContinue |
                        Where-Object {
                            (
                                (
                                    ($_.Id -in @(7000, 7009, 7023, 7031, 7034)) -and
                                    ($_.Message -match [Regex]::Escape($ServiceName))
                                ) -or (
                                    $_.ProviderName -in @(
                                        "PostgreSQL",
                                        "MotorDeskPostgreSQL"
                                    )
                                )
                            )
                        } |
                        Select-Object -First 1
                    )

                    if ($serviceEvent) {
                        $eventDetail = (
                            "[$($serviceEvent.LogName)/$($serviceEvent.ProviderName) " +
                            "ID $($serviceEvent.Id)] $($serviceEvent.Message)"
                        )
                        break
                    }
                }
                catch {
                    # El mensaje original de Start-Service sigue siendo util si
                    # el Visor de eventos no esta disponible en este Windows.
                }
            }

            if ($eventDetail) {
                break
            }

            Start-Sleep -Seconds 1
        }

        $scDetail = (
            & sc.exe queryex $ServiceName 2>&1 | Out-String
        ).Trim()

        $diagnostic = "No pudo iniciarse el servicio '$ServiceName'."

        if ($eventDetail) {
            $diagnostic += " Evento de Windows:`n$eventDetail"
        }

        if ($scDetail) {
            $diagnostic += "`nEstado de SCM:`n$scDetail"
        }

        $diagnostic += (
            "`nConsulta tambien: " +
            (Join-Path $LogDir "postgresql-startup.log")
        )

        throw $diagnostic
    }

    Wait-PostgreSql `
        -PgIsReady $pgIsReady `
        -ServerPort $Port


    # --------------------------------------------------------
    # 75% - USUARIO Y BD
    # --------------------------------------------------------

    Write-InstallStatus -Percent 75 -Message "Creando la base de datos de MotorDesk"

    $env:PGPASSWORD = $superPassword

    try {

        $quotedDatabaseUser =
            '"' + $DatabaseUser + '"'

        $quotedDatabaseName =
            '"' + $DatabaseName + '"'

        $escapedApplicationPassword =
            $applicationPassword.Replace("'", "''")

        & $psql `
            -h "127.0.0.1" `
            -p "$Port" `
            -U $superUser `
            -d postgres `
            -v ON_ERROR_STOP=1 `
            -c (
                "CREATE ROLE $quotedDatabaseUser " +
                "LOGIN PASSWORD '$escapedApplicationPassword';"
            )

        if ($LASTEXITCODE -ne 0) {
            throw (
                "No se ha podido crear el usuario " +
                "de MotorDesk."
            )
        }

        & $psql `
            -h "127.0.0.1" `
            -p "$Port" `
            -U $superUser `
            -d postgres `
            -v ON_ERROR_STOP=1 `
            -c (
                "CREATE DATABASE $quotedDatabaseName " +
                "OWNER $quotedDatabaseUser;"
            )

        if ($LASTEXITCODE -ne 0) {
            throw (
                "No se ha podido crear la base de datos " +
                "de MotorDesk."
            )
        }
    }
    finally {

        Remove-Item `
            Env:PGPASSWORD `
            -ErrorAction SilentlyContinue
    }


    # --------------------------------------------------------
    # 85% - PROGRAMDATA
    # --------------------------------------------------------

    Write-InstallStatus -Percent 85 -Message "Preparando copias de seguridad y archivos"

    New-Item `
        -ItemType Directory `
        -Path $ConfigDir `
        -Force | Out-Null

    foreach (
        $persistentDirectory in @(
            (Join-Path $ConfigDir "uploads"),
            (Join-Path $ConfigDir "backups"),
            (Join-Path $ConfigDir "logs")
        )
    ) {

        New-Item `
            -ItemType Directory `
            -Path $persistentDirectory `
            -Force | Out-Null
    }


    # El backend se ejecuta bajo la sesión del usuario que abre MotorDesk.
    # NetworkService conserva permisos para PostgreSQL y futuras tareas
    # internas que puedan necesitar ProgramData.

    Invoke-Icacls `
        -Arguments @(
            $ConfigDir,
            "/grant",
            "*S-1-5-20:(OI)(CI)M",
            "/C"
        ) `
        -ErrorMessage (
            "No se han podido preparar los datos " +
            "persistentes de MotorDesk"
        )


    # --------------------------------------------------------
    # 90% - .ENV
    # --------------------------------------------------------

    Write-InstallStatus -Percent 90 -Message "Generando la configuracion segura"

    $encodedApplicationPassword =
        [Uri]::EscapeDataString($applicationPassword)

    $databaseUrl =
        "postgresql+psycopg2://" +
        $DatabaseUser +
        ":" +
        $encodedApplicationPassword +
        "@127.0.0.1:" +
        $Port +
        "/" +
        $DatabaseName

    $configLines = @(
        "DATABASE_URL=$databaseUrl",
        "PG_DUMP_PATH=$pgDump",
        "SECRET_KEY=$secretKey",
        "ENCRYPTION_KEY=$encryptionKey",
        "ALGORITHM=HS256",
        "ACCESS_TOKEN_EXPIRE_MINUTES=360",
        # Una instalación nueva comienza protegida: el backend crea una copia
        # inmediatamente si no existe ninguna y, después, cuando transcurren
        # veinticuatro horas desde la última copia correcta.
        "BACKUP_AUTO_ENABLED=true",
        "BACKUP_INTERVAL_HOURS=24",
        "BACKUP_CHECK_MINUTES=15",
        "MOTORDESK_BACKUP_DIR=$(Join-Path $ConfigDir 'backups')",
        "MOTORDESK_NATIVE_FRONTEND=true",
        "MOTORDESK_HTTPS_ENABLED=true",
        "MOTORDESK_HTTPS_PORT=8443",
        # MotorDesk publica la interfaz para los equipos de la LAN; PostgreSQL
        # se mantiene siempre en 127.0.0.1 y nunca se expone por esta opcion.
        "MOTORDESK_BIND_HOST=0.0.0.0"
    )

    # WhatsApp solo se habilita cuando llega la configuración completa. No
    # aceptamos estados parciales: darían una pantalla de conexión que no
    # puede completar el intercambio OAuth con Meta.
    $metaValores = @(
        $MetaAppId,
        $MetaAppSecret,
        $MetaConfigId
    )

    $metaValoresPresentes = @(
        $metaValores | Where-Object {
            -not [string]::IsNullOrWhiteSpace($_)
        }
    ).Count

    if ($metaValoresPresentes -ne 0 -and $metaValoresPresentes -ne 3) {
        throw (
            "La configuración de WhatsApp de MotorDesk está incompleta. " +
            "Se requieren META_APP_ID, META_APP_SECRET y META_CONFIG_ID."
        )
    }

    if ($metaValoresPresentes -eq 3) {
        $configLines += @(
            "META_APP_ID=$MetaAppId",
            "META_APP_SECRET=$MetaAppSecret",
            "META_CONFIG_ID=$MetaConfigId"
        )
    }

    # La IA se activa solo si el instalador ha recibido una clave. Los demas
    # parametros de Groq conservan los valores seguros por defecto del backend.
    if (-not [string]::IsNullOrWhiteSpace($GroqApiKey)) {
        $configLines += "GROQ_API_KEY=$GroqApiKey"
    }

    if (-not [string]::IsNullOrWhiteSpace($GoogleOAuthClientSecret)) {
        $configLines += "GOOGLE_OAUTH_CLIENT_SECRET=$GoogleOAuthClientSecret"
    }

    $utf8WithoutBom = New-Object `
        System.Text.UTF8Encoding($false)

    [IO.File]::WriteAllText(
        $configPath,
        (
            ($configLines -join [Environment]::NewLine) +
            [Environment]::NewLine
        ),
        $utf8WithoutBom
    )

    $configCreated = $true


    # --------------------------------------------------------
    # PROTEGER .ENV
    # --------------------------------------------------------

    Write-InstallStatus -Percent 95 -Message "Protegiendo las credenciales de MotorDesk"

    $currentUserSid =
        [Security.Principal.WindowsIdentity]::GetCurrent().
            User.Value

    $currentUserAccess =
        "*${currentUserSid}:(R)"

    Invoke-Icacls `
        -Arguments @(
            $configPath,
            "/grant:r",
            "*S-1-5-18:(F)",
            "*S-1-5-32-544:(F)",
            # El backend se lanza desde la cuenta que abre MotorDesk. Todos
            # los usuarios locales pueden leer la configuración, pero nunca
            # modificarla; así un cambio de cuenta de Windows no desactiva
            # WhatsApp, IA ni la conexión a la base de datos.
            "*S-1-5-32-545:(R)",
            # NetworkService solo puede leer los secretos. Esto permite usar
            # el backend como servicio sin exponer la configuracion.
            "*S-1-5-20:(R)",
            $currentUserAccess,
            "/C"
        ) `
        -ErrorMessage (
            "No se han podido asignar permisos " +
            "al archivo de configuracion"
        )

    Invoke-Icacls `
        -Arguments @(
            $configPath,
            "/inheritance:r",
            "/C"
        ) `
        -ErrorMessage (
            "No se ha podido proteger la configuracion " +
            "privada de MotorDesk"
        )


    # --------------------------------------------------------
    # 100%
    # --------------------------------------------------------

    Write-Host ""
    Write-InstallStatus -Percent 100 -Message "Base de datos preparada correctamente"
    Write-Host ""
    Write-Host "Servicio: $ServiceName"
    Write-Host "Puerto: $Port"
    Write-Host "Base de datos: $DatabaseName"
    Write-Host "Configuracion: $configPath"
    Write-Host "Log: $LogFile"
    Write-Host ""

    if ($transcriptStarted) {
        Stop-Transcript | Out-Null
        $transcriptStarted = $false
    }

    exit 0
}
catch {

    $errorMessage = $_.Exception.Message

    try {
        Write-InstallStatus `
            -Percent 0 `
            -Message ("Error: " + $errorMessage)
    }
    catch {
        # El error original sigue siendo mas importante que un fallo al
        # actualizar la pantalla de progreso.
    }

    Write-Host ""
    Write-Host "============================================"
    Write-Host " ERROR FATAL - MOTORDesk PostgreSQL"
    Write-Host "============================================"
    Write-Host ""
    Write-Host $errorMessage
    Write-Host ""

    if ($_.ScriptStackTrace) {
        Write-Host "Traza:"
        Write-Host $_.ScriptStackTrace
        Write-Host ""
    }

    # Si llegamos a registrar el servicio durante ESTA ejecución
    # pero posteriormente fallamos, no dejamos un servicio roto.
    if ($serviceRegistered) {

        Write-Host "Revirtiendo el servicio incompleto..."

        Stop-Service `
            -Name $ServiceName `
            -Force `
            -ErrorAction SilentlyContinue

        & sc.exe delete $ServiceName | Out-Null

        $serviceRegistered = $false
    }

    # La instalacion nunca borra una ruta preexistente. Pero si esta ejecucion
    # la creo y fallo despues, la retiramos para que el usuario pueda reparar
    # o volver a ejecutar el instalador sin quedar bloqueado por restos.
    if ($configCreated -and (Test-Path -LiteralPath $configPath)) {
        Remove-Item -LiteralPath $configPath -Force -ErrorAction SilentlyContinue
    }

    if ($dataDirCreated -and (Test-Path -LiteralPath $DataDir)) {
        Remove-Item -LiteralPath $DataDir -Recurse -Force -ErrorAction SilentlyContinue
    }

    if ($installDirCreated -and (Test-Path -LiteralPath $InstallDir)) {
        Remove-Item -LiteralPath $InstallDir -Recurse -Force -ErrorAction SilentlyContinue
    }

    Remove-Item `
        Env:PGPASSWORD `
        -ErrorAction SilentlyContinue

    if ($transcriptStarted) {

        try {
            Stop-Transcript | Out-Null
        }
        catch {
            # El fallo al cerrar el log no debe ocultar
            # el error original.
        }

        $transcriptStarted = $false
    }

    exit 1
}
