"""Preferencias comunes de contenido para presupuestos, pedidos y documentos."""

from sqlalchemy import (
    Boolean,
    Column,
    Integer,
    String,
    Text
)

from app.database.database import Base


class ConfiguracionDocumentos(Base):
    """Controla datos visibles, textos por defecto y validez de presupuestos."""


    __tablename__ = "configuracion_documentos"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    # =====================================================
    # DATOS DEL TALLER VISIBLES
    # =====================================================

    mostrar_telefono = Column(
        Boolean,
        nullable=False,
        default=True
    )

    mostrar_email = Column(
        Boolean,
        nullable=False,
        default=True
    )

    mostrar_direccion = Column(
        Boolean,
        nullable=False,
        default=True
    )

    mostrar_nif_cif = Column(
        Boolean,
        nullable=False,
        default=True
    )

    mostrar_web = Column(
        Boolean,
        nullable=False,
        default=False
    )

    # Cuenta de destino que el taller facilita cuando un cliente paga por
    # transferencia. No se usa para efectivo, tarjeta, Bizum ni otros cobros.
    iban_cobros = Column(
        String(34),
        nullable=True,
    )

    # =====================================================
    # PRESUPUESTOS
    # =====================================================

    validez_presupuesto_dias = Column(
        Integer,
        nullable=False,
        default=30
    )

    # =====================================================
    # TEXTOS
    # =====================================================

    pie_documentos = Column(
        Text,
        nullable=True
    )

    observaciones_presupuesto = Column(
        Text,
        nullable=True
    )

    observaciones_orden = Column(
        Text,
        nullable=True
    )

    observaciones_pedido_compra = Column(
        Text,
        nullable=True
    )
