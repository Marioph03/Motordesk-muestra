from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from app.core.permissions import require_permission
from app.database.database import get_db
from app.schemas.ausencia_personal import (
    AusenciaPersonalCreate,
    AusenciaPersonalResponse,
    AusenciaPersonalUpdate,
)
from app.services.ausencia_personal_service import (
    AusenciaPersonalService,
)


router = APIRouter(
    prefix="/ausencias-personal",
    tags=["Disponibilidad del personal"],
)


@router.get("", response_model=list[AusenciaPersonalResponse])
def listar_ausencias(
    usuario_id: int | None = None,
    db: Session = Depends(get_db),
    usuario_actual=Depends(require_permission("personal.ver")),
):
    return AusenciaPersonalService.get_all(db, usuario_id)


@router.get("/rango", response_model=list[AusenciaPersonalResponse])
def listar_ausencias_por_rango(
    fecha_inicio: datetime,
    fecha_fin: datetime,
    usuario_id: int | None = None,
    db: Session = Depends(get_db),
    usuario_actual=Depends(require_permission("personal.ver")),
):
    try:
        return AusenciaPersonalService.get_by_rango(
            db,
            fecha_inicio,
            fecha_fin,
            usuario_id,
        )
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error))


@router.get("/usuario/{usuario_id}/disponible")
def comprobar_disponibilidad_usuario(
    usuario_id: int,
    fecha_inicio: datetime,
    fecha_fin: datetime,
    db: Session = Depends(get_db),
    usuario_actual=Depends(require_permission("personal.ver")),
):
    try:
        return {
            "usuario_id": usuario_id,
            "disponible": AusenciaPersonalService.usuario_disponible(
                db,
                usuario_id,
                fecha_inicio,
                fecha_fin,
            ),
        }
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error))


@router.get("/{ausencia_id}", response_model=AusenciaPersonalResponse)
def obtener_ausencia(
    ausencia_id: int,
    db: Session = Depends(get_db),
    usuario_actual=Depends(require_permission("personal.ver")),
):
    try:
        return AusenciaPersonalService.get_by_id(db, ausencia_id)
    except ValueError as error:
        raise HTTPException(status_code=404, detail=str(error))


@router.post(
    "",
    response_model=AusenciaPersonalResponse,
    status_code=status.HTTP_201_CREATED,
)
def crear_ausencia(
    datos: AusenciaPersonalCreate,
    db: Session = Depends(get_db),
    usuario_actual=Depends(require_permission("personal.editar")),
):
    try:
        return AusenciaPersonalService.create(db, datos)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error))


@router.patch("/{ausencia_id}", response_model=AusenciaPersonalResponse)
def actualizar_ausencia(
    ausencia_id: int,
    datos: AusenciaPersonalUpdate,
    db: Session = Depends(get_db),
    usuario_actual=Depends(require_permission("personal.editar")),
):
    try:
        return AusenciaPersonalService.update(db, ausencia_id, datos)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error))


@router.delete("/{ausencia_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_ausencia(
    ausencia_id: int,
    db: Session = Depends(get_db),
    usuario_actual=Depends(require_permission("personal.editar")),
):
    try:
        AusenciaPersonalService.delete(db, ausencia_id)
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    except ValueError as error:
        raise HTTPException(status_code=404, detail=str(error))
"""API de ausencias y disponibilidad del personal para planificación."""
