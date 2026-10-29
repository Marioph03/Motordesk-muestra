"""Gestión de albaranes de proveedor y su confirmación idempotente en stock."""

from datetime import datetime
from decimal import Decimal

from sqlalchemy.orm import Session

from app.models.albaran_proveedor import (
    AlbaranProveedor
)

from app.models.linea_albaran_proveedor import (
    LineaAlbaranProveedor
)
from app.models.linea_devolucion_proveedor import (
    LineaDevolucionProveedor
)
from app.models.devolucion_proveedor import (
    DevolucionProveedor
)

from app.schemas.albaran_proveedor import (
    AlbaranProveedorCreate
)

from app.models.movimiento_stock import TipoMovimientoStock
from app.models.pedido_compra import EstadoPedidoCompra
from app.repositories.articulo_stock_repository import ArticuloStockRepository
from app.repositories.linea_pedido_compra_repository import LineaPedidoCompraRepository
from app.repositories.pedido_compra_repository import PedidoCompraRepository
from app.services.stock_service import StockService


class AlbaranProveedorService:

    @staticmethod
    def obtener_lineas_devolvibles(
        db: Session,
        albaran_id: int,
    ) -> list[dict]:
        albaran = (
            db.query(AlbaranProveedor)
            .filter(AlbaranProveedor.id == albaran_id)
            .first()
        )

        if albaran is None:
            raise ValueError("Albarán no encontrado")
        if albaran.estado != "CONFIRMADO":
            raise ValueError(
                "Solo se pueden devolver artículos de un albarán confirmado"
            )

        resultado = []
        for linea in albaran.lineas:
            cantidad_devuelta = sum(
                (
                    Decimal(item.cantidad)
                    for item in (
                        db.query(LineaDevolucionProveedor)
                        .join(DevolucionProveedor)
                        .filter(
                            LineaDevolucionProveedor.linea_albaran_id
                            == linea.id,
                            DevolucionProveedor.estado == "CONFIRMADA",
                        )
                        .all()
                    )
                ),
                Decimal("0"),
            )
            cantidad_recibida = Decimal(linea.cantidad_recibida)
            articulo = linea.articulo
            resultado.append({
                "linea_albaran_id": linea.id,
                "articulo_stock_id": linea.articulo_stock_id,
                "cantidad_recibida": float(cantidad_recibida),
                "cantidad_devuelta": float(cantidad_devuelta),
                "cantidad_disponible": float(
                    max(Decimal("0"), cantidad_recibida - cantidad_devuelta)
                ),
                "coste_unitario": (
                    float(linea.coste_unitario)
                    if linea.coste_unitario is not None
                    else None
                ),
                "articulo": {
                    "id": articulo.id,
                    "referencia": articulo.referencia,
                    "nombre": articulo.nombre,
                    "descripcion": getattr(articulo, "descripcion", None),
                },
            })
        return resultado

    @staticmethod
    def siguiente_numero(
        db: Session
    ) -> str:

        anio = datetime.now().year

        ultimo = (
            db.query(
                AlbaranProveedor
            )
            .filter(
                AlbaranProveedor
                .numero_interno
                .like(
                    f"AP-{anio}-%"
                )
            )
            .order_by(
                AlbaranProveedor
                .id
                .desc()
            )
            .first()
        )

        secuencia = 1

        if ultimo:

            secuencia = (
                int(
                    ultimo
                    .numero_interno
                    .split("-")[-1]
                )
                + 1
            )

        return (
            f"AP-{anio}-"
            f"{secuencia:06d}"
        )


    @staticmethod
    def crear(
        db: Session,
        datos: AlbaranProveedorCreate
    ) -> AlbaranProveedor:

        if not datos.lineas:

            raise ValueError(
                "El albarán debe tener "
                "al menos una línea"
            )


        albaran = AlbaranProveedor(

            numero_interno=
                AlbaranProveedorService
                .siguiente_numero(db),

            numero_proveedor=
                datos.numero_proveedor,

            proveedor_id=
                datos.proveedor_id,

            pedido_compra_id=
                datos.pedido_compra_id,

            fecha=
                datos.fecha,

            estado=
                "BORRADOR",

            observaciones=
                datos.observaciones
        )

        db.add(albaran)

        db.flush()


        for linea in datos.lineas:

            db.add(
                LineaAlbaranProveedor(

                    albaran_id=
                        albaran.id,

                    articulo_stock_id=
                        linea.articulo_stock_id,

                    cantidad_recibida=
                        linea.cantidad_recibida,

                    coste_unitario=
                        linea.coste_unitario
                )
            )


        db.commit()

        db.refresh(albaran)

        return albaran


    @staticmethod
    def confirmar(
        db: Session,
        albaran_id: int
    ) -> AlbaranProveedor:
        """Registra la entrada de mercancía y confirma el albarán de forma atómica."""
        albaran = (
            db.query(AlbaranProveedor)
            .filter(AlbaranProveedor.id == albaran_id)
            .first()
        )

        if albaran is None:
            raise ValueError("Albarán no encontrado")
        if albaran.estado == "CONFIRMADO":
            raise ValueError("El albarán ya está confirmado")
        if albaran.estado == "ANULADO":
            raise ValueError("No se puede confirmar un albarán anulado")
        if albaran.estado != "BORRADOR":
            raise ValueError("Solo se pueden confirmar albaranes en borrador")
        if not albaran.lineas:
            raise ValueError("El albarán no tiene líneas")

        try:
            pedido = None
            lineas_pedido_por_articulo = {}
            recibidas_por_articulo = {}

            if albaran.pedido_compra_id is not None:
                pedido = PedidoCompraRepository.get_by_id(
                    db,
                    albaran.pedido_compra_id
                )
                if pedido is None:
                    raise ValueError("El pedido asociado no existe")
                if pedido.proveedor_id != albaran.proveedor_id:
                    raise ValueError(
                        "El proveedor del albarán no coincide con el pedido"
                    )
                if pedido.estado not in (
                    EstadoPedidoCompra.ENVIADO.value,
                    EstadoPedidoCompra.RECIBIDO_PARCIAL.value,
                ):
                    raise ValueError(
                        "Solo se pueden recibir albaranes de pedidos enviados"
                    )

                lineas_pedido_por_articulo = {
                    linea.articulo_stock_id: linea
                    for linea in pedido.lineas
                }
                recibidas_por_articulo = {
                    linea.articulo_stock_id: Decimal(linea.cantidad_recibida)
                    for linea in pedido.lineas
                }

            for linea in albaran.lineas:
                cantidad = Decimal(linea.cantidad_recibida)
                if cantidad <= 0:
                    raise ValueError(
                        "La cantidad recibida debe ser mayor que cero"
                    )

                articulo = ArticuloStockRepository.get_by_id(
                    db,
                    linea.articulo_stock_id
                )
                if articulo is None:
                    raise ValueError(
                        "Uno de los artículos del albarán no existe"
                    )

                if pedido is not None:
                    linea_pedido = lineas_pedido_por_articulo.get(articulo.id)
                    if linea_pedido is None:
                        raise ValueError(
                            f"El artículo {articulo.referencia} no pertenece "
                            "al pedido asociado"
                        )

                    nueva_recibida = (
                        recibidas_por_articulo[articulo.id] + cantidad
                    )
                    if nueva_recibida > Decimal(linea_pedido.cantidad_pedida):
                        pendiente = (
                            Decimal(linea_pedido.cantidad_pedida)
                            - recibidas_por_articulo[articulo.id]
                        )
                        raise ValueError(
                            f"No se pueden recibir {cantidad} unidades de "
                            f"{linea_pedido.descripcion}. Quedan pendientes "
                            f"{pendiente}."
                        )
                    recibidas_por_articulo[articulo.id] = nueva_recibida

                StockService._aplicar_movimiento(
                    db=db,
                    articulo=articulo,
                    tipo=TipoMovimientoStock.ENTRADA_COMPRA.value,
                    cantidad=cantidad,
                    suma=True,
                    motivo=(
                        f"Entrada por albarán "
                        f"{albaran.numero_interno}"
                    ),
                    commit=False,
                )

                if linea.coste_unitario is not None:
                    articulo.coste = Decimal(linea.coste_unitario)

            if pedido is not None:
                for articulo_id, cantidad_recibida in recibidas_por_articulo.items():
                    LineaPedidoCompraRepository.update(
                        db,
                        lineas_pedido_por_articulo[articulo_id],
                        {"cantidad_recibida": cantidad_recibida},
                    )
                AlbaranProveedorService._actualizar_estado_pedido(
                    db,
                    pedido.id
                )

            albaran.estado = "CONFIRMADO"
            db.flush()
            db.commit()
            db.refresh(albaran)
            return albaran
        except Exception:
            db.rollback()
            raise


    @staticmethod
    def anular(
        db: Session,
        albaran_id: int
    ) -> AlbaranProveedor:
        albaran = (
            db.query(AlbaranProveedor)
            .filter(AlbaranProveedor.id == albaran_id)
            .first()
        )

        if albaran is None:
            raise ValueError("Albarán no encontrado")
        if albaran.estado == "CONFIRMADO":
            raise ValueError("No se puede anular un albarán confirmado")
        if albaran.estado == "ANULADO":
            raise ValueError("El albarán ya está anulado")

        try:
            albaran.estado = "ANULADO"
            db.commit()
            db.refresh(albaran)
            return albaran
        except Exception:
            db.rollback()
            raise


    @staticmethod
    def _actualizar_estado_pedido(
        db: Session,
        pedido_id: int
    ) -> None:
        pedido = PedidoCompraRepository.get_by_id(db, pedido_id)
        if pedido is None:
            return

        lineas = LineaPedidoCompraRepository.get_by_pedido(db, pedido.id)
        hay_algo_recibido = any(
            Decimal(linea.cantidad_recibida) > 0
            for linea in lineas
        )
        todo_recibido = bool(lineas) and all(
            Decimal(linea.cantidad_recibida)
            >= Decimal(linea.cantidad_pedida)
            for linea in lineas
        )

        if todo_recibido:
            cambios = {
                "estado": EstadoPedidoCompra.RECIBIDO.value,
                "fecha_recepcion": datetime.now(),
            }
        elif hay_algo_recibido:
            cambios = {
                "estado": EstadoPedidoCompra.RECIBIDO_PARCIAL.value,
            }
        else:
            cambios = {
                "estado": EstadoPedidoCompra.ENVIADO.value,
            }

        PedidoCompraRepository.update(db, pedido, cambios)
