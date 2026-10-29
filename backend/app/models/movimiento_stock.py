"""Historial de movimientos; no actualiza stock sin conservar su motivo."""

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


class TipoMovimientoStock(str, Enum):

    ENTRADA = "ENTRADA"

    ENTRADA_COMPRA = "ENTRADA_COMPRA"

    SALIDA = "SALIDA"

    AJUSTE_POSITIVO = "AJUSTE_POSITIVO"

    AJUSTE_NEGATIVO = "AJUSTE_NEGATIVO"

    CONSUMO_ORDEN = "CONSUMO_ORDEN"

    DEVOLUCION_ORDEN = "DEVOLUCION_ORDEN"

    DEVOLUCION_PROVEEDOR = "DEVOLUCION_PROVEEDOR"


class MovimientoStock(Base):

    __tablename__ = "movimientos_stock"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    articulo_id = Column(
        Integer,
        ForeignKey(
            "articulos_stock.id",
            ondelete="RESTRICT"
        ),
        nullable=False,
        index=True
    )

    tipo = Column(
        String(30),
        nullable=False,
        index=True
    )

    cantidad = Column(
        Numeric(
            precision=12,
            scale=2
        ),
        nullable=False
    )

    stock_anterior = Column(
        Numeric(
            precision=12,
            scale=2
        ),
        nullable=False
    )

    stock_resultante = Column(
        Numeric(
            precision=12,
            scale=2
        ),
        nullable=False
    )

    motivo = Column(
        Text,
        nullable=True
    )

    orden_id = Column(
        Integer,
        ForeignKey(
            "ordenes_reparacion.id",
            ondelete="SET NULL"
        ),
        nullable=True,
        index=True
    )

    fecha = Column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        index=True
    )

    articulo = relationship(
        "ArticuloStock",
        back_populates="movimientos"
    )

    orden = relationship(
        "OrdenReparacion",
        foreign_keys=[orden_id]
    )
