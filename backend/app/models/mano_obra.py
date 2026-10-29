from sqlalchemy import Boolean, Column, ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import relationship

from app.database.database import Base


class ManoObra(Base):
    __tablename__ = "mano_obra"

    id = Column(Integer, primary_key=True, index=True)

    orden_id = Column(
        Integer,
        ForeignKey("ordenes_reparacion.id"),
        nullable=False
    )
    
    descuento_porcentaje = Column(
    Numeric(5, 2),
    default=0,
    nullable=False
    )

    concepto = Column(String(255), nullable=False)

    # Código de operación facilitado por el fabricante para una reparación
    # en garantía. No se utiliza en órdenes ordinarias ni presupuestos.
    codigo_mano_obra = Column(String(100), nullable=True)

    horas = Column(Numeric(5, 2), nullable=False)

    precio_hora = Column(Numeric(10, 2), nullable=False)

    total = Column(Numeric(10, 2), nullable=False)

    cubierto_garantia = Column(Boolean, default=False, nullable=False)

    orden = relationship(
        "OrdenReparacion",
        back_populates="mano_obra"
    )
"""Trabajo de mano de obra imputado a una orden de reparación."""
