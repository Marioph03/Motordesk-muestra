@echo off
setlocal

REM Compila backend, frontend, lanzador e instalador desde el código actual.
REM No almacena secretos: las integraciones se toman de las variables de
REM entorno MOTORDESK_* que estén definidas en el equipo de desarrollo.
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0installer\scripts\build-installer.ps1"

if errorlevel 1 (
    echo.
    echo La generacion del instalador ha fallado. Revisa el mensaje anterior.
    pause
    exit /b 1
)

echo.
echo Instalador generado correctamente en installer\output.
pause
