from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app.database.database import Base


class DevolucionProveedor(Base):
    __tablename__ = "devoluciones_proveedor"

    id = Column(Integer, primary_key=True, index=True)
    numero = Column(String(50), nullable=False, unique=True, index=True)
    proveedor_id = Column(Integer, ForeignKey("proveedores.id"), nullable=False, index=True)
    albaran_origen_id = Column(
        Integer,
        ForeignKey("albaranes_proveedor.id"),
        nullable=False,
        index=True,
    )
    estado = Column(String(30), nullable=False, default="BORRADOR", index=True)
    resolucion = Column(String(30), nullable=False, default="PENDIENTE", index=True)
    motivo = Column(String(50), nullable=False)
    observaciones = Column(Text, nullable=True)
    fecha = Column(DateTime, nullable=False, default=datetime.now, index=True)

    proveedor = relationship("Proveedor")
    albaran_origen = relationship("AlbaranProveedor")
    lineas = relationship(
        "LineaDevolucionProveedor",
        back_populates="devolucion",
        cascade="all, delete-orphan",
        order_by="LineaDevolucionProveedor.id",
    )
"""Documento de devolución de artículos a proveedor y su estado operativo."""
