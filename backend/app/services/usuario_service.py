"""Operaciones de alta y mantenimiento de usuarios, sin exponer contraseñas."""

from sqlalchemy.orm import Session

from app.core.security import get_password_hash
from app.repositories.usuario_repository import UsuarioRepository
from app.schemas.usuario import UsuarioCreate, UsuarioUpdate


class UsuarioService:
    """Coordina el repositorio de usuarios y el hash seguro de credenciales."""


    @staticmethod
    def get_all(db: Session):
        return UsuarioRepository.get_all(db)

    @staticmethod
    def get_by_id(db: Session, usuario_id: int):

        usuario = UsuarioRepository.get_by_id(
            db,
            usuario_id
        )

        if usuario is None:
            raise ValueError("Usuario no encontrado")

        return usuario

    @staticmethod
    def create(
        db: Session,
        usuario: UsuarioCreate
    ):

        existente = UsuarioRepository.get_by_email(
            db,
            usuario.email
        )

        if existente:
            raise ValueError(
                "Ya existe un usuario con ese email"
            )

        datos = usuario.model_dump()

        password = datos.pop("password")

        datos["password_hash"] = get_password_hash(
            password
        )

        return UsuarioRepository.create(
            db,
            datos
        )

    @staticmethod
    def update(
        db: Session,
        usuario_id: int,
        datos: UsuarioUpdate
    ):

        usuario = UsuarioRepository.get_by_id(
            db,
            usuario_id
        )

        if usuario is None:
            raise ValueError(
                "Usuario no encontrado"
            )

        datos_actualizados = datos.model_dump(
            exclude_unset=True
        )

        if "password" in datos_actualizados:

            password = datos_actualizados.pop(
                "password"
            )

            datos_actualizados[
                "password_hash"
            ] = get_password_hash(password)

        return UsuarioRepository.update(
            db,
            usuario,
            datos_actualizados
        )

    @staticmethod
    def delete(
        db: Session,
        usuario_id: int
    ):

        usuario = UsuarioRepository.get_by_id(
            db,
            usuario_id
        )

        if usuario is None:
            raise ValueError(
                "Usuario no encontrado"
            )

        UsuarioRepository.delete(
            db,
            usuario
        )
        
    @staticmethod
    def reset_password(
        db: Session,
        usuario_id: int,
        nueva_password: str
    ):

        usuario = UsuarioRepository.get_by_id(
        db,
        usuario_id
    )

        if usuario is None:
            raise ValueError(
                "Usuario no encontrado"
            )

        usuario.password_hash = get_password_hash(
            nueva_password
        )

        db.commit()
        db.refresh(usuario)

        return {
            "mensaje": "Contraseña actualizada correctamente"
        }
