param(
    [Parameter(Mandatory = $true)]
    [string]$ConfigPath,

    [string]$IntegrationConfigPath = "",

    # Compatibilidad con ejecuciones de soporte antiguas. El Setup actual usa
    # el fichero temporal y no expone secretos como argumentos.
    [string]$MetaAppId = "",

    [string]$MetaAppSecret = "",

    [string]$MetaConfigId = "",

    # Opcional para que el actualizador sea compatible con instalaciones
    # anteriores y no altere la IA si el paquete no incluye una clave.
    [string]$GroqApiKey = "",

    [string]$GoogleOAuthClientSecret = ""
)

$ErrorActionPreference = "Stop"


function Import-IntegrationConfig {
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

# Este registro contiene solamente el motivo técnico del fallo; nunca se
# anotan parámetros, claves, tokens ni el contenido del archivo .env.
$logDir = Join-Path (Split-Path -Parent $ConfigPath) "logs"
$logFile = Join-Path $logDir "update-integrations.log"

trap {
    try {
        New-Item -ItemType Directory -Path $logDir -Force | Out-Null
        $entry = "$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') | ERROR | " +
            $_.Exception.Message + [Environment]::NewLine
        [IO.File]::AppendAllText(
            $logFile,
            $entry,
            [System.Text.UTF8Encoding]::new($false)
        )
    }
    catch {
        # El error original sigue siendo más importante que un fallo al loguear.
    }

    throw $_
}

# Se ejecuta únicamente sobre instalaciones existentes. Conserva los datos y
# actualiza la configuración local sin recrear PostgreSQL ni tocar archivos
# de los usuarios.
$valores = @($MetaAppId, $MetaAppSecret, $MetaConfigId)

$actualizarMeta = -not ($valores | Where-Object {
    [string]::IsNullOrWhiteSpace($_)
})

if (-not (Test-Path -LiteralPath $ConfigPath -PathType Leaf)) {
    throw "No se encuentra la configuración existente de MotorDesk."
}

$lineasActuales = Get-Content -LiteralPath $ConfigPath
$directorioDatos = Split-Path -Parent $ConfigPath
$directorioCopias = Join-Path $directorioDatos "backups"
$pgDumpMotorDesk = Join-Path $env:ProgramFiles "MotorDesk\PostgreSQL\bin\pg_dump.exe"

New-Item -ItemType Directory -Path $directorioCopias -Force | Out-Null

$lineasActualizadas = @(
    $lineasActuales | Where-Object {
        (
            -not $actualizarMeta -or $_ -notmatch '^META_APP_ID='
        ) -and (
            -not $actualizarMeta -or $_ -notmatch '^META_APP_SECRET='
        ) -and (
            -not $actualizarMeta -or $_ -notmatch '^META_CONFIG_ID='
        ) -and (
            [string]::IsNullOrWhiteSpace($GroqApiKey) -or
            $_ -notmatch '^GROQ_API_KEY='
        ) -and (
            [string]::IsNullOrWhiteSpace($GoogleOAuthClientSecret) -or
            $_ -notmatch '^GOOGLE_OAUTH_CLIENT_SECRET='
        ) -and (
            $_ -notmatch '^MOTORDESK_HTTPS_ENABLED='
        ) -and (
            $_ -notmatch '^MOTORDESK_HTTPS_PORT='
        ) -and (
            $_ -notmatch '^PG_DUMP_PATH='
        ) -and (
            $_ -notmatch '^MOTORDESK_BACKUP_DIR='
        ) -and (
            $_ -notmatch '^BACKUP_AUTO_ENABLED='
        ) -and (
            $_ -notmatch '^BACKUP_INTERVAL_HOURS='
        ) -and (
            $_ -notmatch '^BACKUP_CHECK_MINUTES='
        )
    }
)

$lineasNuevas = @(
    $lineasActualizadas
    "MOTORDESK_HTTPS_ENABLED=true"
    "MOTORDESK_HTTPS_PORT=8443"
    "MOTORDESK_BACKUP_DIR=$directorioCopias"
    "BACKUP_AUTO_ENABLED=true"
    "BACKUP_INTERVAL_HOURS=24"
    "BACKUP_CHECK_MINUTES=15"
)

if (Test-Path -LiteralPath $pgDumpMotorDesk -PathType Leaf) {
    $lineasNuevas += "PG_DUMP_PATH=$pgDumpMotorDesk"
}

if ($actualizarMeta) {
    $lineasNuevas += @(
        "META_APP_ID=$MetaAppId"
        "META_APP_SECRET=$MetaAppSecret"
        "META_CONFIG_ID=$MetaConfigId"
    )
}

if (-not [string]::IsNullOrWhiteSpace($GroqApiKey)) {
    $lineasNuevas += "GROQ_API_KEY=$GroqApiKey"
}

if (-not [string]::IsNullOrWhiteSpace($GoogleOAuthClientSecret)) {
    $lineasNuevas += "GOOGLE_OAUTH_CLIENT_SECRET=$GoogleOAuthClientSecret"
}

# Escribimos sobre el archivo existente en vez de renombrar un temporal. En
# algunos Windows Move-Item no puede sustituir un .env con ACL restringida,
# aunque el administrador sí pueda modificar su contenido.
[IO.File]::WriteAllLines(
    $ConfigPath,
    $lineasNuevas,
    [System.Text.UTF8Encoding]::new($false)
)

# Restablece el aislamiento de credenciales de la instalación inicial.
$usuarioActualSid = [Security.Principal.WindowsIdentity]::GetCurrent().User.Value

& icacls.exe $ConfigPath `
    "/inheritance:r" `
    "/grant:r" `
    "*S-1-5-18:(F)" `
    "*S-1-5-32-544:(F)" `
    "*S-1-5-32-545:(R)" `
    "*S-1-5-20:(R)" `
    "*${usuarioActualSid}:(R)" `
    "/C" | Out-Null

if ($LASTEXITCODE -ne 0) {
    throw "No se han podido restaurar los permisos del .env de MotorDesk."
}

Write-Host "Configuración local de MotorDesk actualizada correctamente."
