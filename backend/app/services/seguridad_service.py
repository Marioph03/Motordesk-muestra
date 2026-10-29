from sqlalchemy.orm import Session

from app.models.usuario import Usuario

from app.core.security import get_password_hash, verify_password


class SeguridadService:

    @staticmethod
    def obtener_info(
        usuario: Usuario
    ) -> dict:

        return {
            "id":
                usuario.id,

            "nombre":
                usuario.nombre,

            "email":
                usuario.email,

            "rol":
                usuario.rol,

            "ultimo_acceso":
                (
                    usuario.ultimo_acceso.isoformat()
                    if getattr(
                        usuario,
                        "ultimo_acceso",
                        None
                    )
                    else None
                )
        }


    @staticmethod
    def cambiar_password(
        db: Session,
        usuario: Usuario,
        password_actual: str,
        password_nueva: str
    ):

        if not verify_password(
            password_actual,
            usuario.password_hash
        ):

            raise ValueError(
                "La contraseña actual no es correcta"
            )


        if verify_password(
            password_nueva,
            usuario.password_hash
        ):

            raise ValueError(
                "La nueva contraseña debe ser distinta"
            )


        usuario.password_hash = get_password_hash(password_nueva)


        db.commit()
        db.refresh(usuario)

        return usuario
"""Operaciones de seguridad del perfil, especialmente cambio de contraseña."""
