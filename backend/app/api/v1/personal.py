from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.permissions import require_permission
from app.database.database import get_db
from app.schemas.disponibilidad_personal import (
    DisponibilidadPersonalResponse,
)
from app.schemas.planificacion_personal import (
    UsuarioPlanificacionResponse,
)
from app.services.personal_service import PersonalService
from app.services.ausencia_personal_service import (
    AusenciaPersonalService,
)
from app.schemas.registro_jornada import HorarioJornadaUpdate, MarcajeJornadaCreate, RegistroJornadaResponse
from app.services.registro_jornada_service import RegistroJornadaService
from app.repositories.empresa_repository import EmpresaRepository
from app.services.pdf_service import PdfService
from app.services.permisos_service import PermisosService
from fastapi.responses import StreamingResponse


router = APIRouter(
    prefix="/personal",
    tags=["Personal"],
)


@router.get("/jornadas", response_model=list[RegistroJornadaResponse])
def listar_jornadas(mes: str, db: Session = Depends(get_db), usuario_actual=Depends(require_permission("personal.ver"))):
    try:
        return RegistroJornadaService.listado(db, mes)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error))


@router.post("/jornadas/marcar", response_model=RegistroJornadaResponse)
def marcar_jornada(datos: MarcajeJornadaCreate, db: Session = Depends(get_db), usuario_actual=Depends(require_permission("personal.ver"))):
    if datos.usuario_id != usuario_actual.id and not PermisosService.usuario_tiene_permiso(db, usuario_actual, "personal.editar"):
        raise HTTPException(status_code=403, detail="Solo puedes registrar tu propia jornada")
    try:
        return RegistroJornadaService.marcar(db, datos.usuario_id, datos.fecha, datos.presente)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error))


@router.patch("/jornadas/horario/{usuario_id}")
def actualizar_horario_jornada(usuario_id: int, datos: HorarioJornadaUpdate, db: Session = Depends(get_db), usuario_actual=Depends(require_permission("personal.editar"))):
    try:
        return RegistroJornadaService.actualizar_horario(db, usuario_id, datos.hora_entrada, datos.hora_salida)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error))


@router.get("/jornadas/pdf")
def pdf_jornadas(mes: str, db: Session = Depends(get_db), usuario_actual=Depends(require_permission("personal.ver"))):
    try:
        registros = RegistroJornadaService.listado(db, mes)
        return StreamingResponse(PdfService.generar_registro_jornada(registros, mes, EmpresaRepository.get_first(db)), media_type="application/pdf", headers={"Content-Disposition": f'inline; filename="registro_jornada_{mes}.pdf"'})
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error))


@router.get(
    "/planificacion",
    response_model=list[UsuarioPlanificacionResponse],
)
def planificacion_personal(
    fecha_inicio: datetime,
    fecha_fin: datetime,
    db: Session = Depends(get_db),
    usuario_actual=Depends(require_permission("personal.ver")),
):
    try:
        return PersonalService.obtener_planificacion(
            db,
            fecha_inicio,
            fecha_fin,
        )
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error))


@router.get(
    "/disponibilidad",
    response_model=list[DisponibilidadPersonalResponse],
)
def disponibilidad_personal(
    fecha_inicio: datetime,
    fecha_fin: datetime,
    excluir_cita_id: int | None = None,
    excluir_orden_id: int | None = None,
    db: Session = Depends(get_db),
    usuario_actual=Depends(require_permission("personal.ver")),
):
    try:
        return AusenciaPersonalService.obtener_disponibilidad_personal(
            db,
            fecha_inicio,
            fecha_fin,
            excluir_cita_id=excluir_cita_id,
            excluir_orden_id=excluir_orden_id,
        )
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error))
"""API de disponibilidad, planificación y resumen del personal del taller."""
