from sqlalchemy.orm import Session

from app.models.usuario import Usuario


class UsuarioRepository:

    @staticmethod
    def get_activos(db: Session):
        return (
            db.query(Usuario)
            .filter(Usuario.activo.is_(True))
            .order_by(
                Usuario.nombre.asc(),
                Usuario.apellidos.asc(),
            )
            .all()
        )

    @staticmethod
    def get_all(db: Session):
        return (
            db.query(Usuario)
            .order_by(
                Usuario.nombre.asc(),
                Usuario.apellidos.asc(),
            )
            .all()
        )

    @staticmethod
    def get_by_id(db: Session, usuario_id: int):
        return (
            db.query(Usuario)
            .filter(Usuario.id == usuario_id)
            .first()
        )

    @staticmethod
    def get_by_email(db: Session, email: str):
        """Busca una cuenta con un correo normalizado.

        El correo no distingue mayúsculas/minúsculas. Centralizar esta regla
        evita falsos 401 si el navegador autocompleta espacios o mayúsculas.
        """
        email_normalizado = (email or "").strip().lower()

        if not email_normalizado:
            return None

        return (
            db.query(Usuario)
            .filter(Usuario.email == email_normalizado)
            .first()
        )

    @staticmethod
    def create(db: Session, datos: dict):

        usuario = Usuario(**datos)

        db.add(usuario)
        db.commit()
        db.refresh(usuario)

        return usuario

    @staticmethod
    def update(db: Session, usuario: Usuario, datos: dict):

        for key, value in datos.items():
            setattr(usuario, key, value)

        db.commit()
        db.refresh(usuario)

        return usuario

    @staticmethod
    def delete(db: Session, usuario: Usuario):

        db.delete(usuario)
        db.commit()
"""Acceso a usuarios, roles y disponibilidad base del equipo."""
