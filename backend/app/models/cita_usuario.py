from sqlalchemy import (
    Column,
    ForeignKey,
    Integer,
    Table
)

from app.database.database import Base


cita_usuarios = Table(
    "cita_usuarios",
    Base.metadata,

    Column(
        "cita_id",
        Integer,
        ForeignKey(
            "citas.id",
            ondelete="CASCADE"
        ),
        primary_key=True
    ),

    Column(
        "usuario_id",
        Integer,
        ForeignKey(
            "usuarios.id",
            ondelete="CASCADE"
        ),
        primary_key=True
    )
)
"""Tabla asociativa para asignar varios usuarios a una cita."""
