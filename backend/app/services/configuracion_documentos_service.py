"""Valores visibles y textos predeterminados compartidos por los documentos."""

from sqlalchemy.orm import Session

from app.models.configuracion_documentos import (
    ConfiguracionDocumentos
)

from app.schemas.configuracion_documentos import (
    ConfiguracionDocumentosUpdate
)


class ConfiguracionDocumentosService:
    """Evita que cada PDF mantenga datos comerciales hardcodeados."""

    @staticmethod
    def obtener(
        db: Session
    ) -> ConfiguracionDocumentos:

        configuracion = (
            db.query(
                ConfiguracionDocumentos
            )
            .first()
        )

        if configuracion is None:

            configuracion = (
                ConfiguracionDocumentos()
            )

            db.add(
                configuracion
            )

            db.commit()

            db.refresh(
                configuracion
            )

        return configuracion


    @staticmethod
    def actualizar(
        db: Session,
        datos: ConfiguracionDocumentosUpdate
    ) -> ConfiguracionDocumentos:

        configuracion = (
            ConfiguracionDocumentosService
            .obtener(db)
        )

        valores = datos.model_dump(
            exclude_unset=True
        )

        for campo, valor in valores.items():

            setattr(
                configuracion,
                campo,
                valor
            )

        db.commit()

        db.refresh(
            configuracion
        )

        return configuracion
