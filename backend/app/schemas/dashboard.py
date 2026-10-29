from pydantic import BaseModel
from datetime import datetime


class DashboardFactura(BaseModel):
    id: int
    numero: str
    estado: str
    total: float
    fecha_emision: datetime
    cliente: dict | None = None
    
    model_config = {"from_attributes": True}


class DashboardOrden(BaseModel):
    id: int
    numero: str
    estado: str
    fecha_entrada: datetime
    descripcion_averia: str
    importe_total: float
    vehiculo: dict | None = None
    
    model_config = {"from_attributes": True}


class DashboardFacturacionMes(BaseModel):
    periodo: str
    etiqueta: str
    total: float


class DashboardAlerta(BaseModel):
    tipo: str
    titulo: str
    mensaje: str
    cantidad: int
    ruta: str


class DashboardResponse(BaseModel):

    clientes: int
    vehiculos: int

    ordenes_abiertas: int
    ordenes_cerradas: int

    presupuestos: int
    stock_actual: float
    stock_bajo: int
    citas_hoy: int
    cobros_pendientes: int

    facturas: int

    facturacion_mes: float
    facturacion_anual: float
    facturacion_ultimos_meses: list[DashboardFacturacionMes]

    alertas: list[DashboardAlerta]

    ultimas_facturas: list[DashboardFactura]
    ultimas_ordenes: list[DashboardOrden]
"""Contrato del resumen operativo que consume la pantalla de inicio."""
