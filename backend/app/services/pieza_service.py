from sqlalchemy.orm import Session
from decimal import Decimal

from app.repositories.pieza_repository import PiezaRepository
from app.repositories.orden_reparacion_repository import OrdenReparacionRepository
from app.models.orden_reparacion import EstadoReparacion
from app.services.orden_reparacion_service import OrdenReparacionService
from app.repositories.proveedor_repository import ProveedorRepository   
from app.repositories.articulo_stock_repository import ArticuloStockRepository
from app.services.stock_service import StockService

from app.schemas.pieza import (
    PiezaCreate,
    PiezaUpdate
)

from app.schemas.pieza import PiezaResponse
from app.schemas.paginated_response import PaginatedResponse
from app.schemas.pagination import PaginationParams

class PiezaService:

    @staticmethod
    def _calcular_importe_sin_iva(
        cantidad: Decimal,
        precio_unitario: Decimal,
        descuento_porcentaje: Decimal,
    ) -> Decimal:
        """Calcula el importe de una pieza antes de IVA.

        El precio unitario es siempre una base sin IVA: el descuento se aplica
        directamente sobre esa base y el IVA se añade únicamente al recalcular
        el total de la orden o al generar su factura.
        """
        importe_bruto = cantidad * precio_unitario
        return importe_bruto * (
            Decimal("1") - descuento_porcentaje / Decimal("100")
        )

    @staticmethod
    def _validar_uso_stock(orden, articulo_stock_id: int | None) -> None:
        if articulo_stock_id is not None and orden.tipo not in {"OR", "GA"}:
            raise ValueError(
                "Solo se puede consumir stock en órdenes de reparación o garantías"
            )

    @staticmethod
    def _validar_orden_editable(orden) -> None:
        if orden.estado in {EstadoReparacion.FACTURADA.value, EstadoReparacion.ANULADA.value}:
            raise ValueError("No se pueden modificar las piezas de una orden anulada o facturada")
        if orden.tipo == "PR" and orden.estado != EstadoReparacion.BORRADOR.value:
            raise ValueError("No se pueden modificar las piezas de un presupuesto que no está en borrador")

    @staticmethod
    def get_by_orden(db: Session, orden_id: int):

        orden = OrdenReparacionRepository.get_by_id(
            db,
            orden_id
        )

        if orden is None:
            raise ValueError(
                "La orden de reparación no existe"
            )

        return PiezaRepository.get_by_orden(
            db,
            orden_id
        )

    @staticmethod
    def create(
        db: Session,
        orden_id: int,
        pieza: PiezaCreate
    ):

        orden = OrdenReparacionRepository.get_by_id(
            db,
            orden_id
        )

        if orden is None:
            raise ValueError(
                "La orden de reparación no existe"
            )

        PiezaService._validar_orden_editable(orden)
        PiezaService._validar_uso_stock(orden, pieza.articulo_stock_id)

        if pieza.proveedor_id is not None and ProveedorRepository.get_by_id(db, pieza.proveedor_id) is None:
            raise ValueError("El proveedor no existe")

        articulo = None
        if pieza.articulo_stock_id is not None:
            articulo = ArticuloStockRepository.get_by_id(
                db,
                pieza.articulo_stock_id,
            )
            if articulo is None:
                raise ValueError("Artículo de almacén no encontrado")

            # La pieza conserva la foto económica del artículo al añadirla.
            descripcion = articulo.nombre
            referencia = articulo.referencia
            precio_unitario = articulo.precio_venta
        else:
            descripcion = pieza.descripcion
            referencia = pieza.referencia
            precio_unitario = pieza.precio_unitario

        total = PiezaService._calcular_importe_sin_iva(
            pieza.cantidad,
            precio_unitario,
            pieza.descuento_porcentaje,
        )

        datos = {
            "descripcion": descripcion,
            "cantidad": pieza.cantidad,
            "precio_unitario": precio_unitario,
            "descuento_porcentaje": pieza.descuento_porcentaje,
            "cubierto_garantia": pieza.cubierto_garantia,
            "proveedor_id": pieza.proveedor_id,
            "referencia": referencia,
            "articulo_stock_id": pieza.articulo_stock_id,
            "total": total
        }

        try:
            if articulo is not None:
                StockService.consumir_desde_orden(
                    db,
                    articulo.id,
                    pieza.cantidad,
                    orden_id,
                    commit=False,
                )

            nueva = PiezaRepository.create(db, orden_id, datos, commit=False)
            OrdenReparacionService.recalcular_totales(
                db,
                orden_id,
                commit=False,
            )
            db.commit()
            db.refresh(nueva)
        except Exception:
            db.rollback()
            raise

        return nueva

    @staticmethod
    def update(
        db: Session,
        pieza_id: int,
        datos: PiezaUpdate
    ):

        pieza = PiezaRepository.get_by_id(
            db,
            pieza_id
        )

        if pieza is None:
            raise ValueError(
                "La pieza no existe"
            )

        orden = OrdenReparacionRepository.get_by_id(db, pieza.orden_id)
        if orden is None:
            raise ValueError("La orden de reparación no existe")
        PiezaService._validar_orden_editable(orden)

        datos_actualizados = datos.model_dump(
            exclude_unset=True
        )

        nueva_cantidad = Decimal(
            datos_actualizados.get("cantidad", pieza.cantidad)
        )
        articulo_anterior_id = pieza.articulo_stock_id
        articulo_nuevo_id = datos_actualizados.get(
            "articulo_stock_id",
            articulo_anterior_id,
        )
        PiezaService._validar_uso_stock(orden, articulo_nuevo_id)

        proveedor_id = datos_actualizados.get("proveedor_id", pieza.proveedor_id)
        if proveedor_id is not None and ProveedorRepository.get_by_id(db, proveedor_id) is None:
            raise ValueError("El proveedor no existe")

        articulo_nuevo = None
        if articulo_nuevo_id is not None and articulo_nuevo_id != articulo_anterior_id:
            articulo_nuevo = ArticuloStockRepository.get_by_id(db, articulo_nuevo_id)
            if articulo_nuevo is None:
                raise ValueError("Artículo de almacén no encontrado")

            datos_actualizados.update({
                "descripcion": articulo_nuevo.nombre,
                "referencia": articulo_nuevo.referencia,
                "precio_unitario": articulo_nuevo.precio_venta,
            })

        if (
            "cantidad" in datos_actualizados
            or "precio_unitario" in datos_actualizados
            or "descuento_porcentaje" in datos_actualizados
            or articulo_nuevo_id != articulo_anterior_id
            ):

            cantidad = nueva_cantidad

            precio = datos_actualizados.get(
            "precio_unitario",
            pieza.precio_unitario
            )

            descuento = datos_actualizados.get(
            "descuento_porcentaje",
            pieza.descuento_porcentaje
            )

            datos_actualizados["total"] = (
                PiezaService._calcular_importe_sin_iva(
                    cantidad,
                    precio,
                    descuento,
                )
            )

        # Ajusta existencias antes de guardar la pieza. Si falta stock, la
        # pieza no llega a modificarse.
        cantidad_anterior = Decimal(pieza.cantidad)
        try:
            if articulo_nuevo_id != articulo_anterior_id:
                if articulo_anterior_id is not None:
                    StockService.devolver_desde_orden(
                        db, articulo_anterior_id, cantidad_anterior, pieza.orden_id,
                        commit=False,
                    )
                if articulo_nuevo_id is not None:
                    StockService.consumir_desde_orden(
                        db, articulo_nuevo_id, nueva_cantidad, pieza.orden_id,
                        commit=False,
                    )
            elif articulo_anterior_id is not None:
                diferencia = nueva_cantidad - cantidad_anterior
                if diferencia > 0:
                    StockService.consumir_desde_orden(
                        db, articulo_anterior_id, diferencia, pieza.orden_id,
                        commit=False,
                    )
                elif diferencia < 0:
                    cantidad_devolver = abs(diferencia)
                    StockService.devolver_desde_orden(
                        db, articulo_anterior_id, cantidad_devolver, pieza.orden_id,
                        commit=False,
                    )

            pieza = PiezaRepository.update(
                db,
                pieza,
                datos_actualizados,
                commit=False,
            )
            OrdenReparacionService.recalcular_totales(
                db,
                pieza.orden_id,
                commit=False,
            )
            db.commit()
            db.refresh(pieza)
        except Exception:
            db.rollback()
            raise

        return pieza

    @staticmethod
    def delete(
        db: Session,
        pieza_id: int
    ):

        pieza = PiezaRepository.get_by_id(
            db,
            pieza_id
        )

        if pieza is None:
            raise ValueError(
                "La pieza no existe"
            )

        orden = OrdenReparacionRepository.get_by_id(db, pieza.orden_id)
        if orden is None:
            raise ValueError("La orden de reparación no existe")
        PiezaService._validar_orden_editable(orden)

        orden_id = pieza.orden_id

        try:
            if pieza.articulo_stock_id is not None:
                StockService.devolver_desde_orden(
                    db,
                    pieza.articulo_stock_id,
                    Decimal(pieza.cantidad),
                    orden_id,
                    commit=False,
                )

            PiezaRepository.delete(db, pieza, commit=False)
            OrdenReparacionService.recalcular_totales(
                db,
                orden_id,
                commit=False,
            )
            db.commit()
        except Exception:
            db.rollback()
            raise
        
    @staticmethod
    def get_paginated(
        db: Session,
        pagination: PaginationParams
    ):
        items, total = PiezaRepository.get_paginated(
            db,
            pagination
        )

        return PaginatedResponse[PiezaResponse].create(
            items=items,
            total=total,
            page=pagination.page,
            size=pagination.size
        )
"""Gestión de piezas de órdenes y sincronización trazable con el almacén."""
