"""Pagos reales aplicados a facturas para calcular cobros y deuda pendiente."""

from datetime import datetime
from enum import Enum

from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text
)

from sqlalchemy.orm import relationship

from app.database.database import Base


class MetodoPago(str, Enum):
    EFECTIVO = "EFECTIVO"
    TARJETA = "TARJETA"
    TRANSFERENCIA = "TRANSFERENCIA"
    BIZUM = "BIZUM"
    OTRO = "OTRO"


class PagoFactura(Base):
    """Abono individual de una factura; es la fuente del saldo económico exacto."""

    __tablename__ = "pagos_factura"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    factura_id = Column(
        Integer,
        ForeignKey("facturas.id"),
        nullable=False
    )

    importe = Column(
        Numeric(10, 2),
        nullable=False
    )

    metodo_pago = Column(
        String(30),
        nullable=False
    )

    referencia = Column(
        String(100),
        nullable=True
    )

    observaciones = Column(
        Text,
        nullable=True
    )

    fecha_pago = Column(
        DateTime,
        default=datetime.utcnow,
        nullable=False
    )

    created_at = Column(
        DateTime,
        default=datetime.utcnow,
        nullable=False
    )

    factura = relationship(
        "Factura",
        back_populates="pagos"
    )
