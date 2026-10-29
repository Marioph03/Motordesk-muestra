from datetime import date
from decimal import Decimal

from pydantic import (
    BaseModel,
    ConfigDict,
    Field
)


class LineaAlbaranProveedorCreate(BaseModel):

    articulo_stock_id: int

    cantidad_recibida: Decimal = Field(
        gt=0
    )

    coste_unitario: Decimal | None = Field(
        default=None,
        ge=0
    )


class LineaAlbaranProveedorResponse(
    LineaAlbaranProveedorCreate
):

    id: int

    model_config = ConfigDict(
        from_attributes=True
    )


class AlbaranProveedorCreate(BaseModel):

    numero_proveedor: str | None = None

    proveedor_id: int

    pedido_compra_id: int | None = None

    fecha: date

    observaciones: str | None = None

    lineas: list[
        LineaAlbaranProveedorCreate
    ]


class AlbaranProveedorResponse(BaseModel):

    id: int

    numero_interno: str
    numero_proveedor: str | None

    proveedor_id: int
    pedido_compra_id: int | None

    fecha: date
    estado: str

    observaciones: str | None

    lineas: list[
        LineaAlbaranProveedorResponse
    ]

    model_config = ConfigDict(
        from_attributes=True
    )
    
"""Contratos de albaranes proveedor, líneas y confirmación de recepción."""
