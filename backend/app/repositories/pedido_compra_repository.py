from sqlalchemy import func
from sqlalchemy.orm import (
    Session,
    joinedload
)

from app.models.pedido_compra import (
    EstadoPedidoCompra,
    PedidoCompra,
)
from app.models.proveedor import Proveedor

from app.models.linea_pedido_compra import (
    LineaPedidoCompra
)


class PedidoCompraRepository:

    @staticmethod
    def get_pendientes(
        db: Session,
    ) -> list[PedidoCompra]:
        """Pedidos enviados que aún tienen mercancía pendiente de recibir."""
        return (
            db.query(PedidoCompra)
            .filter(
                PedidoCompra.estado.in_([
                    EstadoPedidoCompra.ENVIADO.value,
                    EstadoPedidoCompra.RECIBIDO_PARCIAL.value,
                ])
            )
            .order_by(PedidoCompra.fecha_envio.asc())
            .all()
        )

    @staticmethod
    def get_en_rango(
        db: Session,
        fecha_inicio,
        fecha_fin,
    ):
        return (
            db.query(PedidoCompra)
            .filter(
                PedidoCompra.fecha >= fecha_inicio,
                PedidoCompra.fecha < fecha_fin,
            )
            .order_by(PedidoCompra.fecha.desc())
            .all()
        )

    @staticmethod
    def get_proveedores_mayor_volumen(
        db: Session,
        fecha_inicio,
        fecha_fin,
        limite: int = 10,
    ):
        estados_validos = (
            EstadoPedidoCompra.ENVIADO.value,
            EstadoPedidoCompra.RECIBIDO_PARCIAL.value,
            EstadoPedidoCompra.RECIBIDO.value,
        )
        return (
            db.query(
                Proveedor.id.label("proveedor_id"),
                Proveedor.nombre,
                func.count(PedidoCompra.id).label("pedidos"),
                func.sum(PedidoCompra.total).label("total_compras"),
            )
            .join(
                PedidoCompra,
                PedidoCompra.proveedor_id == Proveedor.id,
            )
            .filter(
                PedidoCompra.fecha >= fecha_inicio,
                PedidoCompra.fecha < fecha_fin,
                PedidoCompra.estado.in_(estados_validos),
            )
            .group_by(Proveedor.id, Proveedor.nombre)
            .order_by(func.sum(PedidoCompra.total).desc())
            .limit(limite)
            .all()
        )

    @staticmethod
    def get_all(
        db: Session
    ):
        return (
            db.query(PedidoCompra)
            .options(
                joinedload(
                    PedidoCompra.proveedor
                ),
                joinedload(
                    PedidoCompra.lineas
                )
            )
            .order_by(
                PedidoCompra.fecha.desc()
            )
            .all()
        )


    @staticmethod
    def get_by_id(
        db: Session,
        pedido_id: int
    ):
        return (
            db.query(PedidoCompra)
            .options(
                joinedload(
                    PedidoCompra.proveedor
                ),
                joinedload(
                    PedidoCompra.lineas
                )
                .joinedload(
                    LineaPedidoCompra.articulo_stock
                )
            )
            .filter(
                PedidoCompra.id == pedido_id
            )
            .first()
        )


    @staticmethod
    def get_last(
        db: Session
    ):
        return (
            db.query(PedidoCompra)
            .order_by(
                PedidoCompra.id.desc()
            )
            .first()
        )


    @staticmethod
    def get_by_proveedor(
        db: Session,
        proveedor_id: int
    ):
        return (
            db.query(PedidoCompra)
            .options(
                joinedload(
                    PedidoCompra.lineas
                )
            )
            .filter(
                PedidoCompra.proveedor_id
                ==
                proveedor_id
            )
            .order_by(
                PedidoCompra.fecha.desc()
            )
            .all()
        )


    @staticmethod
    def create(
        db: Session,
        datos: dict
    ):

        pedido = PedidoCompra(
            **datos
        )

        db.add(pedido)

        db.flush()

        return pedido


    @staticmethod
    def update(
        db: Session,
        pedido: PedidoCompra,
        datos: dict
    ):

        for key, value in datos.items():

            setattr(
                pedido,
                key,
                value
            )

        db.flush()

        return pedido
"""Consultas de pedidos de compra y sus estados de recepción."""
