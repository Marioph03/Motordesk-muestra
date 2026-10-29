"""Contratos de albaranes de venta de recambios."""

from datetime import date
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.cliente import ClienteSelect


class LineaAlbaranVentaCreate(BaseModel):
    articulo_stock_id: int
    cantidad: Decimal = Field(gt=0)
    precio_unitario: Decimal | None = Field(default=None, ge=0)
    descuento_porcentaje: Decimal = Field(default=Decimal("0"), ge=0, le=100)


class LineaAlbaranVentaResponse(BaseModel):
    id: int
    articulo_stock_id: int
    referencia: str
    descripcion: str
    cantidad: Decimal
    precio_unitario: Decimal
    descuento_porcentaje: Decimal
    total: Decimal

    model_config = ConfigDict(from_attributes=True)


class AlbaranVentaCreate(BaseModel):
    cliente_id: int
    fecha: date
    observaciones: str | None = None
    lineas: list[LineaAlbaranVentaCreate] = Field(min_length=1)


class AlbaranVentaResponse(BaseModel):
    id: int
    numero: str
    cliente_id: int
    cliente: ClienteSelect
    fecha: date
    estado: str
    factura_id: int | None = None
    observaciones: str | None
    total: Decimal
    lineas: list[LineaAlbaranVentaResponse]

    model_config = ConfigDict(from_attributes=True)
