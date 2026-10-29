from sqlalchemy import (
    Column,
    ForeignKey,
    Integer,
    Table,
)

from app.database.database import Base


orden_usuarios = Table(
    "orden_usuarios",
    Base.metadata,
    Column(
        "orden_id",
        Integer,
        ForeignKey(
            "ordenes_reparacion.id",
            ondelete="CASCADE",
        ),
        primary_key=True,
    ),
    Column(
        "usuario_id",
        Integer,
        ForeignKey(
            "usuarios.id",
            ondelete="CASCADE",
        ),
        primary_key=True,
    ),
)
"""Tabla asociativa para asignar miembros del equipo a órdenes de reparación."""
