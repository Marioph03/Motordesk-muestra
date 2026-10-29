from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from app.database.database import Base


class WhatsAppPlantilla(Base):
    __tablename__ = "whatsapp_plantillas"

    id = Column(Integer, primary_key=True, index=True)

    configuracion_id = Column(
        Integer,
        ForeignKey(
            "configuracion_whatsapp.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    # Tipo interno utilizado por MotorDesk:
    # FACTURA, PRESUPUESTO, RECORDATORIO_CITA...
    tipo = Column(
        String(50),
        nullable=False,
    )

    # Nombre exacto de la plantilla registrada en Meta
    nombre_meta = Column(
        String(150),
        nullable=False,
    )

    # Ej.: es, es_ES...
    idioma = Column(
        String(20),
        nullable=False,
        default="es",
    )

    # Estado conocido en Meta:
    # PENDING, APPROVED, REJECTED, etc.
    estado = Column(
        String(30),
        nullable=False,
        default="PENDING",
    )

    configuracion = relationship(
        "ConfiguracionWhatsApp",
        back_populates="plantillas",
    )