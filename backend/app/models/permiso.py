from sqlalchemy import (
    Column,
    Integer,
    String
)

from sqlalchemy.orm import relationship

from app.database.database import Base


class Permiso(Base):

    __tablename__ = "permisos"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    codigo = Column(
        String(100),
        unique=True,
        nullable=False,
        index=True
    )

    nombre = Column(
        String(150),
        nullable=False
    )

    modulo = Column(
        String(50),
        nullable=False,
        index=True
    )

    descripcion = Column(
        String(255),
        nullable=True
    )

    roles = relationship(
        "Rol",
        secondary="rol_permisos",
        back_populates="permisos"
    )
"""Permiso granular identificable por código y agrupado por módulo."""
