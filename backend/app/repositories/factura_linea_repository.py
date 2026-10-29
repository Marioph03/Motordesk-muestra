from sqlalchemy.orm import Session

from app.models.factura_linea import FacturaLinea


class FacturaLineaRepository:

    @staticmethod
    def get_by_factura(
        db: Session,
        factura_id: int
    ):
        return (
            db.query(FacturaLinea)
            .filter(
                FacturaLinea.factura_id == factura_id
            )
            .all()
        )

    @staticmethod
    def create(
        db: Session,
        datos: dict
    ):

        linea = FacturaLinea(**datos)

        db.add(linea)
        db.commit()
        db.refresh(linea)

        return linea

    @staticmethod
    def update(
        db: Session,
        linea: FacturaLinea,
        datos: dict
    ):

        for key, value in datos.items():
            setattr(
                linea,
                key,
                value
            )

        db.commit()
        db.refresh(linea)

        return linea

    @staticmethod
    def delete(
        db: Session,
        linea: FacturaLinea
    ):

        db.delete(linea)
        db.commit()
        
    @staticmethod
    def get_by_id(
        db: Session,
        linea_id: int
    ):
        return (
            db.query(FacturaLinea)
            .filter(
                FacturaLinea.id == linea_id
            )
            .first()
        )
        
    @staticmethod
    def delete_by_origen(
        db: Session,
        factura_id: int,
        origenes: list[str]
    ):

        (
            db.query(FacturaLinea)
            .filter(
            FacturaLinea.factura_id == factura_id,
            FacturaLinea.origen.in_(origenes)
        )
        .delete(
            synchronize_session=False
        )
    )

        db.commit()
"""Consultas y persistencia de líneas que componen una factura."""
