from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.core.security import get_current_user

from app.schemas.dashboard import DashboardResponse
from app.services.dashboard_service import DashboardService

router = APIRouter(
    prefix="/dashboard",
    tags=["Dashboard"]
)


@router.get(
    "/",
    response_model=DashboardResponse
)
def get_dashboard(
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return DashboardService.get_dashboard(
        db
    )
"""Endpoint autenticado del resumen operativo de la pantalla inicial."""
