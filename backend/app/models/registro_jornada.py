"""Marcajes diarios de la jornada laboral."""

from datetime import datetime

from sqlalchemy import Boolean, Column, Date, DateTime, ForeignKey, Integer, Time, UniqueConstraint
from sqlalchemy.orm import relationship

from app.database.database import Base


class RegistroJornada(Base):
    __tablename__ = "registros_jornada"
    __table_args__ = (UniqueConstraint("usuario_id", "fecha", name="uq_registro_jornada_usuario_fecha"),)

    id = Column(Integer, primary_key=True)
    usuario_id = Column(Integer, ForeignKey("usuarios.id", ondelete="CASCADE"), nullable=False, index=True)
    fecha = Column(Date, nullable=False, index=True)
    presente = Column(Boolean, nullable=False, default=False)
    hora_entrada = Column(Time, nullable=True)
    hora_salida = Column(Time, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    usuario = relationship("Usuario")
