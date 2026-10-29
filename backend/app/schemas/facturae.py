"""Contratos de los datos destinatarios de Facturae."""

from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field, field_validator


class FacturaeDestinoUpdate(BaseModel):
    nombre: str = Field(min_length=1, max_length=255)
    nif: str = Field(min_length=1, max_length=20)
    direccion: str | None = Field(default=None, max_length=255)
    codigo_postal: str | None = Field(default=None, max_length=10)
    ciudad: str | None = Field(default=None, max_length=100)
    provincia: str | None = Field(default=None, max_length=100)
    oficina_contable: str = Field(min_length=1, max_length=10)
    organo_gestor: str = Field(min_length=1, max_length=10)
    unidad_tramitadora: str = Field(min_length=1, max_length=10)
    expediente: str | None = Field(default=None, max_length=100)
    referencia_contrato: str | None = Field(default=None, max_length=100)
    referencia_receptor: str | None = Field(default=None, max_length=100)
    observaciones: str | None = None

    @field_validator("nif", "oficina_contable", "organo_gestor", "unidad_tramitadora", mode="before")
    @classmethod
    def normalizar_codigo(cls, value: str) -> str:
        return value.strip().upper() if isinstance(value, str) else value


class FacturaeDestinoResponse(FacturaeDestinoUpdate):
    id: int
    factura_id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
