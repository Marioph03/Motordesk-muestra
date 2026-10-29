from sqlalchemy import Boolean, Column, Integer, String

from app.database.database import Base


class ConfiguracionFacturacion(Base):
    __tablename__ = "configuracion_facturacion"

    id = Column(Integer, primary_key=True, index=True)

    # El modo seguro por defecto nunca debe realizar comunicaciones fiscales.
    modo_facturacion = Column(String(20), nullable=False, default="PRUEBAS")
    serie_pruebas = Column(String(20), nullable=False, default="TP")
    serie_facturas = Column(String(20), nullable=False, default="F")
    permitir_envio_aeat = Column(Boolean, nullable=False, default=False)
"""Configuración fiscal única de series, pruebas y envío VERI*FACTU."""
