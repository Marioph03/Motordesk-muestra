from datetime import date

from sqlalchemy import (
    Column,
    Date,
    Integer,
    String,
    Text
)

from app.database.database import Base


class CierreAgenda(Base):

    __tablename__ = "cierres_agenda"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    fecha = Column(
        Date,
        nullable=False,
        index=True
    )

    motivo = Column(
        String(150),
        nullable=False
    )

    observaciones = Column(
        Text,
        nullable=True
    )
"""Cierres excepcionales que impiden reservar citas durante un intervalo."""
