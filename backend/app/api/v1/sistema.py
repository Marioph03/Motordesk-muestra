from fastapi import (
    APIRouter,
    Depends,
    HTTPException
)

from fastapi.responses import FileResponse

from sqlalchemy.orm import Session

from app.database.database import (
    get_db
)

from app.schemas.sistema import (
    BackupInfoResponse,
    EstadoSistemaResponse,
    RestablecerDatosRequest,
)
from app.core.permissions import require_permission
from app.models.usuario import Usuario

from app.services.sistema_service import (
    SistemaService
)


router = APIRouter(
    prefix="/configuracion/sistema",
    tags=["Configuración - Sistema"]
)


@router.get(
    "/estado",
    response_model=EstadoSistemaResponse
)
def estado_sistema(
    db: Session = Depends(get_db)
):

    return (
        SistemaService
        .estado_sistema(db)
    )


@router.get(
    "/backup",
    response_model=BackupInfoResponse
)
def obtener_ultima_copia():

    return (
        SistemaService
        .ultima_copia()
    )


@router.post(
    "/backup"
)
def crear_copia():

    try:

        archivo = (
            SistemaService
            .crear_backup()
        )

        return {
            "message":
                "Copia de seguridad creada",

            "archivo":
                archivo.name
        }

    except ValueError as e:

        raise HTTPException(
            status_code=400,
            detail=str(e)
        )


@router.get(
    "/backup/descargar"
)
def descargar_ultima_copia():

    info = (
        SistemaService
        .ultima_copia()
    )

    if not info["disponible"]:

        raise HTTPException(
            status_code=404,
            detail=(
                "No hay copias "
                "de seguridad"
            )
        )


    archivo = (
        SistemaService
        .BACKUP_DIR
        /
        info["nombre_archivo"]
    )


    return FileResponse(
        path=archivo,
        filename=archivo.name,
        media_type=
            "application/octet-stream"
    )


@router.post("/restablecer-datos")
def restablecer_datos(
    datos: RestablecerDatosRequest,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_permission("permisos.gestionar")),
):
    if datos.confirmacion != "RESTABLECER":
        raise HTTPException(status_code=400, detail="Confirma la acción escribiendo RESTABLECER")
    try:
        copia = SistemaService.crear_backup()
        tablas = SistemaService.restablecer_datos_prueba(db)
        return {"message": "Datos de prueba eliminados. Se conservaron configuración, empresa, usuarios e integraciones.", "backup": copia.name, "tablas": tablas}
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
"""Operaciones administrativas de sistema y generación de copias seguras."""
