"""Gestión de datos previos a la generación y firma de Facturae."""

from sqlalchemy.orm import Session

from app.models.factura import EstadoFactura, Factura
from app.models.facturae_destino import FacturaeDestino
from app.schemas.facturae import FacturaeDestinoUpdate


class FacturaeService:
    @staticmethod
    def obtener_destino(db: Session, factura_id: int) -> FacturaeDestino | None:
        return db.query(FacturaeDestino).filter(FacturaeDestino.factura_id == factura_id).first()

    @staticmethod
    def guardar_destino(db: Session, factura_id: int, datos: FacturaeDestinoUpdate) -> FacturaeDestino:
        factura = db.get(Factura, factura_id)
        if factura is None:
            raise ValueError("Factura no encontrada")
        if factura.estado != EstadoFactura.BORRADOR.value:
            raise ValueError("Los datos de Facturae solo se pueden modificar en borrador")

        destino = FacturaeService.obtener_destino(db, factura_id)
        valores = datos.model_dump()
        if destino is None:
            destino = FacturaeDestino(factura_id=factura_id, **valores)
            db.add(destino)
        else:
            for campo, valor in valores.items():
                setattr(destino, campo, valor)
        db.commit()
        db.refresh(destino)
        return destino
