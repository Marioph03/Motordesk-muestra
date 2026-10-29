"""Configuración de horario y cierres usada al validar todas las citas."""

from sqlalchemy.orm import Session

from app.models.configuracion_agenda import (
    ConfiguracionAgenda
)

from app.models.cierre_agenda import (
    CierreAgenda
)

from app.schemas.configuracion_agenda import (
    ConfiguracionAgendaUpdate,
    CierreAgendaCreate
)

from datetime import datetime

class ConfiguracionAgendaService:

    @staticmethod
    def obtener(
        db: Session
    ):

        config = (
            db.query(
                ConfiguracionAgenda
            )
            .first()
        )

        if config is None:

            config = (
                ConfiguracionAgenda()
            )

            db.add(config)
            db.commit()
            db.refresh(config)

        return config


    @staticmethod
    def actualizar(
        db: Session,
        datos: ConfiguracionAgendaUpdate
    ):

        config = (
            ConfiguracionAgendaService
            .obtener(db)
        )

        valores = datos.model_dump()

        for campo, valor in valores.items():

            setattr(
                config,
                campo,
                valor
            )

        db.commit()
        db.refresh(config)

        return config


    @staticmethod
    def listar_cierres(
        db: Session
    ):

        return (
            db.query(CierreAgenda)
            .order_by(
                CierreAgenda.fecha.asc()
            )
            .all()
        )


    @staticmethod
    def crear_cierre(
        db: Session,
        datos: CierreAgendaCreate
    ):

        cierre = CierreAgenda(
            **datos.model_dump()
        )

        db.add(cierre)
        db.commit()
        db.refresh(cierre)

        return cierre


    @staticmethod
    def eliminar_cierre(
        db: Session,
        cierre_id: int
    ):

        cierre = (
            db.query(CierreAgenda)
            .filter(
                CierreAgenda.id
                == cierre_id
            )
            .first()
        )

        if cierre is None:
            raise ValueError(
                "Cierre no encontrado"
            )

        db.delete(cierre)
        db.commit()
        
    @staticmethod
    def validar_fecha_cita(
        db: Session,
        fecha_inicio: datetime,
        fecha_fin: datetime
    ):

        """Aplica horario semanal y cierres extraordinarios a cualquier cita."""

        if fecha_fin <= fecha_inicio:
            raise ValueError(
                "La fecha final debe ser posterior a la inicial"
            )

        config = (
            ConfiguracionAgendaService
            .obtener(db)
        )

        dias = {
            0: (
                config.lunes_activo,
                config.lunes_inicio,
                config.lunes_fin
            ),
            1: (
                config.martes_activo,
                config.martes_inicio,
                config.martes_fin
            ),
            2: (
                config.miercoles_activo,
                config.miercoles_inicio,
                config.miercoles_fin
            ),
            3: (
                config.jueves_activo,
                config.jueves_inicio,
                config.jueves_fin
            ),
            4: (
                config.viernes_activo,
                config.viernes_inicio,
                config.viernes_fin
            ),
            5: (
                config.sabado_activo,
                config.sabado_inicio,
                config.sabado_fin
            ),
            6: (
                config.domingo_activo,
                config.domingo_inicio,
                config.domingo_fin
            )
        }

        activo, hora_inicio, hora_fin = (
            dias[fecha_inicio.weekday()]
        )

        if not activo:
            raise ValueError(
                "El taller está cerrado ese día"
            )

        cierre = (
            db.query(CierreAgenda)
            .filter(
                CierreAgenda.fecha
                == fecha_inicio.date()
            )
            .first()
        )

        if cierre:
            raise ValueError(
                f"El taller está cerrado ese día: "
                f"{cierre.motivo}"
            )

        apertura = datetime.combine(
            fecha_inicio.date(),
            datetime.strptime(
                hora_inicio,
                "%H:%M"
            ).time()
        )

        cierre_horario = datetime.combine(
            fecha_inicio.date(),
            datetime.strptime(
                hora_fin,
                "%H:%M"
            ).time()
        )

        if fecha_inicio < apertura:
            raise ValueError(
                f"La cita no puede comenzar antes "
                f"de las {hora_inicio}"
            )

        if fecha_fin > cierre_horario:
            raise ValueError(
                f"La cita no puede finalizar después "
                f"de las {hora_fin}"
            )
