import subprocess
import sys
import time
import urllib.error
import urllib.request
import webbrowser
import ssl
from pathlib import Path
import ctypes
import os


# El lanzador nativo siempre abre el extremo HTTPS local. Meta Embedded
# Signup rechaza HTTP y las instalaciones antiguas pueden conservar un .env
# previo; por ello no dependemos de que ese archivo active TLS correctamente.
HTTPS_PORT = 8443
BACKEND_URL = f"https://localhost:{HTTPS_PORT}"
# La edicion nativa agrupa la API bajo /backend. Esta comprobacion valida el
# backend real, no el HTML de Angular que puede responder 200 para rutas SPA.
HEALTH_URL = f"{BACKEND_URL}/backend/bootstrap/status"

BACKEND_EXE = Path(
    r"C:\Program Files\MotorDesk\Backend\MotorDeskBackend.exe"
)

BACKEND_DIR = BACKEND_EXE.parent
BACKEND_LOG = (
    Path(os.environ.get("PROGRAMDATA", r"C:\\ProgramData"))
    / "MotorDesk"
    / "logs"
    / "backend-startup.log"
)

CREATE_NO_WINDOW = 0x08000000
DETACHED_PROCESS = 0x00000008


def mostrar_error(mensaje: str) -> None:
    ctypes.windll.user32.MessageBoxW(
        0,
        mensaje,
        "MotorDesk",
        0x10,
    )


def backend_disponible() -> bool:
    try:
        # El certificado es local y el instalador lo registra como confiable
        # para el navegador. El lanzador comprueba solo disponibilidad, por
        # lo que evita depender del almacén de certificados de cada usuario.
        contexto = ssl._create_unverified_context()
        with urllib.request.urlopen(HEALTH_URL, timeout=2, context=contexto) as respuesta:
            return respuesta.status == 200
    except (urllib.error.URLError, TimeoutError, OSError):
        return False


def iniciar_backend() -> None:
    if not BACKEND_EXE.is_file():
        raise FileNotFoundError(
            f"No se encuentra el backend de MotorDesk:\n{BACKEND_EXE}"
        )

    # Un ejecutable de escritorio no tiene consola. Conservamos stdout/stderr
    # para diagnosticar fallos de importacion, base de datos o configuracion.
    BACKEND_LOG.parent.mkdir(parents=True, exist_ok=True)

    # El lanzador y el backend son dos ejecutables distintos empaquetados con
    # PyInstaller. Un ejecutable "onefile" hereda variables internas _PYI_ al
    # crear procesos hijos; si llegan al backend, PyInstaller puede creer que
    # es un hijo del mismo binario y rechazarlo por seguridad. El backend debe
    # comenzar como un proceso independiente, conservando el resto del entorno
    # de Windows (PATH, ProgramData, etc.).
    entorno_backend = {
        clave: valor
        for clave, valor in os.environ.items()
        if not clave.startswith("_PYI_")
    }

    # Forzamos la configuracion propia de la aplicacion de escritorio. Esto
    # hace que una actualizacion sobre una instalacion antigua no vuelva a
    # arrancar solamente en HTTP:8000 por valores heredados del archivo local.
    # HTTP:8000 puede mantenerse como compatibilidad LAN desde el backend,
    # pero el lanzador, el navegador y Embedded Signup usan siempre HTTPS:8443.
    entorno_backend.update(
        {
            "MOTORDESK_NATIVE_FRONTEND": "true",
            "MOTORDESK_HTTPS_ENABLED": "true",
            "MOTORDESK_HTTPS_PORT": str(HTTPS_PORT),
            # La base de datos continúa aislada en 127.0.0.1:55432, pero la
            # interfaz web sí debe escuchar en la LAN del taller para que los
            # demás equipos accedan al mismo MotorDesk sin instalar nada.
            "MOTORDESK_BIND_HOST": "0.0.0.0",
            "MOTORDESK_BACKEND_PORT": "8000",
        }
    )

    with BACKEND_LOG.open("wb") as log_file:
        subprocess.Popen(
            [str(BACKEND_EXE)],
            cwd=str(BACKEND_DIR),
            stdin=subprocess.DEVNULL,
            stdout=log_file,
            stderr=subprocess.STDOUT,
            creationflags=CREATE_NO_WINDOW | DETACHED_PROCESS,
            close_fds=True,
            env=entorno_backend,
        )


def esperar_backend(segundos: int = 240) -> bool:
    limite = time.monotonic() + segundos

    while time.monotonic() < limite:
        if backend_disponible():
            return True

        time.sleep(0.5)

    return False


def main() -> int:
    try:
        if not backend_disponible():
            iniciar_backend()

            # Una instalacion nueva puede tardar mientras PostgreSQL crea el
            # esquema completo. No se debe declarar fallo a los 30 segundos.
            if not esperar_backend():
                mostrar_error(
                    "MotorDesk no ha terminado de iniciar su servidor local "
                    "en HTTPS (puerto 8443).\n\n"
                    "La primera ejecucion o una actualizacion puede tardar hasta cuatro minutos "
                    "mientras se prepara la base de datos.\n\n"
                    "Si el problema continua, consulta:\n"
                    "C:\\ProgramData\\MotorDesk\\logs\\backend-startup.log"
                )
                return 1

        webbrowser.open(BACKEND_URL)

        return 0

    except Exception as exc:
        mostrar_error(
            "No se ha podido iniciar MotorDesk.\n\n"
            f"Detalle: {exc}"
        )
        return 1


if __name__ == "__main__":
    sys.exit(main())
