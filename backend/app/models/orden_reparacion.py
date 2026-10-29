"""Modelo de órdenes de reparación y sus variantes de presupuesto/garantía."""

from datetime import datetime
from enum import Enum

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    JSON
)
from sqlalchemy.orm import relationship

from app.database.database import Base
from sqlalchemy.dialects.postgresql import JSONB
from app.models.orden_usuario import orden_usuarios


class EstadoReparacion(str, Enum):
    """Estados agrupados por tipo de documento dentro del mismo modelo."""

    # Órdenes de reparación
    ABIERTA = "Abierta"
    EN_PROCESO = "En proceso"
    CERRADA = "Cerrada"
    FACTURADA = "Facturada"
    ANULADA = "Anulada"

    # Presupuestos
    BORRADOR = "Borrador"
    ENVIADO = "Enviado"
    ACEPTADO = "Aceptado"
    RECHAZADO = "Rechazado"

    # Garantías
    GARANTIA_ABIERTA = "Garantía abierta"
    GARANTIA_REVISION = "En revisión"
    GARANTIA_APROBADA = "Garantía aprobada"
    GARANTIA_RECHAZADA = "Garantía rechazada"
    GARANTIA_REPARACION = "En reparación"
    GARANTIA_RESUELTA = "Resuelta"


class OrdenReparacion(Base):
    """Orden operativa de un vehículo; los importes se calculan en servicios."""
    __tablename__ = "ordenes_reparacion"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    numero = Column(
        String(20),
        unique=True,
        nullable=False
    )

    tipo = Column(
        String(2),
        nullable=False,
        default="OR"
    )

    total_mano_obra = Column(
        Numeric(10, 2),
        default=0,
        nullable=False
    )

    total_piezas = Column(
        Numeric(10, 2),
        default=0,
        nullable=False
    )

    subtotal = Column(
        Numeric(10, 2),
        default=0,
        nullable=False
    )

    base_imponible = Column(
        Numeric(10, 2),
        default=0,
        nullable=False
    )
    
    iva = Column(
        Numeric(10, 2),
        default=0,
        nullable=False
    )

    importe_total = Column(
        Numeric(10, 2),
        default=0,
        nullable=False
    )

    garantia = Column(
        Boolean,
        default=False,
        nullable=False
    )

    garantia_meses = Column(
        Integer,
        nullable=True
    )

    vehiculo_id = Column(
        Integer,
        ForeignKey("vehiculos.id"),
        nullable=False
    )

    fecha_entrada = Column(
        DateTime,
        default=datetime.utcnow,
        nullable=False
    )

    fecha_salida = Column(
        DateTime,
        nullable=True
    )

    # Lectura del cuentakilómetros al recibir el vehículo. Permanece ligada a
    # esta orden como dato histórico, aunque el vehículo se actualice después.
    kilometros_entrada = Column(
        Integer,
        nullable=True,
    )

    estado = Column(
        String(20),
        default=EstadoReparacion.ABIERTA.value,
        nullable=False
    )

    coste_asumido_taller = Column(Numeric(10, 2), default=0, nullable=False)
    trabajos_no_cubiertos = Column(Numeric(10, 2), default=0, nullable=False)
    iva_cliente_garantia = Column(Numeric(10, 2), default=0, nullable=False)
    total_cliente_garantia = Column(Numeric(10, 2), default=0, nullable=False)

    fecha_envio_presupuesto = Column(
        DateTime,
        nullable=True
    )

    canal_envio_presupuesto = Column(
        String(20),
        nullable=True
    )

    fecha_respuesta_presupuesto = Column(
        DateTime,
        nullable=True
    )

    resolucion_garantia = Column(
        Text,
        nullable=True
    )

    fecha_resolucion_garantia = Column(
        DateTime,
        nullable=True,
        index=True,
    )

    descripcion_averia = Column(
        Text,
        nullable=False
    )

    diagnostico = Column(
        Text
    )

    observaciones = Column(
        Text
    )

    observaciones_internas = Column(
        Text
    )

    danos = Column(
        JSON,
        nullable=True
    )

    vehicle_damage = Column(
    JSONB,
    nullable=True,
    default=dict
    )

    presupuesto_origen_id = Column(
    Integer,
    ForeignKey(
        "ordenes_reparacion.id",
        ondelete="SET NULL"
    ),
    nullable=True
    )

    # Referencias de una reparación realizada en garantía.
    orden_origen_garantia_id = Column(
        Integer,
        ForeignKey("ordenes_reparacion.id", ondelete="SET NULL"),
        nullable=True
    )

    factura_origen_garantia_id = Column(
        Integer,
        ForeignKey("facturas.id", ondelete="SET NULL"),
        nullable=True
    )

    vehiculo = relationship(
        "Vehiculo",
        back_populates="ordenes_reparacion"
    )

    mano_obra = relationship(
        "ManoObra",
        back_populates="orden",
        cascade="all, delete-orphan"
    )

    piezas = relationship(
        "Pieza",
        back_populates="orden",
        cascade="all, delete-orphan"
    )
    
    facturas = relationship(
        "Factura",
        back_populates="orden",
        foreign_keys="Factura.orden_id"
    )   
    
    archivos = relationship(
    "ArchivoOrden",
    back_populates="orden",
    cascade="all, delete-orphan"
    )
    
    presupuesto_origen = relationship(
    "OrdenReparacion",
    remote_side=[id],
    foreign_keys=[presupuesto_origen_id],
    back_populates="ordenes_generadas"
    )

    ordenes_generadas = relationship(
    "OrdenReparacion",
    foreign_keys=[presupuesto_origen_id],
    back_populates="presupuesto_origen"
    )

    orden_origen_garantia = relationship(
        "OrdenReparacion",
        remote_side=[id],
        foreign_keys=[orden_origen_garantia_id],
        back_populates="ordenes_garantia_derivadas"
    )

    ordenes_garantia_derivadas = relationship(
        "OrdenReparacion",
        foreign_keys=[orden_origen_garantia_id],
        back_populates="orden_origen_garantia"
    )

    factura_origen_garantia = relationship(
        "Factura",
        foreign_keys=[factura_origen_garantia_id]
    )

    cita_origen_id = Column(
    Integer,
    ForeignKey(
        "citas.id",
        ondelete="SET NULL"
    ),
    nullable=True
    )
    
    cita_origen = relationship(
    "Cita",
    foreign_keys=[cita_origen_id]
    )

    usuarios_asignados = relationship(
        "Usuario",
        secondary="orden_usuarios",
        back_populates="ordenes_asignadas",
    )
