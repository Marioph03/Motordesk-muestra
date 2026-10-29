"""Modelo de agenda: citas, estados y asignación de personal."""

from datetime import datetime
from enum import Enum

from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text
)

from sqlalchemy.orm import relationship

from app.database.database import Base
from app.models.cita_usuario import cita_usuarios


class EstadoCita(str, Enum):
    """Estados operativos que determinan si una cita bloquea disponibilidad."""

    PENDIENTE = "Pendiente"
    CONFIRMADA = "Confirmada"
    EN_TALLER = "En taller"
    COMPLETADA = "Completada"
    CANCELADA = "Cancelada"
    NO_PRESENTADO = "No presentado"


class Cita(Base):
    """Reserva de agenda para un cliente, vehículo y equipo asignado."""

    __tablename__ = "citas"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    cliente_id = Column(
        Integer,
        ForeignKey(
            "clientes.id",
            ondelete="RESTRICT"
        ),
        nullable=False,
        index=True
    )

    vehiculo_id = Column(
        Integer,
        ForeignKey(
            "vehiculos.id",
            ondelete="RESTRICT"
        ),
        nullable=False,
        index=True
    )

    fecha_inicio = Column(
        DateTime,
        nullable=False,
        index=True
    )

    fecha_fin = Column(
        DateTime,
        nullable=False
    )

    motivo = Column(
        String(500),
        nullable=False
    )

    observaciones = Column(
        Text,
        nullable=True
    )

    estado = Column(
        String(30),
        default=EstadoCita.PENDIENTE.value,
        nullable=False,
        index=True
    )

    orden_generada_id = Column(
        Integer,
        ForeignKey(
            "ordenes_reparacion.id",
            ondelete="SET NULL"
        ),
        nullable=True
    )

    created_at = Column(
        DateTime,
        default=datetime.utcnow,
        nullable=False
    )

    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )

    cliente = relationship(
        "Cliente"
    )

    vehiculo = relationship(
        "Vehiculo"
    )

    orden_generada = relationship(
        "OrdenReparacion",
        foreign_keys=[orden_generada_id]
    )

    fecha_confirmacion = Column(DateTime, nullable=True)

    canal_confirmacion = Column(String(20), nullable=True)

    fecha_recordatorio = Column(DateTime, nullable=True)
    canal_recordatorio = Column(String(20), nullable=True)

    fecha_reprogramacion = Column(DateTime, nullable=True)
    fecha_inicio_anterior = Column(DateTime, nullable=True)
    fecha_fin_anterior = Column(DateTime, nullable=True)
    
    usuarios_asignados = relationship(
    "Usuario",
    secondary="cita_usuarios",
    back_populates="citas_asignadas"
    )
