from sqlalchemy import (
    Column,
    ForeignKey,
    Integer,
    Table
)

from app.database.database import Base


rol_permisos = Table(
    "rol_permisos",
    Base.metadata,

    Column(
        "rol_id",
        Integer,
        ForeignKey(
            "roles.id",
            ondelete="CASCADE"
        ),
        primary_key=True
    ),

    Column(
        "permiso_id",
        Integer,
        ForeignKey(
            "permisos.id",
            ondelete="CASCADE"
        ),
        primary_key=True
    )
)
"""Tabla asociativa que materializa los permisos concedidos a cada rol."""
