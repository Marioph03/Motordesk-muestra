"""Proveedor de recambios, documentos de compra y condiciones comerciales."""

from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Integer, String, Text

from app.database.database import Base

from sqlalchemy.orm import relationship


class Proveedor(Base):
    """Empresa proveedora que puede recibir pedidos, albaranes y devoluciones."""

    __tablename__ = "proveedores"

    id = Column(Integer, primary_key=True, index=True)
    codigo = Column(String(20), unique=True, index=True)

    nombre = Column(
        String(150),
        nullable=False
    )

    cif = Column(
        String(20),
        unique=True,
        nullable=False
    )

    telefono = Column(
        String(20)
    )

    email = Column(
        String(255)
    )

    direccion = Column(
        String(255)
    )

    ciudad = Column(
        String(100)
    )

    provincia = Column(
        String(100)
    )

    codigo_postal = Column(
        String(10)
    )

    observaciones = Column(Text)

    activo = Column(
        Boolean,
        default=True,
        nullable=False
    )

    created_at = Column(
        DateTime,
        default=datetime.utcnow,
        nullable=False
    )

    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )
    
    piezas = relationship(
    "Pieza",
    back_populates="proveedor"
    )   
    
    pedidos_compra = relationship(
    "PedidoCompra",
    back_populates="proveedor"
    )
