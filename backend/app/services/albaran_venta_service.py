"""Venta de recambios: borrador, confirmación y salida trazable de stock."""

from datetime import datetime
from decimal import Decimal

from sqlalchemy.orm import Session, selectinload

from app.models.albaran_venta import AlbaranVenta
from app.models.cliente import Cliente
from app.models.linea_albaran_venta import LineaAlbaranVenta
from app.models.movimiento_stock import TipoMovimientoStock
from app.repositories.articulo_stock_repository import ArticuloStockRepository
from app.schemas.albaran_venta import AlbaranVentaCreate
from app.services.stock_service import StockService


class AlbaranVentaService:
    @staticmethod
    def siguiente_numero(db: Session) -> str:
        anio = datetime.now().year
        ultimo = (
            db.query(AlbaranVenta)
            .filter(AlbaranVenta.numero.like(f"AV-{anio}-%"))
            .order_by(AlbaranVenta.id.desc())
            .first()
        )
        secuencia = int(ultimo.numero.split("-")[-1]) + 1 if ultimo else 1
        return f"AV-{anio}-{secuencia:06d}"

    @staticmethod
    def listar(db: Session) -> list[AlbaranVenta]:
        return (
            db.query(AlbaranVenta)
            .options(
                selectinload(AlbaranVenta.cliente),
                selectinload(AlbaranVenta.lineas),
                selectinload(AlbaranVenta.factura_enlace),
            )
            .order_by(AlbaranVenta.fecha.desc(), AlbaranVenta.id.desc())
            .all()
        )

    @staticmethod
    def obtener(db: Session, albaran_id: int) -> AlbaranVenta | None:
        return (
            db.query(AlbaranVenta)
            .options(
                selectinload(AlbaranVenta.cliente),
                selectinload(AlbaranVenta.lineas),
                selectinload(AlbaranVenta.factura_enlace),
            )
            .filter(AlbaranVenta.id == albaran_id)
            .first()
        )

    @staticmethod
    def crear(db: Session, datos: AlbaranVentaCreate) -> AlbaranVenta:
        if db.query(Cliente).filter(Cliente.id == datos.cliente_id).first() is None:
            raise ValueError("El cliente seleccionado no existe")

        try:
            albaran = AlbaranVenta(
                numero=AlbaranVentaService.siguiente_numero(db),
                cliente_id=datos.cliente_id,
                fecha=datos.fecha,
                estado="BORRADOR",
                observaciones=(datos.observaciones or "").strip() or None,
                total=Decimal("0"),
            )
            db.add(albaran)
            db.flush()

            total_albaran = Decimal("0")
            articulos_ids = set()
            for linea in datos.lineas:
                if linea.articulo_stock_id in articulos_ids:
                    raise ValueError("No repitas el mismo artículo en el albarán")
                articulos_ids.add(linea.articulo_stock_id)

                articulo = ArticuloStockRepository.get_by_id(db, linea.articulo_stock_id)
                if articulo is None or not articulo.activo:
                    raise ValueError("Uno de los artículos seleccionados no está disponible")

                precio = Decimal(linea.precio_unitario if linea.precio_unitario is not None else articulo.precio_venta)
                total_linea = Decimal(linea.cantidad) * precio * (
                    Decimal("1") - Decimal(linea.descuento_porcentaje) / Decimal("100")
                )
                total_albaran += total_linea
                db.add(LineaAlbaranVenta(
                    albaran_id=albaran.id,
                    articulo_stock_id=articulo.id,
                    referencia=articulo.referencia,
                    descripcion=articulo.nombre,
                    cantidad=linea.cantidad,
                    precio_unitario=precio,
                    descuento_porcentaje=linea.descuento_porcentaje,
                    total=total_linea,
                ))

            albaran.total = total_albaran
            db.commit()
            return AlbaranVentaService.obtener(db, albaran.id)  # type: ignore[return-value]
        except Exception:
            db.rollback()
            raise

    @staticmethod
    def confirmar(db: Session, albaran_id: int) -> AlbaranVenta:
        albaran = AlbaranVentaService.obtener(db, albaran_id)
        if albaran is None:
            raise ValueError("Albarán de venta no encontrado")
        if albaran.estado == "CONFIRMADO":
            raise ValueError("El albarán ya está confirmado")
        if albaran.estado == "ANULADO":
            raise ValueError("No se puede confirmar un albarán anulado")

        try:
            for linea in albaran.lineas:
                articulo = ArticuloStockRepository.get_by_id(db, linea.articulo_stock_id)
                if articulo is None:
                    raise ValueError("Uno de los artículos del albarán ya no existe")
                StockService._aplicar_movimiento(
                    db=db,
                    articulo=articulo,
                    tipo=TipoMovimientoStock.SALIDA.value,
                    cantidad=Decimal(linea.cantidad),
                    suma=False,
                    motivo=f"Venta por albarán {albaran.numero}",
                    commit=False,
                )
            albaran.estado = "CONFIRMADO"
            db.commit()
            return AlbaranVentaService.obtener(db, albaran.id)  # type: ignore[return-value]
        except Exception:
            db.rollback()
            raise

    @staticmethod
    def anular(db: Session, albaran_id: int) -> AlbaranVenta:
        albaran = AlbaranVentaService.obtener(db, albaran_id)
        if albaran is None:
            raise ValueError("Albarán de venta no encontrado")
        if albaran.estado != "BORRADOR":
            raise ValueError("Solo se pueden anular albaranes de venta en borrador")
        albaran.estado = "ANULADO"
        db.commit()
        return AlbaranVentaService.obtener(db, albaran.id)  # type: ignore[return-value]
