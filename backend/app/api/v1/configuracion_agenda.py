from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Response,
    status
)

from sqlalchemy.orm import Session

from app.database.database import get_db

from app.schemas.configuracion_agenda import (
    ConfiguracionAgendaResponse,
    ConfiguracionAgendaUpdate,
    CierreAgendaCreate,
    CierreAgendaResponse
)

from app.services.configuracion_agenda_service import (
    ConfiguracionAgendaService
)


router = APIRouter(
    prefix="/configuracion/agenda",
    tags=["Configuración - Agenda"]
)


@router.get(
    "",
    response_model=ConfiguracionAgendaResponse
)
def obtener_configuracion(
    db: Session = Depends(get_db)
):

    return (
        ConfiguracionAgendaService
        .obtener(db)
    )


@router.put(
    "",
    response_model=ConfiguracionAgendaResponse
)
def actualizar_configuracion(
    datos: ConfiguracionAgendaUpdate,
    db: Session = Depends(get_db)
):

    return (
        ConfiguracionAgendaService
        .actualizar(
            db,
            datos
        )
    )


@router.get(
    "/cierres",
    response_model=list[
        CierreAgendaResponse
    ]
)
def listar_cierres(
    db: Session = Depends(get_db)
):

    return (
        ConfiguracionAgendaService
        .listar_cierres(db)
    )


@router.post(
    "/cierres",
    response_model=CierreAgendaResponse,
    status_code=status.HTTP_201_CREATED
)
def crear_cierre(
    datos: CierreAgendaCreate,
    db: Session = Depends(get_db)
):

    return (
        ConfiguracionAgendaService
        .crear_cierre(
            db,
            datos
        )
    )


@router.delete(
    "/cierres/{cierre_id}",
    status_code=status.HTTP_204_NO_CONTENT
)
def eliminar_cierre(
    cierre_id: int,
    db: Session = Depends(get_db)
):

    try:

        ConfiguracionAgendaService.eliminar_cierre(
            db,
            cierre_id
        )

        return Response(
            status_code=status.HTTP_204_NO_CONTENT
        )

    except ValueError as e:

        raise HTTPException(
            status_code=404,
            detail=str(e)
        )
"""Configuración de horarios, cierres y duración de citas del taller."""
