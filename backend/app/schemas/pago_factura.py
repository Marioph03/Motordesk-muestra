from datetime import datetime
from decimal import Decimal
from typing import Annotated, Optional

from pydantic import BaseModel, ConfigDict, Field

from app.models.pago_factura import MetodoPago


class PagoFacturaCreate(BaseModel):
    importe: Annotated[
        Decimal,
        Field(gt=Decimal("0"), max_digits=10, decimal_places=2)
    ]
    metodo_pago: MetodoPago
    referencia: Optional[str] = None
    observaciones: Optional[str] = None


class PagoFacturaResponse(BaseModel):
    id: int
    factura_id: int
    importe: Decimal
    metodo_pago: str
    referencia: Optional[str] = None
    observaciones: Optional[str] = None
    fecha_pago: datetime
    created_at: datetime

    model_config = ConfigDict(
        from_attributes=True
    )
"""Contratos de pagos registrados sobre facturas comerciales."""
