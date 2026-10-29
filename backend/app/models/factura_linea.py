from datetime import datetime

from sqlalchemy import (
    Column,
    ForeignKey,
    Integer,
    Numeric,
    String,
    DateTime
)
from sqlalchemy.orm import relationship

from app.database.database import Base


class FacturaLinea(Base):
    __tablename__ = "factura_lineas"

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

    albaran_venta_id = Column(
        Integer,
        ForeignKey("albaranes_venta.id"),
        nullable=True,
        index=True,
    )

    # Clasifica líneas comerciales y permite identificar de manera expresa
    # una comisión que se ha documentado como exenta de IVA.
    categoria_fiscal = Column(
        String(30),
        nullable=False,
        default="VENTA_SERVICIO",
    )

    motivo_exencion = Column(
        String(255),
        nullable=True,
    )

    origen = Column(
        String(20),
        nullable=False
    )
    
    created_at = Column(
    DateTime,
    default=datetime.utcnow,
    nullable=False
    )

    updated_at = Column(
    DateTime,
    default=datetime.utcnow,
    onupdate=datetime.utcnow,
    nullable=False
    )

    descripcion = Column(
        String(255),
        nullable=False
    )

    cantidad = Column(
        Numeric(10, 2),
        nullable=False
    )

    precio_unitario = Column(
        Numeric(10, 2),
        nullable=False
    )

    descuento_porcentaje = Column(
        Numeric(5, 2),
        default=0,
        nullable=False
    )

    subtotal = Column(
        Numeric(10, 2),
        nullable=False
    )

    iva = Column(
        Numeric(5, 2),
        default=21,
        nullable=False
    )

    total = Column(
        Numeric(10, 2),
        nullable=False
    )

    factura = relationship(
        "Factura",
        back_populates="lineas"
    )

    albaran_venta = relationship("AlbaranVenta")
"""Línea económica de factura, con cantidades, impuestos e importes persistidos."""
