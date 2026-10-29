<#!
.SYNOPSIS
    Genera un instalador de MotorDesk exclusivamente a partir del código
    actual del repositorio.

.DESCRIPTION
    Este es el único comando de empaquetado que se debe usar antes de
    distribuir MotorDesk. Borra únicamente artefactos generados y vuelve a
    crear, en este orden: backend PyInstaller, frontend Angular, lanzador y
    finalmente el instalador de Inno Setup.

    Así se evita que un Setup nuevo copie accidentalmente un frontend o un
    backend compilado días antes. La versión por defecto incorpora la fecha y
    hora del empaquetado, por lo que Windows e Inno Setup reconocen cada build
    como una actualización distinta.
#>
[CmdletBinding()]
param(
    [string]$Version,
    [string]$PythonPath = "",
    [switch]$SkipDependencyInstall,
    [switch]$ReuseBuildArtifacts,
    # Solo para builds de desarrollo que deliberadamente no distribuyen las
    # integraciones. Un instalador para talleres no debe usar este modificador.
    [switch]$AllowWithoutIntegrations
)

$ErrorActionPreference = "Stop"

$Root = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
$BackendDir = Join-Path $Root "backend"
$FrontendDir = Join-Path $Root "frontend"
$InstallerDir = Join-Path $Root "installer"

function Import-OptionalIntegrationSettings {
    <#
    Las credenciales de desarrollo se guardan en backend/.env, que no viaja
    al repositorio. Para evitar una build accidental sin WhatsApp o IA,
    copiamos solo los valores de integración al entorno de ESTE proceso de
    compilación. Las variables que el operador haya definido en Windows
    mantienen prioridad y nunca se escriben en pantalla.
    #>
    $envFile = Join-Path $BackendDir ".env"
    if (-not (Test-Path -LiteralPath $envFile -PathType Leaf)) {
        return
    }

    $values = @{}
    foreach ($line in Get-Content -LiteralPath $envFile) {
        $text = $line.Trim()
        if ($text -match '^(?<key>[A-Za-z_][A-Za-z0-9_]*)=(?<value>.*)$') {
            $values[$Matches.key] = $Matches.value.Trim().Trim('"').Trim("'")
        }
    }

    $mapping = @{
        "MOTORDESK_META_APP_ID" = "META_APP_ID"
        "MOTORDESK_META_APP_SECRET" = "META_APP_SECRET"
        "MOTORDESK_META_CONFIG_ID" = "META_CONFIG_ID"
        "MOTORDESK_GROQ_API_KEY" = "GROQ_API_KEY"
        "MOTORDESK_GOOGLE_OAUTH_CLIENT_SECRET" = "GOOGLE_OAUTH_CLIENT_SECRET"
    }

    foreach ($target in $mapping.Keys) {
        if (
            [string]::IsNullOrWhiteSpace([Environment]::GetEnvironmentVariable($target)) -and
            -not [string]::IsNullOrWhiteSpace($values[$mapping[$target]])
        ) {
            [Environment]::SetEnvironmentVariable(
                $target,
                $values[$mapping[$target]],
                "Process"
            )
        }
    }

    # El Config ID no es secreto y coincide con el valor por defecto del
    # backend. Garantiza que una build use Embedded Signup aunque el .env de
    # desarrollo no lo declare de forma explícita.
    if ([string]::IsNullOrWhiteSpace(
        [Environment]::GetEnvironmentVariable("MOTORDESK_META_CONFIG_ID")
    )) {
        [Environment]::SetEnvironmentVariable(
            "MOTORDESK_META_CONFIG_ID",
            "1547065099596140",
            "Process"
        )
    }
}

Import-OptionalIntegrationSettings

if ([string]::IsNullOrWhiteSpace($Version)) {
    $Version = Get-Date -Format "yyyy.M.d.HHmm"
}

if ($Version -notmatch '^\d+(\.\d+){1,3}$') {
    throw "La versión '$Version' debe contener entre dos y cuatro grupos numéricos, por ejemplo 2026.9.11.1030."
}

if ([string]::IsNullOrWhiteSpace($PythonPath)) {
    $PythonPath = Join-Path $Root ".venv\Scripts\python.exe"
}

if (-not (Test-Path -LiteralPath $PythonPath -PathType Leaf)) {
    throw "No se encuentra Python para empaquetar: $PythonPath"
}

