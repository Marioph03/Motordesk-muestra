from sqlalchemy import Column, ForeignKey, Integer, UniqueConstraint

from app.database.database import Base


class FacturaProveedorAlbaran(Base):
    __tablename__ = "factura_proveedor_albaranes"

    id = Column(Integer, primary_key=True)
    factura_proveedor_id = Column(
        Integer,
        ForeignKey("facturas_proveedor.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    albaran_proveedor_id = Column(
        Integer,
        ForeignKey("albaranes_proveedor.id"),
        nullable=False,
        index=True,
    )

    __table_args__ = (
        UniqueConstraint(
            "factura_proveedor_id",
            "albaran_proveedor_id",
            name="uq_factura_proveedor_albaran",
        ),
        UniqueConstraint(
            "albaran_proveedor_id",
            name="uq_albaran_proveedor_factura",
        ),
    )
"""Tabla asociativa que impide reutilizar un albarán en varias facturas proveedor."""
