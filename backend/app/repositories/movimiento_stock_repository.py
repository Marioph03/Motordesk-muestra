from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload

from app.models.articulo_stock import (
    ArticuloStock
)

from app.models.movimiento_stock import (
    MovimientoStock,
    TipoMovimientoStock
)


class MovimientoStockRepository:

    @staticmethod
    def get_en_rango(
        db: Session,
        fecha_inicio,
        fecha_fin,
    ):
        return (
            db.query(MovimientoStock)
            .filter(
                MovimientoStock.fecha >= fecha_inicio,
                MovimientoStock.fecha < fecha_fin,
            )
            .order_by(MovimientoStock.fecha.desc())
            .all()
        )

    @staticmethod
    def get_mas_consumidos_en_rango(
        db: Session,
        fecha_inicio,
        fecha_fin,
        limite: int = 10,
    ):
        return (
            db.query(
                ArticuloStock.id.label("articulo_id"),
                ArticuloStock.referencia,
                ArticuloStock.nombre,
                func.sum(MovimientoStock.cantidad).label(
                    "cantidad_consumida"
                ),
            )
            .join(
                MovimientoStock,
                MovimientoStock.articulo_id == ArticuloStock.id,
            )
            .filter(
                MovimientoStock.tipo
                == TipoMovimientoStock.CONSUMO_ORDEN.value,
                MovimientoStock.fecha >= fecha_inicio,
                MovimientoStock.fecha < fecha_fin,
            )
            .group_by(
                ArticuloStock.id,
                ArticuloStock.referencia,
                ArticuloStock.nombre,
            )
            .order_by(func.sum(MovimientoStock.cantidad).desc())
            .limit(limite)
            .all()
        )

    @staticmethod
    def get_mas_consumidos(
        db: Session,
        limite: int = 10
    ):
        return (
            db.query(
                ArticuloStock.id.label("articulo_id"),
                ArticuloStock.referencia,
                ArticuloStock.nombre,
                func.sum(MovimientoStock.cantidad).label(
                    "cantidad_consumida"
                )
            )
            .join(
                MovimientoStock,
                MovimientoStock.articulo_id == ArticuloStock.id
            )
            .filter(
                MovimientoStock.tipo
                == TipoMovimientoStock.CONSUMO_ORDEN.value
            )
            .group_by(
                ArticuloStock.id,
                ArticuloStock.referencia,
                ArticuloStock.nombre
            )
            .order_by(
                func.sum(MovimientoStock.cantidad).desc()
            )
            .limit(limite)
            .all()
        )

    @staticmethod
    def get_by_id(
        db: Session,
        movimiento_id: int
    ):

        return (
            db.query(MovimientoStock)
            .options(
                joinedload(
                    MovimientoStock.articulo
                ),
                joinedload(
                    MovimientoStock.orden
                )
            )
            .filter(
                MovimientoStock.id
                ==
                movimiento_id
            )
            .first()
        )


    @staticmethod
    def get_by_articulo(
        db: Session,
        articulo_id: int
    ):

        return (
            db.query(MovimientoStock)
            .options(
                joinedload(
                    MovimientoStock.orden
                )
            )
            .filter(
                MovimientoStock.articulo_id
                ==
                articulo_id
            )
            .order_by(
                MovimientoStock.fecha.desc()
            )
            .all()
        )


    @staticmethod
    def get_all(
        db: Session
    ):

        return (
            db.query(MovimientoStock)
            .options(
                joinedload(
                    MovimientoStock.articulo
                ),
                joinedload(
                    MovimientoStock.orden
                )
            )
            .order_by(
                MovimientoStock.fecha.desc()
            )
            .all()
        )


    @staticmethod
    def create(
        db: Session,
        datos: dict
    ):

        movimiento = MovimientoStock(
            **datos
        )

        db.add(movimiento)
        db.flush()

        return movimiento
"""Consultas de trazabilidad de almacén y agregados de consumo."""
