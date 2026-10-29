from datetime import datetime

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


class Actividad(Base):

    __tablename__ = "actividad"

    # =========================================================
    # IDENTIFICACIÓN
    # =========================================================

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    empresa_id = Column(
    Integer,
    ForeignKey("empresa.id"),
    nullable=False
    )

    usuario_id = Column(
        Integer,
        ForeignKey("usuarios.id"),
        nullable=False
    )

    # =========================================================
    # INFORMACIÓN
    # =========================================================

    modulo = Column(
        String(50),
        nullable=False
    )

    accion = Column(
        String(50),
        nullable=False
    )

    registro_id = Column(
        Integer,
        nullable=True
    )

    descripcion = Column(
        Text,
        nullable=False
    )

    ip = Column(
        String(45),
        nullable=True
    )

    # =========================================================
    # FECHA
    # =========================================================

    created_at = Column(
        DateTime,
        default=datetime.utcnow,
        nullable=False
    )

    # =========================================================
    # RELACIONES
    # =========================================================

    empresa = relationship(
        "Empresa",
    back_populates="actividades"
    )

    usuario = relationship(
        "Usuario",
        back_populates="actividades"
    )
"""Registro de actividad funcional mostrado en auditoría y seguimiento."""
