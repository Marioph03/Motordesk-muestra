from sqlalchemy.orm import Session

from app.models.mano_obra import ManoObra
from app.schemas.mano_obra import ManoObraCreate

from app.schemas.pagination import PaginationParams
from app.repositories.base_repository import BaseRepository
class ManoObraRepository:

    @staticmethod
    def get_by_orden(db: Session, orden_id: int):
        return (
            db.query(ManoObra)
            .filter(ManoObra.orden_id == orden_id)
            .all()
        )

    @staticmethod
    def get_by_id(db: Session, linea_id: int):
        return (
            db.query(ManoObra)
            .filter(ManoObra.id == linea_id)
            .first()
        )

    @staticmethod
    def create(db: Session, orden_id: int, datos: dict):

        linea = ManoObra(
            orden_id=orden_id,
            **datos
        )

        db.add(linea)
        db.commit()
        db.refresh(linea)

        return linea

    @staticmethod
    def update(db: Session, linea: ManoObra, datos: dict):

        for key, value in datos.items():
            setattr(linea, key, value)

        db.commit()
        db.refresh(linea)

        return linea

    @staticmethod
    def delete(db: Session, linea: ManoObra):

        db.delete(linea)
        db.commit()
        
    @staticmethod
    def get_paginated(
        db: Session,
        pagination: PaginationParams
    ):
        query = (
            db.query(ManoObra)
            .order_by(ManoObra.descripcion)
        )

        return BaseRepository.paginate(
            query,
            pagination
        )
"""Consultas de trabajos de mano de obra asociados a órdenes."""
