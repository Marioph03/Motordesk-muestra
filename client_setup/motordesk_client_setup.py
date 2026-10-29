"""Configurador gráfico de un puesto cliente de MotorDesk.

Este ejecutable no instala MotorDesk ni PostgreSQL. Solo incorpora la CA
pública del servidor seleccionado en Windows y asocia ``motordesk.lan`` a su
IP local para que el navegador pueda abrir HTTPS sin advertencias.
"""

from __future__ import annotations

import ctypes
import ipaddress
import os
import socket
import subprocess
import sys
import tempfile
import urllib.error
import urllib.request
import webbrowser
from pathlib import Path


SERVER_NAME = "motordesk.lan"
CREATE_NO_WINDOW = 0x08000000


def mostrar_mensaje(titulo: str, mensaje: str, es_error: bool = False) -> None:
    """Muestra un mensaje nativo sin depender de bibliotecas externas."""
    tipo = 0x10 if es_error else 0x40
    ctypes.windll.user32.MessageBoxW(None, mensaje, titulo, tipo)


def es_administrador() -> bool:
    """Indica si el proceso tiene permiso para modificar Windows."""
    try:
        return bool(ctypes.windll.shell32.IsUserAnAdmin())
    except AttributeError:
        return False


def validar_ip(valor: str) -> str:
    """Valida una IPv4 privada del servidor, sin aceptar texto arbitrario."""
    try:
        direccion = ipaddress.ip_address(valor.strip())
    except ValueError as exc:
        raise ValueError("Introduce una dirección IPv4 válida.") from exc

    if not isinstance(direccion, ipaddress.IPv4Address) or not direccion.is_private:
        raise ValueError("La dirección debe ser una IPv4 privada de la red local.")

    return str(direccion)


def actualizar_hosts(ip_servidor: str) -> None:
    """Asocia el nombre local estable al servidor indicado de forma idempotente."""
    hosts = Path(os.environ["WINDIR"]) / "System32" / "drivers" / "etc" / "hosts"
    lineas = hosts.read_text(encoding="ascii", errors="ignore").splitlines()
    nombre = SERVER_NAME.lower()
    filtradas = [
        linea
        for linea in lineas
        if nombre not in linea.lower().split("#", 1)[0].split()
    ]
    filtradas.append(f"{ip_servidor}\t{SERVER_NAME}\t# MotorDesk")
    hosts.write_text("\r\n".join(filtradas) + "\r\n", encoding="ascii")


def descargar_e_instalar_certificado(ip_servidor: str) -> None:
    """Obtiene la CA pública del servidor e incorpórala a Windows."""
    url = f"http://{ip_servidor}:8000/motordesk-ca.cer"
    descriptor, ruta_temporal = tempfile.mkstemp(suffix=".cer", prefix="motordesk-ca-")
    os.close(descriptor)
    certificado = Path(ruta_temporal)

    try:
        try:
            with urllib.request.urlopen(url, timeout=15) as respuesta:
                certificado.write_bytes(respuesta.read())
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            raise RuntimeError(
                "No se ha podido descargar el certificado del servidor. "
                "Comprueba que MotorDesk está abierto y que la IP es correcta."
            ) from exc

        resultado = subprocess.run(
            ["certutil.exe", "-addstore", "-f", "Root", str(certificado)],
            capture_output=True,
            text=True,
            check=False,
        )
        if resultado.returncode != 0:
            raise RuntimeError(
                "Windows no ha podido instalar el certificado de MotorDesk."
            )
    finally:
        certificado.unlink(missing_ok=True)


def configurar_puesto(ip_servidor: str) -> None:
    """Completa la configuración privilegiada y comprueba HTTPS al final."""
    descargar_e_instalar_certificado(ip_servidor)
    actualizar_hosts(ip_servidor)
    subprocess.run(["ipconfig", "/flushdns"], capture_output=True, check=False)

    try:
        socket.gethostbyname(SERVER_NAME)
    except OSError as exc:
        raise RuntimeError("No se ha podido registrar motordesk.lan en este equipo.") from exc


