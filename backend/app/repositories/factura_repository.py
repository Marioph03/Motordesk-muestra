from datetime import timedelta

from sqlalchemy.orm import Session
from sqlalchemy.orm import joinedload

from app.models.factura import Factura
from app.models.factura_albaran_venta import FacturaAlbaranVenta
from app.models.factura_linea import FacturaLinea
from sqlalchemy import or_

from app.models.cliente import Cliente
from app.models.vehiculo import Vehiculo

from app.schemas.pagination import PaginationParams
from app.repositories.base_repository import BaseRepository
from app.schemas.factura_filtro import FacturaFiltro


class FacturaRepository:

    @staticmethod
    def _aplicar_filtros(query, filtros: FacturaFiltro):
        """Aplica los filtros del listado tanto a la consulta simple como paginada."""
        if filtros.estado:
            query = query.filter(Factura.estado == filtros.estado)

        if filtros.cliente_id:
            query = query.filter(Factura.cliente_id == filtros.cliente_id)

        if filtros.vehiculo_id:
            query = query.filter(Factura.vehiculo_id == filtros.vehiculo_id)

        if filtros.tipo_documento:
            query = query.filter(Factura.tipo_documento == filtros.tipo_documento)

        if filtros.fecha_desde:
            query = query.filter(Factura.fecha_emision >= filtros.fecha_desde)

        if filtros.fecha_hasta:
            # La fecha del filtro no lleva hora; incluimos por completo el día
            # seleccionado sin depender de la precisión del campo DateTime.
            query = query.filter(
                Factura.fecha_emision < filtros.fecha_hasta + timedelta(days=1)
            )

        if filtros.total_desde is not None:
            query = query.filter(Factura.total >= filtros.total_desde)

        if filtros.total_hasta is not None:
            query = query.filter(Factura.total <= filtros.total_hasta)

        if filtros.numero:
            query = query.filter(Factura.numero.ilike(f"%{filtros.numero}%"))

        return query

    @staticmethod
    def get_emitidas_en_rango(
        db: Session,
        fecha_inicio,
        fecha_fin,
    ):
        return (
            db.query(Factura)
            .filter(
                Factura.fecha_emision >= fecha_inicio,
                Factura.fecha_emision < fecha_fin,
            )
            .order_by(Factura.fecha_emision.asc())
            .all()
        )

    @staticmethod
    def get_all(db: Session):
        return db.query(Factura).all()

    @staticmethod
    def get_by_id(
        db: Session,
        factura_id: int
    ):

        return (
            db.query(Factura)
            .options(
                joinedload(Factura.cliente),
                joinedload(Factura.vehiculo),
                joinedload(Factura.orden),
                joinedload(Factura.lineas).joinedload(FacturaLinea.albaran_venta),
                joinedload(Factura.albaranes_venta).joinedload(
                    FacturaAlbaranVenta.albaran_venta
                ),
            )
            .filter(Factura.id == factura_id)
            .first()
        )

    @staticmethod
    def get_by_numero(
        db: Session,
        numero: str
    ):
        return (
            db.query(Factura)
            .filter(Factura.numero == numero)
            .first()
        )

    @staticmethod
    def get_by_orden(
        db: Session,
        orden_id: int
    ):
        return (
            db.query(Factura)
            .options(
                joinedload(Factura.cliente),
                joinedload(Factura.vehiculo),
                joinedload(Factura.orden),
                joinedload(Factura.lineas).joinedload(FacturaLinea.albaran_venta),
                joinedload(Factura.albaranes_venta).joinedload(
                    FacturaAlbaranVenta.albaran_venta
                ),
            )
            .filter(Factura.orden_id == orden_id)
            .order_by(Factura.id.desc())
            .first()
        )

    @staticmethod
    def get_by_albaran_venta(db: Session, albaran_venta_id: int):
        return (
            db.query(Factura)
            .join(FacturaAlbaranVenta)
            .filter(FacturaAlbaranVenta.albaran_venta_id == albaran_venta_id)
            .first()
        )

    @staticmethod
    def get_by_id_for_update(
        db: Session,
        factura_id: int
    ):
        return (
            db.query(Factura)
            .filter(Factura.id == factura_id)
            .with_for_update()
            .first()
        )

    @staticmethod
    def create(
        db: Session,
        datos: dict
    ):
        factura = Factura(**datos)

        db.add(factura)
        db.commit()
        db.refresh(factura)

        return factura

    @staticmethod
    def update(
        db: Session,
        factura: Factura,
        datos: dict
    ):

        for key, value in datos.items():
            setattr(
                factura,
                key,
                value
            )

        db.commit()
        db.refresh(factura)

        return factura

    @staticmethod
    def delete(
        db: Session,
        factura: Factura
    ):

        db.delete(factura)
        db.commit()
        
    @staticmethod
    def get_last_by_tipo_documento(
        db: Session,
        tipo_documento: str
    ):

        return (
            db.query(Factura)
            .filter(
                Factura.tipo_documento == tipo_documento
            )
            .order_by(
                Factura.id.desc()
            )
            .first()
        )
        
    @staticmethod
    def buscar(
        db: Session,
        texto: str
    ):

        return (
            db.query(Factura)
            .options(
                joinedload(Factura.cliente),
                joinedload(Factura.vehiculo),
                joinedload(Factura.orden)
            )
            .join(Cliente)
            .outerjoin(Vehiculo)
            .filter(
                or_(
                    Factura.numero.ilike(f"%{texto}%"),
                    Factura.estado.ilike(f"%{texto}%"),
                    Factura.tipo_documento.ilike(f"%{texto}%"),
                    Cliente.nombre.ilike(f"%{texto}%"),
                    Cliente.apellidos.ilike(f"%{texto}%"),
                    Vehiculo.matricula.ilike(f"%{texto}%")
                )
            )
            .order_by(
                Factura.fecha_emision.desc()
            )
            .all()
        )
        
    @staticmethod
    def filtrar(
        db: Session,
        filtros: FacturaFiltro
    ):

        query = (
        db.query(Factura)
            .options(
                joinedload(Factura.cliente),
                joinedload(Factura.vehiculo),
                joinedload(Factura.orden)
            )
        )

        query = FacturaRepository._aplicar_filtros(query, filtros)

        return (
            query
            .order_by(Factura.fecha_emision.desc())
            .all()
        )
        
    @staticmethod
    def get_paginated(
        db: Session,
        pagination: PaginationParams,
        filtros: FacturaFiltro | None = None,
    ):

        query = (
            db.query(Factura)
            .options(
                joinedload(Factura.cliente),
                joinedload(Factura.vehiculo),
                joinedload(Factura.orden)
            )
            .order_by(
                Factura.fecha_emision.desc()
            )
        )

        if filtros:
            query = FacturaRepository._aplicar_filtros(query, filtros)

        return BaseRepository.paginate(
            query,
            pagination
        )
    
"""Consultas de facturas, filtros comerciales y rangos de emisión."""
