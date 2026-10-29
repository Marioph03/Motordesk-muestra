"""Ciclo de pedidos: borrador, envío, recepción y actualización de stock."""

from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP

from sqlalchemy.orm import Session

from app.models.pedido_compra import (
    EstadoPedidoCompra
)

from app.models.movimiento_stock import (
    TipoMovimientoStock
)

from app.repositories.pedido_compra_repository import (
    PedidoCompraRepository
)

from app.repositories.linea_pedido_compra_repository import (
    LineaPedidoCompraRepository
)

from app.repositories.articulo_stock_repository import (
    ArticuloStockRepository
)

from app.repositories.proveedor_repository import (
    ProveedorRepository
)

from app.schemas.pedido_compra import (
    PedidoCompraCreate,
    PedidoCompraUpdate,
    LineaPedidoCompraCreate,
    LineaPedidoCompraUpdate
)

from app.services.stock_service import StockService


class PedidoCompraService:

    @staticmethod
    def obtener_pedidos(
        db: Session,
    ):
        return PedidoCompraRepository.get_all(db)


    @staticmethod
    def obtener_pedido(
        db: Session,
        pedido_id: int,
    ):
        return PedidoCompraService._get_pedido(
            db,
            pedido_id,
        )

    @staticmethod
    def crear_pedido(
        db: Session,
        datos: PedidoCompraCreate
    ):

        proveedor = (
            ProveedorRepository.get_by_id(
                db,
                datos.proveedor_id
            )
        )

        if proveedor is None:
            raise ValueError(
                "Proveedor no encontrado"
            )

        if not proveedor.activo:
            raise ValueError(
                "El proveedor está inactivo"
            )

        numero = (
            PedidoCompraService
            ._generar_numero(db)
        )

        datos_db = datos.model_dump()

        datos_db.update({
            "numero": numero,
            "estado":
                EstadoPedidoCompra
                .BORRADOR.value,

            "subtotal":
                Decimal("0.00"),

            "iva_total":
                Decimal("0.00"),

            "total":
                Decimal("0.00")
        })

        try:

            pedido = (
                PedidoCompraRepository.create(
                    db,
                    datos_db
                )
            )

            db.commit()
            db.refresh(pedido)

            return (
                PedidoCompraRepository.get_by_id(
                    db,
                    pedido.id
                )
            )

        except Exception:

            db.rollback()
            raise


    @staticmethod
    def actualizar_pedido(
        db: Session,
        pedido_id: int,
        datos: PedidoCompraUpdate
    ):

        pedido = (
            PedidoCompraService
            ._get_pedido(
                db,
                pedido_id
            )
        )

        PedidoCompraService._validar_editable(pedido)

        cambios = datos.model_dump(
            exclude_unset=True
        )

        if "proveedor_id" in cambios:

            proveedor = (
                ProveedorRepository.get_by_id(
                    db,
                    cambios["proveedor_id"]
                )
            )

            if proveedor is None:
                raise ValueError(
                    "Proveedor no encontrado"
                )

            if not proveedor.activo:
                raise ValueError(
                    "El proveedor está inactivo"
                )

            # Si ya tiene líneas, no permitir
            # cambiar proveedor.
            if pedido.lineas and proveedor.id != pedido.proveedor_id:
                raise ValueError(
                    "No se puede cambiar el proveedor "
                    "de un pedido que ya tiene líneas"
                )

        try:

            PedidoCompraRepository.update(
                db,
                pedido,
                cambios
            )

            db.commit()

            return (
                PedidoCompraRepository.get_by_id(
                    db,
                    pedido.id
                )
            )

        except Exception:

            db.rollback()
            raise


    @staticmethod
    def añadir_linea(
        db: Session,
        pedido_id: int,
        datos: LineaPedidoCompraCreate
    ):

        pedido = (
            PedidoCompraService
            ._get_pedido(
                db,
                pedido_id
            )
        )

        PedidoCompraService._validar_editable(pedido)

        articulo = None
        referencia = (datos.referencia or "").strip()
        descripcion = (datos.descripcion or "").strip()

        if datos.articulo_stock_id is not None:
            articulo = ArticuloStockRepository.get_by_id(
                db, datos.articulo_stock_id
            )
            if articulo is None or not articulo.activo:
                raise ValueError("El artículo seleccionado no está disponible")

            existente = LineaPedidoCompraRepository.get_by_articulo_en_pedido(
                db, pedido.id, articulo.id
            )
            if existente is not None:
                raise ValueError("Este artículo ya está incluido en el pedido")

            referencia = articulo.referencia
            descripcion = articulo.nombre
        else:
            if not referencia or not descripcion:
                raise ValueError(
                    "Indica referencia y descripción para el artículo nuevo"
                )
            if ArticuloStockRepository.get_by_referencia(db, referencia):
                raise ValueError(
                    "Ese artículo ya existe en almacén; selecciónalo de la lista"
                )

        cantidad = Decimal(
            datos.cantidad_pedida
        )

        coste_unitario = (
            Decimal(
                datos.coste_unitario
            )
            if datos.coste_unitario
                is not None
            else Decimal(articulo.coste)
            if articulo is not None else Decimal("0")
        )

        iva = (
            Decimal(
                datos.iva
            )
            if datos.iva
                is not None
            else Decimal(articulo.iva)
            if articulo is not None else Decimal("21")
        )

        importes = (
            PedidoCompraService
            ._calcular_linea(
                cantidad,
                coste_unitario,
                iva
            )
        )

        datos_linea = {
            "pedido_id":
                pedido.id,

            "articulo_stock_id":
                articulo.id if articulo is not None else None,

            "referencia":
                referencia,

            "descripcion":
                descripcion,

            "cantidad_pedida":
                cantidad,

            "cantidad_recibida":
                Decimal("0"),

            "coste_unitario":
                coste_unitario,

            "iva":
                iva,

            **importes
        }

        try:

            linea = (
                LineaPedidoCompraRepository
                .create(
                    db,
                    datos_linea
                )
            )

            PedidoCompraService._recalcular_totales(
                db,
                pedido
            )

            db.commit()
            db.refresh(linea)

            return linea

        except Exception:

            db.rollback()
            raise


    @staticmethod
    def actualizar_linea(
        db: Session,
        linea_id: int,
        datos: LineaPedidoCompraUpdate
    ):

        linea = (
            LineaPedidoCompraRepository
            .get_by_id(
                db,
                linea_id
            )
        )

        if linea is None:
            raise ValueError(
                "Línea de pedido no encontrada"
            )

        pedido = linea.pedido

        PedidoCompraService._validar_editable(pedido)

        cambios = datos.model_dump(
            exclude_unset=True
        )

        cantidad = Decimal(
            cambios.get(
                "cantidad_pedida",
                linea.cantidad_pedida
            )
        )

        coste_unitario = Decimal(
            cambios.get(
                "coste_unitario",
                linea.coste_unitario
            )
        )

        iva = Decimal(
            cambios.get(
                "iva",
                linea.iva
            )
        )

        importes = (
            PedidoCompraService
            ._calcular_linea(
                cantidad,
                coste_unitario,
                iva
            )
        )

        cambios.update(
            importes
        )

        try:

            linea = (
                LineaPedidoCompraRepository
                .update(
                    db,
                    linea,
                    cambios
                )
            )

            PedidoCompraService._recalcular_totales(
                db,
                pedido
            )

            db.commit()
            db.refresh(linea)

            return linea

        except Exception:

            db.rollback()
            raise


    @staticmethod
    def eliminar_linea(
        db: Session,
        linea_id: int
    ):

        linea = (
            LineaPedidoCompraRepository
            .get_by_id(
                db,
                linea_id
            )
        )

        if linea is None:
            raise ValueError(
                "Línea de pedido no encontrada"
            )

        pedido = linea.pedido

        PedidoCompraService._validar_editable(pedido)

        try:

            LineaPedidoCompraRepository.delete(
                db,
                linea
            )

            PedidoCompraService._recalcular_totales(
                db,
                pedido
            )

            db.commit()

        except Exception:

            db.rollback()
            raise


    # =====================================================
    # HELPERS
    # =====================================================

    @staticmethod
    def _generar_numero(
        db: Session
    ) -> str:

        anio = datetime.now().year

        ultimo = (
            PedidoCompraRepository.get_last(
                db
            )
        )

        if ultimo is None:
            siguiente = 1

        else:

            try:
                siguiente = (
                    int(
                        ultimo.numero.split(
                            "-"
                        )[-1]
                    )
                    + 1
                )

            except Exception:
                siguiente = ultimo.id + 1

        return (
            f"PC-{anio}-{siguiente:06d}"
        )


    @staticmethod
    def _calcular_linea(
        cantidad: Decimal,
        coste_unitario: Decimal,
        iva: Decimal
    ) -> dict:

        subtotal = (
            cantidad *
            coste_unitario
        ).quantize(
            Decimal("0.01"),
            rounding=ROUND_HALF_UP
        )

        iva_importe = (
            subtotal *
            iva /
            Decimal("100")
        ).quantize(
            Decimal("0.01"),
            rounding=ROUND_HALF_UP
        )

        total = (
            subtotal +
            iva_importe
        ).quantize(
            Decimal("0.01"),
            rounding=ROUND_HALF_UP
        )

        return {
            "subtotal":
                subtotal,

            "iva_importe":
                iva_importe,

            "total":
                total
        }


    @staticmethod
    def _recalcular_totales(
        db: Session,
        pedido
    ):

        # Flush para asegurarnos de que altas,
        # modificaciones o borrados de líneas
        # están reflejados en la BD.
        db.flush()

        lineas = (
            LineaPedidoCompraRepository
            .get_by_pedido(
                db,
                pedido.id
            )
        )

        subtotal = sum(
            (
                Decimal(linea.subtotal)
                for linea in lineas
            ),
            Decimal("0.00")
        )

        iva_total = sum(
            (
                Decimal(
                    linea.iva_importe
                )
                for linea in lineas
            ),
            Decimal("0.00")
        )

        total = (
            subtotal +
            iva_total
        )

        PedidoCompraRepository.update(
            db,
            pedido,
            {
                "subtotal":
                    subtotal,

                "iva_total":
                    iva_total,

                "total":
                    total
            }
        )


    @staticmethod
    def _get_pedido(
        db: Session,
        pedido_id: int
    ):

        pedido = (
            PedidoCompraRepository.get_by_id(
                db,
                pedido_id
            )
        )

        if pedido is None:
            raise ValueError(
                "Pedido de compra no encontrado"
            )

        return pedido


    @staticmethod
    def _validar_editable(
        pedido
    ):

        if (
            pedido.estado
            !=
            EstadoPedidoCompra.BORRADOR.value
        ):
            raise ValueError(
                "Solo se pueden modificar "
                "pedidos en borrador"
            )

    @staticmethod
    def enviar_pedido(
        db: Session,
        pedido_id: int
    ):
        """Pasa un borrador con líneas a enviado y fija la fecha de salida."""

        pedido = PedidoCompraService._get_pedido(
            db,
            pedido_id
        )

        if (
            pedido.estado
            != EstadoPedidoCompra.BORRADOR.value
        ):
            raise ValueError(
                "Solo se pueden enviar pedidos en borrador"
            )

        if not pedido.lineas:
            raise ValueError(
                "No se puede enviar un pedido sin líneas"
            )

        try:

            PedidoCompraRepository.update(
                db,
                pedido,
                {
                    "estado":
                        EstadoPedidoCompra.ENVIADO.value,

                    "fecha_envio":
                        datetime.now()
                }
            )

            db.commit()
            db.refresh(pedido)

            return (
                PedidoCompraRepository.get_by_id(
                    db,
                    pedido.id
            )
        )

        except Exception:

            db.rollback()
            raise
        
    @staticmethod
    def cancelar_pedido(
        db: Session,
        pedido_id: int
    ):
        """Cancela un pedido solo si no se ha recibido mercancía de ninguna línea."""

        pedido = PedidoCompraService._get_pedido(
            db,
            pedido_id
        )

        if pedido.estado in (
            EstadoPedidoCompra.RECIBIDO.value,
            EstadoPedidoCompra.CANCELADO.value
        ):
            raise ValueError(
                "El pedido no se puede cancelar "
                "en su estado actual"
            )

        if any(
            Decimal(linea.cantidad_recibida) > 0
            for linea in pedido.lineas
        ):
            raise ValueError(
                "No se puede cancelar un pedido "
                "que ya tiene mercancía recibida"
            )

        try:

            PedidoCompraRepository.update(
                db,
                pedido,
                {
                    "estado":
                        EstadoPedidoCompra.CANCELADO.value
                }
            )

            db.commit()
            db.refresh(pedido)

            return pedido

        except Exception:

            db.rollback()
            raise
        
    @staticmethod
    def recibir_mercancia(
        db: Session,
        pedido_id: int,
        datos
    ):
        """Registra una recepción parcial o total y crea entradas de stock atómicas."""

        pedido = PedidoCompraService._get_pedido(
            db,
            pedido_id
        )

        if pedido.estado not in (
            EstadoPedidoCompra.ENVIADO.value,
            EstadoPedidoCompra.RECIBIDO_PARCIAL.value
        ):
            raise ValueError(
                "Solo se puede recibir mercancía "
                "de pedidos enviados o parcialmente recibidos"
            )

        if not datos.lineas:
            raise ValueError(
                "Debes indicar al menos una línea a recibir"
            )

        try:

            for recepcion in datos.lineas:

                linea = (
                    LineaPedidoCompraRepository
                    .get_by_id(
                        db,
                        recepcion.linea_id
                    )
                )

                if linea is None:
                    raise ValueError(
                        "Línea de pedido no encontrada"
                    )

                if linea.pedido_id != pedido.id:
                    raise ValueError(
                        "La línea no pertenece al pedido"
                    )

                cantidad_recibir = Decimal(
                    recepcion.cantidad
                )

                ya_recibida = Decimal(
                    linea.cantidad_recibida
                )

                pedida = Decimal(
                    linea.cantidad_pedida
                )

                pendiente = (
                    pedida - ya_recibida
                )

                if cantidad_recibir > pendiente:
                    raise ValueError(
                        f"No se pueden recibir "
                        f"{cantidad_recibir} unidades de "
                        f"{linea.descripcion}. "
                        f"Quedan pendientes {pendiente}."
                    )

                articulo = linea.articulo_stock
                if articulo is None:
                    articulo = ArticuloStockRepository.get_by_referencia(
                        db, linea.referencia
                    )
                    if articulo is None:
                        articulo = ArticuloStockRepository.create(
                            db,
                            {
                                "referencia": linea.referencia.strip(),
                                "nombre": linea.descripcion.strip(),
                                "coste": Decimal(linea.coste_unitario),
                                "precio_venta": Decimal("0"),
                                "iva": Decimal(linea.iva),
                                "stock_actual": Decimal("0"),
                                "stock_minimo": Decimal("0"),
                                "activo": True,
                                "proveedor_habitual_id": pedido.proveedor_id,
                            },
                        )
                    LineaPedidoCompraRepository.update(
                        db, linea, {"articulo_stock_id": articulo.id}
                    )

                # Entrada de stock SIN commit independiente
                StockService._aplicar_movimiento(
                    db=db,
                    articulo=articulo,
                    tipo=TipoMovimientoStock.ENTRADA_COMPRA.value,
                    cantidad=cantidad_recibir,
                    suma=True,
                    motivo=(
                        f"Recepción pedido "
                        f"{pedido.numero}"
                    ),
                    commit=False
                )

                nueva_recibida = (
                    ya_recibida
                    +
                    cantidad_recibir
                )

                LineaPedidoCompraRepository.update(
                    db,
                    linea,
                    {
                        "cantidad_recibida":
                            nueva_recibida
                    }
                )

            db.flush()

            lineas_actualizadas = (
                LineaPedidoCompraRepository
                .get_by_pedido(
                    db,
                    pedido.id
                )
            )

            todo_recibido = all(
                Decimal(linea.cantidad_recibida)
                >=
                Decimal(linea.cantidad_pedida)

                for linea in lineas_actualizadas
            )

            nuevo_estado = (
                EstadoPedidoCompra.RECIBIDO.value
                if todo_recibido
                else
                EstadoPedidoCompra.RECIBIDO_PARCIAL.value
            )

            cambios_pedido = {
                "estado": nuevo_estado
            }

            if todo_recibido:
                cambios_pedido[
                    "fecha_recepcion"
                ] = datetime.now()

            PedidoCompraRepository.update(
                db,
                pedido,
                cambios_pedido
            )

            db.commit()

            return (
                PedidoCompraRepository.get_by_id(
                    db,
                    pedido.id
                )
            )

        except Exception:

            db.rollback()
            raise
        
    @staticmethod
    def generar_pedidos_reposicion(
        db: Session
    ):

        articulos = (
            ArticuloStockRepository
            .get_stock_bajo(db)
        )

        if not articulos:
            raise ValueError(
                "No hay artículos pendientes de reposición"
            )

        articulos_pendientes = (
            LineaPedidoCompraRepository
            .get_articulos_con_reposicion_pendiente(db)
        )

        grupos = {}

        for articulo in articulos:

            if articulo.id in articulos_pendientes:
                continue

            proveedor_id = (
                articulo.proveedor_habitual_id
            )

            if not proveedor_id:
                continue

            cantidad = (
                Decimal(articulo.stock_minimo)
                -
                Decimal(articulo.stock_actual)
            )

            if cantidad <= 0:
                continue

            grupos.setdefault(
                proveedor_id,
                []
            ).append(
                {
                    "articulo":
                        articulo,

                    "cantidad":
                        cantidad
                }
            )

        if not grupos:
            raise ValueError(
                "Los artículos con stock bajo "
                "no tienen proveedor habitual configurado"
            )

        pedidos_creados_ids = []

        try:

            for proveedor_id, items in grupos.items():

                proveedor = ProveedorRepository.get_by_id(
                    db,
                    proveedor_id,
                )

                if proveedor is None or not proveedor.activo:
                    raise ValueError(
                        "El proveedor habitual de uno de los artículos "
                        "no está disponible"
                    )

                pedido = PedidoCompraRepository.create(
                    db,
                    {
                        "numero": PedidoCompraService._generar_numero(db),
                        "proveedor_id": proveedor_id,
                        "estado": EstadoPedidoCompra.BORRADOR.value,
                        "observaciones": (
                            "Pedido generado desde necesidades de reposición"
                        ),
                        "subtotal": Decimal("0.00"),
                        "iva_total": Decimal("0.00"),
                        "total": Decimal("0.00"),
                    },
                )

                for item in items:

                    articulo = item[
                        "articulo"
                    ]

                    cantidad = item[
                        "cantidad"
                    ]

                    importes = PedidoCompraService._calcular_linea(
                        cantidad,
                        Decimal(articulo.coste),
                        Decimal(articulo.iva),
                    )

                    LineaPedidoCompraRepository.create(
                        db,
                        {
                            "pedido_id": pedido.id,
                            "articulo_stock_id": articulo.id,
                            "referencia": articulo.referencia,
                            "descripcion": articulo.nombre,
                            "cantidad_pedida": cantidad,
                            "cantidad_recibida": Decimal("0.00"),
                            "coste_unitario": Decimal(articulo.coste),
                            "iva": Decimal(articulo.iva),
                            **importes,
                        },
                    )

                PedidoCompraService._recalcular_totales(
                    db,
                    pedido,
                )
                pedidos_creados_ids.append(pedido.id)

            db.commit()

            return [
                PedidoCompraRepository.get_by_id(
                    db,
                    pedido_id,
                )
                for pedido_id in pedidos_creados_ids
            ]

        except Exception:

            db.rollback()
            raise
