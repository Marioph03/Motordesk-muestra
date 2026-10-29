from sqlalchemy import Boolean, Column, ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import relationship

from app.database.database import Base


class Pieza(Base):
    __tablename__ = "piezas"

    id = Column(Integer, primary_key=True, index=True)

    orden_id = Column(
        Integer,
        ForeignKey("ordenes_reparacion.id"),
        nullable=False
    )

    proveedor_id = Column(
        Integer,
        ForeignKey("proveedores.id"),
        nullable=True
    )

    descripcion = Column(String(255), nullable=False)

    cantidad = Column(Numeric(10, 2), nullable=False)

    precio_unitario = Column(Numeric(10, 2), nullable=False)
    
    descuento_porcentaje = Column(
    Numeric(5, 2),
    default=0,
    nullable=False
    )

    total = Column(Numeric(10, 2), nullable=False)

    cubierto_garantia = Column(Boolean, default=False, nullable=False)
    
    referencia = Column(
    String(100),
    nullable=True
    )

    orden = relationship(
        "OrdenReparacion",
        back_populates="piezas"
    )
    
    proveedor = relationship(
        "Proveedor",
        back_populates="piezas"
    )

    articulo_stock_id = Column(
    Integer,
    ForeignKey(
        "articulos_stock.id",
        ondelete="SET NULL"
    ),
    nullable=True,
    index=True
    )

    articulo_stock = relationship(
    "ArticuloStock"
    )
"""Pieza de almacén reservada o consumida dentro de una orden de reparación."""
