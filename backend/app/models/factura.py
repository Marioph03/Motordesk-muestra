"""Modelo de facturas, estado fiscal y estado económico de cobro."""

from datetime import datetime
from enum import Enum

from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    Boolean
)
from sqlalchemy.orm import relationship

from app.database.database import Base


class TipoDocumento(str, Enum):
    PROFORMA = "PROFORMA"
    FACTURA = "FACTURA"
    PRESUPUESTO = "PRESUPUESTO"
    ALBARAN = "ALBARAN"
    ABONO = "ABONO"


class TipoFactura(str, Enum):
    REPARACION = "REPARACION"
    PRESUPUESTO = "PRESUPUESTO"
    GARANTIA = "GARANTIA"
    RECAMBIO = "RECAMBIO"
    VENTAS_COMISIONES = "VENTAS_COMISIONES"


class EstadoFactura(str, Enum):
    BORRADOR = "BORRADOR"
    EMITIDA = "EMITIDA"
    ANULADA = "ANULADA"

class EstadoCobro(str, Enum):
    PENDIENTE = "PENDIENTE"
    PARCIAL = "PARCIAL"
    PAGADA = "PAGADA"

class Factura(Base):
    """Documento facturable asociado a cliente y, opcionalmente, a una orden.

    El pendiente real se calcula desde pagos registrados; ``estado_cobro`` es
    un indicador operativo y no debe usarse como cálculo económico aislado.
    """
    __tablename__ = "facturas"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    numero = Column(
        String(30),
        unique=True,
        nullable=False
    )

    # Conserva cómo se creó cada factura, aunque el modo se cambie después.
    es_prueba = Column(
        Boolean,
        nullable=False,
        default=False,
        index=True,
    )

    modo_facturacion = Column(
        String(20),
        nullable=True,
    )

    tipo_documento = Column(
        String(20),
        nullable=False
    )

    tipo_factura = Column(
        String(20),
        nullable=False
    )

    estado = Column(
        String(20),
        default=EstadoFactura.BORRADOR.value,
        nullable=False
    )

    cliente_id = Column(
        Integer,
        ForeignKey("clientes.id"),
        nullable=False
    )

    vehiculo_id = Column(
        Integer,
        ForeignKey("vehiculos.id")
    )

    orden_id = Column(
        Integer,
        ForeignKey("ordenes_reparacion.id"),
        # Una factura manual puede no estar vinculada a una orden.
        nullable=True
    )

    # Una venta directa de almacén puede convertirse en una única factura de
    # recambio. La restricción unique evita duplicarla por doble clic o dos
    # usuarios trabajando a la vez.
    subtotal = Column(
        Numeric(10, 2),
        default=0,
        nullable=False
    )

    descuento_porcentaje = Column(
        Numeric(5, 2),
        default=0,
        nullable=False
    )

    base_imponible = Column(
        Numeric(10, 2),
        default=0,
        nullable=False
    )

    iva = Column(
        Numeric(5, 2),
        default=21,
        nullable=False
    )

    cuota_iva = Column(
        Numeric(10, 2),
        default=0,
        nullable=False
    )

    total = Column(
        Numeric(10, 2),
        default=0,
        nullable=False
    )

    observaciones = Column(
        Text
    )

    fecha_emision = Column(
        DateTime,
        default=datetime.utcnow,
        nullable=False
    )

    estado_cobro = Column(
    String(20),
    default=EstadoCobro.PENDIENTE.value,
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

    enviada_verifactu = Column(
        Boolean,
        default=False,
        nullable=False
    )

    hash_verifactu = Column(
        String(255),
        nullable=True
    )

    fecha_envio_verifactu = Column(
        DateTime,
        nullable=True
    )

    lineas = relationship(
        "FacturaLinea",
        back_populates="factura",
        cascade="all, delete-orphan",
        order_by="FacturaLinea.id",
    )
    
    cliente = relationship(
    "Cliente",
    back_populates="facturas"
    )

    vehiculo = relationship(
        "Vehiculo",
        back_populates="facturas"
        )

    orden = relationship(
        "OrdenReparacion",
        back_populates="facturas",
        foreign_keys=[orden_id]
        )

    albaranes_venta = relationship(
        "FacturaAlbaranVenta",
        back_populates="factura",
        cascade="all, delete-orphan",
    )

    pagos = relationship(
    "PagoFactura",
    back_populates="factura",
    cascade="all, delete-orphan"
    )
    
    registros_verifactu = relationship(
    "RegistroVerifactu",
    back_populates="factura",
    order_by="RegistroVerifactu.id"
    )

    facturae_destino = relationship(
        "FacturaeDestino",
        back_populates="factura",
        uselist=False,
        cascade="all, delete-orphan",
    )
