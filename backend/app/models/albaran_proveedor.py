from sqlalchemy import (
    Column,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text
)

from sqlalchemy.orm import relationship

from datetime import datetime

from app.database.database import Base


class AlbaranProveedor(Base):

    __tablename__ = "albaranes_proveedor"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    numero_interno = Column(
        String(50),
        nullable=False,
        unique=True,
        index=True
    )

    numero_proveedor = Column(
        String(100),
        nullable=True,
        index=True
    )

    proveedor_id = Column(
        Integer,
        ForeignKey(
            "proveedores.id"
        ),
        nullable=False,
        index=True
    )

    pedido_compra_id = Column(
        Integer,
        ForeignKey(
            "pedidos_compra.id"
        ),
        nullable=True,
        index=True
    )

    fecha = Column(
        Date,
        nullable=False
    )

    estado = Column(
        String(30),
        nullable=False,
        default="BORRADOR"
    )

    observaciones = Column(
        Text,
        nullable=True
    )

    created_at = Column(
        DateTime,
        nullable=False,
        default=datetime.now
    )

    proveedor = relationship(
        "Proveedor"
    )

    pedido_compra = relationship(
        "PedidoCompra"
    )

    lineas = relationship(
        "LineaAlbaranProveedor",
        back_populates="albaran",
        cascade="all, delete-orphan"
    )
"""Albarán recibido de proveedor y su ciclo de confirmación de mercancía."""
