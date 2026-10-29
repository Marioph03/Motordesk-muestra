"""Pedido de compra a proveedor y sus estados de envío y recepción."""

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


class EstadoPedidoCompra(str, Enum):
    BORRADOR = "BORRADOR"
    ENVIADO = "ENVIADO"
    RECIBIDO_PARCIAL = "RECIBIDO_PARCIAL"
    RECIBIDO = "RECIBIDO"
    CANCELADO = "CANCELADO"


class PedidoCompra(Base):

    __tablename__ = "pedidos_compra"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    numero = Column(
        String(50),
        nullable=False,
        unique=True,
        index=True
    )

    proveedor_id = Column(
        Integer,
        ForeignKey(
            "proveedores.id",
            ondelete="RESTRICT"
        ),
        nullable=False,
        index=True
    )

    estado = Column(
        String(30),
        nullable=False,
        default=EstadoPedidoCompra.BORRADOR.value,
        index=True
    )

    fecha = Column(
        DateTime,
        nullable=False,
        default=datetime.utcnow
    )

    fecha_envio = Column(
        DateTime,
        nullable=True
    )

    fecha_recepcion = Column(
        DateTime,
        nullable=True
    )

    observaciones = Column(
        Text,
        nullable=True
    )

    subtotal = Column(
        Numeric(12, 2),
        nullable=False,
        default=0
    )

    iva_total = Column(
        Numeric(12, 2),
        nullable=False,
        default=0
    )

    total = Column(
        Numeric(12, 2),
        nullable=False,
        default=0
    )

    created_at = Column(
        DateTime,
        nullable=False,
        default=datetime.utcnow
    )

    updated_at = Column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )

    proveedor = relationship(
        "Proveedor",
        back_populates="pedidos_compra"
    )

    lineas = relationship(
        "LineaPedidoCompra",
        back_populates="pedido",
        cascade="all, delete-orphan",
        order_by="LineaPedidoCompra.id"
    )
