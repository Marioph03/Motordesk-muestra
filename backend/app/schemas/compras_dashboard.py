from pydantic import BaseModel


class ComprasResumenResponse(BaseModel):
    pedidos_total: int
    pedidos_pendientes: int
    albaranes_total: int
    albaranes_borrador: int
    facturas_total: int
    facturas_pendientes: int
    facturas_proximas_vencer: int
    devoluciones_total: int
    devoluciones_pendientes: int
"""Indicadores de compras usados en la vista de resumen del Dashboard."""
