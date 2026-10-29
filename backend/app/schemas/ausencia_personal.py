from datetime import datetime

from pydantic import BaseModel, ConfigDict


class AusenciaPersonalCreate(BaseModel):
    usuario_id: int
    tipo: str
    fecha_inicio: datetime
    fecha_fin: datetime
    observaciones: str | None = None


class AusenciaPersonalUpdate(BaseModel):
    tipo: str | None = None
    fecha_inicio: datetime | None = None
    fecha_fin: datetime | None = None
    observaciones: str | None = None


class AusenciaPersonalResponse(BaseModel):
    id: int
    usuario_id: int
    tipo: str
    fecha_inicio: datetime
    fecha_fin: datetime
    observaciones: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(
        from_attributes=True
    )
"""Contratos de alta, edición y consulta de ausencias del personal."""
