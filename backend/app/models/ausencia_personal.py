"""Ausencias del equipo usadas para validar disponibilidad en agenda y órdenes."""

from datetime import datetime
from enum import Enum

from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import relationship

from app.database.database import Base


class TipoAusenciaPersonal(str, Enum):
    """Clasificación mínima de disponibilidad sin almacenar datos sensibles."""

    VACACIONES = "VACACIONES"
    AUSENCIA = "AUSENCIA"
    OTRO = "OTRO"


class AusenciaPersonal(Base):
    """Intervalo en el que una persona no puede asignarse a trabajo o citas."""

    __tablename__ = "ausencias_personal"

    id = Column(
        Integer,
        primary_key=True,
        index=True,
    )

    usuario_id = Column(
        Integer,
        ForeignKey(
            "usuarios.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    tipo = Column(
        String(30),
        nullable=False,
        index=True,
    )

    fecha_inicio = Column(
        DateTime,
        nullable=False,
        index=True,
    )

    fecha_fin = Column(
        DateTime,
        nullable=False,
        index=True,
    )

    observaciones = Column(
        Text,
        nullable=True,
    )

    created_at = Column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
    )

    updated_at = Column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )

    usuario = relationship(
        "Usuario",
        back_populates="ausencias",
    )
