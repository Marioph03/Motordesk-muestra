from datetime import date, timedelta

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.albaran_proveedor import AlbaranProveedor
from app.models.devolucion_proveedor import DevolucionProveedor
from app.models.factura_proveedor import FacturaProveedor
from app.models.pedido_compra import PedidoCompra


class ComprasDashboardService:
    @staticmethod
    def obtener_resumen(db: Session) -> dict[str, int]:
        contar = lambda modelo, *filtros: (
            db.query(func.count(modelo.id)).filter(*filtros).scalar() or 0
        )
        hoy = date.today()
        limite_vencimiento = hoy + timedelta(days=7)

        return {
            "pedidos_total": contar(PedidoCompra),
            "pedidos_pendientes": contar(
                PedidoCompra,
                PedidoCompra.estado.in_(("BORRADOR", "ENVIADO", "RECIBIDO_PARCIAL")),
            ),
            "albaranes_total": contar(AlbaranProveedor),
            "albaranes_borrador": contar(
                AlbaranProveedor,
                AlbaranProveedor.estado == "BORRADOR",
            ),
            "facturas_total": contar(FacturaProveedor),
            "facturas_pendientes": contar(
                FacturaProveedor,
                FacturaProveedor.estado_pago == "PENDIENTE",
            ),
            "facturas_proximas_vencer": contar(
                FacturaProveedor,
                FacturaProveedor.estado_pago == "PENDIENTE",
                FacturaProveedor.fecha_vencimiento.isnot(None),
                FacturaProveedor.fecha_vencimiento >= hoy,
                FacturaProveedor.fecha_vencimiento <= limite_vencimiento,
            ),
            "devoluciones_total": contar(DevolucionProveedor),
            "devoluciones_pendientes": contar(
                DevolucionProveedor,
                DevolucionProveedor.estado == "CONFIRMADA",
                DevolucionProveedor.resolucion == "PENDIENTE",
            ),
        }
"""Indicadores de compras y recepciones pendientes para el Dashboard."""
