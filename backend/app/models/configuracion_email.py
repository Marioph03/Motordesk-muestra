"""Configuración SMTP cifrada y aislada por empresa."""

from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app.database.database import Base


class ConfiguracionEmail(Base):
    __tablename__ = "configuracion_email"

    id = Column(Integer, primary_key=True, index=True)
    empresa_id = Column(Integer, ForeignKey("empresa.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    activo = Column(Boolean, nullable=False, default=False)
    proveedor = Column(String(30), nullable=False, default="gmail")
    host = Column(String(255), nullable=False)
    puerto = Column(Integer, nullable=False, default=587)
    seguridad = Column(String(20), nullable=False, default="starttls")
    usuario = Column(String(255), nullable=False)
    remitente = Column(String(255), nullable=True)
    password_cifrada = Column(Text, nullable=True)
    metodo_autenticacion = Column(String(30), nullable=False, default="password")
    google_refresh_token_cifrada = Column(Text, nullable=True)
    microsoft_refresh_token_cifrada = Column(Text, nullable=True)

    empresa = relationship("Empresa", back_populates="configuracion_email")