function Get-InnoSetupCompiler {
    # El operador de asignación desempaqueta una colección con un único
    # elemento. Conservamos explícitamente el array: indexar una cadena
    # devolvería solo su primer carácter ("C"), no la ruta de ISCC.exe.
    $candidatos = @(
        @(
            (Join-Path ${env:ProgramFiles(x86)} "Inno Setup 6\ISCC.exe"),
            (Join-Path $env:ProgramFiles "Inno Setup 6\ISCC.exe")
        ) | Where-Object { $_ -and (Test-Path -LiteralPath $_ -PathType Leaf) }
    )

    if ($candidatos.Count -gt 0) {
        return [string]$candidatos[0]
    }

    $comando = Get-Command "ISCC.exe" -ErrorAction SilentlyContinue
    if ($comando) {
        return $comando.Source
    }

    throw "No se encontró ISCC.exe. Instala Inno Setup 6 antes de generar el instalador."
}

function Invoke-Checked {
    param(
        [string]$Step,
        [scriptblock]$Action
    )

    Write-Host "`n==> $Step" -ForegroundColor Cyan
    & $Action
    if ($LASTEXITCODE -ne 0) {
        throw "$Step terminó con código $LASTEXITCODE."
    }
}

function Remove-BuildOutput {
    param([string]$Path)

    if (Test-Path -LiteralPath $Path) {
        Remove-Item -LiteralPath $Path -Force -Recurse
    }
}

$requiredFiles = @(
    (Join-Path $BackendDir "MotorDeskBackend.spec"),
    (Join-Path $BackendDir "run_motordesk.py"),
    (Join-Path $FrontendDir "package.json"),
    (Join-Path $Root "MotorDesk.spec"),
    (Join-Path $Root "MotorDeskClientConfig.spec"),
    (Join-Path $Root "client_setup\motordesk_client_setup.py"),
    (Join-Path $InstallerDir "MotorDesk.iss"),
    (Join-Path $InstallerDir "dependencies\postgresql-17.11-1-windows-x64-binaries.zip"),
    (Join-Path $InstallerDir "dependencies\vc_redist.x64.exe")
)

foreach ($file in $requiredFiles) {
    if (-not (Test-Path -LiteralPath $file -PathType Leaf)) {
        throw "Falta un archivo necesario para el instalador: $file"
    }
}

$iscc = Get-InnoSetupCompiler

 $integracionesRequeridas = @(
    "MOTORDESK_META_APP_ID",
    "MOTORDESK_META_APP_SECRET",
    "MOTORDESK_META_CONFIG_ID",
    "MOTORDESK_GROQ_API_KEY",
    "MOTORDESK_GOOGLE_OAUTH_CLIENT_SECRET"
)

$integracionesAusentes = @(
    $integracionesRequeridas | Where-Object {
        [string]::IsNullOrWhiteSpace(
            [Environment]::GetEnvironmentVariable($_)
        )
    }
)

if ($integracionesAusentes.Count -gt 0) {
    if ($AllowWithoutIntegrations) {
        Write-Warning (
            "Build de desarrollo sin integraciones: " +
            ($integracionesAusentes -join ', ')
        )
    }
    else {
        throw (
            "No se generará un instalador incompleto. Faltan: " +
            ($integracionesAusentes -join ', ') +
            ". Define las variables MOTORDESK_* antes de compilar."
        )
    }
}

$integrationPayloadPath = Join-Path $InstallerDir "generated\installer-integrations.env"

function Write-IntegrationPayload {
    # Este fichero existe solo durante la invocación de Inno Setup. Mantiene
    # las claves fuera de argumentos de línea de comandos y se elimina en el
    # bloque finally inferior, incluso ante un fallo de compilación.
    $payloadDir = Split-Path -Parent $integrationPayloadPath
    New-Item -ItemType Directory -Force -Path $payloadDir | Out-Null

    $payload = @(
        "META_APP_ID=$([Environment]::GetEnvironmentVariable('MOTORDESK_META_APP_ID'))",
        "META_APP_SECRET=$([Environment]::GetEnvironmentVariable('MOTORDESK_META_APP_SECRET'))",
        "META_CONFIG_ID=$([Environment]::GetEnvironmentVariable('MOTORDESK_META_CONFIG_ID'))",
        "GROQ_API_KEY=$([Environment]::GetEnvironmentVariable('MOTORDESK_GROQ_API_KEY'))",
        "GOOGLE_OAUTH_CLIENT_SECRET=$([Environment]::GetEnvironmentVariable('MOTORDESK_GOOGLE_OAUTH_CLIENT_SECRET'))"
    )

    [IO.File]::WriteAllLines(
        $integrationPayloadPath,
        $payload,
        [System.Text.UTF8Encoding]::new($false)
    )
}

