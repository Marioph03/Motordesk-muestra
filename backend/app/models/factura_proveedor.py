from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import Column, Date, DateTime, ForeignKey, Integer, Numeric, String, Text, UniqueConstraint
from sqlalchemy.orm import relationship

from app.database.database import Base


class FacturaProveedor(Base):
    __tablename__ = "facturas_proveedor"

    id = Column(Integer, primary_key=True, index=True)
    proveedor_id = Column(Integer, ForeignKey("proveedores.id"), nullable=False, index=True)
    numero_factura = Column(String(100), nullable=False)
    tipo_gasto = Column(String(30), nullable=False, default="COMPRA")
    fecha_factura = Column(Date, nullable=False, default=date.today, index=True)
    fecha_vencimiento = Column(Date, nullable=True, index=True)
    base_imponible = Column(Numeric(12, 2), nullable=False, default=Decimal("0.00"))
    porcentaje_iva = Column(Numeric(5, 2), nullable=False, default=Decimal("0.00"))
    iva = Column(Numeric(12, 2), nullable=False, default=Decimal("0.00"))
    porcentaje_retencion = Column(Numeric(5, 2), nullable=False, default=Decimal("0.00"))
    retencion_irpf = Column(Numeric(12, 2), nullable=False, default=Decimal("0.00"))
    total = Column(Numeric(12, 2), nullable=False, default=Decimal("0.00"))
    estado_pago = Column(String(30), nullable=False, default="PENDIENTE", index=True)
    fecha_pago = Column(Date, nullable=True)
    archivo_pdf = Column(String(500), nullable=True)
    observaciones = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.now)

    proveedor = relationship("Proveedor")
    albaranes = relationship(
        "AlbaranProveedor",
        secondary="factura_proveedor_albaranes",
    )

    __table_args__ = (
        UniqueConstraint(
            "proveedor_id",
            "numero_factura",
            name="uq_factura_proveedor_numero",
        ),
    )
"""Factura recibida de proveedor, albaranes asociados, pago y adjunto PDF."""
