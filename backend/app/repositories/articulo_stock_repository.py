from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from app.models.articulo_stock import ArticuloStock


class ArticuloStockRepository:

    @staticmethod
    def get_all(
        db: Session,
        solo_activos: bool = True,
        controla_stock: bool | None = None,
    ):

        query = db.query(
            ArticuloStock
        )

        if solo_activos:
            query = query.filter(
                ArticuloStock.activo.is_(True)
            )

        if controla_stock is not None:
            query = query.filter(ArticuloStock.controla_stock.is_(controla_stock))

        return (
            query
            .order_by(
                ArticuloStock.nombre.asc()
            )
            .all()
        )


    @staticmethod
    def get_by_id(
        db: Session,
        articulo_id: int
    ):

        return (
            db.query(ArticuloStock)
            .filter(
                ArticuloStock.id == articulo_id
            )
            .first()
        )


    @staticmethod
    def get_by_referencia(
        db: Session,
        referencia: str
    ):
        """Busca una referencia ignorando mayúsculas y espacios exteriores."""
        return (
            db.query(ArticuloStock)
            .filter(
                func.upper(
                    func.trim(ArticuloStock.referencia)
                ) == referencia.strip().upper()
            )
            .first()
        )


    @staticmethod
    def buscar(
        db: Session,
        texto: str
    ):

        patron = f"%{texto}%"

        return (
            db.query(ArticuloStock)
            .filter(
                or_(
                    ArticuloStock.referencia.ilike(
                        patron
                    ),
                    ArticuloStock.nombre.ilike(
                        patron
                    ),
                    ArticuloStock.marca.ilike(
                        patron
                    ),
                    ArticuloStock.categoria.ilike(
                        patron
                    )
                )
            )
            .order_by(
                ArticuloStock.nombre.asc()
            )
            .all()
        )


    @staticmethod
    def get_stock_bajo(
        db: Session
    ):

        return (
            db.query(ArticuloStock)
            .filter(
                ArticuloStock.activo.is_(True),
                ArticuloStock.controla_stock.is_(True),
                ArticuloStock.stock_actual
                <
                ArticuloStock.stock_minimo
            )
            .order_by(
                ArticuloStock.stock_actual.asc()
            )
            .all()
        )


    @staticmethod
    def create(
        db: Session,
        datos: dict
    ):

        articulo = ArticuloStock(
            **datos
        )

        db.add(articulo)
        db.flush()

        return articulo


    @staticmethod
    def update(
        db: Session,
        articulo: ArticuloStock,
        datos: dict
    ):

        for key, value in datos.items():
            setattr(
                articulo,
                key,
                value
            )

        db.flush()

        return articulo
"""Consultas de catálogo, existencias y filtros de artículos de almacén."""
