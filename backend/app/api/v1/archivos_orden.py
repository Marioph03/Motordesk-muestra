from pathlib import Path

from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    UploadFile,
    status
)
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.core.security import get_current_user
from app.database.database import get_db
from app.schemas.archivo_orden import ArchivoOrdenResponse
from app.services.archivo_orden_service import ArchivoOrdenService


router = APIRouter(
    prefix="/ordenes-reparacion/{orden_id}/archivos",
    tags=["Archivos de órdenes"],
    dependencies=[
        Depends(get_current_user)
    ]
)


@router.get(
    "/",
    response_model=list[ArchivoOrdenResponse]
)
def get_archivos(
    orden_id: int,
    db: Session = Depends(get_db)
):
    try:
        return ArchivoOrdenService.get_by_orden(
            db,
            orden_id
        )

    except ValueError as e:
        raise HTTPException(
            status_code=404,
            detail=str(e)
        )


@router.post(
    "/",
    response_model=ArchivoOrdenResponse,
    status_code=status.HTTP_201_CREATED
)
async def subir_archivo(
    orden_id: int,
    archivo: UploadFile = File(...),
    categoria: str = Form("Otro"),
    db: Session = Depends(get_db)
):
    try:
        return await ArchivoOrdenService.subir(
            db,
            orden_id,
            archivo,
            categoria
        )

    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )


@router.get(
    "/{archivo_id}/descargar"
)
def descargar_archivo(
    orden_id: int,
    archivo_id: int,
    db: Session = Depends(get_db)
):
    try:
        archivo = ArchivoOrdenService.get_by_id(
            db,
            orden_id,
            archivo_id
        )

        ruta = Path(archivo.ruta)

        if not ruta.is_file():
            raise HTTPException(
                status_code=404,
                detail="El archivo físico no existe"
            )

        return FileResponse(
            path=ruta,
            media_type=archivo.tipo_mime,
            filename=archivo.nombre_original
        )

    except ValueError as e:
        raise HTTPException(
            status_code=404,
            detail=str(e)
        )


@router.delete(
    "/{archivo_id}",
    status_code=status.HTTP_204_NO_CONTENT
)
def eliminar_archivo(
    orden_id: int,
    archivo_id: int,
    db: Session = Depends(get_db)
):
    try:
        ArchivoOrdenService.delete(
            db,
            orden_id,
            archivo_id
        )

    except ValueError as e:
        raise HTTPException(
            status_code=404,
            detail=str(e)
        )
"""API autenticada para adjuntar, consultar y eliminar archivos de una orden."""