Write-Host "MotorDesk: compilación limpia de la versión $Version" -ForegroundColor Green

# Solo se eliminan salidas reproducibles. Nunca toca código fuente, .env,
# backups, base de datos ni archivos de usuario.
if (-not $ReuseBuildArtifacts) {
    Remove-BuildOutput (Join-Path $BackendDir "build")
    Remove-BuildOutput (Join-Path $BackendDir "dist")
    Remove-BuildOutput (Join-Path $FrontendDir "dist")
    Remove-BuildOutput (Join-Path $Root "build")
    Remove-BuildOutput (Join-Path $Root "dist")
}
Remove-BuildOutput (Join-Path $InstallerDir "output")
New-Item -ItemType Directory -Force -Path (Join-Path $InstallerDir "output") | Out-Null

if (-not $ReuseBuildArtifacts -and -not $SkipDependencyInstall) {
    Invoke-Checked "Actualizando dependencias Python" {
        & $PythonPath -m pip install -r (Join-Path $BackendDir "requirements.txt")
    }

    Invoke-Checked "Comprobando PyInstaller" {
        & $PythonPath -m pip install "pyinstaller==6.22.2"
    }

    Invoke-Checked "Instalando dependencias Angular" {
        Push-Location $FrontendDir
        try {
            $env:INIT_CWD = $FrontendDir
            & npm.cmd ci
        }
        finally { Pop-Location }
    }
}

if (-not $ReuseBuildArtifacts) {
Invoke-Checked "Empaquetando backend" {
    Push-Location $BackendDir
    try { & $PythonPath -m PyInstaller --noconfirm --clean .\MotorDeskBackend.spec }
    finally { Pop-Location }
}

Invoke-Checked "Compilando frontend" {
    Push-Location $FrontendDir
    try {
        $env:INIT_CWD = $FrontendDir
        & npm.cmd run build
    }
    finally { Pop-Location }
}

Invoke-Checked "Empaquetando lanzador" {
    Push-Location $Root
    try { & $PythonPath -m PyInstaller --noconfirm --clean .\MotorDesk.spec }
    finally { Pop-Location }
}

Invoke-Checked "Empaquetando configurador de puestos cliente" {
    Push-Location $Root
    try { & $PythonPath -m PyInstaller --noconfirm --clean .\MotorDeskClientConfig.spec }
    finally { Pop-Location }
}
}

$artefactosEsperados = @(
    (Join-Path $BackendDir "dist\MotorDeskBackend\MotorDeskBackend.exe"),
    (Join-Path $FrontendDir "dist\frontend\browser\index.html"),
    (Join-Path $Root "dist\MotorDesk\MotorDesk.exe"),
    (Join-Path $Root "dist\MotorDesk-Configurar-Cliente.exe")
)

foreach ($artefacto in $artefactosEsperados) {
    if (-not (Test-Path -LiteralPath $artefacto -PathType Leaf)) {
        throw "Falta el artefacto necesario para Inno Setup: $artefacto"
    }
}

Write-IntegrationPayload
try {
    Invoke-Checked "Generando instalador Inno Setup" {
        Push-Location $InstallerDir
        try { & $iscc "/DMyAppVersion=$Version" .\MotorDesk.iss }
        finally { Pop-Location }
    }
}
finally {
    Remove-Item -LiteralPath $integrationPayloadPath -Force -ErrorAction SilentlyContinue
}

$setupPath = Join-Path $InstallerDir "output\MotorDesk-Setup-$Version.exe"
if (-not (Test-Path -LiteralPath $setupPath -PathType Leaf)) {
    throw "Inno Setup no generó el instalador esperado: $setupPath"
}

Write-Host "`nInstalador generado correctamente:" -ForegroundColor Green
Write-Host $setupPath
