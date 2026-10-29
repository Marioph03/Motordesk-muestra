from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.permissions import require_permission
from app.database.database import get_db
from app.models.usuario import Usuario
from app.schemas.compras_dashboard import ComprasResumenResponse
from app.services.compras_dashboard_service import ComprasDashboardService


router = APIRouter(prefix="/compras", tags=["Compras"])


@router.get("/resumen", response_model=ComprasResumenResponse)
def obtener_resumen(
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_permission("compras.ver")),
):
    return ComprasDashboardService.obtener_resumen(db)
"""Indicadores de compras mostrados en el Dashboard operativo."""
