from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.permissions import require_roles
from app.core.roles import RolUsuario
from app.database.database import get_db
from app.schemas.pieza import (
    PiezaCreate,
    PiezaUpdate,
    PiezaResponse
)
from app.services.pieza_service import PiezaService

from app.schemas.pagination import PaginationParams
from app.schemas.paginated_response import PaginatedResponse
from app.core.security import get_current_user

router = APIRouter(
    prefix="/ordenes-reparacion/{orden_id}/piezas",
    tags=["Piezas"],
    dependencies=[
        Depends(
            require_roles(
                RolUsuario.ADMINISTRADOR,
                RolUsuario.MECANICO
            )
        )
    ]
)


@router.get("/", response_model=list[PiezaResponse])
def get_piezas(
    orden_id: int,
    db: Session = Depends(get_db)
):
    return PiezaService.get_by_orden(
        db,
        orden_id
    )


@router.post("/", response_model=PiezaResponse, status_code=201)
def crear_pieza(
    orden_id: int,
    pieza: PiezaCreate,
    db: Session = Depends(get_db)
):
    try:
        return PiezaService.create(
            db,
            orden_id,
            pieza
        )
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )


@router.patch("/{pieza_id}", response_model=PiezaResponse)
def actualizar_pieza(
    orden_id: int,
    pieza_id: int,
    datos: PiezaUpdate,
    db: Session = Depends(get_db)
):
    try:
        return PiezaService.update(
            db,
            pieza_id,
            datos
        )
    except ValueError as e:
        raise HTTPException(
            status_code=404,
            detail=str(e)
        )


@router.delete("/{pieza_id}")
def eliminar_pieza(
    orden_id: int,
    pieza_id: int,
    db: Session = Depends(get_db)
):
    try:
        PiezaService.delete(
            db,
            pieza_id
        )

        return {
            "mensaje": "Pieza eliminada correctamente"
        }

    except ValueError as e:
        raise HTTPException(
            status_code=404,
            detail=str(e)
        )
"""Endpoints de piezas y consumos asociados a órdenes de reparación."""
