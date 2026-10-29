"""Entidad de cliente y sus relaciones de negocio con el taller."""

from sqlalchemy import Boolean, Column, DateTime, Integer, String, Text
from sqlalchemy.sql import func

from app.database.database import Base
from sqlalchemy.orm import relationship


class Cliente(Base):
    """Persona o empresa cliente; concentra datos de contacto y trazabilidad."""

    __tablename__ = "clientes"

    id = Column(Integer, primary_key=True, index=True)
    codigo = Column(String(20), unique=True, index=True)

    nombre = Column(String(100), nullable=False)
    apellidos = Column(String(150))
    dni = Column(String(20), unique=True)

    telefono = Column(String(20))
    email = Column(String(100))

    direccion = Column(String(200))
    ciudad = Column(String(100))
    provincia = Column(String(100))
    codigo_postal = Column(String(10))

    observaciones = Column(Text)

    activo = Column(Boolean, default=True)

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now()
    )

    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now()
    )
    
    vehiculos = relationship(
    "Vehiculo",
    back_populates="cliente",
    cascade="all, delete-orphan"
    )
    
    facturas = relationship(
    "Factura",
    back_populates="cliente"
    )
