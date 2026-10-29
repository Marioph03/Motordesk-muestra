from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel


class TrabajoFrecuenteInforme(BaseModel):
    descripcion: str
    total: int


class ResumenOrdenesInforme(BaseModel):
    total: int
    cerradas: int
    facturadas: int
    garantias: int
    presupuestos: int
    en_curso: int
    trabajos_frecuentes: list[TrabajoFrecuenteInforme]


class ResumenFacturacionInforme(BaseModel):
    facturas_emitidas: int
    facturas_anuladas: int
    total_facturado: Decimal
    ticket_medio: Decimal
    evolucion_diaria: list["FacturacionDiaInforme"]


class FacturacionDiaInforme(BaseModel):
    fecha: date
    total: Decimal


class ArticuloConsumidoInforme(BaseModel):
    articulo_id: int
    referencia: str
    nombre: str
    cantidad_consumida: Decimal


class ResumenStockInforme(BaseModel):
    movimientos: int
    unidades_consumidas: Decimal
    entradas_compra: Decimal
    ajustes_positivos: Decimal
    ajustes_negativos: Decimal
    articulos_mas_consumidos: list[ArticuloConsumidoInforme]


class ProveedorCompraInforme(BaseModel):
    proveedor_id: int
    nombre: str
    pedidos: int
    total_compras: Decimal


class ResumenComprasInforme(BaseModel):
    pedidos: int
    recibidos: int
    recibidos_parciales: int
    cancelados: int
    total_compras: Decimal
    ticket_medio: Decimal
    proveedores_top: list[ProveedorCompraInforme]


class ResumenIvaInforme(BaseModel):
    iva_repercutido: Decimal
    iva_soportado: Decimal
    diferencia: Decimal


class ResumenGarantiasInforme(BaseModel):
    total: int
    abiertas: int
    en_revision: int
    aprobadas: int
    rechazadas: int
    en_reparacion: int
    resueltas: int
    tiempo_medio_resolucion_horas: float
    tiempo_medio_resolucion_dias: float


class PersonalUsuarioInforme(BaseModel):
    usuario_id: int
    nombre: str
    rol: str
    ordenes_asignadas: int
    citas_asignadas: int
    ausencias: int
    dias_ausencia: float
    actividad_total: int


class ResumenPersonalInforme(BaseModel):
    usuarios_activos: int
    detalle: list[PersonalUsuarioInforme]


class ResumenGeneralInforme(BaseModel):

    fecha_inicio: datetime
    fecha_fin: datetime

    ordenes: ResumenOrdenesInforme
    facturacion: ResumenFacturacionInforme
    stock: ResumenStockInforme
    compras: ResumenComprasInforme
    iva: ResumenIvaInforme
    garantias: ResumenGarantiasInforme
    personal: ResumenPersonalInforme
"""Contratos de agregados de informes por facturación, stock y personal."""
