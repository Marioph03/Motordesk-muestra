"""Parámetros de horario y duración predeterminada de la agenda."""

from sqlalchemy import (
    Boolean,
    Column,
    Integer,
    String
)

from app.database.database import Base


class ConfiguracionAgenda(Base):
    """Configuración única que valida cuándo es posible reservar una cita."""


    __tablename__ = "configuracion_agenda"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    duracion_cita_minutos = Column(
        Integer,
        nullable=False,
        default=30
    )

    lunes_activo = Column(
        Boolean,
        default=True
    )

    lunes_inicio = Column(
        String(5),
        default="08:00"
    )

    lunes_fin = Column(
        String(5),
        default="18:00"
    )

    martes_activo = Column(
        Boolean,
        default=True
    )

    martes_inicio = Column(
        String(5),
        default="08:00"
    )

    martes_fin = Column(
        String(5),
        default="18:00"
    )

    miercoles_activo = Column(
        Boolean,
        default=True
    )

    miercoles_inicio = Column(
        String(5),
        default="08:00"
    )

    miercoles_fin = Column(
        String(5),
        default="18:00"
    )

    jueves_activo = Column(
        Boolean,
        default=True
    )

    jueves_inicio = Column(
        String(5),
        default="08:00"
    )

    jueves_fin = Column(
        String(5),
        default="18:00"
    )

    viernes_activo = Column(
        Boolean,
        default=True
    )

    viernes_inicio = Column(
        String(5),
        default="08:00"
    )

    viernes_fin = Column(
        String(5),
        default="18:00"
    )

    sabado_activo = Column(
        Boolean,
        default=False
    )

    sabado_inicio = Column(
        String(5),
        default="09:00"
    )

    sabado_fin = Column(
        String(5),
        default="14:00"
    )

    domingo_activo = Column(
        Boolean,
        default=False
    )

    domingo_inicio = Column(
        String(5),
        default="09:00"
    )

    domingo_fin = Column(
        String(5),
        default="14:00"
    )
