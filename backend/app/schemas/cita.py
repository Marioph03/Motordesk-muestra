"""Contratos de agenda incluyendo personal asignado y rango de reserva."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class CitaCreate(BaseModel):
    cliente_id: int
    vehiculo_id: int
    usuarios_ids: list[int] = []

    fecha_inicio: datetime
    fecha_fin: datetime

    motivo: str

    observaciones: Optional[str] = None


class CitaUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    cliente_id: Optional[int] = None
    vehiculo_id: Optional[int] = None
    usuarios_ids: list[int] | None = None

    fecha_inicio: Optional[datetime] = None
    fecha_fin: Optional[datetime] = None

    motivo: Optional[str] = None
    observaciones: Optional[str] = None

class ClienteCitaResponse(BaseModel):
    id: int
    nombre: str
    apellidos: str | None = None

    model_config = ConfigDict(from_attributes=True)


class VehiculoCitaResponse(BaseModel):
    id: int
    marca: str | None = None
    modelo: str | None = None
    matricula: str | None = None

    model_config = ConfigDict(from_attributes=True)


class UsuarioCitaResponse(BaseModel):
    id: int
    nombre: str
    apellidos: str
    rol: str

    model_config = ConfigDict(from_attributes=True)


class CitaResponse(BaseModel):
    id: int

    cliente_id: int
    vehiculo_id: int

    fecha_inicio: datetime
    fecha_fin: datetime

    motivo: str
    observaciones: Optional[str] = None

    estado: str

    orden_generada_id: Optional[int] = None

    fecha_confirmacion: datetime | None = None
    canal_confirmacion: str | None = None
    fecha_recordatorio: datetime | None = None
    canal_recordatorio: str | None = None

    fecha_reprogramacion: datetime | None = None
    fecha_inicio_anterior: datetime | None = None
    fecha_fin_anterior: datetime | None = None

    cliente: ClienteCitaResponse
    vehiculo: VehiculoCitaResponse
    usuarios_asignados: list[UsuarioCitaResponse] = []

    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(
        from_attributes=True
    )
