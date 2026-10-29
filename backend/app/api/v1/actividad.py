from datetime import date

from fastapi import (
    APIRouter,
    Depends,
    HTTPException
)

from sqlalchemy.orm import Session

from app.core.security import get_current_user
from app.database.database import get_db

from app.schemas.actividad import ActividadResponse
from app.schemas.actividad_filtro import ActividadFiltro
from app.schemas.paginated_response import PaginatedResponse
from app.schemas.pagination import PaginationParams

from app.services.actividad_service import ActividadService


router = APIRouter(
    prefix="/actividad",
    tags=["Actividad"],
    dependencies=[Depends(get_current_user)]
)


# =========================================================
# LISTADO PAGINADO
# =========================================================

@router.get(
    "/",
    response_model=PaginatedResponse[ActividadResponse]
)
def get_actividad(
    pagination: PaginationParams = Depends(),

    usuario_id: int | None = None,
    modulo: str | None = None,
    accion: str | None = None,
    fecha_desde: date | None = None,
    fecha_hasta: date | None = None,

    db: Session = Depends(get_db)
):

    filtro = ActividadFiltro(
        usuario_id=usuario_id,
        modulo=modulo,
        accion=accion,
        fecha_desde=fecha_desde,
        fecha_hasta=fecha_hasta
    )

    return ActividadService.get_paginated(
        db,
        pagination,
        filtro
    )


# =========================================================
# OBTENER POR ID
# =========================================================

@router.get(
    "/{actividad_id}",
    response_model=ActividadResponse
)
def get_actividad_by_id(
    actividad_id: int,
    db: Session = Depends(get_db)
):

    try:

        return ActividadService.get_by_id(
            db,
            actividad_id
        )

    except ValueError:

        raise HTTPException(
            status_code=404,
            detail="Actividad no encontrada"
        )
"""Endpoints de auditoría funcional y actividad reciente del sistema."""
