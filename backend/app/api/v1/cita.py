"""Endpoints de citas; el servicio valida horarios, solapes y personal."""

from datetime import datetime

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Response,
    status,
)
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.schemas.cita import (
    CitaCreate,
    CitaResponse,
    CitaUpdate,
)
from app.services.cita_service import CitaService


router = APIRouter(
    prefix="/citas",
    tags=["Citas"]
)


@router.get(
    "",
    response_model=list[CitaResponse]
)
def listar_citas(
    db: Session = Depends(get_db)
):
    return CitaService.get_all(db)


@router.get(
    "/rango",
    response_model=list[CitaResponse]
)
def listar_citas_por_rango(
    fecha_inicio: datetime,
    fecha_fin: datetime,
    db: Session = Depends(get_db)
):
    try:
        return CitaService.get_by_rango(
            db,
            fecha_inicio,
            fecha_fin
        )

    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )


@router.get(
    "/{cita_id}",
    response_model=CitaResponse
)
def obtener_cita(
    cita_id: int,
    db: Session = Depends(get_db)
):
    try:
        return CitaService.get_by_id(
            db,
            cita_id
        )

    except ValueError as e:
        raise HTTPException(
            status_code=404,
            detail=str(e)
        )


@router.post(
    "",
    response_model=CitaResponse,
    status_code=status.HTTP_201_CREATED
)
def crear_cita(
    datos: CitaCreate,
    db: Session = Depends(get_db)
):
    try:
        return CitaService.create(
            db,
            datos
        )

    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )


@router.patch(
    "/{cita_id}",
    response_model=CitaResponse
)
def actualizar_cita(
    cita_id: int,
    datos: CitaUpdate,
    db: Session = Depends(get_db)
):
    try:
        return CitaService.update(
            db,
            cita_id,
            datos
        )

    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )


@router.post("/{cita_id}/crear-orden")
def crear_orden_desde_cita(
    cita_id: int,
    db: Session = Depends(get_db),
):
    try:
        return CitaService.crear_orden_desde_cita(db, cita_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{cita_id}/confirmar", response_model=CitaResponse)
def confirmar_cita(cita_id: int, db: Session = Depends(get_db)):
    try: return CitaService.confirmar(db, cita_id)
    except ValueError as e: raise HTTPException(status_code=400, detail=str(e))

@router.post("/{cita_id}/en-taller", response_model=CitaResponse)
def marcar_en_taller(cita_id: int, db: Session = Depends(get_db)):
    try: return CitaService.marcar_en_taller(db, cita_id)
    except ValueError as e: raise HTTPException(status_code=400, detail=str(e))

@router.post("/{cita_id}/completar", response_model=CitaResponse)
def completar_cita(cita_id: int, db: Session = Depends(get_db)):
    try: return CitaService.completar(db, cita_id)
    except ValueError as e: raise HTTPException(status_code=400, detail=str(e))

@router.post("/{cita_id}/cancelar", response_model=CitaResponse)
def cancelar_cita(cita_id: int, db: Session = Depends(get_db)):
    try: return CitaService.cancelar(db, cita_id)
    except ValueError as e: raise HTTPException(status_code=400, detail=str(e))

@router.post("/{cita_id}/no-presentado", response_model=CitaResponse)
def no_presentado(cita_id: int, db: Session = Depends(get_db)):
    try: return CitaService.marcar_no_presentado(db, cita_id)
    except ValueError as e: raise HTTPException(status_code=400, detail=str(e))


@router.post("/{cita_id}/enviar-confirmacion-email", response_model=CitaResponse)
def enviar_confirmacion_email(cita_id: int, db: Session = Depends(get_db)):
    try:
        return CitaService.enviar_confirmacion_email(db, cita_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=502, detail=str(e))


@router.post("/{cita_id}/recordatorio-email")
def enviar_recordatorio_email(cita_id: int, db: Session = Depends(get_db)):
    try:
        return CitaService.enviar_recordatorio_email(db, cita_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=502, detail=str(e))


@router.post("/{cita_id}/avisar-reprogramacion-email", response_model=CitaResponse)
def avisar_reprogramacion_email(cita_id: int, db: Session = Depends(get_db)):
    try:
        return CitaService.enviar_aviso_reprogramacion_email(db, cita_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=502, detail=str(e))


@router.post("/{cita_id}/crear-presupuesto")
def crear_presupuesto_desde_cita(
    cita_id: int,
    db: Session = Depends(get_db),
):
    try:
        return CitaService.crear_presupuesto_desde_cita(db, cita_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete(
    "/{cita_id}",
    status_code=status.HTTP_204_NO_CONTENT
)
def eliminar_cita(
    cita_id: int,
    db: Session = Depends(get_db)
):
    try:
        CitaService.delete(
            db,
            cita_id
        )

        return Response(
            status_code=status.HTTP_204_NO_CONTENT
        )

    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )
