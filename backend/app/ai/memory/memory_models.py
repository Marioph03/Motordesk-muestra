from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class MensajeMemoria(BaseModel):

    rol: str

    contenido: str

    creada_en: str = Field(
        default_factory=lambda:
            datetime.utcnow().isoformat()
    )


class ContextoConversacion(BaseModel):

    usuario_id: int

    mensajes: list[MensajeMemoria] = Field(
        default_factory=list
    )

    cliente_id: int | None = None

    vehiculo_id: int | None = None

    orden_id: int | None = None

    factura_id: int | None = None

    cita_id: int | None = None

    matricula: str | None = None

    actualizado_en: str = Field(
        default_factory=lambda:
            datetime.utcnow().isoformat()
    )

    metadata: dict[str, Any] = Field(
        default_factory=dict
    )
"""Modelos de mensajes y metadatos almacenados temporalmente por la IA."""
