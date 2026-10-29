from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class FacturaProveedorCreate(BaseModel):
    proveedor_id: int
    numero_factura: str = Field(min_length=1, max_length=100)
    tipo_gasto: str = Field(default="COMPRA", max_length=30)
    fecha_factura: date
    fecha_vencimiento: date | None = None
    base_imponible: Decimal = Field(ge=0)
    porcentaje_iva: Decimal = Field(ge=0, le=100)
    porcentaje_retencion: Decimal = Field(default=Decimal("0"), ge=0, le=100)
    observaciones: str | None = None
    albaranes_ids: list[int] = []


class AlbaranFacturaProveedorResponse(BaseModel):
    id: int
    numero_interno: str
    numero_proveedor: str | None = None
    fecha: date
    model_config = ConfigDict(from_attributes=True)


class FacturaProveedorResponse(BaseModel):
    id: int
    proveedor_id: int
    numero_factura: str
    tipo_gasto: str
    fecha_factura: date
    fecha_vencimiento: date | None
    base_imponible: Decimal
    porcentaje_iva: Decimal
    iva: Decimal
    porcentaje_retencion: Decimal
    retencion_irpf: Decimal
    total: Decimal
    estado_pago: str
    fecha_pago: date | None
    archivo_pdf: str | None
    observaciones: str | None
    created_at: datetime
    albaranes: list[AlbaranFacturaProveedorResponse] = []
    model_config = ConfigDict(from_attributes=True)


class MarcarFacturaProveedorPagadaRequest(BaseModel):
    fecha_pago: date | None = None
"""Contratos de facturas recibidas, albaranes asociados y adjunto PDF."""
