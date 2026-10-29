"""Configuración segura de WhatsApp Business por empresa."""

from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app.database.database import Base


class ConfiguracionWhatsApp(Base):
    """Almacena los parámetros de integración de Meta sin exponer el token."""

    __tablename__ = "configuracion_whatsapp"

    id = Column(Integer, primary_key=True, index=True)

    # Una única configuración de WhatsApp por empresa.
    # La tabla real del proyecto se llama ``empresa`` (en singular).
    empresa_id = Column(
        Integer,
        ForeignKey("empresa.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )

    # Estado de la integración.
    activo = Column(Boolean, nullable=False, default=False)

    # Datos de Meta / WhatsApp Business.
    whatsapp_business_account_id = Column(String(100), nullable=True)
    phone_number_id = Column(String(100), nullable=True)
    numero_whatsapp = Column(String(30), nullable=True)

    # Nunca se guardará el token de Meta en texto plano.
    access_token_cifrado = Column(Text, nullable=True)

    empresa = relationship("Empresa", back_populates="configuracion_whatsapp")

    # Plantillas asociadas a esta configuración de WhatsApp Business.
    plantillas = relationship(
        "WhatsAppPlantilla",
        back_populates="configuracion",
        cascade="all, delete-orphan",
    )
