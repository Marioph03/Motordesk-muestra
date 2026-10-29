"""Administración de usuarios, roles y resumen operativo del equipo."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.permissions import require_permission
from app.database.database import get_db
from app.schemas.usuario import (
    UsuarioCreate,
    UsuarioUpdate,
    UsuarioResponse
)
from app.services.usuario_service import UsuarioService
from app.schemas.usuario import ResetPasswordRequest
from app.schemas.resumen_operativo_personal import (
    ResumenOperativoPersonalResponse,
)
from app.services.personal_service import PersonalService

router = APIRouter(
    prefix="/usuarios",
    tags=["Usuarios"]
)


@router.get("/", response_model=list[UsuarioResponse])
def get_usuarios(
    db: Session = Depends(get_db),
    usuario_actual = Depends(
        require_permission("personal.ver")
    ),
):
    return UsuarioService.get_all(db)


@router.get(
    "/{usuario_id}/resumen-operativo",
    response_model=ResumenOperativoPersonalResponse,
)
def resumen_operativo_usuario(
    usuario_id: int,
    db: Session = Depends(get_db),
    usuario_actual=Depends(require_permission("personal.ver")),
):
    try:
        return PersonalService.obtener_resumen_operativo(db, usuario_id)
    except ValueError as error:
        raise HTTPException(status_code=404, detail=str(error))


@router.get("/{usuario_id}", response_model=UsuarioResponse)
def get_usuario(
    usuario_id: int,
    db: Session = Depends(get_db),
    usuario_actual = Depends(
        require_permission("personal.ver")
    ),
):
    try:
        return UsuarioService.get_by_id(
            db,
            usuario_id
        )

    except ValueError as e:
        raise HTTPException(
            status_code=404,
            detail=str(e)
        )


@router.post("/", response_model=UsuarioResponse)
def create_usuario(
    usuario: UsuarioCreate,
    db: Session = Depends(get_db),
    usuario_actual = Depends(
        require_permission("personal.editar")
    ),
):
    return UsuarioService.create(
        db,
        usuario
    )


@router.patch("/{usuario_id}", response_model=UsuarioResponse)
def actualizar_usuario(
    usuario_id: int,
    datos: UsuarioUpdate,
    db: Session = Depends(get_db),
    usuario_actual = Depends(
        require_permission("personal.editar")
    ),
):
    try:
        return UsuarioService.update(
            db,
            usuario_id,
            datos
        )

    except ValueError as e:
        raise HTTPException(
            status_code=404,
            detail=str(e)
        )


@router.delete("/{usuario_id}")
def eliminar_usuario(
    usuario_id: int,
    db: Session = Depends(get_db),
    usuario_actual = Depends(
        require_permission("personal.editar")
    ),
):
    try:

        UsuarioService.delete(
            db,
            usuario_id
        )

        return {
            "mensaje": "Usuario eliminado correctamente"
        }

    except ValueError as e:
        raise HTTPException(
            status_code=404,
            detail=str(e)
        )
        
@router.patch("/{usuario_id}/reset-password")
def reset_password(
    usuario_id: int,
    datos: ResetPasswordRequest,
    db: Session = Depends(get_db),
    usuario_actual = Depends(
        require_permission("personal.editar")
    ),
):
    try:
        return UsuarioService.reset_password(
            db,
            usuario_id,
            datos.password
        )

    except ValueError as e:
        raise HTTPException(
            status_code=404,
            detail=str(e)
        )
