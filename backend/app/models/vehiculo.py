"""Entidad de vehículo vinculada a un cliente y a su historial de taller."""

from sqlalchemy import Column, Date, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from app.database.database import Base


class Vehiculo(Base):
    """Vehículo identificado por matrícula y asociado a un único cliente."""

    __tablename__ = "vehiculos"

    id = Column(Integer, primary_key=True, index=True)
    codigo = Column(String(20), unique=True, index=True)

    cliente_id = Column(
        Integer,
        ForeignKey("clientes.id"),
        nullable=False
    )

    matricula = Column(String(10), unique=True, nullable=False, index=True)
    bastidor = Column(String(17), unique=True)

    marca = Column(String(50), nullable=False)
    modelo = Column(String(50), nullable=False)
    version = Column(String(50))

    anio = Column(Integer)
    fecha_matriculacion = Column(Date)
    color = Column(String(30))

    combustible = Column(String(30))
    transmision = Column(String(30))

    kilometros = Column(Integer)

    observaciones = Column(String(500))

    cliente = relationship(
        "Cliente",
        back_populates="vehiculos"
    )
    
    ordenes_reparacion = relationship(
    "OrdenReparacion",
    back_populates="vehiculo",
    cascade="all, delete-orphan"
    )
    
    facturas = relationship(
    "Factura",
    back_populates="vehiculo"
    )
