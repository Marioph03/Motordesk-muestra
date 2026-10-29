"""Contratos de acciones de IA que requieren confirmación explícita del usuario."""

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class EstadoAccion(str, Enum):
    """Ciclo de vida de una propuesta de modificación individual."""


    PENDIENTE = "PENDIENTE"

    CONFIRMADA = "CONFIRMADA"

    EJECUTADA = "EJECUTADA"

    CANCELADA = "CANCELADA"

    EXPIRADA = "EXPIRADA"

    ERROR = "ERROR"


class TipoAccion(str, Enum):
    """Operaciones mutables expuestas deliberadamente a MotorDesk AI."""


    CREAR_CLIENTE = "CREAR_CLIENTE"

    CREAR_VEHICULO = "CREAR_VEHICULO"

    CREAR_CITA = "CREAR_CITA"

    CREAR_ORDEN = "CREAR_ORDEN"

    AJUSTAR_STOCK = "AJUSTAR_STOCK"

    CREAR_PEDIDO_COMPRA = "CREAR_PEDIDO_COMPRA"


class AccionPendiente(BaseModel):
    """Propuesta inmutable hasta su confirmación por el usuario propietario."""


    id: str

    tipo: TipoAccion

    estado: EstadoAccion = (
        EstadoAccion.PENDIENTE
    )

    datos: dict[str, Any] = Field(
        default_factory=dict
    )

    resumen: str

    usuario_id: int | None = None

    creada_en: str

    confirmada_en: str | None = None

    ejecutada_en: str | None = None

    resultado: dict[str, Any] | None = None
