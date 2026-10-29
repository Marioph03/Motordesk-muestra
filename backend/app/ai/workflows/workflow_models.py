"""Contratos de operaciones IA compuestas por varios pasos dependientes."""

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class EstadoWorkflow(str, Enum):
    """Ciclo de vida global de un workflow pendiente de confirmación."""


    PENDIENTE = "PENDIENTE"

    EJECUTANDO = "EJECUTANDO"

    COMPLETADO = "COMPLETADO"

    CANCELADO = "CANCELADO"

    EXPIRADO = "EXPIRADO"

    ERROR = "ERROR"


class EstadoPasoWorkflow(str, Enum):

    PENDIENTE = "PENDIENTE"

    EJECUTANDO = "EJECUTANDO"

    COMPLETADO = "COMPLETADO"

    ERROR = "ERROR"

    OMITIDO = "OMITIDO"


class TipoWorkflow(str, Enum):
    """Flujos de negocio complejos permitidos por la IA."""


    ALTA_CLIENTE_VEHICULO = (
        "ALTA_CLIENTE_VEHICULO"
    )

    ALTA_CLIENTE_VEHICULO_CITA = (
        "ALTA_CLIENTE_VEHICULO_CITA"
    )

    ALTA_CLIENTE_VEHICULO_ORDEN = (
        "ALTA_CLIENTE_VEHICULO_ORDEN"
    )
    
class TipoPasoWorkflow(str, Enum):

    CREAR_CLIENTE = "CREAR_CLIENTE"

    CREAR_VEHICULO = "CREAR_VEHICULO"

    CREAR_CITA = "CREAR_CITA"

    CREAR_ORDEN = "CREAR_ORDEN"


class PasoWorkflow(BaseModel):
    """Paso declarativo ejecutado en orden dentro de una transacción controlada."""


    orden: int

    tipo: TipoPasoWorkflow

    estado: EstadoPasoWorkflow = (
        EstadoPasoWorkflow.PENDIENTE
    )

    datos: dict[str, Any] = Field(
        default_factory=dict
    )

    resumen: str

    resultado: dict[str, Any] | None = None

    error: str | None = None


class WorkflowPendiente(BaseModel):
    """Workflow asociado a un usuario; se confirma sin delegar un 'sí' al modelo."""


    id: str

    tipo: TipoWorkflow

    estado: EstadoWorkflow = (
        EstadoWorkflow.PENDIENTE
    )

    usuario_id: int

    resumen: str

    pasos: list[PasoWorkflow] = Field(
        default_factory=list
    )

    creada_en: str

    ejecutada_en: str | None = None

    resultado: dict[str, Any] | None = None

    error: str | None = None