def ejecutar_configuracion(ip_servidor: str) -> int:
    """Ejecuta la operación elevada y comunica un resultado comprensible."""
    try:
        configurar_puesto(validar_ip(ip_servidor))
    except Exception as exc:  # El detalle no contiene secretos.
        mostrar_mensaje("MotorDesk", str(exc), es_error=True)
        return 1

    mostrar_mensaje(
        "MotorDesk",
        "Este equipo ya está preparado.\n\n"
        "A partir de ahora abre:\nhttps://motordesk.lan:8443",
    )
    webbrowser.open("https://motordesk.lan:8443")
    return 0


def elevar(ip_servidor: str) -> None:
    """Relanza el mismo ejecutable con UAC únicamente tras pedir la IP."""
    parametros = f'--configurar "{ip_servidor}"'
    resultado = ctypes.windll.shell32.ShellExecuteW(
        None,
        "runas",
        sys.executable,
        parametros,
        None,
        1,
    )
    if resultado <= 32:
        mostrar_mensaje(
            "MotorDesk",
            "Se necesita autorización de administrador para configurar el certificado.",
            es_error=True,
        )


def pedir_ip_servidor() -> str | None:
    """Abre un diálogo WPF, disponible en las ediciones soportadas de Windows."""
    script = r'''
Add-Type -AssemblyName PresentationFramework
[xml]$xaml = @'
<Window xmlns="http://schemas.microsoft.com/winfx/2006/xaml/presentation"
        Title="MotorDesk - Configurar este equipo" Height="265" Width="510"
        WindowStartupLocation="CenterScreen" ResizeMode="NoResize">
  <Grid Margin="24">
    <Grid.RowDefinitions>
      <RowDefinition Height="Auto" />
      <RowDefinition Height="Auto" />
      <RowDefinition Height="Auto" />
      <RowDefinition Height="Auto" />
      <RowDefinition Height="*" />
    </Grid.RowDefinitions>
    <TextBlock Grid.Row="0" FontSize="18" FontWeight="SemiBold"
               Text="Conectar este equipo a MotorDesk" />
    <TextBlock Grid.Row="1" Margin="0,12,0,18" TextWrapping="Wrap"
               Text="Introduce la IP del ordenador servidor. Se instalará el certificado local para abrir MotorDesk sin avisos de seguridad." />
    <TextBlock Grid.Row="2" Text="IP del servidor MotorDesk" />
    <TextBox Grid.Row="3" Name="ServerIp" Margin="0,5,0,0" MinWidth="420" />
    <Button Grid.Row="4" Name="ContinueButton" Content="Configurar este equipo"
            HorizontalAlignment="Right" VerticalAlignment="Bottom" Width="175"
            IsDefault="True" />
  </Grid>
</Window>
'@
$reader = New-Object System.Xml.XmlNodeReader $xaml
$window = [Windows.Markup.XamlReader]::Load($reader)
$input = $window.FindName('ServerIp')
$button = $window.FindName('ContinueButton')
$button.Add_Click({ $window.DialogResult = $true })
$input.Focus() | Out-Null
if ($window.ShowDialog()) { [Console]::Write($input.Text) }
'''
    resultado = subprocess.run(
        [
            os.path.join(os.environ["WINDIR"], "System32", "WindowsPowerShell", "v1.0", "powershell.exe"),
            "-NoProfile",
            "-WindowStyle", "Hidden",
            "-Command",
            script,
        ],
        capture_output=True,
        text=True,
        check=False,
        creationflags=CREATE_NO_WINDOW,
    )
    return resultado.stdout.strip() or None


def main() -> int:
    if len(sys.argv) == 3 and sys.argv[1] == "--configurar":
        if not es_administrador():
            mostrar_mensaje(
                "MotorDesk",
                "Hace falta permiso de administrador.",
                es_error=True,
            )
            return 1
        return ejecutar_configuracion(sys.argv[2])

    ip_servidor = pedir_ip_servidor()
    if ip_servidor is None:
        return 0

    try:
        elevar(validar_ip(ip_servidor))
    except ValueError as exc:
        mostrar_mensaje("MotorDesk", str(exc), es_error=True)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
