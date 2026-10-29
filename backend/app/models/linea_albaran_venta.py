"""Línea de recambio vendida mediante un albarán de venta."""

from sqlalchemy import Column, ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import relationship

from app.database.database import Base


class LineaAlbaranVenta(Base):
    __tablename__ = "lineas_albaran_venta"

    id = Column(Integer, primary_key=True, index=True)
    albaran_id = Column(
        Integer,
        ForeignKey("albaranes_venta.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    articulo_stock_id = Column(
        Integer,
        ForeignKey("articulos_stock.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    referencia = Column(String(100), nullable=False)
    descripcion = Column(String(255), nullable=False)
    cantidad = Column(Numeric(12, 2), nullable=False)
    precio_unitario = Column(Numeric(12, 2), nullable=False)
    descuento_porcentaje = Column(Numeric(5, 2), nullable=False, default=0)
    total = Column(Numeric(12, 2), nullable=False)

    albaran = relationship("AlbaranVenta", back_populates="lineas")
    articulo = relationship("ArticuloStock")
