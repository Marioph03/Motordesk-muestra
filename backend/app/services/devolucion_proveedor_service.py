"""Devoluciones a proveedor y salida controlada de existencias relacionadas."""

from datetime import datetime
from decimal import Decimal

from sqlalchemy.orm import Session

from app.models.albaran_proveedor import AlbaranProveedor
from app.models.devolucion_proveedor import DevolucionProveedor
from app.models.linea_albaran_proveedor import LineaAlbaranProveedor
from app.models.linea_devolucion_proveedor import LineaDevolucionProveedor
from app.models.movimiento_stock import TipoMovimientoStock
from app.repositories.articulo_stock_repository import ArticuloStockRepository
from app.schemas.devolucion_proveedor import DevolucionProveedorCreate
from app.services.stock_service import StockService


class DevolucionProveedorService:
    MOTIVOS_VALIDOS = {
        "DEFECTUOSO",
        "ERROR_PEDIDO",
        "NO_CORRESPONDE",
        "SOBRANTE",
        "OTRO",
    }
    RESOLUCIONES_VALIDAS = {
        "PENDIENTE",
        "ABONO",
        "SUSTITUCION",
        "RECHAZADA",
    }

    @staticmethod
    def siguiente_numero(db: Session) -> str:
        anio = datetime.now().year
        ultimo = (
            db.query(DevolucionProveedor)
            .filter(DevolucionProveedor.numero.like(f"DEV-{anio}-%"))
            .order_by(DevolucionProveedor.id.desc())
            .first()
        )
        secuencia = 1 if ultimo is None else int(ultimo.numero.rsplit("-", 1)[-1]) + 1
        return f"DEV-{anio}-{secuencia:06d}"

    @staticmethod
    def crear(
        db: Session,
        datos: DevolucionProveedorCreate,
    ) -> DevolucionProveedor:
        if not datos.lineas:
            raise ValueError("La devolución debe tener al menos una línea")

        motivo = datos.motivo.strip().upper()
        if motivo not in DevolucionProveedorService.MOTIVOS_VALIDOS:
            raise ValueError("Motivo de devolución no válido")

        try:
            albaran = DevolucionProveedorService._validar_albaran_origen(
                db,
                datos.albaran_origen_id,
                datos.proveedor_id,
            )
            DevolucionProveedorService._validar_lineas(
                db,
                albaran,
                datos.lineas,
            )

            devolucion = DevolucionProveedor(
                numero=DevolucionProveedorService.siguiente_numero(db),
                proveedor_id=datos.proveedor_id,
                albaran_origen_id=albaran.id,
                motivo=motivo,
                observaciones=datos.observaciones,
                estado="BORRADOR",
                resolucion="PENDIENTE",
            )
            db.add(devolucion)
            db.flush()

            for linea in datos.lineas:
                db.add(
                    LineaDevolucionProveedor(
                        devolucion_id=devolucion.id,
                        linea_albaran_id=linea.linea_albaran_id,
                        articulo_stock_id=linea.articulo_stock_id,
                        cantidad=Decimal(linea.cantidad),
                    )
                )

            db.commit()
            db.refresh(devolucion)
            return devolucion
        except Exception:
            db.rollback()
            raise

    @staticmethod
    def confirmar(
        db: Session,
        devolucion_id: int,
    ) -> DevolucionProveedor:
        """Confirma una devolución y descuenta de stock sus líneas una sola vez."""
        devolucion = DevolucionProveedorService._obtener(db, devolucion_id)
        if devolucion.estado == "CONFIRMADA":
            raise ValueError("La devolución ya está confirmada")
        if devolucion.estado == "ANULADA":
            raise ValueError("No se puede confirmar una devolución anulada")
        if devolucion.estado != "BORRADOR":
            raise ValueError("Solo se pueden confirmar devoluciones en borrador")
        if not devolucion.lineas:
            raise ValueError("La devolución no tiene líneas")

        try:
            albaran = DevolucionProveedorService._validar_albaran_origen(
                db,
                devolucion.albaran_origen_id,
                devolucion.proveedor_id,
            )
            DevolucionProveedorService._validar_lineas(
                db,
                albaran,
                devolucion.lineas,
            )

            for linea in devolucion.lineas:
                articulo = ArticuloStockRepository.get_by_id(
                    db,
                    linea.articulo_stock_id,
                )
                if articulo is None:
                    raise ValueError("Artículo de stock no encontrado")

                StockService._aplicar_movimiento(
                    db=db,
                    articulo=articulo,
                    tipo=TipoMovimientoStock.DEVOLUCION_PROVEEDOR.value,
                    cantidad=Decimal(linea.cantidad),
                    suma=False,
                    motivo=(
                        f"Devolución a proveedor {devolucion.numero} "
                        f"(albarán {albaran.numero_interno})"
                    ),
                    commit=False,
                )

            devolucion.estado = "CONFIRMADA"
            db.flush()
            db.commit()
            db.refresh(devolucion)
            return devolucion
        except Exception:
            db.rollback()
            raise

    @staticmethod
    def resolver(
        db: Session,
        devolucion_id: int,
        resolucion: str,
    ) -> DevolucionProveedor:
        resolucion_normalizada = resolucion.strip().upper()
        if resolucion_normalizada not in DevolucionProveedorService.RESOLUCIONES_VALIDAS:
            raise ValueError("Resolución de devolución no válida")

        devolucion = DevolucionProveedorService._obtener(db, devolucion_id)
        if devolucion.estado != "CONFIRMADA":
            raise ValueError("Solo se puede resolver una devolución confirmada")

        try:
            devolucion.resolucion = resolucion_normalizada
            db.commit()
            db.refresh(devolucion)
            return devolucion
        except Exception:
            db.rollback()
            raise

    @staticmethod
    def cantidad_ya_devuelta(
        db: Session,
        linea_albaran_id: int,
    ) -> Decimal:
        lineas = (
            db.query(LineaDevolucionProveedor)
            .join(DevolucionProveedor)
            .filter(
                LineaDevolucionProveedor.linea_albaran_id == linea_albaran_id,
                DevolucionProveedor.estado == "CONFIRMADA",
            )
            .all()
        )
        return sum((Decimal(linea.cantidad) for linea in lineas), Decimal("0"))

    @staticmethod
    def _obtener(db: Session, devolucion_id: int) -> DevolucionProveedor:
        devolucion = (
            db.query(DevolucionProveedor)
            .filter(DevolucionProveedor.id == devolucion_id)
            .first()
        )
        if devolucion is None:
            raise ValueError("Devolución no encontrada")
        return devolucion

    @staticmethod
    def _validar_albaran_origen(
        db: Session,
        albaran_id: int,
        proveedor_id: int,
    ) -> AlbaranProveedor:
        albaran = (
            db.query(AlbaranProveedor)
            .filter(AlbaranProveedor.id == albaran_id)
            .first()
        )
        if albaran is None:
            raise ValueError("Albarán de origen no encontrado")
        if albaran.estado != "CONFIRMADO":
            raise ValueError("Solo se puede devolver mercancía de un albarán confirmado")
        if albaran.proveedor_id != proveedor_id:
            raise ValueError("El proveedor no coincide con el albarán de origen")
        return albaran

    @staticmethod
    def _validar_lineas(
        db: Session,
        albaran: AlbaranProveedor,
        lineas,
    ) -> None:
        lineas_albaran = {linea.id: linea for linea in albaran.lineas}
        cantidades_actuales: dict[int, Decimal] = {}

        for linea in lineas:
            origen = lineas_albaran.get(linea.linea_albaran_id)
            if origen is None:
                raise ValueError("Una línea no pertenece al albarán de origen")
            if origen.articulo_stock_id != linea.articulo_stock_id:
                raise ValueError("El artículo no coincide con la línea del albarán")

            cantidad = Decimal(linea.cantidad)
            if cantidad <= 0:
                raise ValueError("La cantidad a devolver debe ser mayor que cero")

            cantidades_actuales[origen.id] = (
                cantidades_actuales.get(origen.id, Decimal("0")) + cantidad
            )

        for linea_albaran_id, cantidad_actual in cantidades_actuales.items():
            origen = lineas_albaran[linea_albaran_id]
            cantidad_disponible = (
                Decimal(origen.cantidad_recibida)
                - DevolucionProveedorService.cantidad_ya_devuelta(db, origen.id)
            )
            if cantidad_actual > cantidad_disponible:
                raise ValueError("No se puede devolver más cantidad de la recibida")
