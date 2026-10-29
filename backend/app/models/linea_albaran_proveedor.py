from sqlalchemy import (
    Column,
    ForeignKey,
    Integer,
    Numeric
)

from sqlalchemy.orm import relationship

from app.database.database import Base


class LineaAlbaranProveedor(Base):

    __tablename__ = "lineas_albaran_proveedor"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    albaran_id = Column(
        Integer,
        ForeignKey(
            "albaranes_proveedor.id",
            ondelete="CASCADE"
        ),
        nullable=False,
        index=True
    )

    articulo_stock_id = Column(
        Integer,
        ForeignKey(
            "articulos_stock.id"
        ),
        nullable=False,
        index=True
    )

    cantidad_recibida = Column(
        Numeric(12, 2),
        nullable=False
    )

    coste_unitario = Column(
        Numeric(12, 2),
        nullable=True
    )

    albaran = relationship(
        "AlbaranProveedor",
        back_populates="lineas"
    )

    articulo = relationship(
        "ArticuloStock"
    )
"""Línea de mercancía recibida en un albarán de proveedor."""
