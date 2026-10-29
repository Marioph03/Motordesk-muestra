"""Rutas persistentes para ficheros generados por cada instalación.

En desarrollo usamos el directorio de trabajo del backend. En el ejecutable
nativo, los ficheros editables nunca pueden vivir dentro de ``Program Files``:
la instalación los guarda en ``C:\\ProgramData\\MotorDesk``.
"""

import os
import sys
from pathlib import Path


def directorio_datos() -> Path:
    """Devuelve la raíz que contiene los datos editables de MotorDesk."""
    if (
        getattr(sys, "frozen", False)
        or os.getenv("MOTORDESK_NATIVE_FRONTEND") == "true"
    ):
        return Path(os.environ.get("PROGRAMDATA", r"C:\\ProgramData")) / "MotorDesk"

    return Path.cwd()


def directorio_static() -> Path:
    """Devuelve la carpeta ``static`` que sirve la aplicación actual."""
    return directorio_datos() / "static"


def directorio_logos_taller() -> Path:
    """Devuelve y crea, si hace falta, la carpeta persistente de logos."""
    ruta = directorio_static() / "uploads" / "taller"
    ruta.mkdir(parents=True, exist_ok=True)
    return ruta
