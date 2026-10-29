from decimal import Decimal

from sqlalchemy.orm import Session

from app.models.factura import EstadoFactura, TipoFactura
from app.repositories.factura_repository import FacturaRepository
from app.repositories.factura_linea_repository import FacturaLineaRepository
from app.schemas.factura_linea import (
    FacturaLineaCreate,
    FacturaLineaUpdate
)
from app.services.factura_service import FacturaService


class FacturaLineaService:

    CATEGORIAS_FISCALES = {
        "VENTA_SERVICIO",
        "COMISION_SUJETA",
        "COMISION_EXENTA",
    }

    @staticmethod
    def _validar_factura_borrador(factura) -> None:
        if factura.estado != EstadoFactura.BORRADOR.value:
            raise ValueError(
                "Las líneas solo se pueden modificar en una factura en borrador"
            )

    @staticmethod
    def _validar_linea_manual(linea) -> None:
        if linea.origen != "MANUAL":
            raise ValueError(
                "Las líneas procedentes de la orden solo se actualizan desde la orden"
            )

    @staticmethod
    def _validar_importes(
        cantidad: Decimal,
        precio_unitario: Decimal,
        descuento_porcentaje: Decimal,
        iva: Decimal,
    ) -> None:
        if cantidad <= Decimal("0"):
            raise ValueError("La cantidad de la línea debe ser mayor que cero")
        if precio_unitario < Decimal("0"):
            raise ValueError("El precio unitario no puede ser negativo")
        if not Decimal("0") <= descuento_porcentaje <= Decimal("100"):
            raise ValueError("El descuento debe estar entre 0 y 100")
        if not Decimal("0") <= iva <= Decimal("100"):
            raise ValueError("El IVA debe estar entre 0 y 100")

    @staticmethod
    def _validar_categoria_fiscal(
        categoria_fiscal: str,
        iva: Decimal,
        motivo_exencion: str | None,
    ) -> None:
        if categoria_fiscal not in FacturaLineaService.CATEGORIAS_FISCALES:
            raise ValueError("La categoría fiscal de la línea no es válida")

        if categoria_fiscal == "COMISION_EXENTA":
            if iva != Decimal("0"):
                raise ValueError("Una comisión exenta debe tener IVA 0 %")
            if not motivo_exencion or not motivo_exencion.strip():
                raise ValueError(
                    "Indica el motivo legal de exención de la comisión"
                )
        elif motivo_exencion and motivo_exencion.strip():
            raise ValueError(
                "El motivo de exención solo corresponde a comisiones exentas"
            )

    @staticmethod
    def _validar_categoria_para_factura(factura, categoria_fiscal: str) -> None:
        if (
            categoria_fiscal != "VENTA_SERVICIO"
            and factura.tipo_factura != TipoFactura.VENTAS_COMISIONES.value
        ):
            raise ValueError(
                "Las comisiones solo se pueden incluir en una factura de ventas y comisiones"
            )

    @staticmethod
    def get_by_factura(
        db: Session,
        factura_id: int
    ):

        factura = FacturaRepository.get_by_id(
            db,
            factura_id
        )

        if factura is None:
            raise ValueError(
                "Factura no encontrada"
            )

        return FacturaLineaRepository.get_by_factura(
            db,
            factura_id
        )

    @staticmethod
    def create(
        db: Session,
        factura_id: int,
        linea: FacturaLineaCreate
    ):

        factura = FacturaRepository.get_by_id(
            db,
            factura_id
        )

        if factura is None:
            raise ValueError(
                "Factura no encontrada"
            )

        FacturaLineaService._validar_factura_borrador(factura)

        if linea.origen != "MANUAL":
            raise ValueError(
                "Las líneas de mano de obra y piezas se generan desde la orden"
            )

        FacturaLineaService._validar_importes(
            linea.cantidad,
            linea.precio_unitario,
            linea.descuento_porcentaje,
            linea.iva,
        )
        FacturaLineaService._validar_categoria_fiscal(
            linea.categoria_fiscal,
            linea.iva,
            linea.motivo_exencion,
        )
        FacturaLineaService._validar_categoria_para_factura(
            factura,
            linea.categoria_fiscal,
        )

        subtotal = (
            linea.cantidad *
            linea.precio_unitario
        )

        descuento = (
            subtotal *
            linea.descuento_porcentaje
        ) / Decimal("100")

        subtotal -= descuento

        datos = linea.model_dump()

        datos["factura_id"] = factura_id
        datos["subtotal"] = subtotal
        # El importe de una línea es siempre su base con el descuento ya
        # aplicado. El IVA se calcula solo en el resumen de la factura.
        datos["total"] = subtotal

        nueva_linea = FacturaLineaRepository.create(
            db,
            datos
        )

        FacturaService.recalcular_totales(
            db,
            factura_id
        )

        return nueva_linea

    @staticmethod
    def update(
        db: Session,
        linea_id: int,
        datos: FacturaLineaUpdate
    ):

        linea = FacturaLineaRepository.get_by_id(
            db,
            linea_id
        )

        if linea is None:
            raise ValueError(
                "Línea no encontrada"
            )

        factura = FacturaRepository.get_by_id(db, linea.factura_id)
        if factura is None:
            raise ValueError("Factura no encontrada")

        FacturaLineaService._validar_factura_borrador(factura)
        FacturaLineaService._validar_linea_manual(linea)

        datos_actualizados = datos.model_dump(
            exclude_unset=True
        )

        cantidad = datos_actualizados.get(
            "cantidad",
            linea.cantidad
        )

        precio = datos_actualizados.get(
            "precio_unitario",
            linea.precio_unitario
        )

        descuento = datos_actualizados.get(
            "descuento_porcentaje",
            linea.descuento_porcentaje
        )

        iva = datos_actualizados.get(
            "iva",
            linea.iva
        )
        categoria_fiscal = datos_actualizados.get(
            "categoria_fiscal",
            linea.categoria_fiscal,
        )
        motivo_exencion = datos_actualizados.get(
            "motivo_exencion",
            linea.motivo_exencion,
        )

        FacturaLineaService._validar_importes(
            cantidad,
            precio,
            descuento,
            iva,
        )
        FacturaLineaService._validar_categoria_fiscal(
            categoria_fiscal,
            iva,
            motivo_exencion,
        )
        FacturaLineaService._validar_categoria_para_factura(
            factura,
            categoria_fiscal,
        )

        subtotal = cantidad * precio

        subtotal -= (
            subtotal *
            descuento /
            Decimal("100")
        )

        datos_actualizados["subtotal"] = subtotal
        datos_actualizados["total"] = subtotal

        linea = FacturaLineaRepository.update(
            db,
            linea,
            datos_actualizados
        )

        FacturaService.recalcular_totales(
            db,
            linea.factura_id
        )

        return linea

    @staticmethod
    def delete(
        db: Session,
        linea_id: int
    ):

        linea = FacturaLineaRepository.get_by_id(
            db,
            linea_id
        )

        if linea is None:
            raise ValueError(
                "Línea no encontrada"
            )

        factura = FacturaRepository.get_by_id(db, linea.factura_id)
        if factura is None:
            raise ValueError("Factura no encontrada")

        FacturaLineaService._validar_factura_borrador(factura)
        FacturaLineaService._validar_linea_manual(linea)

        factura_id = linea.factura_id

        FacturaLineaRepository.delete(
            db,
            linea
        )

        FacturaService.recalcular_totales(
            db,
            factura_id
        )
"""Reglas de edición de líneas y recálculo de totales de factura en borrador."""
