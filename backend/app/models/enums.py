from enum import Enum


class EstadoReparacion(str, Enum):
    PENDIENTE = "Pendiente"
    EN_PROCESO = "En proceso"
    FINALIZADA = "Finalizada"
    ENTREGADA = "Entregada"
"""Enumeraciones transversales reutilizadas por varios módulos de negocio."""
