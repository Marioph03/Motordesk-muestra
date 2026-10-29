from sqlalchemy import Column, ForeignKey, Integer, Numeric
from sqlalchemy.orm import relationship

from app.database.database import Base


class LineaDevolucionProveedor(Base):
    __tablename__ = "lineas_devolucion_proveedor"

    id = Column(Integer, primary_key=True, index=True)
    devolucion_id = Column(
        Integer,
        ForeignKey("devoluciones_proveedor.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    linea_albaran_id = Column(
        Integer,
        ForeignKey("lineas_albaran_proveedor.id"),
        nullable=False,
        index=True,
    )
    articulo_stock_id = Column(
        Integer,
        ForeignKey("articulos_stock.id"),
        nullable=False,
        index=True,
    )
    cantidad = Column(Numeric(12, 2), nullable=False)

    devolucion = relationship("DevolucionProveedor", back_populates="lineas")
    linea_albaran = relationship("LineaAlbaranProveedor")
    articulo = relationship("ArticuloStock")
"""Línea de artículo devuelto a proveedor y la cantidad efectivamente devuelta."""
