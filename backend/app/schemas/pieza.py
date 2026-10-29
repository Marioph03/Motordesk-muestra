from decimal import Decimal
from typing import Optional

from pydantic import BaseModel


class PiezaBase(BaseModel):
    descripcion: str
    cantidad: Decimal
    precio_unitario: Decimal
    descuento_porcentaje: Decimal = Decimal("0")
    cubierto_garantia: bool = False
    articulo_stock_id: int | None = None


class PiezaCreate(PiezaBase):
    pass
    proveedor_id: int | None = None
    referencia: str | None = None
    articulo_stock_id: int | None = None


class PiezaUpdate(BaseModel):
    descripcion: Optional[str] = None
    cantidad: Optional[Decimal] = None
    precio_unitario: Optional[Decimal] = None
    proveedor_id: int | None = None
    referencia: str | None = None
    descuento_porcentaje: Optional[Decimal] = None
    cubierto_garantia: Optional[bool] = None
    articulo_stock_id: int | None = None


class PiezaResponse(PiezaBase):
    id: int
    orden_id: int
    total: Decimal
    proveedor_id: int | None
    referencia: str | None
    articulo_stock_id: int | None = None

    model_config = {
        "from_attributes": True
    }
"""Contratos de piezas imputadas a órdenes de reparación."""
