from datetime import datetime

from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String
)
from sqlalchemy.orm import relationship

from app.database.database import Base


class ArchivoOrden(Base):
    __tablename__ = "archivos_orden"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    orden_id = Column(
        Integer,
        ForeignKey(
            "ordenes_reparacion.id",
            ondelete="CASCADE"
        ),
        nullable=False,
        index=True
    )

    nombre_original = Column(
        String(255),
        nullable=False
    )

    nombre_archivo = Column(
        String(255),
        nullable=False
    )

    tipo_mime = Column(
        String(100),
        nullable=False
    )

    categoria = Column(
        String(50),
        nullable=False,
        default="Otro"
    )

    ruta = Column(
        String(500),
        nullable=False
    )

    tamano = Column(
        Integer,
        nullable=False
    )

    created_at = Column(
        DateTime,
        default=datetime.utcnow,
        nullable=False
    )

    orden = relationship(
        "OrdenReparacion",
        back_populates="archivos"
    )
"""Metadatos de adjuntos almacenados para una orden de reparación."""
