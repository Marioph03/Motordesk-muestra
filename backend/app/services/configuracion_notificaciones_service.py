from sqlalchemy.orm import Session

from app.models.configuracion_notificaciones import (
    ConfiguracionNotificaciones
)

from app.schemas.configuracion_notificaciones import (
    ConfiguracionNotificacionesUpdate
)


class ConfiguracionNotificacionesService:

    @staticmethod
    def obtener(
        db: Session
    ) -> ConfiguracionNotificaciones:

        config = (
            db.query(
                ConfiguracionNotificaciones
            )
            .first()
        )

        if config is None:

            config = (
                ConfiguracionNotificaciones()
            )

            db.add(config)
            db.commit()
            db.refresh(config)

        return config


    @staticmethod
    def actualizar(
        db: Session,
        datos: ConfiguracionNotificacionesUpdate
    ) -> ConfiguracionNotificaciones:

        config = (
            ConfiguracionNotificacionesService
            .obtener(db)
        )

        valores = datos.model_dump(
            exclude_unset=True
        )

        for campo, valor in valores.items():

            setattr(
                config,
                campo,
                valor
            )

        db.commit()
        db.refresh(config)

        return config
"""Obtención e inicialización de preferencias de alertas del taller."""
