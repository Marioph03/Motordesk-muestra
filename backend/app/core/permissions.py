"""Dependencias reutilizables para autorización basada en permisos y roles."""

from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.security import get_current_user
from app.core.roles import RolUsuario, normalizar_nombre_rol
from app.database.database import get_db
from app.models.usuario import Usuario
from app.services.permisos_service import PermisosService


def require_permission(codigo_permiso: str):
    """Devuelve una dependencia FastAPI que exige un permiso concreto.

    Es la protección preferida para endpoints nuevos. Los permisos se resuelven
    contra la base de datos en cada petición, así que un cambio de rol se aplica
    inmediatamente y no depende de volver a emitir un JWT.
    """

    def verificar_permiso(
        db: Session = Depends(get_db),
        usuario: Usuario = Depends(get_current_user),
    ) -> Usuario:
        if not usuario.activo:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Usuario inactivo",
            )

        tiene_permiso = PermisosService.usuario_tiene_permiso(
            db,
            usuario,
            codigo_permiso,
        )

        if not tiene_permiso:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=(
                    "No tienes permisos para realizar esta acción"
                ),
            )

        return usuario

    return verificar_permiso


def require_roles(*roles: RolUsuario | str):
    """Compatibilidad con los routers que aún protegen por rol directo."""

    roles_permitidos = {
        normalizar_nombre_rol(rol)
        for rol in roles
    }

    def verificar_rol(
        usuario: Usuario = Depends(get_current_user),
    ) -> Usuario:
        if not usuario.activo:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Usuario inactivo",
            )

        if normalizar_nombre_rol(usuario.rol) not in roles_permitidos:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tienes permisos para realizar esta acción",
            )

        return usuario

    return verificar_rol
