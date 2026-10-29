from sqlalchemy import (
    Column,
    ForeignKey,
    Integer,
    Numeric,
    String
)

from sqlalchemy.orm import relationship

from app.database.database import Base


class LineaPedidoCompra(Base):

    __tablename__ = "lineas_pedido_compra"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    pedido_id = Column(
        Integer,
        ForeignKey(
            "pedidos_compra.id",
            ondelete="CASCADE"
        ),
        nullable=False,
        index=True
    )

    articulo_stock_id = Column(
        Integer,
        ForeignKey(
            "articulos_stock.id",
            ondelete="RESTRICT"
        ),
        nullable=True,
        index=True
    )

    # Snapshot para conservar el histórico
    referencia = Column(
        String(100),
        nullable=False
    )

    descripcion = Column(
        String(255),
        nullable=False
    )

    cantidad_pedida = Column(
        Numeric(12, 2),
        nullable=False
    )

    cantidad_recibida = Column(
        Numeric(12, 2),
        nullable=False,
        default=0
    )

    coste_unitario = Column(
        Numeric(12, 2),
        nullable=False
    )

    iva = Column(
        Numeric(5, 2),
        nullable=False,
        default=21
    )

    subtotal = Column(
        Numeric(12, 2),
        nullable=False,
        default=0
    )

    iva_importe = Column(
        Numeric(12, 2),
        nullable=False,
        default=0
    )

    total = Column(
        Numeric(12, 2),
        nullable=False,
        default=0
    )

    pedido = relationship(
        "PedidoCompra",
        back_populates="lineas"
    )

    articulo_stock = relationship(
        "ArticuloStock"
    )
"""Snapshot histórico de cada línea solicitada a proveedor y sus recepciones."""
