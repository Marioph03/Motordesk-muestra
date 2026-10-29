from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.permissions import require_roles
from app.core.roles import RolUsuario
from app.database.database import get_db
from app.schemas.mano_obra import (
    ManoObraCreate,
    ManoObraUpdate,
    ManoObraResponse
)
from app.services.mano_obra_service import ManoObraService
from app.core.security import get_current_user
from app.schemas.pagination import PaginationParams
from app.schemas.paginated_response import PaginatedResponse

router = APIRouter(
    prefix="/ordenes-reparacion/{orden_id}/mano-obra",
    tags=["Mano de Obra"],
    dependencies=[
        Depends(
            require_roles(
                RolUsuario.ADMINISTRADOR,
                RolUsuario.MECANICO
            )
        )
    ]
)

@router.get("/", response_model=list[ManoObraResponse])
def get_lineas(
    orden_id: int,
    db: Session = Depends(get_db)
):
    try:
        return ManoObraService.get_by_orden(
            db,
            orden_id
        )
    except ValueError as e:
        raise HTTPException(
            status_code=404,
            detail=str(e)
        )


@router.post("/", response_model=ManoObraResponse, status_code=201)
def crear_linea(
    orden_id: int,
    mano_obra: ManoObraCreate,
    db: Session = Depends(get_db)
):
    try:
        return ManoObraService.create(
            db,
            orden_id,
            mano_obra
        )
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )


@router.patch("/{linea_id}", response_model=ManoObraResponse)
def actualizar_linea(
    orden_id: int,
    linea_id: int,
    datos: ManoObraUpdate,
    db: Session = Depends(get_db)
):
    try:
        return ManoObraService.update(
            db,
            linea_id,
            datos
        )
    except ValueError as e:
        raise HTTPException(
            status_code=404,
            detail=str(e)
        )


@router.delete("/{linea_id}")
def eliminar_linea(
    orden_id: int,
    linea_id: int,
    db: Session = Depends(get_db)
):
    try:
        ManoObraService.delete(
            db,
            linea_id
        )

        return {
            "mensaje": "Línea eliminada correctamente"
        }

    except ValueError as e:
        raise HTTPException(
            status_code=404,
            detail=str(e)
        )
"""Endpoints de trabajos de mano de obra facturables en órdenes."""
