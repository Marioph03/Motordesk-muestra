from sqlalchemy import or_
from sqlalchemy.orm import Session, joinedload

from app.models.orden_reparacion import EstadoReparacion, OrdenReparacion
from app.models.vehiculo import Vehiculo
from app.models.cliente import Cliente

from app.repositories.base_repository import BaseRepository
from app.schemas.pagination import PaginationParams


class OrdenReparacionRepository:

    @staticmethod
    def get_garantias_pendientes(
        db: Session,
    ) -> list[OrdenReparacion]:
        return (
            db.query(OrdenReparacion)
            .filter(
                OrdenReparacion.tipo == "GA",
                OrdenReparacion.estado.notin_([
                    EstadoReparacion.GARANTIA_RECHAZADA.value,
                    EstadoReparacion.GARANTIA_RESUELTA.value,
                ]),
            )
            .order_by(OrdenReparacion.fecha_entrada.asc())
            .all()
        )

    @staticmethod
    def get_presupuestos_pendientes(
        db: Session,
    ) -> list[OrdenReparacion]:
        """Presupuestos ya enviados que todavía esperan respuesta del cliente."""
        return (
            db.query(OrdenReparacion)
            .filter(
                OrdenReparacion.tipo == "PR",
                OrdenReparacion.estado == EstadoReparacion.ENVIADO.value,
            )
            .order_by(OrdenReparacion.fecha_envio_presupuesto.asc())
            .all()
        )

    @staticmethod
    def count_por_usuario_en_rango(
        db: Session,
        usuario_id: int,
        fecha_inicio,
        fecha_fin,
    ) -> int:
        from app.models.usuario import Usuario

        return (
            db.query(OrdenReparacion)
            .join(OrdenReparacion.usuarios_asignados)
            .filter(
                Usuario.id == usuario_id,
                OrdenReparacion.fecha_entrada >= fecha_inicio,
                OrdenReparacion.fecha_entrada < fecha_fin,
            )
            .count()
        )

    @staticmethod
    def get_garantias_en_rango(
        db: Session,
        fecha_inicio,
        fecha_fin,
    ):
        """Garantías abiertas en el periodo, según su entrada al taller."""
        return (
            db.query(OrdenReparacion)
            .filter(
                OrdenReparacion.tipo == "GA",
                OrdenReparacion.fecha_entrada >= fecha_inicio,
                OrdenReparacion.fecha_entrada < fecha_fin,
            )
            .order_by(OrdenReparacion.fecha_entrada.desc())
            .all()
        )

    @staticmethod
    def get_en_rango(
        db: Session,
        fecha_inicio,
        fecha_fin,
    ):
        """Obtiene documentos por la fecha de entrada al taller."""
        return (
            db.query(OrdenReparacion)
            .filter(
                OrdenReparacion.fecha_entrada >= fecha_inicio,
                OrdenReparacion.fecha_entrada < fecha_fin,
            )
            .order_by(OrdenReparacion.fecha_entrada.desc())
            .all()
        )

    @staticmethod
    def get_all(db: Session):
        return (
            db.query(OrdenReparacion)
            .options(
                joinedload(OrdenReparacion.vehiculo)
                .joinedload(Vehiculo.cliente),
                joinedload(OrdenReparacion.usuarios_asignados),
            )
            .all()
        )

    @staticmethod
    def get_by_id(db: Session, orden_id: int):
        return (
            db.query(OrdenReparacion)
            .options(
                joinedload(OrdenReparacion.vehiculo)
                .joinedload(Vehiculo.cliente),
                joinedload(OrdenReparacion.usuarios_asignados),
            )
            .filter(
                OrdenReparacion.id == orden_id
            )
            .first()
        )

    @staticmethod
    def create(
        db: Session,
        numero: str,
        datos: dict,
        commit: bool = True,
    ):
        nueva = OrdenReparacion(
            numero=numero,
            tipo=datos["tipo"],
            estado=datos["estado"],
            vehiculo_id=datos["vehiculo_id"],
            kilometros_entrada=datos.get("kilometros_entrada"),
            descripcion_averia=datos["descripcion_averia"],
            diagnostico=datos.get("diagnostico"),
            observaciones=datos.get("observaciones"),
            observaciones_internas=datos.get("observaciones_internas"),
            garantia=datos["garantia"],
            garantia_meses=datos["garantia_meses"],
            vehicle_damage=datos.get("vehicle_damage"),
            cita_origen_id=datos.get("cita_origen_id"),
            presupuesto_origen_id=datos.get("presupuesto_origen_id"),
            orden_origen_garantia_id=datos.get("orden_origen_garantia_id"),
            factura_origen_garantia_id=datos.get("factura_origen_garantia_id"),
        )

        db.add(nueva)
        if commit:
            db.commit()
            db.refresh(nueva)
        else:
            db.flush()

        return nueva

    @staticmethod
    def update(
        db: Session,
        orden_db: OrdenReparacion,
        datos: dict,
        commit: bool = True,
    ):

        for key, value in datos.items():
            setattr(
                orden_db,
                key,
                value
            )

        if commit:
            db.commit()
            db.refresh(orden_db)
        else:
            db.flush()

        return orden_db

    @staticmethod
    def get_last_by_tipo(
        db: Session,
        tipo: str
    ):
        return (
            db.query(OrdenReparacion)
            .filter(
                OrdenReparacion.tipo == tipo
            )
            .order_by(
                OrdenReparacion.id.desc()
            )
            .first()
        )

    @staticmethod
    def buscar(
        db: Session,
        texto: str
    ):
        return (
            db.query(OrdenReparacion)
            .options(
                joinedload(OrdenReparacion.vehiculo)
                .joinedload(Vehiculo.cliente)
            )
            .join(
                OrdenReparacion.vehiculo
            )
            .join(
                Vehiculo.cliente
            )
            .filter(
                or_(
                    OrdenReparacion.estado.ilike(
                        f"%{texto}%"
                    ),
                    Vehiculo.matricula.ilike(
                        f"%{texto}%"
                    ),
                    Vehiculo.marca.ilike(
                        f"%{texto}%"
                    ),
                    Vehiculo.modelo.ilike(
                        f"%{texto}%"
                    ),
                    Cliente.nombre.ilike(
                        f"%{texto}%"
                    ),
                    Cliente.apellidos.ilike(
                        f"%{texto}%"
                    )
                )
            )
            .all()
        )

    @staticmethod
    def get_paginated(
        db: Session,
        pagination: PaginationParams,
        tipo: str | None = None,
        estado: str | None = None,
    ):
        query = (
            db.query(OrdenReparacion)
            .options(
                joinedload(OrdenReparacion.vehiculo)
                .joinedload(Vehiculo.cliente)
            )
            .order_by(
                OrdenReparacion.fecha_entrada.desc()
            )
        )

        if tipo is not None:
            query = query.filter(OrdenReparacion.tipo == tipo)

        if estado is not None:
            query = query.filter(OrdenReparacion.estado == estado)

        return BaseRepository.paginate(
            query,
            pagination
        )

    @staticmethod
    def delete(
        db: Session,
        orden_db: OrdenReparacion
    ):
        db.delete(orden_db)
        db.commit()
"""Consultas de órdenes, presupuestos, garantías y asignaciones de taller."""
