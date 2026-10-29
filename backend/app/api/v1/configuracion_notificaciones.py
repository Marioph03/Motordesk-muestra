from fastapi import (
    APIRouter,
    Depends
)

from sqlalchemy.orm import Session

from app.database.database import (
    get_db
)

from app.schemas.configuracion_notificaciones import (
    ConfiguracionNotificacionesResponse,
    ConfiguracionNotificacionesUpdate
)

from app.services.configuracion_notificaciones_service import (
    ConfiguracionNotificacionesService
)


router = APIRouter(
    prefix="/configuracion/notificaciones",
    tags=["Configuración - Notificaciones"]
)


@router.get(
    "",
    response_model=
        ConfiguracionNotificacionesResponse
)
def obtener_configuracion(
    db: Session = Depends(get_db)
):

    return (
        ConfiguracionNotificacionesService
        .obtener(db)
    )


@router.put(
    "",
    response_model=
        ConfiguracionNotificacionesResponse
)
def actualizar_configuracion(
    datos:
        ConfiguracionNotificacionesUpdate,

    db: Session = Depends(get_db)
):

    return (
        ConfiguracionNotificacionesService
        .actualizar(
            db,
            datos
        )
    )
"""Preferencias de categorías de avisos visibles al usuario."""
