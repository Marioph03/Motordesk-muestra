from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel


class FacturaLineaCreate(BaseModel):

    origen: str

    descripcion: str

    cantidad: Decimal

    precio_unitario: Decimal

    descuento_porcentaje: Decimal = Decimal("0")

    iva: Decimal = Decimal("21")

    categoria_fiscal: str = "VENTA_SERVICIO"

    motivo_exencion: str | None = None


class FacturaLineaUpdate(BaseModel):

    descripcion: str | None = None

    cantidad: Decimal | None = None

    precio_unitario: Decimal | None = None

    descuento_porcentaje: Decimal | None = None

    iva: Decimal | None = None

    categoria_fiscal: str | None = None

    motivo_exencion: str | None = None


class FacturaLineaResponse(BaseModel):

    id: int

    factura_id: int

    albaran_venta_id: int | None = None

    origen: str

    descripcion: str

    cantidad: Decimal

    precio_unitario: Decimal

    descuento_porcentaje: Decimal

    subtotal: Decimal

    iva: Decimal

    categoria_fiscal: str = "VENTA_SERVICIO"

    motivo_exencion: str | None = None

    total: Decimal

    created_at: datetime

    updated_at: datetime

    model_config = {
        "from_attributes": True
    }
"""Contratos de líneas económicas editables en una factura en borrador."""
