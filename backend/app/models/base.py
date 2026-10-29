from sqlalchemy import Boolean, Column, DateTime, Integer
from sqlalchemy.sql import func

from app.database.database import Base


class BaseModel(Base):
    __abstract__ = True

    id = Column(Integer, primary_key=True, index=True)

    activo = Column(Boolean, default=True)

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now()
    )

    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now()
    )
"""Elementos base compartidos por los modelos de persistencia del dominio."""
