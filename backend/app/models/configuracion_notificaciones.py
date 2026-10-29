"""Interruptores de las categorías de alertas visibles en MotorDesk."""

from sqlalchemy import (
    Boolean,
    Column,
    Integer
)

from app.database.database import Base


class ConfiguracionNotificaciones(Base):
    """Preferencias únicas del taller para filtrar avisos del Dashboard."""


    __tablename__ = "configuracion_notificaciones"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    stock_bajo = Column(
        Boolean,
        nullable=False,
        default=True
    )

    pedidos_pendientes = Column(
        Boolean,
        nullable=False,
        default=True
    )

    garantias_pendientes = Column(
        Boolean,
        nullable=False,
        default=True
    )

    presupuestos_pendientes = Column(
        Boolean,
        nullable=False,
        default=True
    )

    citas_proximas = Column(
        Boolean,
        nullable=False,
        default=True
    )

    ausencias_personal = Column(
        Boolean,
        nullable=False,
        default=True
    )
