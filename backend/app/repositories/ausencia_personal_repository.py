from datetime import datetime, time

from sqlalchemy.orm import Session, joinedload

from app.models.ausencia_personal import AusenciaPersonal


class AusenciaPersonalRepository:

    @staticmethod
    def get_hoy(
        db: Session,
    ) -> list[AusenciaPersonal]:
        """Ausencias que afectan al día natural actual.

        ``fecha_fin`` es exclusiva, por lo que el límite final también lo es.
        """
        ahora = datetime.now()
        inicio_hoy = datetime.combine(ahora.date(), time.min)
        fin_hoy = datetime.combine(ahora.date(), time.max)
        return (
            db.query(AusenciaPersonal)
            .filter(
                AusenciaPersonal.fecha_inicio <= fin_hoy,
                AusenciaPersonal.fecha_fin > inicio_hoy,
            )
            .order_by(AusenciaPersonal.fecha_inicio.asc())
            .all()
        )

    @staticmethod
    def get_usuario_en_rango(
        db: Session,
        usuario_id: int,
        fecha_inicio,
        fecha_fin,
    ) -> list[AusenciaPersonal]:
        return (
            db.query(AusenciaPersonal)
            .filter(
                AusenciaPersonal.usuario_id == usuario_id,
                AusenciaPersonal.fecha_inicio < fecha_fin,
                AusenciaPersonal.fecha_fin > fecha_inicio,
            )
            .order_by(AusenciaPersonal.fecha_inicio.asc())
            .all()
        )

    @staticmethod
    def get_all(
        db: Session,
        usuario_id: int | None = None,
    ) -> list[AusenciaPersonal]:
        consulta = (
            db.query(AusenciaPersonal)
            .options(joinedload(AusenciaPersonal.usuario))
        )

        if usuario_id is not None:
            consulta = consulta.filter(
                AusenciaPersonal.usuario_id == usuario_id
            )

        return consulta.order_by(
            AusenciaPersonal.fecha_inicio.desc()
        ).all()
    
    @staticmethod
    def get_by_id(
        db: Session,
        ausencia_id: int,
    ) -> AusenciaPersonal | None:
        return (
            db.query(AusenciaPersonal)
            .filter(AusenciaPersonal.id == ausencia_id)
            .first()
        )

    @staticmethod
    def get_by_usuario(
        db: Session,
        usuario_id: int
    ):
        return (
            db.query(AusenciaPersonal)
            .filter(
                AusenciaPersonal.usuario_id
                == usuario_id
            )
            .order_by(
                AusenciaPersonal.fecha_inicio.desc()
            )
            .all()
        )
        
    @staticmethod
    def get_en_rango(
        db: Session,
        fecha_inicio,
        fecha_fin
    ):

        return (
            db.query(AusenciaPersonal)
            .options(
                joinedload(
                    AusenciaPersonal.usuario
                )
            )
            .filter(
                AusenciaPersonal.fecha_inicio
                < fecha_fin,

                AusenciaPersonal.fecha_fin
                > fecha_inicio
            )
            .order_by(
                AusenciaPersonal.fecha_inicio.asc()
            )
            .all()
        )

    @staticmethod
    def get_solapadas(
        db: Session,
        usuario_id: int,
        fecha_inicio: datetime,
        fecha_fin: datetime,
        excluir_ausencia_id: int | None = None,
    ) -> list[AusenciaPersonal]:
        consulta = db.query(AusenciaPersonal).filter(
            AusenciaPersonal.usuario_id == usuario_id,
            AusenciaPersonal.fecha_inicio < fecha_fin,
            AusenciaPersonal.fecha_fin > fecha_inicio,
        )

        if excluir_ausencia_id is not None:
            consulta = consulta.filter(
                AusenciaPersonal.id != excluir_ausencia_id
            )

        return consulta.all()

    @staticmethod
    def get_by_rango(
        db: Session,
        fecha_inicio: datetime,
        fecha_fin: datetime,
        usuario_id: int | None = None,
    ) -> list[AusenciaPersonal]:
        consulta = db.query(AusenciaPersonal).filter(
            AusenciaPersonal.fecha_inicio < fecha_fin,
            AusenciaPersonal.fecha_fin > fecha_inicio,
        )

        if usuario_id is not None:
            consulta = consulta.filter(
                AusenciaPersonal.usuario_id == usuario_id
            )

        return consulta.order_by(
            AusenciaPersonal.fecha_inicio.asc()
        ).all()

    @staticmethod
    def create(
        db: Session,
        datos: dict,
    ) -> AusenciaPersonal:
        ausencia = AusenciaPersonal(**datos)
        db.add(ausencia)
        db.commit()
        db.refresh(ausencia)
        return ausencia

    @staticmethod
    def update(
        db: Session,
        ausencia: AusenciaPersonal,
        datos: dict,
    ) -> AusenciaPersonal:
        for campo, valor in datos.items():
            setattr(ausencia, campo, valor)

        db.commit()
        db.refresh(ausencia)
        return ausencia

    @staticmethod
    def delete(
        db: Session,
        ausencia: AusenciaPersonal,
    ) -> None:
        db.delete(ausencia)
        db.commit()
        
"""Consultas de ausencias y detección de intervalos solapados del personal."""
