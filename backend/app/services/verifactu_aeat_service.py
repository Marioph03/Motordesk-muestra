from datetime import datetime, timezone
from pathlib import Path

import requests
from requests_pkcs12 import post

from sqlalchemy.orm import Session

from app.models.registro_verifactu import (
    EstadoRegistroVerifactu,
    TipoRegistroVerifactu,
)
from app.models.factura import EstadoFactura
from app.models.orden_reparacion import EstadoReparacion
from app.repositories.registro_verifactu_repository import (
    RegistroVerifactuRepository
)
from app.services.verifactu_soap_service import (
    VerifactuSoapService
)
from app.services.verifactu_response_service import (
    VerifactuResponseService
)
from app.config.verifactu_config import (
    VerifactuConfig
)
from app.services.certificado_electronico_service import (
    CertificadoElectronicoService
)
from app.services.configuracion_facturacion_service import ConfiguracionFacturacionService


class VerifactuAeatService:
    @staticmethod
    def validar_configuracion_produccion(
        db: Session,
        empresa_id: int,
    ) -> None:
        """Verifica toda la configuración necesaria antes de emitir una factura real."""
        configuracion = ConfiguracionFacturacionService.obtener(db)
        if configuracion.modo_facturacion != "VERIFACTU" or not configuracion.permitir_envio_aeat:
            raise ValueError("El envío a AEAT no está habilitado en la configuración de facturación")
        if VerifactuConfig.ENVIRONMENT.upper() not in {"PROD", "PRODUCTION"}:
            raise ValueError("VERIFACTU_ENV debe ser PROD para enviar a la AEAT real")
        if not VerifactuConfig.NIF_PRODUCTOR:
            raise ValueError("Configura VERIFACTU_PRODUCTOR_NIF antes de la emisión real")
        VerifactuAeatService._obtener_certificado_taller(
            db,
            empresa_id,
        )

    @staticmethod
    def enviar_registro_produccion(
        db: Session,
        registro_id: int,
        empresa_id: int,
    ):
        """Envía solo registros reales tras las dos barreras de activación."""
        VerifactuAeatService.validar_configuracion_produccion(
            db,
            empresa_id,
        )
        registro = RegistroVerifactuRepository.get_by_id(db, registro_id)
        if registro is None or registro.factura is None:
            raise ValueError("Registro VERI*FACTU no encontrado")
        if registro.factura.es_prueba:
            raise ValueError("No se puede enviar una factura de prueba a la AEAT")
        cert_path, cert_password = (
            VerifactuAeatService
            ._obtener_certificado_taller(
                db,
                empresa_id,
            )
        )

        return VerifactuAeatService.enviar_registro(
            db=db,
            registro_id=registro_id,
            cert_path=cert_path,
            cert_password=cert_password,
            endpoint=VerifactuConfig.PROD_ENDPOINT,
        )

    @staticmethod
    def enviar_registro(
        db: Session,
        registro_id: int,
        cert_path: str,
        cert_password: str,
        endpoint: str
    ):

        registro = (
            RegistroVerifactuRepository.get_by_id(
                db,
                registro_id
            )
        )

        if registro is None:
            raise ValueError(
                "Registro VERI*FACTU no encontrado"
            )

        if registro.estado in (
            EstadoRegistroVerifactu.ACEPTADO.value,
            EstadoRegistroVerifactu.ACEPTADO_CON_ERRORES.value,
        ):
            raise ValueError(
                "El registro ya fue aceptado por AEAT"
            )

        cert_file = Path(cert_path)

        if not cert_file.exists():
            raise ValueError(
                "No se encuentra el certificado configurado"
            )

        ahora = datetime.now(
            timezone.utc
        )

        registro.intentos_envio += 1
        registro.fecha_ultimo_intento = ahora
        registro.estado = (
            EstadoRegistroVerifactu
            .ENVIANDO.value
        )

        db.commit()
        db.refresh(registro)

        try:

            headers = {
                "Content-Type":
                "text/xml; charset=utf-8",

                "SOAPAction": ""
            }
            
            soap_xml = (
                VerifactuSoapService.envolver(
                registro.xml_registro
                )
        )

            response = post(
                endpoint,
                data=soap_xml.encode(
                    "utf-8"
                ),
                headers=headers,
                pkcs12_filename=str(cert_file),
                pkcs12_password=cert_password,
                timeout=30
            )

            registro.respuesta_aeat = (
                response.text
            )

            if response.status_code != 200:

                registro.estado = (
                    EstadoRegistroVerifactu
                    .ERROR.value
                )

                registro.codigo_respuesta = str(
                    response.status_code
                )

                registro.mensaje_error = (
                    response.text
                )

                db.commit()
                db.refresh(registro)

                raise ValueError(
                    "AEAT respondió con HTTP "
                    f"{response.status_code}"
                )

            resultado = VerifactuResponseService.procesar(
                response.text
            )

            registro.estado = resultado["estado"]
            registro.codigo_respuesta = resultado["codigo_error"]
            registro.mensaje_error = resultado["descripcion_error"]

            if resultado["estado"] in (
                EstadoRegistroVerifactu.ACEPTADO.value,
                EstadoRegistroVerifactu.ACEPTADO_CON_ERRORES.value,
            ):
                registro.fecha_aceptacion = datetime.now(timezone.utc)
                if registro.tipo_registro == TipoRegistroVerifactu.ANULACION.value:
                    registro.factura.estado = EstadoFactura.ANULADA.value
                    orden = registro.factura.orden
                    if (
                        orden is not None
                        and orden.tipo != "GA"
                        and orden.estado == EstadoReparacion.FACTURADA.value
                    ):
                        orden.estado = EstadoReparacion.CERRADA.value

            db.commit()
            db.refresh(registro)

            return {
                "status_code": response.status_code,
                "estado": resultado["estado"],
                "estado_envio": resultado.get("estado_envio"),
                "estado_registro": resultado.get("estado_registro"),
                "codigo_error": resultado.get("codigo_error"),
                "descripcion_error": resultado.get("descripcion_error"),
                "csv": resultado.get("csv"),
            }

        except requests.RequestException as e:

            registro.estado = (
                EstadoRegistroVerifactu
                .ERROR.value
            )

            registro.mensaje_error = str(e)

            db.commit()
            db.refresh(registro)

            raise ValueError(
                f"Error conectando con AEAT: {e}"
            )


    @staticmethod
    def enviar_registro_test(
        db: Session,
        registro_id: int,
        empresa_id: int,
    ):

        if (
            VerifactuConfig
            .ENVIRONMENT
            .upper()
            != "TEST"
        ):
            raise ValueError(
                "El entorno VERI*FACTU no está "
                "configurado como TEST"
            )

        cert_path, cert_password = (
            VerifactuAeatService
            ._obtener_certificado_taller(
                db,
                empresa_id,
            )
        )

        return (
            VerifactuAeatService
            .enviar_registro(
                db=db,
                registro_id=registro_id,
                cert_path=cert_path,
                cert_password=cert_password,
                endpoint=(
                    VerifactuConfig
                    .TEST_ENDPOINT
                ),
            )
        )

    @staticmethod
    def _obtener_certificado_taller(
        db: Session,
        empresa_id: int,
    ) -> tuple[str, str]:
        return (
            CertificadoElectronicoService
            .obtener_credenciales_envio(
                db,
                empresa_id,
            )
        )
