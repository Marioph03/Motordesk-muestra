"""Registro de pagos y cálculo de pendiente de las facturas."""

from decimal import Decimal

from sqlalchemy.orm import Session

from app.models.factura import (
    EstadoFactura,
    EstadoCobro
)
from app.repositories.factura_repository import FacturaRepository
from app.repositories.pago_factura_repository import PagoFacturaRepository
from app.schemas.pago_factura import PagoFacturaCreate


class PagoFacturaService:

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

        return PagoFacturaRepository.get_by_factura(
            db,
            factura_id
        )

    @staticmethod
    def calcular_importes(
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

        pagos = PagoFacturaRepository.get_by_factura(
            db,
            factura_id
        )

        importe_pagado = sum(
            (
                pago.importe
                for pago in pagos
            ),
            Decimal("0.00")
        )

        total_factura = Decimal(
            str(factura.total)
        )

        importe_pendiente = (
            total_factura -
            importe_pagado
        )

        if importe_pendiente < Decimal("0.00"):
            importe_pendiente = Decimal("0.00")

        return {
            "total": total_factura,
            "importe_pagado": importe_pagado,
            "importe_pendiente": importe_pendiente
        }

    @staticmethod
    def recalcular_estado_cobro(
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

        importes = (
            PagoFacturaService.calcular_importes(
                db,
                factura_id
            )
        )

        importe_pagado = importes[
            "importe_pagado"
        ]

        total = importes[
            "total"
        ]

        if importe_pagado <= Decimal("0.00"):

            factura.estado_cobro = (
                EstadoCobro.PENDIENTE.value
            )

        elif importe_pagado < total:

            factura.estado_cobro = (
                EstadoCobro.PARCIAL.value
            )

        else:

            factura.estado_cobro = (
                EstadoCobro.PAGADA.value
            )

        db.commit()
        db.refresh(factura)

        return factura

    @staticmethod
    def create(
        db: Session,
        factura_id: int,
        pago: PagoFacturaCreate
    ):

        factura = FacturaRepository.get_by_id_for_update(
            db,
            factura_id
        )

        if factura is None:
            raise ValueError(
                "Factura no encontrada"
            )

        # Solo se pueden cobrar facturas emitidas
        if factura.estado != EstadoFactura.EMITIDA.value:
            raise ValueError(
                "Solo se pueden registrar cobros "
                "en facturas emitidas"
            )

        importe = Decimal(
            str(pago.importe)
        )

        if importe <= Decimal("0.00"):
            raise ValueError(
                "El importe del cobro debe ser mayor que 0"
            )

        importes = (
            PagoFacturaService.calcular_importes(
                db,
                factura_id
            )
        )

        pendiente = importes[
            "importe_pendiente"
        ]

        if pendiente <= Decimal("0.00"):
            raise ValueError(
                "La factura ya está completamente pagada"
            )

        if importe > pendiente:
            raise ValueError(
                f"El importe supera la cantidad pendiente "
                f"({pendiente:.2f} €)"
            )

        datos = pago.model_dump()

        datos["factura_id"] = factura_id
        datos["importe"] = importe

        nuevo_pago = PagoFacturaRepository.create(
            db,
            datos
        )

        PagoFacturaService.recalcular_estado_cobro(
            db,
            factura_id
        )

        return nuevo_pago

    @staticmethod
    def delete(
        db: Session,
        pago_id: int
    ):

        pago = PagoFacturaRepository.get_by_id(
            db,
            pago_id
        )

        if pago is None:
            raise ValueError(
                "Cobro no encontrado"
            )

        factura = FacturaRepository.get_by_id_for_update(
            db,
            pago.factura_id
        )

        if factura is None:
            raise ValueError(
                "Factura no encontrada"
            )

        if factura.estado == EstadoFactura.ANULADA.value:
            raise ValueError(
                "No se pueden modificar cobros "
                "de una factura anulada"
            )

        factura_id = pago.factura_id

        PagoFacturaRepository.delete(
            db,
            pago
        )

        PagoFacturaService.recalcular_estado_cobro(
            db,
            factura_id
        )
