from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class MovimientoStockCreate(BaseModel):

    cantidad: Decimal = Field(
        gt=0
    )

    motivo: str | None = None


class AjusteStockCreate(BaseModel):

    cantidad: Decimal = Field(
        gt=0
    )

    motivo: str


class MovimientoStockResponse(BaseModel):

    id: int

    articulo_id: int

    tipo: str

    cantidad: Decimal

    stock_anterior: Decimal
    stock_resultante: Decimal

    motivo: str | None = None

    orden_id: int | None = None

    fecha: datetime

    model_config = ConfigDict(
        from_attributes=True
    )
"""Representación de movimientos trazables que cambian existencias."""
