from sqlalchemy.orm import Session

from app.services.dashboard_service import DashboardService


DASHBOARD_TOOLS = [

    {
        "type": "function",

        "function": {

            "name":
                "obtener_dashboard",

            "description": (
                "Obtiene las métricas actuales del taller. "
                "Úsala para consultar facturación, órdenes "
                "abiertas o cerradas, presupuestos, clientes "
                "o vehículos."
            ),

            "parameters": {

                "type": "object",

                "properties": {},

                "additionalProperties": False
            }
        }
    }

]


def obtener_dashboard(
    db: Session
) -> dict:
    dashboard = DashboardService.get_dashboard(db)

    if hasattr(
        dashboard,
        "model_dump"
    ):
        return dashboard.model_dump()

    if isinstance(
        dashboard,
        dict
    ):
        return dashboard

    return {
        "facturacion_mes": getattr(
            dashboard,
            "facturacion_mes",
            0
        ),
        "facturacion_anual": getattr(
            dashboard,
            "facturacion_anual",
            0
        ),
        "ordenes_abiertas": getattr(
            dashboard,
            "ordenes_abiertas",
            0
        ),
        "ordenes_cerradas": getattr(
            dashboard,
            "ordenes_cerradas",
            0
        ),
        "presupuestos": getattr(
            dashboard,
            "presupuestos",
            0
        ),
        "clientes": getattr(
            dashboard,
            "clientes",
            0
        ),
        "vehiculos": getattr(
            dashboard,
            "vehiculos",
            0
        )
    }
"""Herramientas IA que consultan el resumen operativo del Dashboard."""
