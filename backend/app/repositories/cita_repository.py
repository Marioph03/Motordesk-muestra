from datetime import datetime, timedelta

from sqlalchemy.orm import Session, joinedload

from app.models.cita import Cita, EstadoCita
from app.models.usuario import Usuario
from app.models.vehiculo import Vehiculo


class CitaRepository:

    @staticmethod
    def get_proximas(
        db: Session,
        horas: int = 24,
    ) -> list[Cita]:
        """Citas activas cuya hora de inicio cae en las próximas ``horas``."""
        ahora = datetime.now()
        limite = ahora + timedelta(hours=horas)
        return (
            db.query(Cita)
            .filter(
                Cita.fecha_inicio >= ahora,
                Cita.fecha_inicio < limite,
                Cita.estado.notin_([
                    EstadoCita.CANCELADA.value,
                    EstadoCita.NO_PRESENTADO.value,
                    EstadoCita.COMPLETADA.value,
                ]),
            )
            .order_by(Cita.fecha_inicio.asc())
            .all()
        )

    @staticmethod
    def count_por_usuario_en_rango(
        db: Session,
        usuario_id: int,
        fecha_inicio,
        fecha_fin,
    ) -> int:
        return (
            db.query(Cita)
            .join(Cita.usuarios_asignados)
            .filter(
                Usuario.id == usuario_id,
                Cita.fecha_inicio >= fecha_inicio,
                Cita.fecha_inicio < fecha_fin,
                Cita.estado.notin_([
                    EstadoCita.CANCELADA.value,
                    EstadoCita.NO_PRESENTADO.value,
                ]),
            )
            .count()
        )

    @staticmethod
    def get_all(
        db: Session
    ):
        return (
            db.query(Cita)
            .options(
                joinedload(Cita.cliente),
                joinedload(Cita.vehiculo),
                joinedload(Cita.usuarios_asignados)
            )
            .order_by(
                Cita.fecha_inicio.asc()
            )
            .all()
        )

    @staticmethod
    def get_by_id(
        db: Session,
        cita_id: int
    ):
        return (
            db.query(Cita)
            .options(
                joinedload(Cita.cliente),
                joinedload(Cita.vehiculo),
                joinedload(Cita.orden_generada),
                joinedload(Cita.usuarios_asignados)
            )
            .filter(
                Cita.id == cita_id
            )
            .first()
        )

    @staticmethod
    def get_by_rango(
        db: Session,
        fecha_inicio,
        fecha_fin
    ):
        return (
            db.query(Cita)
            .options(
                joinedload(Cita.cliente),
                joinedload(Cita.vehiculo),
                joinedload(Cita.usuarios_asignados)
            )
            .filter(
                Cita.fecha_inicio < fecha_fin,
                Cita.fecha_fin > fecha_inicio
            )
            .order_by(
                Cita.fecha_inicio.asc()
            )
            .all()
        )

    @staticmethod
    def get_solapadas(
        db: Session,
        fecha_inicio,
        fecha_fin,
        excluir_cita_id: int | None = None
    ):

        query = (
            db.query(Cita)
            .filter(
                Cita.fecha_inicio < fecha_fin,
                Cita.fecha_fin > fecha_inicio,
                Cita.estado.notin_([
                    "Cancelada",
                    "No presentado"
                ])
            )
        )

        if excluir_cita_id is not None:
            query = query.filter(
                Cita.id != excluir_cita_id
            )

        return query.all()

    @staticmethod
    def get_solapadas_usuario(
        db: Session,
        usuario_id: int,
        fecha_inicio,
        fecha_fin,
        excluir_cita_id: int | None = None,
    ):
        """Citas activas que coinciden con el intervalo de un profesional."""

        query = (
            db.query(Cita)
            .join(Cita.usuarios_asignados)
            .filter(
                Usuario.id == usuario_id,
                Cita.fecha_inicio < fecha_fin,
                Cita.fecha_fin > fecha_inicio,
                Cita.estado.notin_([
                    EstadoCita.CANCELADA.value,
                    EstadoCita.NO_PRESENTADO.value,
                    EstadoCita.COMPLETADA.value,
                ]),
            )
        )

        if excluir_cita_id is not None:
            query = query.filter(Cita.id != excluir_cita_id)

        return query.all()

    @staticmethod
    def create(
        db: Session,
        datos: dict,
        commit: bool = True,
    ):

        cita = Cita(
            **datos
        )

        db.add(cita)

        if commit:
            db.commit()
            db.refresh(cita)
        else:
            db.flush()

        return cita

    @staticmethod
    def update(
        db: Session,
        cita: Cita,
        datos: dict,
        usuarios_asignados: list | None = None,
        commit: bool = True,
    ):

        for key, value in datos.items():
            setattr(
                cita,
                key,
                value
            )

        if usuarios_asignados is not None:
            cita.usuarios_asignados = usuarios_asignados

        if commit:
            db.commit()
            db.refresh(cita)
        else:
            db.flush()

        return cita

    @staticmethod
    def delete(
        db: Session,
        cita: Cita
    ):

        db.delete(cita)
        db.commit()
"""Consultas de agenda, asignaciones y conflictos temporales de citas."""
