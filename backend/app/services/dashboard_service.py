"""Resumen inmediato y alertas configurables que alimentan el Dashboard."""

from sqlalchemy.orm import Session

from app.repositories.articulo_stock_repository import ArticuloStockRepository
from app.repositories.ausencia_personal_repository import AusenciaPersonalRepository
from app.repositories.cita_repository import CitaRepository
from app.repositories.dashboard_repository import DashboardRepository
from app.repositories.orden_reparacion_repository import OrdenReparacionRepository
from app.repositories.pedido_compra_repository import PedidoCompraRepository
from app.services.configuracion_notificaciones_service import ConfiguracionNotificacionesService


class DashboardService:
    """Compone indicadores de hoy sin duplicar la lógica de cada módulo."""


    @staticmethod
    def get_dashboard(
        db: Session
    ):
        dashboard = DashboardRepository.get_stats(db)
        configuracion = ConfiguracionNotificacionesService.obtener(db)
        alertas = []

        if configuracion.stock_bajo:
            articulos = ArticuloStockRepository.get_stock_bajo(db)
            if articulos:
                alertas.append({
                    "tipo": "STOCK",
                    "titulo": "Stock bajo",
                    "mensaje": f"{len(articulos)} artículos necesitan reposición",
                    "cantidad": len(articulos),
                    "ruta": "/stock",
                })

        if configuracion.pedidos_pendientes:
            pedidos = PedidoCompraRepository.get_pendientes(db)
            if pedidos:
                alertas.append({
                    "tipo": "PEDIDO",
                    "titulo": "Pedidos pendientes",
                    "mensaje": f"{len(pedidos)} pedidos pendientes de recibir",
                    "cantidad": len(pedidos),
                    "ruta": "/compras",
                })

        if configuracion.garantias_pendientes:
            garantias = OrdenReparacionRepository.get_garantias_pendientes(db)
            if garantias:
                alertas.append({
                    "tipo": "GARANTIA",
                    "titulo": "Garantías pendientes",
                    "mensaje": f"{len(garantias)} garantías requieren atención",
                    "cantidad": len(garantias),
                    "ruta": "/ordenes",
                })

        if configuracion.presupuestos_pendientes:
            presupuestos = OrdenReparacionRepository.get_presupuestos_pendientes(db)
            if presupuestos:
                alertas.append({
                    "tipo": "PRESUPUESTO",
                    "titulo": "Presupuestos pendientes",
                    "mensaje": f"{len(presupuestos)} presupuestos esperan respuesta",
                    "cantidad": len(presupuestos),
                    "ruta": "/ordenes",
                })

        if configuracion.citas_proximas:
            citas = CitaRepository.get_proximas(db)
            if citas:
                alertas.append({
                    "tipo": "CITA",
                    "titulo": "Citas próximas",
                    "mensaje": f"{len(citas)} citas previstas en las próximas 24 horas",
                    "cantidad": len(citas),
                    "ruta": "/agenda",
                })

        if configuracion.ausencias_personal:
            ausencias = AusenciaPersonalRepository.get_hoy(db)
            if ausencias:
                alertas.append({
                    "tipo": "PERSONAL",
                    "titulo": "Ausencias de personal",
                    "mensaje": f"{len(ausencias)} personas no disponibles hoy",
                    "cantidad": len(ausencias),
                    "ruta": "/personal",
                })

        dashboard["alertas"] = alertas
        return dashboard
