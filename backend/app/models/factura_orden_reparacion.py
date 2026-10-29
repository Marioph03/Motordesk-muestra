from sqlalchemy import Column, ForeignKey, Integer, UniqueConstraint
from sqlalchemy.orm import relationship
from app.database.database import Base

class FacturaOrdenReparacion(Base):
    __tablename__ = "facturas_ordenes_reparacion"
    id = Column(Integer, primary_key=True)
    factura_id = Column(Integer, ForeignKey("facturas.id", ondelete="CASCADE"), nullable=False, index=True)
    orden_id = Column(Integer, ForeignKey("ordenes_reparacion.id"), nullable=False, unique=True, index=True)
    factura = relationship("Factura")
    orden = relationship("OrdenReparacion")
    __table_args__ = (UniqueConstraint("factura_id", "orden_id", name="uq_factura_orden_reparacion"),)
