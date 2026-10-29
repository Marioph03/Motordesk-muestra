"""Albarán de salida de recambios vendidos desde el almacén."""

from datetime import datetime

from sqlalchemy import Column, Date, DateTime, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.orm import relationship

from app.database.database import Base


class AlbaranVenta(Base):
    __tablename__ = "albaranes_venta"

    id = Column(Integer, primary_key=True, index=True)
    numero = Column(String(50), nullable=False, unique=True, index=True)
    cliente_id = Column(Integer, ForeignKey("clientes.id"), nullable=False, index=True)
    fecha = Column(Date, nullable=False)
    estado = Column(String(30), nullable=False, default="BORRADOR", index=True)
    observaciones = Column(Text, nullable=True)
    total = Column(Numeric(12, 2), nullable=False, default=0)
    created_at = Column(DateTime, nullable=False, default=datetime.now)

    cliente = relationship("Cliente")
    lineas = relationship(
        "LineaAlbaranVenta",
        back_populates="albaran",
        cascade="all, delete-orphan",
    )
    factura_enlace = relationship(
        "FacturaAlbaranVenta",
        back_populates="albaran_venta",
        uselist=False,
    )

    @property
    def factura_id(self):
        """Factura de recambio que incluye este albarán, si existe."""
        return self.factura_enlace.factura_id if self.factura_enlace else None
