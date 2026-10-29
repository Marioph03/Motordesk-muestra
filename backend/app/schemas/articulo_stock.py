from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class ArticuloStockCreate(BaseModel):

    referencia: str
    nombre: str

    descripcion: str | None = None
    marca: str | None = None
    categoria: str | None = None
    ubicacion: str | None = None

    coste: Decimal = Field(
        default=Decimal("0"),
        ge=0
    )

    precio_venta: Decimal = Field(
        default=Decimal("0"),
        ge=0
    )

    iva: Decimal = Field(
        default=Decimal("21"),
        ge=0
    )

    stock_inicial: Decimal = Field(
        default=Decimal("0"),
        ge=0
    )

    stock_minimo: Decimal = Field(
        default=Decimal("0"),
        ge=0
    )

    activo: bool = True

    controla_stock: bool = True

    proveedor_habitual_id: int | None = None


class ArticuloStockUpdate(BaseModel):

    referencia: str | None = None
    nombre: str | None = None

    descripcion: str | None = None
    marca: str | None = None
    categoria: str | None = None
    ubicacion: str | None = None

    coste: Decimal | None = Field(
        default=None,
        ge=0
    )

    precio_venta: Decimal | None = Field(
        default=None,
        ge=0
    )

    iva: Decimal | None = Field(
        default=None,
        ge=0
    )

    stock_minimo: Decimal | None = Field(
        default=None,
        ge=0
    )

    activo: bool | None = None

    controla_stock: bool | None = None

    proveedor_habitual_id: int | None = None


class ArticuloStockResponse(BaseModel):

    id: int

    referencia: str
    nombre: str

    descripcion: str | None = None
    marca: str | None = None
    categoria: str | None = None
    ubicacion: str | None = None

    coste: Decimal
    precio_venta: Decimal
    iva: Decimal

    stock_actual: Decimal
    stock_minimo: Decimal

    activo: bool

    controla_stock: bool = True

    proveedor_habitual_id: int | None = None

    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(
        from_attributes=True
    )
"""Contratos de catálogo, existencias y reposición de artículos de stock."""
