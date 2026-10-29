from sqlalchemy.orm import Session

from app.models.empresa import Empresa

from app.schemas.pagination import PaginationParams
from app.repositories.base_repository import BaseRepository

class EmpresaRepository:

    @staticmethod
    def get_all(
        db: Session
    ):
        return (
            db.query(Empresa)
            .order_by(Empresa.nombre)
            .all()
        )

    @staticmethod
    def get_by_id(
        db: Session,
        empresa_id: int
    ):
        return (
            db.query(Empresa)
            .filter(
                Empresa.id == empresa_id
            )
            .first()
        )

    @staticmethod
    def get_by_nif(
        db: Session,
        nif: str
    ):
        return (
            db.query(Empresa)
            .filter(
                Empresa.nif == nif
            )
            .first()
        )

    @staticmethod
    def create(
        db: Session,
        datos: dict
    ):

        empresa = Empresa(
            **datos
        )

        db.add(
            empresa
        )

        db.commit()

        db.refresh(
            empresa
        )

        return empresa

    @staticmethod
    def update(
        db: Session,
        empresa: Empresa,
        datos: dict
    ):

        for campo, valor in datos.items():

            setattr(
                empresa,
                campo,
                valor
            )

        db.commit()

        db.refresh(
            empresa
        )

        return empresa

    @staticmethod
    def delete(
        db: Session,
        empresa: Empresa
    ):

        db.delete(
            empresa
        )

        db.commit()
        
    @staticmethod
    def get_first(
        db: Session
    ):
        return db.query(Empresa).first()
    
    @staticmethod
    def get_paginated(
        db: Session,
        pagination: PaginationParams
    ):
        query = (
            db.query(Empresa)
            .order_by(Empresa.nombre)
        )

        return BaseRepository.paginate(
            query,
            pagination
        )
"""Acceso al registro de empresa utilizado como compatibilidad documental."""
