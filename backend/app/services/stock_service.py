"""Reglas de inventario y resumen operativo de almacén."""

from decimal import Decimal

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.movimiento_stock import (
    TipoMovimientoStock
)

from app.repositories.articulo_stock_repository import (
    ArticuloStockRepository
)

from app.repositories.movimiento_stock_repository import (
    MovimientoStockRepository
)

from app.schemas.articulo_stock import (
    ArticuloStockCreate,
    ArticuloStockUpdate
)


class StockService:

    @staticmethod
    def _normalizar_referencia(
        referencia: str | None,
    ) -> str:
        """Devuelve el formato único con el que se guarda una referencia."""
        return (referencia or "").strip().upper()

    @staticmethod
    def obtener_resumen(
        db: Session
    ):
        articulos = ArticuloStockRepository.get_all(
            db,
            solo_activos=False
        )

        total_articulos = len(articulos)

        activos = [
            articulo
            for articulo in articulos
            if articulo.activo
        ]

        stock_bajo = [
            articulo
            for articulo in activos
            if articulo.stock_actual <= articulo.stock_minimo
        ]

        sin_stock = [
            articulo
            for articulo in activos
            if articulo.stock_actual <= 0
        ]

        valor_coste = sum(
            (
                Decimal(articulo.stock_actual)
                * Decimal(articulo.coste)
            )
            for articulo in activos
        )

        valor_venta = sum(
            (
                Decimal(articulo.stock_actual)
                * Decimal(articulo.precio_venta)
            )
            for articulo in activos
        )

        return {
            "total_articulos": total_articulos,
            "articulos_activos": len(activos),
            "stock_bajo": len(stock_bajo),
            "sin_stock": len(sin_stock),
            "valor_inventario_coste": valor_coste,
            "valor_inventario_venta": valor_venta,
        }

    @staticmethod
    def crear_articulo(
        db: Session,
        datos: ArticuloStockCreate
    ):
        """Crea un artículo y, si procede, deja trazado su stock inicial."""


        referencia = StockService._normalizar_referencia(
            datos.referencia
        )
        nombre = datos.nombre.strip()

        if not referencia:
            raise ValueError(
                "La referencia es obligatoria"
            )

        if not nombre:
            raise ValueError(
                "El nombre del artículo es obligatorio"
            )

        existente = (
            ArticuloStockRepository
            .get_by_referencia(
                db,
                referencia
            )
        )

        if existente:
            raise ValueError(
                "Ya existe un artículo con esa referencia"
            )

        datos_db = datos.model_dump()

        stock_inicial = (
            datos_db.pop(
                "stock_inicial",
                Decimal("0")
            )
        )

        if not datos_db.get("controla_stock", True):
            stock_inicial = Decimal("0")
            datos_db["stock_minimo"] = Decimal("0")

        datos_db["referencia"] = referencia
        datos_db["nombre"] = nombre
        datos_db["stock_actual"] = Decimal("0")

        try:

            articulo = (
                ArticuloStockRepository.create(
                    db,
                    datos_db
                )
            )

            if stock_inicial > 0:

                StockService._registrar_movimiento(
                    db=db,
                    articulo=articulo,
                    tipo=TipoMovimientoStock.ENTRADA.value,
                    cantidad=stock_inicial,
                    motivo="Stock inicial"
                )

            db.commit()
            db.refresh(articulo)

            return articulo

        except IntegrityError as exc:
            db.rollback()
            raise ValueError(
                "Ya existe un artículo con esa referencia"
            ) from exc

        except Exception:
            db.rollback()
            raise


    @staticmethod
    def actualizar_articulo(
        db: Session,
        articulo_id: int,
        datos: ArticuloStockUpdate
    ):
        """Actualiza metadatos de catálogo sin alterar existencias directamente."""


        articulo = (
            ArticuloStockRepository.get_by_id(
                db,
                articulo_id
            )
        )

        if articulo is None:
            raise ValueError(
                "Artículo de stock no encontrado"
            )

        cambios = datos.model_dump(
            exclude_unset=True
        )

        if "referencia" in cambios:

            referencia = StockService._normalizar_referencia(
                cambios["referencia"]
            )

            if not referencia:
                raise ValueError(
                    "La referencia no puede estar vacía"
                )

            existente = (
                ArticuloStockRepository
                .get_by_referencia(
                    db,
                    referencia
                )
            )

            if (
                existente
                and existente.id != articulo.id
            ):
                raise ValueError(
                    "Ya existe otro artículo "
                    "con esa referencia"
                )

            cambios["referencia"] = referencia

        if "nombre" in cambios:

            nombre = (
                cambios["nombre"]
                or ""
            ).strip()

            if not nombre:
                raise ValueError(
                    "El nombre no puede estar vacío"
                )

            cambios["nombre"] = nombre

        if cambios.get("controla_stock") is False and articulo.stock_actual > 0:
            raise ValueError("No se puede quitar el control de stock mientras haya existencias")

        try:

            articulo = (
                ArticuloStockRepository.update(
                    db,
                    articulo,
                    cambios
                )
            )

            db.commit()
            db.refresh(articulo)

            return articulo

        except IntegrityError as exc:
            db.rollback()
            raise ValueError(
                "Ya existe otro artículo con esa referencia"
            ) from exc

        except Exception:
            db.rollback()
            raise


    @staticmethod
    def cambiar_estado_articulo(
        db: Session,
        articulo_id: int,
        activo: bool,
    ):
        articulo = ArticuloStockRepository.get_by_id(
            db,
            articulo_id,
        )

        if articulo is None:
            raise ValueError("Artículo de stock no encontrado")

        if not activo and articulo.stock_actual > 0:
            raise ValueError(
                "No se puede desactivar un artículo "
                "que todavía tiene stock disponible"
            )

        try:
            articulo = ArticuloStockRepository.update(
                db,
                articulo,
                {"activo": activo},
            )
            db.commit()
            db.refresh(articulo)

            return articulo
        except Exception:
            db.rollback()
            raise


    @staticmethod
    def entrada(
        db: Session,
        articulo_id: int,
        cantidad: Decimal,
        motivo: str | None = None
    ):

        articulo = StockService._get_articulo(
            db,
            articulo_id
        )

        StockService._validar_cantidad(
            cantidad
        )

        return StockService._aplicar_movimiento(
            db=db,
            articulo=articulo,
            tipo=TipoMovimientoStock.ENTRADA.value,
            cantidad=cantidad,
            suma=True,
            motivo=motivo
        )


    @staticmethod
    def salida(
        db: Session,
        articulo_id: int,
        cantidad: Decimal,
        motivo: str | None = None
    ):

        articulo = StockService._get_articulo(
            db,
            articulo_id
        )

        StockService._validar_cantidad(
            cantidad
        )

        return StockService._aplicar_movimiento(
            db=db,
            articulo=articulo,
            tipo=TipoMovimientoStock.SALIDA.value,
            cantidad=cantidad,
            suma=False,
            motivo=motivo
        )


    @staticmethod
    def ajuste_positivo(
        db: Session,
        articulo_id: int,
        cantidad: Decimal,
        motivo: str
    ):

        motivo = motivo.strip()

        if not motivo:
            raise ValueError(
                "El motivo del ajuste es obligatorio"
            )

        articulo = StockService._get_articulo(
            db,
            articulo_id
        )

        StockService._validar_cantidad(
            cantidad
        )

        return StockService._aplicar_movimiento(
            db=db,
            articulo=articulo,
            tipo=(
                TipoMovimientoStock
                .AJUSTE_POSITIVO.value
            ),
            cantidad=cantidad,
            suma=True,
            motivo=motivo
        )


    @staticmethod
    def ajuste_negativo(
        db: Session,
        articulo_id: int,
        cantidad: Decimal,
        motivo: str
    ):

        motivo = motivo.strip()

        if not motivo:
            raise ValueError(
                "El motivo del ajuste es obligatorio"
            )

        articulo = StockService._get_articulo(
            db,
            articulo_id
        )

        StockService._validar_cantidad(
            cantidad
        )

        return StockService._aplicar_movimiento(
            db=db,
            articulo=articulo,
            tipo=(
                TipoMovimientoStock
                .AJUSTE_NEGATIVO.value
            ),
            cantidad=cantidad,
            suma=False,
            motivo=motivo
        )


    @staticmethod
    def _aplicar_movimiento(
        db: Session,
        articulo,
        tipo: str,
        cantidad: Decimal,
        suma: bool,
        motivo: str | None = None,
        orden_id: int | None = None,
        commit: bool = True,
    ):

        if not articulo.controla_stock:
            raise ValueError("Este producto no controla existencias")

        stock_anterior = Decimal(
            articulo.stock_actual
        )

        if suma:
            stock_resultante = (
                stock_anterior + cantidad
            )
        else:
            stock_resultante = (
                stock_anterior - cantidad
            )

            if stock_resultante < 0:
                raise ValueError(
                    "No hay stock suficiente "
                    "para realizar esta operación"
                )

        try:

            articulo.stock_actual = (
                stock_resultante
            )

            movimiento = (
                MovimientoStockRepository.create(
                    db,
                    {
                        "articulo_id":
                            articulo.id,

                        "tipo":
                            tipo,

                        "cantidad":
                            cantidad,

                        "stock_anterior":
                            stock_anterior,

                        "stock_resultante":
                            stock_resultante,

                        "motivo":
                            motivo,

                        "orden_id":
                            orden_id
                    }
                )
            )

            if commit:
                db.commit()
                db.refresh(articulo)
                db.refresh(movimiento)
            else:
                db.flush()

            return movimiento

        except Exception:
            if commit:
                db.rollback()
            raise


    @staticmethod
    def _registrar_movimiento(
        db: Session,
        articulo,
        tipo: str,
        cantidad: Decimal,
        motivo: str | None = None,
        orden_id: int | None = None
    ):

        stock_anterior = Decimal(
            articulo.stock_actual
        )

        stock_resultante = (
            stock_anterior + cantidad
        )

        articulo.stock_actual = stock_resultante

        return (
            MovimientoStockRepository.create(
                db,
                {
                    "articulo_id":
                        articulo.id,

                    "tipo":
                        tipo,

                    "cantidad":
                        cantidad,

                    "stock_anterior":
                        stock_anterior,

                    "stock_resultante":
                        stock_resultante,

                    "motivo":
                        motivo,

                    "orden_id":
                        orden_id
                }
            )
        )


    @staticmethod
    def _get_articulo(
        db: Session,
        articulo_id: int
    ):

        articulo = (
            ArticuloStockRepository.get_by_id(
                db,
                articulo_id
            )
        )

        if articulo is None:
            raise ValueError(
                "Artículo de stock no encontrado"
            )

        if not articulo.activo:
            raise ValueError(
                "El artículo está inactivo"
            )

        return articulo


    @staticmethod
    def _validar_cantidad(
        cantidad: Decimal
    ):

        if cantidad <= 0:
            raise ValueError(
                "La cantidad debe ser mayor que 0"
            )
            
    @staticmethod
    def consumir_desde_orden(
        db: Session,
        articulo_id: int,
        cantidad: Decimal,
        orden_id: int,
        commit: bool = True,
    ):
        articulo = StockService._get_articulo(
            db,
            articulo_id
        )

        if not articulo.controla_stock:
            return None

        StockService._validar_cantidad(
            cantidad
        )

        return StockService._aplicar_movimiento(
            db=db,
            articulo=articulo,
            tipo=TipoMovimientoStock.CONSUMO_ORDEN.value,
            cantidad=cantidad,
            suma=False,
            motivo=f"Consumo en orden {orden_id}",
            orden_id=orden_id,
            commit=commit,
        )


    @staticmethod
    def devolver_desde_orden(
        db: Session,
        articulo_id: int,
        cantidad: Decimal,
        orden_id: int,
        commit: bool = True,
    ):
        articulo = StockService._get_articulo(
            db,
            articulo_id
        )

        if not articulo.controla_stock:
            return None

        StockService._validar_cantidad(
            cantidad
        )

        return StockService._aplicar_movimiento(
            db=db,
            articulo=articulo,
            tipo=TipoMovimientoStock.DEVOLUCION_ORDEN.value,
            cantidad=cantidad,
            suma=True,
            motivo=f"Devolución desde orden {orden_id}",
            orden_id=orden_id,
            commit=commit,
        )
        
