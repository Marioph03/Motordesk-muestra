import re
from io import BytesIO

import requests

from app.core.config import settings


class WhatsAppService:

    API_VERSION = "v23.0"

    TEMPLATE_NAME = "orden_reparacion"
    TEMPLATE_FACTURA_NAME = settings.WHATSAPP_FACTURA_TEMPLATE_NAME
    TEMPLATE_PRESUPUESTO_NAME = settings.WHATSAPP_PRESUPUESTO_TEMPLATE_NAME
    TEMPLATE_GARANTIA_NAME = settings.WHATSAPP_GARANTIA_TEMPLATE_NAME
    TEMPLATE_LANGUAGE = "es"


    # =========================================================
    # NORMALIZAR TELÉFONO
    # =========================================================

    @staticmethod
    def normalizar_telefono(
        telefono: str
    ) -> str:

        if not telefono:
            raise ValueError(
                "El cliente no tiene un teléfono registrado"
            )

        telefono = re.sub(
            r"\D",
            "",
            telefono
        )

        # 0034XXXXXXXXX -> 34XXXXXXXXX
        if telefono.startswith("00"):
            telefono = telefono[2:]

        # Número español sin prefijo
        if len(telefono) == 9:
            telefono = f"34{telefono}"

        return telefono


    # =========================================================
    # VALIDAR CREDENCIALES DE WHATSAPP
    # =========================================================

    @staticmethod
    def validar_credenciales(
        access_token: str,
        phone_number_id: str
    ) -> None:

        if not access_token:

            raise ValueError(
                "La empresa no tiene un access token "
                "de WhatsApp configurado"
            )

        if not phone_number_id:

            raise ValueError(
                "La empresa no tiene un Phone Number ID "
                "de WhatsApp configurado"
            )

    @staticmethod
    def obtener_numero_whatsapp(
        access_token: str,
        waba_id: str,
        phone_number_id: str,
    ) -> str | None:
        """Valida que el número pertenece al WABA conectado y devuelve su visible.

        Los IDs recibidos por Embedded Signup no se guardan ciegamente: Meta
        debe confirmar que el Phone Number ID forma parte de la cuenta de
        WhatsApp Business seleccionada por el taller.
        """
        WhatsAppService.validar_credenciales(access_token, phone_number_id)

        try:
            response = requests.get(
                f"https://graph.facebook.com/{WhatsAppService.API_VERSION}/"
                f"{waba_id}/phone_numbers",
                headers={"Authorization": f"Bearer {access_token}"},
                params={"fields": "id,display_phone_number", "limit": 100},
                timeout=30,
            )
        except requests.RequestException as exc:
            raise RuntimeError("No se pudo validar la cuenta de WhatsApp con Meta.") from exc

        if not response.ok:
            raise RuntimeError(
                "Meta no pudo validar la cuenta de WhatsApp seleccionada."
            )

        for numero in response.json().get("data", []):
            if str(numero.get("id")) == str(phone_number_id):
                return numero.get("display_phone_number")

        raise ValueError(
            "El Phone Number ID no pertenece a la cuenta de WhatsApp indicada."
        )


    # =========================================================
    # ENVIAR MENSAJE DE TEXTO
    # =========================================================

    @staticmethod
    def enviar_mensaje_texto(
        telefono: str,
        mensaje: str,
        access_token: str,
        phone_number_id: str
    ) -> dict:

        WhatsAppService.validar_credenciales(
            access_token=access_token,
            phone_number_id=phone_number_id
        )

        if not mensaje or not mensaje.strip():

            raise ValueError(
                "El mensaje de WhatsApp está vacío"
            )


        # =====================================================
        # NORMALIZAR TELÉFONO
        # =====================================================

        telefono = WhatsAppService.normalizar_telefono(
            telefono
        )


        # =====================================================
        # URL
        # =====================================================

        url = (
            "https://graph.facebook.com/"
            f"{WhatsAppService.API_VERSION}/"
            f"{phone_number_id}/messages"
        )


        # =====================================================
        # HEADERS
        # =====================================================

        headers = {
            "Authorization": f"Bearer {access_token}"
        }


        # =====================================================
        # PAYLOAD
        # =====================================================

        payload = {
            "messaging_product": "whatsapp",

            "recipient_type": "individual",

            "to": telefono,

            "type": "text",

            "text": {
                "preview_url": False,
                "body": mensaje
            }
        }


        # =====================================================
        # ENVIAR
        # =====================================================

        try:

            response = requests.post(
                url,
                headers=headers,
                json=payload,
                timeout=30
            )

        except requests.RequestException as e:

            raise RuntimeError(
                f"No se pudo conectar con WhatsApp: {e}"
            ) from e


        # =====================================================
        # VALIDAR RESPUESTA
        # =====================================================

        if not response.ok:

            try:

                detalle = response.json()

            except ValueError:

                detalle = response.text

            raise RuntimeError(
                f"WhatsApp devolvió HTTP "
                f"{response.status_code}: {detalle}"
            )


        return response.json()

    @staticmethod
    def enviar_presupuesto(
        telefono: str,
        nombre_cliente: str,
        numero_presupuesto: str,
        vehiculo: str,
        matricula: str,
        nombre_taller: str,
        importe_total: str,
        pdf_buffer: BytesIO,
        access_token: str,
        phone_number_id: str
    ) -> dict:
        """Envía el PDF con la plantilla aprobada para presupuestos."""

        if not WhatsAppService.TEMPLATE_PRESUPUESTO_NAME:
            raise ValueError(
                "WHATSAPP_PRESUPUESTO_TEMPLATE_NAME no está configurado"
            )

        return WhatsAppService.enviar_orden(
            telefono=telefono,
            nombre_cliente=nombre_cliente,
            numero_orden=numero_presupuesto,
            vehiculo=vehiculo,
            matricula=matricula,
            nombre_taller=nombre_taller,
            pdf_buffer=pdf_buffer,
            access_token=access_token,
            phone_number_id=phone_number_id,
            template_name=WhatsAppService.TEMPLATE_PRESUPUESTO_NAME,
            prefijo_archivo="presupuesto",
            parametro_numero="numero_presupuesto",
            importe_total=importe_total
        )

    @staticmethod
    def enviar_garantia(
        telefono: str,
        nombre_cliente: str,
        numero_garantia: str,
        vehiculo: str,
        matricula: str,
        nombre_taller: str,
        pdf_buffer: BytesIO,
        access_token: str,
        phone_number_id: str,
    ) -> dict:
        """Envía el PDF con la plantilla aprobada específica de garantías."""
        if not WhatsAppService.TEMPLATE_GARANTIA_NAME:
            raise ValueError(
                "WHATSAPP_GARANTIA_TEMPLATE_NAME no está configurado"
            )

        return WhatsAppService.enviar_orden(
            telefono=telefono,
            nombre_cliente=nombre_cliente,
            numero_orden=numero_garantia,
            vehiculo=vehiculo,
            matricula=matricula,
            nombre_taller=nombre_taller,
            pdf_buffer=pdf_buffer,
            access_token=access_token,
            phone_number_id=phone_number_id,
            template_name=WhatsAppService.TEMPLATE_GARANTIA_NAME,
            prefijo_archivo="garantia",
            parametro_numero="numero_garantia",
        )


    # =========================================================
    # SUBIR DOCUMENTO A WHATSAPP
    # =========================================================

    @staticmethod
    def subir_documento(
        pdf_bytes: bytes,
        nombre_archivo: str,
        access_token: str,
        phone_number_id: str
    ) -> str:
        WhatsAppService.validar_credenciales(
            access_token=access_token,
            phone_number_id=phone_number_id
        )
    # =====================================================
    # URL
    # =====================================================

        url = (
            f"https://graph.facebook.com/"
            f"{WhatsAppService.API_VERSION}/"
            f"{phone_number_id}/media"
        )

        headers = {
            "Authorization":
                f"Bearer {access_token}"
        }

        if isinstance(pdf_bytes, BytesIO):
            pdf_bytes.seek(0)
            pdf_bytes = pdf_bytes.read()

        files = {
            "file": (
                nombre_archivo,
                pdf_bytes,
                "application/pdf"
            )
        }

        data = {
            "messaging_product":
                "whatsapp"
        }

    # =====================================================
    # DEBUG PREVIO
    # =====================================================


    # =====================================================
    # COMPROBAR QUE EL TOKEN VE EL NÚMERO
    # =====================================================


    # =====================================================
    # SUBIR PDF
    # =====================================================

        response = requests.post(
            url,
            headers=headers,
            files=files,
            data=data,
            timeout=30
        )


    # =====================================================
    # ERROR
    # =====================================================

        if not response.ok:

            try:
                detalle = response.json()
            except Exception:
                detalle = response.text

            raise RuntimeError(
                f"WhatsApp devolvió HTTP "
                f"{response.status_code} "
                f"al subir el PDF: {detalle}"
            )

        resultado = response.json()

        media_id = resultado.get("id")

        if not media_id:

            raise RuntimeError(
                "Meta no devolvió el media_id."
            )

        return media_id


    # =========================================================
    # ENVIAR ORDEN
    # =========================================================

    @staticmethod
    def enviar_orden(
        telefono: str,
        nombre_cliente: str,
        numero_orden: str,
        vehiculo: str,
        matricula: str,
        nombre_taller: str,
        pdf_buffer: BytesIO,
        access_token: str,
        phone_number_id: str,
        template_name: str | None = None,
        prefijo_archivo: str = "orden",
        parametro_numero: str = "numero_orden",
        importe_total: str | None = None
    ) -> dict:

        WhatsAppService.validar_credenciales(
            access_token=access_token,
            phone_number_id=phone_number_id
        )

    # =====================================================
    # NORMALIZAR TELÉFONO
    # =====================================================

        telefono = WhatsAppService.normalizar_telefono(
            telefono
        )

    # =====================================================
    # GENERAR PDF EN BYTES
    # =====================================================

        pdf_buffer.seek(0)

        pdf_bytes = pdf_buffer.read()

        nombre_pdf = f"{prefijo_archivo}_{numero_orden}.pdf"

    # =====================================================
    # SUBIR DOCUMENTO
    # =====================================================

        media_id = WhatsAppService.subir_documento(
            pdf_bytes=pdf_bytes,
            nombre_archivo=nombre_pdf,
            access_token=access_token,
            phone_number_id=phone_number_id
        )

    # =====================================================
    # URL
    # =====================================================

        url = (
            f"https://graph.facebook.com/"
            f"{WhatsAppService.API_VERSION}/"
            f"{phone_number_id}/messages"
        )

    # =====================================================
    # HEADERS
    # =====================================================

        headers = {
            "Authorization": (
                f"Bearer {access_token}"
            ),
            "Content-Type": "application/json"
        }

    # =====================================================
    # PARÁMETROS DEL BODY
    # =====================================================

        body_parameters = [
            {
                "type": "text",
                "parameter_name": "nombre_cliente",
                "text": str(nombre_cliente)
            },
            {
                "type": "text",
                "parameter_name": parametro_numero,
                "text": str(numero_orden)
            },
            {
                "type": "text",
                "parameter_name": "vehiculo",
                "text": str(vehiculo)
            },
            {
                "type": "text",
                "parameter_name": "matricula",
                "text": str(matricula)
            }
        ]

        # Presupuesto necesita una variable adicional:
        # {{5}} = importe total.
        # Para orden y garantía este parámetro será None
        # y no se añadirá.
        if importe_total is not None:
            body_parameters.append(
                {
                    "type": "text",
                    "parameter_name": "importe_total",
                    "text": str(importe_total)
                }
            )

        # El taller siempre debe ser el último parámetro.
        body_parameters.append(
            {
                "type": "text",
                "parameter_name": "nombre_taller",
                "text": str(nombre_taller)
            }
        )


        # =====================================================
        # PAYLOAD
        # =====================================================

        payload = {
            "messaging_product": "whatsapp",
            "to": telefono,
            "type": "template",
            "template": {
                "name": template_name or WhatsAppService.TEMPLATE_NAME,
                "language": {
                    "code": WhatsAppService.TEMPLATE_LANGUAGE
                },
                "components": [
                    {
                        "type": "header",
                        "parameters": [
                            {
                                "type": "document",
                                "document": {
                                    "id": media_id,
                                    "filename": nombre_pdf
                                }
                            }
                        ]
                    },
                    {
                        "type": "body",
                        "parameters": body_parameters
                    }
                ]
            }
        }

    # =====================================================
    # DEBUG
    # =====================================================


    # =====================================================
    # ENVIAR
    # =====================================================

        try:

            response = requests.post(
                url,
                headers=headers,
                json=payload,
                timeout=30
            )

        except requests.RequestException as e:

            raise RuntimeError(
                f"No se pudo conectar con WhatsApp: {e}"
            ) from e

    # =====================================================
    # DEBUG RESPUESTA
    # =====================================================


    # =====================================================
    # ERROR META
    # =====================================================

        if not response.ok:

            try:
                detalle = response.json()
            except ValueError:
                detalle = response.text

            raise RuntimeError(
                f"WhatsApp devolvió HTTP "
                f"{response.status_code}: {detalle}"
            )

        return response.json()


    # =========================================================
    # INTERCAMBIAR CÓDIGO EMBEDDED SIGNUP
    # =========================================================

    # =========================================================
    # ENVIAR FACTURA CON PDF ADJUNTO
    # =========================================================

    @staticmethod
    def enviar_factura(
        telefono: str,
        nombre_cliente: str,
        numero_factura: str,
        vehiculo: str,
        matricula: str,
        total_factura: str,
        nombre_taller: str,
        pdf_buffer: BytesIO,
        access_token: str,
        phone_number_id: str
    ) -> dict:
        WhatsAppService.validar_credenciales(
            access_token=access_token,
            phone_number_id=phone_number_id
        )

        telefono = WhatsAppService.normalizar_telefono(telefono)
        nombre_pdf = f"factura_{numero_factura.replace('/', '-')}.pdf"
        pdf_buffer.seek(0)
        media_id = WhatsAppService.subir_documento(
            pdf_bytes=pdf_buffer.read(),
            nombre_archivo=nombre_pdf,
            access_token=access_token,
            phone_number_id=phone_number_id
        )

        url = (
            f"https://graph.facebook.com/{WhatsAppService.API_VERSION}/"
            f"{phone_number_id}/messages"
        )
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
        payload = {
            "messaging_product": "whatsapp",
            "to": telefono,
            "type": "template",
            "template": {
                "name": WhatsAppService.TEMPLATE_FACTURA_NAME,
                "language": {"code": WhatsAppService.TEMPLATE_LANGUAGE},
                "components": [
                    {
                        "type": "header",
                        "parameters": [{
                            "type": "document",
                            "document": {"id": media_id, "filename": nombre_pdf}
                        }]
                    },
                    {
                        "type": "body",
                        "parameters": [
                            {
                                "type": "text",
                                "text": str(nombre_cliente)
                            },
                            {
                                "type": "text",
                                "text": str(numero_factura)
                            },
                            {
                                "type": "text",
                                "text": str(vehiculo)
                            },
                            {
                                "type": "text",
                                "text": str(matricula)
                            },
                            {
                                "type": "text",
                                "text": str(total_factura)
                            },
                            {
                                "type": "text",
                                "text": str(nombre_taller)
                            }
                        ]
                    }
                ]
            }
        }

        try:
            response = requests.post(url, headers=headers, json=payload, timeout=30)
        except requests.RequestException as e:
            raise RuntimeError(f"No se pudo conectar con WhatsApp: {e}") from e

        if not response.ok:
            try:
                detalle = response.json()
            except ValueError:
                detalle = response.text
            raise RuntimeError(
                f"WhatsApp devolvió HTTP {response.status_code}: {detalle}"
            )

        return response.json()


    @staticmethod
    def intercambiar_codigo(
        code: str,
        redirect_uri: str | None = None
    ) -> dict:

        # =====================================================
        # VALIDACIONES
        # =====================================================

        if not code:

            raise ValueError(
                "No se ha recibido el código "
                "de autorización de Meta"
            )

        if not settings.META_APP_ID:

            raise ValueError(
                "META_APP_ID no está configurado"
            )

        if not settings.META_APP_SECRET:

            raise ValueError(
                "META_APP_SECRET no está configurado"
            )


        # =====================================================
        # OAUTH ACCESS TOKEN
        # =====================================================

        url = (
            "https://graph.facebook.com/"
            f"{WhatsAppService.API_VERSION}/"
            "oauth/access_token"
        )

        params = {
            "client_id":
                settings.META_APP_ID,

            "client_secret":
                settings.META_APP_SECRET,

            "code":
                code,
        }

        # El popup del SDK no utiliza redirect_uri. Enviarlo si no coincide
        # exactamente con la URL registrada en Meta rechaza el canje del code.
        if redirect_uri:
            params["redirect_uri"] = redirect_uri


        # =====================================================
        # INTERCAMBIAR CÓDIGO
        # =====================================================

        try:

            response = requests.get(
                url,
                params=params,
                timeout=30
            )

        except requests.RequestException as e:

            raise RuntimeError(
                f"No se pudo conectar con Meta: {e}"
            ) from e


        # =====================================================
        # VALIDAR RESPUESTA
        # =====================================================

        if not response.ok:

            try:

                detalle = response.json()

            except ValueError:

                detalle = response.text

            raise RuntimeError(
                f"Meta devolvió HTTP "
                f"{response.status_code}: {detalle}"
            )


        resultado = response.json()

        access_token = resultado.get(
            "access_token"
        )

        if not access_token:

            raise RuntimeError(
                "Meta no devolvió un access token"
            )


        # =====================================================
        # RESULTADO
        # =====================================================

        return {
            "access_token":
                access_token,

            "token_type":
                resultado.get(
                    "token_type"
                )
        }
