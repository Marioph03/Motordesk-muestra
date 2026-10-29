"""Artículo de almacén con existencias, costes y mínimos de reposición."""

from datetime import datetime

from sqlalchemy import (
    Boolean,
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


class ArticuloStock(Base):

    __tablename__ = "articulos_stock"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    referencia = Column(
        String(100),
        nullable=False,
        unique=True,
        index=True
    )

    nombre = Column(
        String(255),
        nullable=False,
        index=True
    )

    descripcion = Column(
        Text,
        nullable=True
    )

    marca = Column(
        String(150),
        nullable=True,
        index=True
    )

    categoria = Column(
        String(150),
        nullable=True,
        index=True
    )

    ubicacion = Column(
        String(100),
        nullable=True
    )

    coste = Column(
        Numeric(
            precision=12,
            scale=2
        ),
        nullable=False,
        default=0
    )

    precio_venta = Column(
        Numeric(
            precision=12,
            scale=2
        ),
        nullable=False,
        default=0
    )

    iva = Column(
        Numeric(
            precision=5,
            scale=2
        ),
        nullable=False,
        default=21
    )

    stock_actual = Column(
        Numeric(
            precision=12,
            scale=2
        ),
        nullable=False,
        default=0
    )

    stock_minimo = Column(
        Numeric(
            precision=12,
            scale=2
        ),
        nullable=False,
        default=0
    )

    activo = Column(
        Boolean,
        nullable=False,
        default=True
    )

    controla_stock = Column(
        Boolean,
        nullable=False,
        default=True,
        server_default="true",
    )

    proveedor_habitual_id = Column(
        Integer,
        ForeignKey(
            "proveedores.id",
            ondelete="SET NULL"
        ),
        nullable=True,
        index=True
    )

    proveedor_habitual = relationship(
        "Proveedor"
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

    movimientos = relationship(
        "MovimientoStock",
        back_populates="articulo",
        order_by="MovimientoStock.fecha.desc()"
    )
