from datetime import datetime

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import relationship

from app.database.database import Base


class CertificadoElectronico(Base):

    __tablename__ = "certificados_electronicos"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    empresa_id = Column(
        Integer,
        ForeignKey(
            "empresa.id",
            ondelete="CASCADE"
        ),
        nullable=False,
        unique=True,
        index=True
    )

    nombre_archivo = Column(
        String(255),
        nullable=False
    )

    ruta_archivo = Column(
        String(500),
        nullable=False
    )

    password_cifrada = Column(
        Text,
        nullable=False
    )

    titular = Column(
        String(255),
        nullable=True
    )

    nif_titular = Column(
        String(20),
        nullable=True
    )

    emisor = Column(
        String(255),
        nullable=True
    )

    fecha_validez_desde = Column(
        DateTime,
        nullable=True
    )

    fecha_caducidad = Column(
        DateTime,
        nullable=True
    )

    activo = Column(
        Boolean,
        default=True,
        nullable=False
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

    empresa = relationship(
        "Empresa",
        back_populates="certificado_electronico"
    )