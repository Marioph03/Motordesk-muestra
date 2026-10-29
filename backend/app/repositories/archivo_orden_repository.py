from sqlalchemy.orm import Session

from app.models.archivo_orden import ArchivoOrden


class ArchivoOrdenRepository:

    @staticmethod
    def create(
        db: Session,
        orden_id: int,
        nombre_original: str,
        nombre_archivo: str,
        tipo_mime: str,
        categoria: str,
        ruta: str,
        tamano: int
    ):
        archivo = ArchivoOrden(
            orden_id=orden_id,
            nombre_original=nombre_original,
            nombre_archivo=nombre_archivo,
            tipo_mime=tipo_mime,
            categoria=categoria,
            ruta=ruta,
            tamano=tamano
        )

        db.add(archivo)
        db.commit()
        db.refresh(archivo)

        return archivo

    @staticmethod
    def get_by_id(
        db: Session,
        archivo_id: int
    ):
        return (
            db.query(ArchivoOrden)
            .filter(
                ArchivoOrden.id == archivo_id
            )
            .first()
        )

    @staticmethod
    def get_by_orden(
        db: Session,
        orden_id: int
    ):
        return (
            db.query(ArchivoOrden)
            .filter(
                ArchivoOrden.orden_id == orden_id
            )
            .order_by(
                ArchivoOrden.created_at.desc()
            )
            .all()
        )

    @staticmethod
    def delete(
        db: Session,
        archivo: ArchivoOrden
    ):
        db.delete(archivo)
        db.commit()
"""Consultas de metadatos de archivos adjuntos a órdenes de reparación."""
