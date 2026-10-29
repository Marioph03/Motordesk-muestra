"""Configuración única que distingue el modo de pruebas del modo VERI*FACTU."""

from sqlalchemy.orm import Session

from app.models.configuracion_facturacion import ConfiguracionFacturacion
from app.schemas.configuracion_facturacion import ConfiguracionFacturacionUpdate


class ConfiguracionFacturacionService:
    """Obtiene o inicializa las preferencias fiscales globales del taller."""

    @staticmethod
    def obtener(db: Session) -> ConfiguracionFacturacion:
        configuracion = db.query(ConfiguracionFacturacion).first()
        if configuracion is None:
            configuracion = ConfiguracionFacturacion(
                modo_facturacion="PRUEBAS",
                serie_pruebas="TP",
                serie_facturas="F",
                permitir_envio_aeat=False,
            )
            db.add(configuracion)
            db.commit()
            db.refresh(configuracion)
        return configuracion

    @staticmethod
    def actualizar(
        db: Session,
        datos: ConfiguracionFacturacionUpdate,
    ) -> ConfiguracionFacturacion:
        if datos.modo_facturacion == "VERIFACTU" and not datos.permitir_envio_aeat:
            raise ValueError(
                "Para activar VERI*FACTU debes habilitar expresamente el envío a la AEAT."
            )

        configuracion = ConfiguracionFacturacionService.obtener(db)
        configuracion.modo_facturacion = datos.modo_facturacion
        configuracion.serie_pruebas = datos.serie_pruebas
        configuracion.serie_facturas = datos.serie_facturas
        configuracion.permitir_envio_aeat = (
            datos.permitir_envio_aeat
            if datos.modo_facturacion == "VERIFACTU"
            else False
        )
        db.commit()
        db.refresh(configuracion)
        return configuracion
