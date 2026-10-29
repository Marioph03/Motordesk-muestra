from fastapi import (
    APIRouter,
    Depends
)

from sqlalchemy.orm import Session

from app.database.database import (
    get_db
)

from app.schemas.configuracion_documentos import (
    ConfiguracionDocumentosResponse,
    ConfiguracionDocumentosUpdate
)

from app.services.configuracion_documentos_service import (
    ConfiguracionDocumentosService
)


router = APIRouter(
    prefix="/configuracion/documentos",
    tags=["Configuración - Documentos"]
)


@router.get(
    "",
    response_model=ConfiguracionDocumentosResponse
)
def obtener_configuracion_documentos(
    db: Session = Depends(get_db)
):

    return (
        ConfiguracionDocumentosService
        .obtener(db)
    )


@router.put(
    "",
    response_model=ConfiguracionDocumentosResponse
)
def actualizar_configuracion_documentos(
    datos: ConfiguracionDocumentosUpdate,
    db: Session = Depends(get_db)
):

    return (
        ConfiguracionDocumentosService
        .actualizar(
            db,
            datos
        )
    )
"""Preferencias que determinan el contenido común de documentos PDF."""
