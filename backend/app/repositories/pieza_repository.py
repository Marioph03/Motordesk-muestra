from sqlalchemy.orm import Session

from app.models.pieza import Pieza

from app.schemas.pagination import PaginationParams
from app.repositories.base_repository import BaseRepository

class PiezaRepository:

    @staticmethod
    def get_by_orden(db: Session, orden_id: int):
        return (
            db.query(Pieza)
            .filter(Pieza.orden_id == orden_id)
            .all()
        )

    @staticmethod
    def get_by_id(db: Session, pieza_id: int):
        return (
            db.query(Pieza)
            .filter(Pieza.id == pieza_id)
            .first()
        )

    @staticmethod
    def create(db: Session, orden_id: int, datos: dict, commit: bool = True):

        nueva = Pieza(
            orden_id=orden_id,
            **datos
        )

        db.add(nueva)
        if commit:
            db.commit()
            db.refresh(nueva)
        else:
            db.flush()

        return nueva

    @staticmethod
    def update(db: Session, pieza: Pieza, datos: dict, commit: bool = True):

        for key, value in datos.items():
            setattr(pieza, key, value)

        if commit:
            db.commit()
            db.refresh(pieza)
        else:
            db.flush()

        return pieza

    @staticmethod
    def delete(db: Session, pieza: Pieza, commit: bool = True):

        db.delete(pieza)
        if commit:
            db.commit()
        else:
            db.flush()
        
    @staticmethod
    def get_paginated(
        db: Session,
        pagination: PaginationParams
    ):
        query = (
            db.query(Pieza)
            .order_by(Pieza.descripcion)
        )

        return BaseRepository.paginate(
            query,
            pagination
        )
"""Consultas de recambios reservados o consumidos por órdenes de reparación."""
