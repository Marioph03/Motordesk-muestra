from sqlalchemy.orm import (
    Session,
    joinedload
)

from app.models.linea_pedido_compra import (
    LineaPedidoCompra
)
from app.models.pedido_compra import (
    EstadoPedidoCompra,
    PedidoCompra,
)


class LineaPedidoCompraRepository:

    @staticmethod
    def get_articulos_con_reposicion_pendiente(
        db: Session,
    ) -> set[int]:
        """Artículos que ya figuran en un pedido aún no recibido."""

        filas = (
            db.query(LineaPedidoCompra.articulo_stock_id)
            .join(
                PedidoCompra,
                PedidoCompra.id == LineaPedidoCompra.pedido_id,
            )
            .filter(
                PedidoCompra.estado.in_([
                    EstadoPedidoCompra.BORRADOR.value,
                    EstadoPedidoCompra.ENVIADO.value,
                    EstadoPedidoCompra.RECIBIDO_PARCIAL.value,
                ]),
                LineaPedidoCompra.cantidad_recibida
                < LineaPedidoCompra.cantidad_pedida,
            )
            .distinct()
            .all()
        )

        return {
            fila.articulo_stock_id
            for fila in filas
        }

    @staticmethod
    def get_by_id(
        db: Session,
        linea_id: int
    ):

        return (
            db.query(LineaPedidoCompra)
            .options(
                joinedload(
                    LineaPedidoCompra.pedido
                ),
                joinedload(
                    LineaPedidoCompra.articulo_stock
                )
            )
            .filter(
                LineaPedidoCompra.id == linea_id
            )
            .first()
        )


    @staticmethod
    def get_by_pedido(
        db: Session,
        pedido_id: int
    ):

        return (
            db.query(LineaPedidoCompra)
            .options(
                joinedload(
                    LineaPedidoCompra.articulo_stock
                )
            )
            .filter(
                LineaPedidoCompra.pedido_id
                ==
                pedido_id
            )
            .order_by(
                LineaPedidoCompra.id.asc()
            )
            .all()
        )


    @staticmethod
    def get_by_articulo_en_pedido(
        db: Session,
        pedido_id: int,
        articulo_stock_id: int
    ):

        return (
            db.query(LineaPedidoCompra)
            .filter(
                LineaPedidoCompra.pedido_id
                ==
                pedido_id,

                LineaPedidoCompra.articulo_stock_id
                ==
                articulo_stock_id
            )
            .first()
        )


    @staticmethod
    def create(
        db: Session,
        datos: dict
    ):

        linea = LineaPedidoCompra(
            **datos
        )

        db.add(linea)

        db.flush()

        return linea


    @staticmethod
    def update(
        db: Session,
        linea: LineaPedidoCompra,
        datos: dict
    ):

        for key, value in datos.items():

            setattr(
                linea,
                key,
                value
            )

        db.flush()

        return linea


    @staticmethod
    def delete(
        db: Session,
        linea: LineaPedidoCompra
    ):

        db.delete(linea)

        db.flush()
"""Acceso a líneas históricas de pedidos y sus cantidades recibidas."""
