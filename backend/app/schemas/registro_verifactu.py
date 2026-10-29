"""Representación segura de registros VERI*FACTU para API y auditoría."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class RegistroVerifactuResponse(BaseModel):
    id: int
    factura_id: int

    tipo_registro: str
    estado: str

    hash_registro: str
    hash_anterior: Optional[str] = None

    factura_anterior_numero: Optional[str] = None
    factura_anterior_fecha: Optional[str] = None

    codigo_respuesta: Optional[str] = None
    mensaje_error: Optional[str] = None

    intentos_envio: int

    fecha_generacion: datetime
    fecha_ultimo_intento: Optional[datetime] = None
    fecha_aceptacion: Optional[datetime] = None

    created_at: datetime

    model_config = ConfigDict(
        from_attributes=True
    )
