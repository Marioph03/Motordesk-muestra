from datetime import datetime

from sqlalchemy.orm import relationship

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Integer,
    Numeric,
    String,
    Text
)

from app.database.database import Base


class Empresa(Base):

    __tablename__ = "empresa"


    # =========================================================
    # IDENTIFICACIÓN
    # =========================================================

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    nombre = Column(
        String(150),
        nullable=False
    )

    nombre_comercial = Column(
        String(150),
        nullable=False
    )

    nif = Column(
        String(20),
        nullable=False
    )


    # =========================================================
    # DIRECCIÓN
    # =========================================================

    direccion = Column(
        String(255),
        nullable=False
    )

    codigo_postal = Column(
        String(10),
        nullable=False
    )

    ciudad = Column(
        String(100),
        nullable=False
    )

    provincia = Column(
        String(100),
        nullable=False
    )


    # =========================================================
    # CONTACTO
    # =========================================================

    telefono = Column(
        String(30),
        nullable=False
    )

    email = Column(
        String(150),
        nullable=False
    )

    web = Column(
        String(150),
        nullable=True
    )


    # =========================================================
    # FACTURACIÓN
    # =========================================================

    iva_defecto = Column(
        Numeric(5, 2),
        default=21,
        nullable=False
    )

    moneda = Column(
        String(5),
        default="EUR",
        nullable=False
    )

    iban = Column(
        String(34),
        nullable=True
    )

    bic = Column(
        String(20),
        nullable=True
    )

    regimen_fiscal = Column(
        String(100),
        nullable=True
    )

    condiciones_factura = Column(
        Text,
        nullable=True
    )


    # =========================================================
    # PERSONALIZACIÓN
    # =========================================================

    logo = Column(
        String(255),
        nullable=True
    )

    color_primario = Column(
        String(7),
        default="#1F3D72",
        nullable=False
    )

    color_secundario = Column(
        String(7),
        default="#6C757D",
        nullable=False
    )


    # =========================================================
    # WHATSAPP BUSINESS
    # =========================================================

    whatsapp_conectado = Column(
        Boolean,
        default=False,
        nullable=False
    )

    whatsapp_waba_id = Column(
        String(100),
        nullable=True
    )

    whatsapp_phone_number_id = Column(
        String(100),
        nullable=True
    )

    whatsapp_access_token = Column(
        Text,
        nullable=True
    )


    # =========================================================
    # FECHAS
    # =========================================================

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
    
    usuarios = relationship(
    "Usuario",
    back_populates="empresa"
    )
    
    actividades = relationship(
    "Actividad",
    back_populates="empresa"
    )

    # Configuración única de la integración WhatsApp Business de la empresa.
    configuracion_whatsapp = relationship(
        "ConfiguracionWhatsApp",
        back_populates="empresa",
        uselist=False,
        cascade="all, delete-orphan",
    )
    configuracion_email = relationship(
        "ConfiguracionEmail",
        back_populates="empresa",
        uselist=False,
        cascade="all, delete-orphan",
    )
    certificado_electronico = relationship(
        "CertificadoElectronico",
        back_populates="empresa",
        uselist=False,
        cascade="all, delete-orphan"
    )

"""Datos históricos de empresa utilizados por integraciones y documentos previos."""
