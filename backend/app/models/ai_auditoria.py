from datetime import datetime

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    JSON,
    String,
    Text
)

from app.database.database import Base


class AIAuditoria(Base):
    __tablename__ = "ai_auditoria"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    usuario_id = Column(
        Integer,
        ForeignKey("usuarios.id"),
        nullable=False,
        index=True
    )

    tipo_evento = Column(
        String(50),
        nullable=False,
        index=True
    )

    recurso = Column(
        String(100),
        nullable=True
    )

    referencia_id = Column(
        String(100),
        nullable=True,
        index=True
    )

    descripcion = Column(
        Text,
        nullable=True
    )

    datos = Column(
        JSON,
        nullable=True
    )

    resultado = Column(
        JSON,
        nullable=True
    )

    exitoso = Column(
        Boolean,
        nullable=False,
        default=True
    )

    error = Column(
        Text,
        nullable=True
    )

    creado_en = Column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        index=True
    )
"""Auditoría persistente y saneada de conversaciones y operaciones de IA."""
