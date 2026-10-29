"""Configuración persistente de identidad, contacto y logo del taller."""

from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
)

from app.database.database import Base


class ConfiguracionTaller(Base):
    """Registro único con los datos corporativos reutilizados por documentos."""


    __tablename__ = "configuracion_taller"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    # =====================================================
    # IDENTIDAD
    # =====================================================

    nombre_comercial = Column(
        String(150),
        nullable=True
    )

    razon_social = Column(
        String(150),
        nullable=True
    )

    nif_cif = Column(
        String(20),
        nullable=True
    )

    # =====================================================
    # CONTACTO
    # =====================================================

    telefono = Column(
        String(30),
        nullable=True
    )

    email = Column(
        String(150),
        nullable=True
    )

    web = Column(
        String(200),
        nullable=True
    )

    # =====================================================
    # DIRECCIÓN
    # =====================================================

    direccion = Column(
        String(250),
        nullable=True
    )

    codigo_postal = Column(
        String(10),
        nullable=True
    )

    localidad = Column(
        String(100),
        nullable=True
    )

    provincia = Column(
        String(100),
        nullable=True
    )

    pais = Column(
        String(100),
        nullable=True,
        default="España"
    )

    # =====================================================
    # IDENTIDAD VISUAL
    # =====================================================

    logo_url = Column(
        Text,
        nullable=True
    )
