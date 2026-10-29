"""Traduce respuestas XML de AEAT a estados y mensajes de MotorDesk."""

from lxml import etree


class VerifactuResponseService:
    """Extrae información tolerante a namespaces de las respuestas SOAP."""


    @staticmethod
    def _texto(
        elemento,
        nombre_local: str
    ):

        encontrado = elemento.xpath(
            f".//*[local-name()='{nombre_local}']"
        )

        if not encontrado:
            return None

        return encontrado[0].text


    @staticmethod
    def procesar(
        xml_respuesta: str
    ) -> dict:

        try:

            root = etree.fromstring(
                xml_respuesta.encode("utf-8")
            )

        except etree.XMLSyntaxError as e:

            raise ValueError(
                f"Respuesta XML de AEAT no válida: {e}"
            )

        # -------------------------------------------------
        # SOAP FAULT
        # -------------------------------------------------

        faults = root.xpath(
            ".//*[local-name()='Fault']"
        )

        if faults:

            fault = faults[0]

            faultcode = (
                VerifactuResponseService._texto(
                    fault,
                    "faultcode"
                )
            )

            faultstring = (
                VerifactuResponseService._texto(
                    fault,
                    "faultstring"
                )
            )

            return {
                "ok": False,
                "estado": "ERROR",
                "estado_envio": None,
                "codigo_error": faultcode,
                "descripcion_error": faultstring,
                "csv": None
            }

        # -------------------------------------------------
        # ESTADO GLOBAL DEL ENVÍO
        # -------------------------------------------------

        estado_envio = (
            VerifactuResponseService._texto(
                root,
                "EstadoEnvio"
            )
        )

        # -------------------------------------------------
        # RESPUESTA DEL REGISTRO
        # -------------------------------------------------

        respuestas_linea = root.xpath(
            ".//*[local-name()='RespuestaLinea']"
        )

        if not respuestas_linea:

            raise ValueError(
                "La respuesta de AEAT no contiene "
                "RespuestaLinea"
            )

        linea = respuestas_linea[0]

        estado_registro = (
            VerifactuResponseService._texto(
                linea,
                "EstadoRegistro"
            )
        )

        codigo_error = (
            VerifactuResponseService._texto(
                linea,
                "CodigoErrorRegistro"
            )
        )

        descripcion_error = (
            VerifactuResponseService._texto(
                linea,
                "DescripcionErrorRegistro"
            )
        )

        csv = (
            VerifactuResponseService._texto(
                linea,
                "CSV"
            )
        )

        # -------------------------------------------------
        # TRADUCIR ESTADO AEAT -> ESTADO MOTORDesk
        # -------------------------------------------------

        if estado_registro == "Correcto":

            estado = "ACEPTADO"
            ok = True

        elif estado_registro == "AceptadoConErrores":

            estado = "ACEPTADO_CON_ERRORES"
            ok = True

        elif estado_registro == "Incorrecto":

            estado = "RECHAZADO"
            ok = False

        else:

            estado = "ERROR"
            ok = False

        return {
            "ok": ok,
            "estado": estado,
            "estado_envio": estado_envio,
            "estado_registro": estado_registro,
            "codigo_error": codigo_error,
            "descripcion_error": descripcion_error,
            "csv": csv
        }
