"""Compatibilidad entre nombres históricos de rol y el sistema de permisos."""

from enum import Enum


class RolUsuario(str, Enum):
    ADMINISTRADOR = "Administrador"
    MECANICO = "Mecanico"
    RECEPCION = "Recepcion"


def normalizar_nombre_rol(nombre: str | RolUsuario | None) -> str:
    """Convierte los nombres heredados de Usuario.rol al nombre del rol."""

    valor = (
        nombre.value
        if isinstance(nombre, RolUsuario)
        else (nombre or "")
    )
    valor = valor.strip().upper()

    equivalencias = {
        "ADMINISTRADOR": "ADMIN",
        "ADMIN": "ADMIN",
        "MECANICO": "MECANICO",
        "RECEPCION": "RECEPCION",
        "ALMACEN": "ALMACEN",
    }

    return equivalencias.get(valor, valor)
