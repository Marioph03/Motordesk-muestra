from sqlalchemy.orm import Session

from app.models.permiso import Permiso


class PermisoRepository:

    @staticmethod
    def get_all(
        db: Session
    ):

        return (
            db.query(Permiso)
            .order_by(
                Permiso.modulo.asc(),
                Permiso.codigo.asc(),
            )
            .all()
        )


    @staticmethod
    def get_by_id(
        db: Session,
        permiso_id: int
    ):

        return (
            db.query(Permiso)
            .filter(
                Permiso.id == permiso_id
            )
            .first()
        )


    @staticmethod
    def get_by_codigo(
        db: Session,
        codigo: str
    ):

        return (
            db.query(Permiso)
            .filter(
                Permiso.codigo == codigo
            )
            .first()
        )


    @staticmethod
    def create(
        db: Session,
        datos: dict
    ):

        permiso = Permiso(
            **datos
        )

        db.add(permiso)
        db.flush()

        return permiso
"""Consultas de permisos disponibles para roles y autorización de acciones."""
