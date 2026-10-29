"""Registro inalterable de eventos fiscales y encadenamiento VERI*FACTU."""

from datetime import datetime
from enum import Enum
from datetime import timezone

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


class TipoRegistroVerifactu(str, Enum):
    """Eventos fiscales que pueden formar parte de la cadena de huellas."""

    ALTA = "ALTA"
    ANULACION = "ANULACION"


class EstadoRegistroVerifactu(str, Enum):
    PENDIENTE = "PENDIENTE"
    ENVIANDO = "ENVIANDO"
    ACEPTADO = "ACEPTADO"
    ACEPTADO_CON_ERRORES = "ACEPTADO_CON_ERRORES"
    RECHAZADO = "RECHAZADO"
    ERROR = "ERROR"


class RegistroVerifactu(Base):
    """Evidencia persistente de alta o anulación vinculada a una factura."""

    __tablename__ = "registros_verifactu"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    factura_id = Column(
    Integer,
    ForeignKey(
        "facturas.id",
        ondelete="RESTRICT"
    ),
    nullable=False,
    index=True
    )

    tipo_registro = Column(
        String(20),
        nullable=False
    )

    estado = Column(
        String(30),
        default=EstadoRegistroVerifactu.PENDIENTE.value,
        nullable=False
    )

    # Huella SHA-256 del propio registro
    hash_registro = Column(
        String(64),
        nullable=False,
        unique=True
    )

    # Huella del registro inmediatamente anterior
    hash_anterior = Column(
        String(64),
        nullable=True
    )

    # Identificación del registro anterior
    factura_anterior_numero = Column(
        String(100),
        nullable=True
    )

    factura_anterior_fecha = Column(
        String(10),
        nullable=True
    )

    # XML exacto generado para el registro
    xml_registro = Column(
        Text,
        nullable=False
    )

    # Respuesta completa de AEAT
    respuesta_aeat = Column(
        Text,
        nullable=True
    )

    # Código/identificador devuelto por AEAT, si procede
    codigo_respuesta = Column(
        String(100),
        nullable=True
    )

    # Mensaje de error o validación
    mensaje_error = Column(
        Text,
        nullable=True
    )

    # Datos útiles para diagnóstico/reintentos
    intentos_envio = Column(
        Integer,
        default=0,
        nullable=False
    )

    fecha_generacion = Column(
    DateTime(timezone=True),
    default=lambda: datetime.now(timezone.utc),
    nullable=False
    )

    fecha_ultimo_intento = Column(
        DateTime(timezone=True),
        nullable=True
    )

    fecha_aceptacion = Column(
        DateTime(timezone=True),
        nullable=True
    )

    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    factura = relationship(
        "Factura",
        back_populates="registros_verifactu"
    )
