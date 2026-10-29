from fastapi import (
    APIRouter,
    Depends,
    HTTPException
)

from sqlalchemy.orm import Session

from app.database.database import get_db

from app.schemas.seguridad import (
    CambiarPasswordRequest,
    SeguridadUsuarioResponse
)

from app.services.seguridad_service import (
    SeguridadService
)

from app.core.security import (
    get_current_user
)


router = APIRouter(
    prefix="/configuracion/seguridad",
    tags=["Configuración - Seguridad"]
)


@router.get(
    "/mi-cuenta",
    response_model=SeguridadUsuarioResponse
)
def mi_cuenta(
    usuario = Depends(
        get_current_user
    )
):

    return (
        SeguridadService
        .obtener_info(
            usuario
        )
    )


@router.post(
    "/cambiar-password"
)
def cambiar_password(
    datos: CambiarPasswordRequest,
    db: Session = Depends(get_db),
    usuario = Depends(
        get_current_user
    )
):

    try:

        SeguridadService.cambiar_password(
            db,
            usuario,
            datos.password_actual,
            datos.password_nueva
        )

        return {
            "message":
                "Contraseña actualizada correctamente"
        }

    except ValueError as e:

        raise HTTPException(
            status_code=400,
            detail=str(e)
        )
"""API de seguridad del perfil, incluida la actualización de credenciales."""
