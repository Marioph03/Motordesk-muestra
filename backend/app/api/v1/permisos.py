from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status
)

from sqlalchemy.orm import Session

from app.database.database import get_db
from app.core.permissions import require_permission

from app.schemas.permiso import (
    PermisoResponse
)

from app.schemas.rol import (
    RolCreate,
    RolUpdate,
    RolResponse
)

from app.services.permisos_service import (
    PermisosService
)


router = APIRouter(
    prefix="/permisos",
    tags=["Roles y permisos"]
)

@router.get(
    "",
    response_model=list[PermisoResponse]
)
def listar_permisos(
    db: Session = Depends(get_db),
    usuario_actual = Depends(
        require_permission("permisos.gestionar")
    ),
):

    return (
        PermisosService.listar_permisos(
            db
        )
    )
    
@router.get(
    "/roles",
    response_model=list[RolResponse]
)
def listar_roles(
    db: Session = Depends(get_db),
    usuario_actual = Depends(
        require_permission("permisos.gestionar")
    ),
):

    return (
        PermisosService.listar_roles(
            db
        )
    )
    
@router.get(
    "/roles/{rol_id}",
    response_model=RolResponse
)
def obtener_rol(
    rol_id: int,
    db: Session = Depends(get_db),
    usuario_actual = Depends(
        require_permission("permisos.gestionar")
    ),
):

    try:

        return PermisosService.obtener_rol(
            db,
            rol_id
        )

    except ValueError as e:

        raise HTTPException(
            status_code=404,
            detail=str(e)
        )
        
@router.post(
    "/roles",
    response_model=RolResponse,
    status_code=status.HTTP_201_CREATED
)
def crear_rol(
    datos: RolCreate,
    db: Session = Depends(get_db),
    usuario_actual = Depends(
        require_permission("permisos.gestionar")
    ),
):

    try:

        return PermisosService.crear_rol(
            db,
            datos
        )

    except ValueError as e:

        raise HTTPException(
            status_code=400,
            detail=str(e)
        )
        
@router.patch(
    "/roles/{rol_id}",
    response_model=RolResponse
)
def actualizar_rol(
    rol_id: int,
    datos: RolUpdate,
    db: Session = Depends(get_db),
    usuario_actual = Depends(
        require_permission("permisos.gestionar")
    ),
):

    try:

        return (
            PermisosService.actualizar_rol(
                db,
                rol_id,
                datos
            )
        )

    except ValueError as e:

        raise HTTPException(
            status_code=400,
            detail=str(e)
        )
        
"""API protegida para roles, permisos y administración de autorizaciones."""
