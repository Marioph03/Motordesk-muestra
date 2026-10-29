"""Gestión del directorio Facturae aislado por empresa."""

from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.models.facturae_organismo import FacturaeOrganismo
from app.schemas.facturae_organismo import FacturaeOrganismoUpdate


class FacturaeOrganismoService:
    @staticmethod
    def listar(db: Session, empresa_id: int, busqueda: str | None = None) -> list[FacturaeOrganismo]:
        consulta = db.query(FacturaeOrganismo).filter(FacturaeOrganismo.empresa_id == empresa_id)
        if busqueda and busqueda.strip():
            patron = f"%{busqueda.strip()}%"
            consulta = consulta.filter(or_(FacturaeOrganismo.nombre.ilike(patron), FacturaeOrganismo.nif.ilike(patron)))
        return consulta.order_by(FacturaeOrganismo.nombre.asc()).all()

    @staticmethod
    def guardar(
        db: Session,
        empresa_id: int,
        datos: FacturaeOrganismoUpdate,
        organismo_id: int | None = None,
    ) -> FacturaeOrganismo:
        organismo = None
        if organismo_id is not None:
            organismo = db.query(FacturaeOrganismo).filter(
                FacturaeOrganismo.id == organismo_id,
                FacturaeOrganismo.empresa_id == empresa_id,
            ).first()
            if organismo is None:
                raise ValueError("Organismo Facturae no encontrado")
        else:
            organismo = db.query(FacturaeOrganismo).filter(
                FacturaeOrganismo.empresa_id == empresa_id,
                FacturaeOrganismo.nif == datos.nif,
            ).first()

        valores = datos.model_dump()
        if organismo is None:
            organismo = FacturaeOrganismo(empresa_id=empresa_id, **valores)
            db.add(organismo)
        else:
            for campo, valor in valores.items():
                setattr(organismo, campo, valor)
        db.commit()
        db.refresh(organismo)
        return organismo
