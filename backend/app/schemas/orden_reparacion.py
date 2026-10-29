"""Contratos de creación, edición y lectura de órdenes de reparación."""

from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.vehiculo import VehiculoSimple
from app.schemas.vehicle_damage import VehicleDamage


# =========================================================
# DAÑOS DEL VEHÍCULO
# =========================================================

class DanoVehiculo(BaseModel):
    zona: str
    tipo: str
    comentario: str | None = None


# =========================================================
# BASE
# =========================================================

class OrdenReparacionBase(BaseModel):
    vehiculo_id: int
    descripcion_averia: str
    kilometros_entrada: int | None = Field(default=None, ge=0)
    vehicle_damage: VehicleDamage | None = None


# =========================================================
# CREATE
# =========================================================

class OrdenReparacionCreate(OrdenReparacionBase):
    tipo: str = "OR"

    garantia: bool = False
    garantia_meses: int | None = None

    vehicle_damage: VehicleDamage | None = None

    presupuesto_origen_id: int | None = None
    orden_origen_garantia_id: int | None = None
    factura_origen_garantia_id: int | None = None
    cita_origen_id: int | None = None

    usuarios_ids: list[int] = Field(
        default_factory=list
    )

    diagnostico: str | None = None
    observaciones: str | None = None
    observaciones_internas: str | None = None


# =========================================================
# UPDATE
# =========================================================

class OrdenReparacionUpdate(BaseModel):
    vehiculo_id: Optional[int] = None

    kilometros_entrada: int | None = Field(default=None, ge=0)

    descripcion_averia: Optional[str] = None

    estado: Optional[str] = None

    fecha_salida: Optional[datetime] = None

    diagnostico: Optional[str] = None

    observaciones: Optional[str] = None

    observaciones_internas: Optional[str] = None

    danos: Optional[list[DanoVehiculo]] = None

    tipo: str | None = None

    garantia: bool | None = None

    garantia_meses: int | None = None

    vehicle_damage: VehicleDamage | None = None

    usuarios_ids: list[int] | None = None


# =========================================================
# USUARIO ASIGNADO
# =========================================================

class UsuarioOrdenResponse(BaseModel):
    id: int
    nombre: str
    apellidos: str
    rol: str

    model_config = ConfigDict(
        from_attributes=True
    )


# =========================================================
# RESPONSE
# =========================================================

class OrdenReparacionResponse(BaseModel):
    id: int
    numero: str

    vehiculo_id: int
    vehiculo: VehiculoSimple

    usuarios_asignados: list[
        UsuarioOrdenResponse
    ] = Field(
        default_factory=list
    )

    presupuesto_origen_id: int | None = None
    orden_origen_garantia_id: int | None = None
    factura_origen_garantia_id: int | None = None
    cita_origen_id: int | None = None

    fecha_entrada: datetime
    fecha_salida: datetime | None
    kilometros_entrada: int | None

    estado: str

    fecha_envio_presupuesto: datetime | None = None
    canal_envio_presupuesto: str | None = None
    fecha_respuesta_presupuesto: datetime | None = None

    resolucion_garantia: str | None = None
    fecha_resolucion_garantia: datetime | None = None

    descripcion_averia: str

    diagnostico: str | None
    observaciones: str | None
    observaciones_internas: str | None

    danos: list[DanoVehiculo] | None

    vehicle_damage: VehicleDamage | None = None

    total_mano_obra: Decimal
    total_piezas: Decimal
    importe_total: Decimal

    coste_asumido_taller: Decimal = Decimal("0")
    trabajos_no_cubiertos: Decimal = Decimal("0")
    iva_cliente_garantia: Decimal = Decimal("0")
    total_cliente_garantia: Decimal = Decimal("0")

    subtotal: Decimal = Decimal("0")

    tipo: str

    base_imponible: Decimal
    iva: Decimal

    garantia: bool
    garantia_meses: int | None

    model_config = ConfigDict(
        from_attributes=True
    )
