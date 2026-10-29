"""Relación entre una factura de recambio y sus albaranes de venta."""

from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, UniqueConstraint
from sqlalchemy.orm import relationship

from app.database.database import Base


class FacturaAlbaranVenta(Base):
    """Impide que un mismo albarán se facture más de una vez."""

    __tablename__ = "facturas_albaranes_venta"

    id = Column(Integer, primary_key=True)
    factura_id = Column(
        Integer,
        ForeignKey("facturas.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    albaran_venta_id = Column(
        Integer,
        ForeignKey("albaranes_venta.id"),
        nullable=False,
        index=True,
    )
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    factura = relationship("Factura", back_populates="albaranes_venta")
    albaran_venta = relationship("AlbaranVenta", back_populates="factura_enlace")

    __table_args__ = (
        UniqueConstraint("factura_id", "albaran_venta_id", name="uq_factura_albaran_venta"),
        UniqueConstraint("albaran_venta_id", name="uq_albaran_venta_factura"),
    )
