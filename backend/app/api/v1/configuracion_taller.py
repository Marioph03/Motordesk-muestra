"""Endpoints de identidad del taller y gestión segura de su logo."""

from fastapi import (
    APIRouter,
    Depends,
    File,
    HTTPException,
    UploadFile
)

from sqlalchemy.orm import Session

from app.database.database import (
    get_db
)

from app.schemas.configuracion_taller import (
    ConfiguracionTallerResponse,
    ConfiguracionTallerUpdate
)

from app.services.configuracion_taller_service import (
    ConfiguracionTallerService
)


router = APIRouter(
    prefix="/configuracion/taller",
    tags=["Configuración - Taller"]
)


@router.get(
    "",
    response_model=ConfiguracionTallerResponse
)
def obtener_configuracion_taller(
    db: Session = Depends(get_db)
):

    return (
        ConfiguracionTallerService
        .obtener(db)
    )


@router.put(
    "",
    response_model=ConfiguracionTallerResponse
)
def actualizar_configuracion_taller(
    datos: ConfiguracionTallerUpdate,
    db: Session = Depends(get_db)
):

    return (
        ConfiguracionTallerService
        .actualizar(
            db,
            datos
        )
    )


@router.post(
    "/logo",
    response_model=ConfiguracionTallerResponse
)
async def actualizar_logo_taller(
    archivo: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    try:
        return await ConfiguracionTallerService.actualizar_logo(
            db,
            archivo
        )
    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error)
        )
