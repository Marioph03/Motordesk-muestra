<#
.SYNOPSIS
    Configura un puesto cliente para acceder con HTTPS al MotorDesk local.

.DESCRIPTION
    Descarga únicamente la CA pública del servidor, la instala en el almacén
    de confianza de Windows y asocia motordesk.lan a la IP privada indicada.
    No instala MotorDesk, PostgreSQL ni copia datos del taller.
#>

param(
    [Parameter(Mandatory = $true)]
    [ValidatePattern('^\d{1,3}(\.\d{1,3}){3}$')]
    [string]$ServerIp,

    [string]$ServerName = "motordesk.lan"
)

$ErrorActionPreference = "Stop"

function Test-Administrator {
    $identity = [Security.Principal.WindowsIdentity]::GetCurrent()
    $principal = New-Object Security.Principal.WindowsPrincipal($identity)
    return $principal.IsInRole(
        [Security.Principal.WindowsBuiltInRole]::Administrator
    )
}

if (-not (Test-Administrator)) {
    $arguments = @(
        "-NoProfile",
        "-ExecutionPolicy", "Bypass",
        "-File", ('"{0}"' -f $PSCommandPath),
        "-ServerIp", $ServerIp,
        "-ServerName", $ServerName
    )

    $process = Start-Process `
        -FilePath "$env:WINDIR\System32\WindowsPowerShell\v1.0\powershell.exe" `
        -ArgumentList $arguments `
        -Verb RunAs `
        -Wait `
        -PassThru

    exit $process.ExitCode
}

$address = $null
if (-not [Net.IPAddress]::TryParse($ServerIp, [ref]$address)) {
    throw "La dirección IP del servidor no es válida: $ServerIp"
}

$downloadPath = Join-Path $env:TEMP "motordesk-local-ca.cer"
$certificateUrl = "http://${ServerIp}:8000/motordesk-ca.cer"

try {
    Write-Host "Descargando el certificado público de MotorDesk..."
    Invoke-WebRequest `
        -UseBasicParsing `
        -Uri $certificateUrl `
        -OutFile $downloadPath

    if (-not (Test-Path -LiteralPath $downloadPath -PathType Leaf)) {
        throw "No se ha podido descargar el certificado local."
    }

    Write-Host "Instalando la CA local en Windows..."
    & certutil.exe -addstore -f Root $downloadPath | Out-Null
    if ($LASTEXITCODE -ne 0) {
        throw "Windows no ha podido instalar el certificado de confianza."
    }

    $hostsPath = Join-Path $env:WINDIR "System32\drivers\etc\hosts"
    $lineas = @(Get-Content -LiteralPath $hostsPath -ErrorAction Stop)
    $nombreEscapado = [Regex]::Escape($ServerName)
    $patronAnterior = "(?i)^\s*\d{1,3}(?:\.\d{1,3}){3}\s+$nombreEscapado(?:\s|$)"
    $lineasActualizadas = @(
        $lineas | Where-Object { $_ -notmatch $patronAnterior }
    )
    $lineasActualizadas += "$ServerIp`t$ServerName # MotorDesk"

    Set-Content `
        -LiteralPath $hostsPath `
        -Value $lineasActualizadas `
        -Encoding ASCII

    Clear-DnsClientCache -ErrorAction SilentlyContinue

    Write-Host "Configuración finalizada correctamente."
    Write-Host "Abre: https://${ServerName}:8443"
}
finally {
    Remove-Item -LiteralPath $downloadPath -Force -ErrorAction SilentlyContinue
}
