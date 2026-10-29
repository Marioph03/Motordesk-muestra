param(
    [Parameter(Mandatory = $true)]
    [string]$SourceDir,

    [string]$InstallDir = "$env:ProgramFiles\MotorDesk\Backend",

    [string]$ServiceName = "MotorDeskBackend",

    [string]$DatabaseServiceName = "MotorDeskPostgreSQL",

    [int]$Port = 8000
)

$ErrorActionPreference = "Stop"

function Assert-Administrator {
    $identity = [Security.Principal.WindowsIdentity]::GetCurrent()
    $principal = New-Object Security.Principal.WindowsPrincipal($identity)

    if (-not $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
        throw "Este script debe ejecutarse como administrador."
    }
}

function Wait-HttpEndpoint {
    param([int]$ServerPort)

    for ($attempt = 1; $attempt -le 30; $attempt++) {
        try {
            $response = Invoke-WebRequest `
                -UseBasicParsing `
                -TimeoutSec 2 `
                -Uri "http://127.0.0.1:$ServerPort/bootstrap/status"

            if ($response.StatusCode -eq 200) {
                return
            }
        }
        catch {
            Start-Sleep -Seconds 1
        }
    }

    throw "MotorDeskBackend no ha respondido en el plazo previsto."
}

Assert-Administrator

if (-not (Test-Path -LiteralPath $SourceDir -PathType Container)) {
    throw "No existe la carpeta compilada del backend: $SourceDir"
}

$sourceExe = Join-Path $SourceDir "MotorDeskBackend.exe"

if (-not (Test-Path -LiteralPath $sourceExe -PathType Leaf)) {
    throw "No se encontro MotorDeskBackend.exe en: $SourceDir"
}

if (Get-Service -Name $ServiceName -ErrorAction SilentlyContinue) {
    throw "Ya existe el servicio '$ServiceName'. No se sobrescribira."
}

if (-not (Get-Service -Name $DatabaseServiceName -ErrorAction SilentlyContinue)) {
    throw "No existe el servicio de base de datos '$DatabaseServiceName'."
}

if (Get-NetTCPConnection -State Listen -LocalPort $Port -ErrorAction SilentlyContinue) {
    throw "El puerto local $Port ya esta en uso."
}

if (Test-Path -LiteralPath $InstallDir) {
    throw "La ruta de backend ya existe y no se sobrescribira: $InstallDir"
}

Write-Host "[75%] Instalando archivos del backend..."
New-Item -ItemType Directory -Path $InstallDir -Force | Out-Null

# Robocopy conserva la estructura generada por PyInstaller, incluyendo
# _internal y sus DLL. Sus codigos 0..7 indican exito con distintas acciones.
& robocopy.exe $SourceDir $InstallDir /E /COPY:DAT /R:2 /W:1 | Out-Null

if ($LASTEXITCODE -gt 7) {
    throw "No se han podido copiar los archivos de MotorDesk (robocopy $LASTEXITCODE)."
}

$backendExe = Join-Path $InstallDir "MotorDeskBackend.exe"

# Protegemos primero la carpeta raiz sin retirar prematuramente los permisos
# necesarios para completar la instalacion.

& icacls.exe $InstallDir `
    /grant:r "*S-1-5-18:(OI)(CI)F" `
    "*S-1-5-32-544:(OI)(CI)F" `
    "*S-1-5-20:(OI)(CI)RX" `
    /T /C | Out-Null

if ($LASTEXITCODE -ne 0) {
    throw "No se han podido asignar los permisos del backend."
}

# Una vez asignados los permisos explícitos necesarios, podemos retirar
# la herencia sin dejarnos fuera de la carpeta durante la operación.
& icacls.exe $InstallDir /inheritance:r /T /C | Out-Null

if ($LASTEXITCODE -ne 0) {
    throw "No se ha podido desactivar la herencia de permisos del backend."
}

Write-Host "[80%] Registrando el servicio MotorDeskBackend..."
& sc.exe create $ServiceName `
    binPath= ('"' + $backendExe + '"') `
    start= auto `
    obj= "NT AUTHORITY\NetworkService" `
    depend= $DatabaseServiceName | Out-Null

if ($LASTEXITCODE -ne 0) {
    throw "No se ha podido registrar el servicio '$ServiceName'."
}

try {
    & sc.exe description $ServiceName `
        "API local de MotorDesk. Depende de MotorDeskPostgreSQL." | Out-Null

    Start-Service -Name $ServiceName
    Wait-HttpEndpoint -ServerPort $Port
}
catch {
    Stop-Service -Name $ServiceName -Force -ErrorAction SilentlyContinue
    & sc.exe delete $ServiceName | Out-Null
    throw
}

Write-Host "[90%] MotorDeskBackend instalado y verificado correctamente."
