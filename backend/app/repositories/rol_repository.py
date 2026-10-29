from sqlalchemy.orm import Session, joinedload

from app.models.rol import Rol


class RolRepository:

    @staticmethod
    def get_all(db: Session):
        return (
            db.query(Rol)
            .options(joinedload(Rol.permisos))
            .order_by(Rol.nombre.asc())
            .all()
        )

    @staticmethod
    def get_by_id(db: Session, rol_id: int):
        return (
            db.query(Rol)
            .options(joinedload(Rol.permisos))
            .filter(Rol.id == rol_id)
            .first()
        )

    @staticmethod
    def get_by_nombre(db: Session, nombre: str):
        return (
            db.query(Rol)
            .options(joinedload(Rol.permisos))
            .filter(Rol.nombre == nombre)
            .first()
        )

    @staticmethod
    def create(db: Session, datos: dict):
        rol = Rol(**datos)
        db.add(rol)
        db.flush()
        return rol

    @staticmethod
    def update(db: Session, rol: Rol, datos: dict):
        for key, value in datos.items():
            setattr(rol, key, value)

        db.flush()
        return rol
"""Consultas de roles y sus relaciones con permisos asignados."""
