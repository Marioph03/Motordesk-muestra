from datetime import datetime

from pydantic import BaseModel


class CitaOperativaResponse(BaseModel):
    id: int
    fecha_inicio: datetime
    fecha_fin: datetime
    motivo: str
    estado: str
    vehiculo_descripcion: str


class OrdenOperativaResponse(BaseModel):
    id: int
    numero: str
    tipo: str
    estado: str
    descripcion_averia: str


class AusenciaOperativaResponse(BaseModel):
    id: int
    tipo: str
    fecha_inicio: datetime
    fecha_fin: datetime
    observaciones: str | None = None


class ResumenOperativoPersonalResponse(BaseModel):
    usuario_id: int
    citas: list[CitaOperativaResponse]
    ordenes: list[OrdenOperativaResponse]
    ausencias: list[AusenciaOperativaResponse]
"""Contrato del resumen de citas, órdenes y ausencias de un usuario."""
