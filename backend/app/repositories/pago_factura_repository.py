from sqlalchemy.orm import Session

from app.models.pago_factura import PagoFactura


class PagoFacturaRepository:

    @staticmethod
    def get_by_factura(
        db: Session,
        factura_id: int
    ):
        return (
            db.query(PagoFactura)
            .filter(
                PagoFactura.factura_id == factura_id
            )
            .order_by(
                PagoFactura.fecha_pago.asc()
            )
            .all()
        )

    @staticmethod
    def get_by_id(
        db: Session,
        pago_id: int
    ):
        return (
            db.query(PagoFactura)
            .filter(
                PagoFactura.id == pago_id
            )
            .first()
        )

    @staticmethod
    def create(
        db: Session,
        datos: dict
    ):

        pago = PagoFactura(**datos)

        db.add(pago)
        db.flush()
        db.refresh(pago)

        return pago

    @staticmethod
    def delete(
        db: Session,
        pago: PagoFactura
    ):

        db.delete(pago)
        db.flush()
"""Acceso a pagos para calcular cobros reales y deuda pendiente de facturas."""
