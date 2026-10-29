from sqlalchemy.orm import Session

from app.repositories.proveedor_repository import ProveedorRepository
from app.schemas.proveedor import (
    ProveedorCreate,
    ProveedorUpdate
)


class ProveedorService:

    @staticmethod
    def get_all(db: Session):
        return ProveedorRepository.get_all(db)

    @staticmethod
    def get_by_id(
        db: Session,
        proveedor_id: int
    ):

        proveedor = ProveedorRepository.get_by_id(
            db,
            proveedor_id
        )

        if proveedor is None:
            raise ValueError(
                "Proveedor no encontrado"
            )

        return proveedor

    @staticmethod
    def create(
        db: Session,
        proveedor: ProveedorCreate
    ):

        existente = ProveedorRepository.get_by_cif(
            db,
            proveedor.cif
        )

        if existente:
            raise ValueError(
                "Ya existe un proveedor con ese CIF"
            )

        return ProveedorRepository.create(
            db,
            proveedor.model_dump()
        )

    @staticmethod
    def update(
        db: Session,
        proveedor_id: int,
        datos: ProveedorUpdate
    ):

        proveedor = ProveedorRepository.get_by_id(
            db,
            proveedor_id
        )

        if proveedor is None:
            raise ValueError(
                "Proveedor no encontrado"
            )

        datos_actualizados = datos.model_dump(
            exclude_unset=True
        )

        if (
            "cif" in datos_actualizados
            and datos_actualizados["cif"] != proveedor.cif
        ):

            existente = ProveedorRepository.get_by_cif(
                db,
                datos_actualizados["cif"]
            )

            if existente:
                raise ValueError(
                    "Ya existe un proveedor con ese CIF"
                )

        return ProveedorRepository.update(
            db,
            proveedor,
            datos_actualizados
        )

    @staticmethod
    def delete(
        db: Session,
        proveedor_id: int
    ):

        proveedor = ProveedorRepository.get_by_id(
            db,
            proveedor_id
        )

        if proveedor is None:
            raise ValueError(
                "Proveedor no encontrado"
            )

        ProveedorRepository.delete(
            db,
            proveedor
        )
"""Reglas de validación y mantenimiento del catálogo de proveedores."""
