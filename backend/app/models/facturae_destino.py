"""Datos administrativos congelados para una factura electrónica Facturae."""

from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app.database.database import Base


class FacturaeDestino(Base):
    __tablename__ = "facturae_destinos"

    id = Column(Integer, primary_key=True, index=True)
    factura_id = Column(Integer, ForeignKey("facturas.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)

    nombre = Column(String(255), nullable=False)
    nif = Column(String(20), nullable=False)
    direccion = Column(String(255), nullable=True)
    codigo_postal = Column(String(10), nullable=True)
    ciudad = Column(String(100), nullable=True)
    provincia = Column(String(100), nullable=True)

    oficina_contable = Column(String(10), nullable=False)
    organo_gestor = Column(String(10), nullable=False)
    unidad_tramitadora = Column(String(10), nullable=False)
    expediente = Column(String(100), nullable=True)
    referencia_contrato = Column(String(100), nullable=True)
    referencia_receptor = Column(String(100), nullable=True)
    observaciones = Column(Text, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    factura = relationship("Factura", back_populates="facturae_destino")
