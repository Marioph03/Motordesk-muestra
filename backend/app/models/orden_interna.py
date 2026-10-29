"""Órdenes para trabajos propios del taller sin venta al cliente."""
from datetime import datetime
from sqlalchemy import Column, DateTime, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.orm import relationship
from app.database.database import Base


class OrdenInterna(Base):
    __tablename__ = "ordenes_internas"
    id = Column(Integer, primary_key=True)
    numero = Column(String(24), unique=True, nullable=False, index=True)
    titulo = Column(String(200), nullable=False)
    categoria = Column(String(50), nullable=False, default="OTRO")
    vehiculo_id = Column(Integer, ForeignKey("vehiculos.id", ondelete="SET NULL"), nullable=True)
    referencia_activo = Column(String(200), nullable=True)
    descripcion = Column(Text, nullable=False)
    estado = Column(String(20), nullable=False, default="ABIERTA")
    responsable_id = Column(Integer, ForeignKey("usuarios.id", ondelete="SET NULL"), nullable=True)
    coste_total = Column(Numeric(12, 2), nullable=False, default=0)
    fecha_apertura = Column(DateTime, nullable=False, default=datetime.utcnow)
    fecha_cierre = Column(DateTime, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    responsable = relationship("Usuario")
    vehiculo = relationship("Vehiculo")
    lineas = relationship("LineaOrdenInterna", back_populates="orden", cascade="all, delete-orphan", order_by="LineaOrdenInterna.id")


class LineaOrdenInterna(Base):
    __tablename__ = "lineas_orden_interna"
    id = Column(Integer, primary_key=True)
    orden_interna_id = Column(Integer, ForeignKey("ordenes_internas.id", ondelete="CASCADE"), nullable=False, index=True)
    tipo = Column(String(12), nullable=False)
    articulo_stock_id = Column(Integer, ForeignKey("articulos_stock.id", ondelete="SET NULL"), nullable=True)
    referencia = Column(String(100), nullable=True)
    descripcion = Column(String(500), nullable=False)
    cantidad = Column(Numeric(12, 2), nullable=False, default=1)
    coste_unitario = Column(Numeric(12, 2), nullable=False, default=0)
    orden = relationship("OrdenInterna", back_populates="lineas")
    articulo = relationship("ArticuloStock")
