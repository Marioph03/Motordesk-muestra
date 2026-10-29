from datetime import date
from decimal import Decimal

from pydantic import BaseModel


class FacturaFiltro(BaseModel):
    estado: str | None = None
    cliente_id: int | None = None
    vehiculo_id: int | None = None
    tipo_documento: str | None = None
    fecha_desde: date | None = None
    fecha_hasta: date | None = None
    total_desde: Decimal | None = None
    total_hasta: Decimal | None = None
    numero: str | None = None
"""Filtros permitidos para búsquedas paginadas de facturas."""
