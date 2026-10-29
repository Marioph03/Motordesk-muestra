"""Contratos de pedidos de compra, sus líneas y recepciones parciales."""

from datetime import datetime
from decimal import Decimal

from pydantic import (
    BaseModel,
    ConfigDict,
    Field
)


# =========================================================
# LINEAS
# =========================================================

class LineaPedidoCompraCreate(BaseModel):

    articulo_stock_id: int | None = None
    referencia: str | None = None
    descripcion: str | None = None

    cantidad_pedida: Decimal = Field(
        gt=0
    )

    coste_unitario: Decimal | None = Field(
        default=None,
        ge=0
    )

    iva: Decimal | None = Field(
        default=None,
        ge=0
    )


class LineaPedidoCompraUpdate(BaseModel):

    cantidad_pedida: Decimal | None = Field(
        default=None,
        gt=0
    )

    coste_unitario: Decimal | None = Field(
        default=None,
        ge=0
    )

    iva: Decimal | None = Field(
        default=None,
        ge=0
    )


class LineaPedidoCompraResponse(BaseModel):

    id: int

    pedido_id: int
    articulo_stock_id: int | None = None

    referencia: str
    descripcion: str

    cantidad_pedida: Decimal
    cantidad_recibida: Decimal

    coste_unitario: Decimal
    iva: Decimal

    subtotal: Decimal
    iva_importe: Decimal
    total: Decimal

    model_config = ConfigDict(
        from_attributes=True
    )


# =========================================================
# PEDIDOS
# =========================================================

class PedidoCompraCreate(BaseModel):

    proveedor_id: int

    observaciones: str | None = None


class PedidoCompraUpdate(BaseModel):

    proveedor_id: int | None = None

    observaciones: str | None = None


class ProveedorPedidoResponse(BaseModel):

    id: int
    nombre: str
    cif: str

    telefono: str | None = None
    email: str | None = None

    model_config = ConfigDict(
        from_attributes=True
    )


class PedidoCompraResponse(BaseModel):

    id: int

    numero: str
    proveedor_id: int

    estado: str

    fecha: datetime

    fecha_envio: datetime | None = None
    fecha_recepcion: datetime | None = None

    observaciones: str | None = None

    subtotal: Decimal
    iva_total: Decimal
    total: Decimal

    created_at: datetime
    updated_at: datetime

    proveedor: ProveedorPedidoResponse

    lineas: list[
        LineaPedidoCompraResponse
    ] = []

    model_config = ConfigDict(
        from_attributes=True
    )


class RecepcionLineaPedidoCreate(BaseModel):

    linea_id: int

    cantidad: Decimal = Field(
        gt=0
    )


class RecepcionPedidoCreate(BaseModel):

    lineas: list[RecepcionLineaPedidoCreate]

    observaciones: str | None = None
