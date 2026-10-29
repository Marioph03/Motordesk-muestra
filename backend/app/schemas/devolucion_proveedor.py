from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class LineaDevolucionProveedorCreate(BaseModel):
    linea_albaran_id: int
    articulo_stock_id: int
    cantidad: Decimal = Field(gt=0)


class LineaDevolucionProveedorResponse(LineaDevolucionProveedorCreate):
    id: int
    model_config = ConfigDict(from_attributes=True)


class DevolucionProveedorCreate(BaseModel):
    proveedor_id: int
    albaran_origen_id: int
    motivo: str
    observaciones: str | None = None
    lineas: list[LineaDevolucionProveedorCreate]


class ResolverDevolucionRequest(BaseModel):
    resolucion: str


class DevolucionProveedorResponse(BaseModel):
    id: int
    numero: str
    proveedor_id: int
    albaran_origen_id: int
    estado: str
    resolucion: str
    motivo: str
    observaciones: str | None
    fecha: datetime
    lineas: list[LineaDevolucionProveedorResponse] = []
    model_config = ConfigDict(from_attributes=True)
"""Contratos de devolución a proveedor y sus líneas de mercancía."""
