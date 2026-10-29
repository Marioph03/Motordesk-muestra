"""Contratos de factura, líneas y contexto de cliente, vehículo y orden."""

from datetime import datetime
from decimal import Decimal

from app.schemas.cliente import ClienteResponse
from app.schemas.vehiculo import VehiculoResponse
from app.schemas.orden_reparacion import OrdenReparacionResponse
from app.schemas.factura_linea import FacturaLineaResponse

from pydantic import BaseModel


class FacturaDesdeAlbaranesVentaCreate(BaseModel):
    albaranes_venta_ids: list[int]

class FacturaDesdeOrdenesCreate(BaseModel):
    ordenes_ids: list[int]
    tipo_documento: str = "FACTURA"
    cliente_id: int


class FacturaCreate(BaseModel):

    tipo_documento: str
    tipo_factura: str
    cliente_id: int
    vehiculo_id: int | None = None
    # Las facturas manuales (ventas directas o trabajos antiguos) no tienen
    # por qué nacer de una orden de reparación.
    orden_id: int | None = None

    descuento_porcentaje: Decimal = Decimal("0")
    iva: Decimal = Decimal("21")
    observaciones: str | None = None


class FacturaUpdate(BaseModel):

    tipo_documento: str | None = None
    tipo_factura: str | None = None
    cliente_id: int | None = None
    vehiculo_id: int | None = None
    orden_id: int | None = None

    descuento_porcentaje: Decimal | None = None
    iva: Decimal | None = None
    observaciones: str | None = None


class FacturaResponse(BaseModel):

    id: int

    numero: str

    es_prueba: bool = False

    modo_facturacion: str | None = None

    tipo_documento: str

    tipo_factura: str

    estado: str

    cliente_id: int

    vehiculo_id: int | None = None

    orden_id: int | None = None

    subtotal: Decimal

    descuento_porcentaje: Decimal

    base_imponible: Decimal

    iva: Decimal

    cuota_iva: Decimal

    total: Decimal

    observaciones: str | None = None

    fecha_emision: datetime

    created_at: datetime

    updated_at: datetime | None = None

    # Relaciones

    cliente: ClienteResponse

    vehiculo: VehiculoResponse | None = None

    orden: OrdenReparacionResponse | None = None

    lineas: list[FacturaLineaResponse] = []

    model_config = {
        "from_attributes": True
    }
