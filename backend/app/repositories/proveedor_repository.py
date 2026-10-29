from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.models.proveedor import Proveedor


class ProveedorRepository:

    @staticmethod
    def get_all(db: Session):
        return db.query(Proveedor).all()

    @staticmethod
    def get_by_id(
        db: Session,
        proveedor_id: int
    ):
        return db.query(Proveedor).filter(
            Proveedor.id == proveedor_id
        ).first()

    @staticmethod
    def get_by_cif(
        db: Session,
        cif: str
    ):
        return db.query(Proveedor).filter(
            Proveedor.cif == cif
        ).first()

    @staticmethod
    def create(
        db: Session,
        datos: dict
    ):
        proveedor = Proveedor(**datos)

        db.add(proveedor)
        # El código se genera con el id definitivo y no puede duplicarse.
        db.flush()
        proveedor.codigo = f"PRO-{proveedor.id:06d}"
        db.commit()
        db.refresh(proveedor)

        return proveedor

    @staticmethod
    def update(
        db: Session,
        proveedor: Proveedor,
        datos: dict
    ):
        for key, value in datos.items():
            setattr(proveedor, key, value)

        db.commit()
        db.refresh(proveedor)

        return proveedor

    @staticmethod
    def delete(
        db: Session,
        proveedor: Proveedor
    ):
        try:
            db.delete(proveedor)
            db.commit()
        except IntegrityError as error:
            db.rollback()
            raise ValueError(
                "No se puede eliminar un proveedor con documentos asociados."
            ) from error
"""Acceso al catálogo de proveedores y su estado operativo."""
