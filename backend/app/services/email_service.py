import smtplib
import ssl
import base64
import requests

from email.message import EmailMessage
from io import BytesIO

from app.core.config import settings
from app.services.configuracion_email_service import ConfiguracionEmailService
from app.services.secretos_service import SecretosService

class EmailService:

    @staticmethod
    def enviar_documento_configurado(db, empresa_id, destinatario, asunto, texto, pdf_buffer, nombre_archivo):
        config = ConfiguracionEmailService.obtener(db, empresa_id)
        if config is None or not config.activo:
            raise ValueError("Configura el correo electrónico en Configuración > Integraciones antes de enviar documentos.")
        mensaje = EmailMessage(); mensaje["From"] = config.remitente or config.usuario; mensaje["To"] = destinatario; mensaje["Subject"] = asunto; mensaje.set_content(texto)
        pdf_buffer.seek(0); mensaje.add_attachment(pdf_buffer.read(), maintype="application", subtype="pdf", filename=nombre_archivo)
        if config.metodo_autenticacion == "google_oauth":
            from app.core.config import settings
            refresh_token = SecretosService.descifrar(config.google_refresh_token_cifrada)
            datos_token = {"client_id": settings.GOOGLE_OAUTH_CLIENT_ID, "refresh_token": refresh_token, "grant_type": "refresh_token"}
            if settings.GOOGLE_OAUTH_CLIENT_SECRET:
                datos_token["client_secret"] = settings.GOOGLE_OAUTH_CLIENT_SECRET
            token = requests.post("https://oauth2.googleapis.com/token", data=datos_token, timeout=20)
            if not token.ok:
                raise RuntimeError("Google revocó la autorización. Vuelve a conectar el correo.")
            raw = base64.urlsafe_b64encode(mensaje.as_bytes()).decode().rstrip("=")
            envio = requests.post("https://gmail.googleapis.com/gmail/v1/users/me/messages/send", headers={"Authorization": f"Bearer {token.json()['access_token']}"}, json={"raw": raw}, timeout=30)
            if not envio.ok:
                raise RuntimeError("Google no pudo enviar el correo.")
            return
        if config.metodo_autenticacion == "microsoft_oauth":
            from app.services.microsoft_email_oauth_service import MicrosoftEmailOAuthService
            MicrosoftEmailOAuthService.enviar_mensaje(config, mensaje)
            return
        password = SecretosService.descifrar(config.password_cifrada)
        try:
            if config.seguridad == "ssl":
                with smtplib.SMTP_SSL(config.host, config.puerto, timeout=30, context=ssl.create_default_context()) as servidor: servidor.login(config.usuario, password); servidor.send_message(mensaje)
            else:
                with smtplib.SMTP(config.host, config.puerto, timeout=30) as servidor: servidor.ehlo(); servidor.starttls(); servidor.ehlo(); servidor.login(config.usuario, password); servidor.send_message(mensaje)
        except smtplib.SMTPAuthenticationError as exc: raise RuntimeError("No se pudo autenticar. En Gmail usa una contraseña de aplicación.") from exc
        except (smtplib.SMTPException, OSError) as exc: raise RuntimeError(f"No se pudo conectar con el servidor SMTP: {exc}") from exc

    @staticmethod
    def enviar_recordatorio_cita(destinatario: str, nombre_cliente: str, fecha: str, hora: str, vehiculo: str, matricula: str, motivo: str) -> None:
        if not destinatario:
            raise ValueError("El cliente no tiene email configurado")
        if not settings.SMTP_USER or not settings.SMTP_PASSWORD:
            raise ValueError("La configuración SMTP está incompleta")
        mensaje = EmailMessage()
        mensaje["From"] = settings.EMAIL_FROM or settings.SMTP_USER
        mensaje["To"] = destinatario
        mensaje["Subject"] = "Recordatorio de cita - MotorDesk"
        mensaje.set_content(f"Hola {nombre_cliente},\n\nTe recordamos tu cita el {fecha} a las {hora}.\nVehículo: {vehiculo} · {matricula}\nMotivo: {motivo}\n\nUn saludo.")
        try:
            with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=30) as servidor:
                servidor.ehlo(); servidor.starttls(); servidor.ehlo(); servidor.login(settings.SMTP_USER, settings.SMTP_PASSWORD); servidor.send_message(mensaje)
        except smtplib.SMTPAuthenticationError as e:
            raise RuntimeError("No se pudo autenticar con el servidor de correo") from e
        except smtplib.SMTPException as e:
            raise RuntimeError(f"Error enviando el correo: {e}") from e

    @staticmethod
    def enviar_confirmacion_cita(destinatario: str, nombre_cliente: str, fecha_inicio, vehiculo: str, motivo: str) -> None:
        if not destinatario:
            raise ValueError("El cliente no tiene un correo electrónico registrado")
        if not settings.SMTP_USER or not settings.SMTP_PASSWORD:
            raise ValueError("La configuración SMTP está incompleta")

        mensaje = EmailMessage()
        mensaje["From"] = settings.EMAIL_FROM or settings.SMTP_USER
        mensaje["To"] = destinatario
        mensaje["Subject"] = "Confirmación de cita - MotorDesk"
        mensaje.set_content(
            f"Hola {nombre_cliente},\n\nConfirmamos tu cita para el {fecha_inicio.strftime('%d/%m/%Y a las %H:%M')}.\n"
            f"Vehículo: {vehiculo}\nMotivo: {motivo}\n\nUn saludo."
        )
        try:
            with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=30) as servidor:
                servidor.ehlo(); servidor.starttls(); servidor.ehlo()
                servidor.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
                servidor.send_message(mensaje)
        except smtplib.SMTPAuthenticationError as e:
            raise RuntimeError("No se pudo autenticar con el servidor de correo") from e
        except smtplib.SMTPException as e:
            raise RuntimeError(f"Error enviando el correo: {e}") from e

    @staticmethod
    def enviar_aviso_reprogramacion_cita(
        destinatario: str,
        nombre_cliente: str,
        fecha_inicio,
        vehiculo: str,
        matricula: str,
    ) -> None:
        if not destinatario:
            raise ValueError("El cliente no tiene un correo electrónico registrado")
        if not settings.SMTP_USER or not settings.SMTP_PASSWORD:
            raise ValueError("La configuración SMTP está incompleta")

        mensaje = EmailMessage()
        mensaje["From"] = settings.EMAIL_FROM or settings.SMTP_USER
        mensaje["To"] = destinatario
        mensaje["Subject"] = "Cambio de cita - MotorDesk"
        mensaje.set_content(
            f"""Hola {nombre_cliente},

Tu cita ha sido reprogramada.

Nueva fecha: {fecha_inicio.strftime('%d/%m/%Y')}
Nueva hora: {fecha_inicio.strftime('%H:%M')}
Vehículo: {vehiculo}
Matrícula: {matricula}

Si necesitas realizar algún cambio, ponte en contacto con nosotros.

Un saludo.
"""
        )

        try:
            with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=30) as servidor:
                servidor.ehlo()
                servidor.starttls()
                servidor.ehlo()
                servidor.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
                servidor.send_message(mensaje)
        except smtplib.SMTPAuthenticationError as e:
            raise RuntimeError("No se pudo autenticar con el servidor de correo") from e
        except smtplib.SMTPException as e:
            raise RuntimeError(f"Error enviando el correo: {e}") from e

    @staticmethod
    def enviar_factura(
        destinatario: str,
        nombre_cliente: str,
        numero_factura: str,
        pdf_buffer: BytesIO
    ) -> None:

        if not destinatario:
            raise ValueError(
                "El cliente no tiene un correo electronico registrado"
            )

        if not settings.SMTP_USER:
            raise ValueError("SMTP_USER no esta configurado")

        if not settings.SMTP_PASSWORD:
            raise ValueError("SMTP_PASSWORD no esta configurado")

        mensaje = EmailMessage()
        mensaje["From"] = settings.EMAIL_FROM or settings.SMTP_USER
        mensaje["To"] = destinatario
        mensaje["Subject"] = f"Factura {numero_factura}"
        mensaje.set_content(
            f"""Hola {nombre_cliente},

Adjuntamos la factura {numero_factura} en formato PDF.

Un saludo.
"""
        )

        pdf_buffer.seek(0)
        mensaje.add_attachment(
            pdf_buffer.read(),
            maintype="application",
            subtype="pdf",
            filename=f"factura_{numero_factura.replace('/', '-')}.pdf"
        )

        try:
            servidor = smtplib.SMTP(
                settings.SMTP_HOST,
                settings.SMTP_PORT,
                timeout=30
            )

            try:
                servidor.ehlo()
                servidor.starttls()
                servidor.ehlo()
                servidor.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
                servidor.send_message(mensaje)
            finally:
                # Gmail puede cerrar la conexión justo después de aceptar el
                # mensaje. No debe convertirse en un 502 si el envío ya fue
                # confirmado por send_message.
                try:
                    servidor.quit()
                except (smtplib.SMTPException, OSError):
                    pass
        except smtplib.SMTPAuthenticationError as e:
            raise RuntimeError(
                "No se pudo autenticar con el servidor de correo"
            ) from e

        except smtplib.SMTPResponseException as e:
            detalle = e.smtp_error.decode(
                "utf-8",
                errors="replace"
            )
            raise RuntimeError(
                f"SMTP {e.smtp_code}: {detalle}"
            ) from e

        except smtplib.SMTPException as e:
            raise RuntimeError(f"Error enviando el correo: {e}") from e

    @staticmethod
    def enviar_orden(
        destinatario: str,
        nombre_cliente: str,
        numero_orden: str,
        vehiculo: str,
        matricula: str,
        pdf_buffer: BytesIO
    ) -> None:

        if not destinatario:
            raise ValueError(
                "El cliente no tiene un correo electrónico registrado"
            )

        if not settings.SMTP_USER:
            raise ValueError(
                "SMTP_USER no está configurado"
            )

        if not settings.SMTP_PASSWORD:
            raise ValueError(
                "SMTP_PASSWORD no está configurado"
            )

        # =====================================================
        # CREAR MENSAJE
        # =====================================================

        mensaje = EmailMessage()

        mensaje["From"] = (
            settings.EMAIL_FROM
            or settings.SMTP_USER
        )

        mensaje["To"] = destinatario

        mensaje["Subject"] = (
            f"Orden de reparación {numero_orden}"
        )

        mensaje.set_content(
            f"""Hola {nombre_cliente},

Adjuntamos la orden de reparación {numero_orden} correspondiente a su vehículo {vehiculo}, matrícula {matricula}.

En el documento PDF adjunto encontrará los datos de la orden y el estado registrado del vehículo.

Un saludo.
"""
        )

        # =====================================================
        # ADJUNTAR PDF
        # =====================================================

        pdf_buffer.seek(0)

        contenido_pdf = pdf_buffer.read()

        mensaje.add_attachment(
            contenido_pdf,
            maintype="application",
            subtype="pdf",
            filename=f"orden_{numero_orden}.pdf"
        )

        # =====================================================
        # ENVIAR
        # =====================================================

        try:

            with smtplib.SMTP(
                settings.SMTP_HOST,
                settings.SMTP_PORT,
                timeout=30
            ) as servidor:

                servidor.ehlo()

                servidor.starttls()

                servidor.ehlo()

                servidor.login(
                    settings.SMTP_USER,
                    settings.SMTP_PASSWORD
                )

                servidor.send_message(
                    mensaje
                )

        except smtplib.SMTPAuthenticationError as e:

            raise RuntimeError(
                "No se pudo autenticar con el servidor de correo"
            ) from e

        except smtplib.SMTPException as e:

            raise RuntimeError(
                f"Error enviando el correo: {e}"
            ) from e

    @staticmethod
    def enviar_presupuesto(
        destinatario: str,
        nombre_cliente: str,
        numero_presupuesto: str,
        vehiculo: str,
        matricula: str,
        pdf_buffer: BytesIO
    ) -> None:
        """Envía un presupuesto con asunto, texto y adjunto propios."""
        if not destinatario:
            raise ValueError("El cliente no tiene un correo electrónico registrado")
        if not settings.SMTP_USER:
            raise ValueError("SMTP_USER no está configurado")
        if not settings.SMTP_PASSWORD:
            raise ValueError("SMTP_PASSWORD no está configurado")

        mensaje = EmailMessage()
        mensaje["From"] = settings.EMAIL_FROM or settings.SMTP_USER
        mensaje["To"] = destinatario
        mensaje["Subject"] = f"Presupuesto {numero_presupuesto}"
        mensaje.set_content(
            f"""Hola {nombre_cliente},

Adjuntamos el presupuesto {numero_presupuesto} para su vehículo {vehiculo}, matrícula {matricula}.

Encontrará el detalle de los trabajos y piezas presupuestados en el PDF adjunto.

Un saludo.
"""
        )

        pdf_buffer.seek(0)
        mensaje.add_attachment(
            pdf_buffer.read(),
            maintype="application",
            subtype="pdf",
            filename=f"presupuesto_{numero_presupuesto}.pdf"
        )

        try:
            with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=30) as servidor:
                servidor.ehlo()
                servidor.starttls()
                servidor.ehlo()
                servidor.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
                servidor.send_message(mensaje)
        except smtplib.SMTPAuthenticationError as e:
            raise RuntimeError("No se pudo autenticar con el servidor de correo") from e
        except smtplib.SMTPException as e:
            raise RuntimeError(f"Error enviando el correo: {e}") from e

    @staticmethod
    def enviar_garantia(
        destinatario: str,
        nombre_cliente: str,
        numero_garantia: str,
        vehiculo: str,
        matricula: str,
        pdf_buffer: BytesIO,
    ) -> None:
        """Envía el documento de garantía con comunicación propia."""
        if not destinatario:
            raise ValueError("El cliente no tiene un correo electrónico registrado")
        if not settings.SMTP_USER:
            raise ValueError("SMTP_USER no está configurado")
        if not settings.SMTP_PASSWORD:
            raise ValueError("SMTP_PASSWORD no está configurado")

        mensaje = EmailMessage()
        mensaje["From"] = settings.EMAIL_FROM or settings.SMTP_USER
        mensaje["To"] = destinatario
        mensaje["Subject"] = f"Garantía {numero_garantia}"
        mensaje.set_content(
            f"""Hola {nombre_cliente},

Adjuntamos el documento de garantía {numero_garantia} correspondiente a su vehículo {vehiculo}, matrícula {matricula}.

En el PDF encontrará el motivo de la garantía, las operaciones realizadas y los conceptos cubiertos o a cargo del cliente.

Un saludo.
"""
        )

        pdf_buffer.seek(0)
        mensaje.add_attachment(
            pdf_buffer.read(),
            maintype="application",
            subtype="pdf",
            filename=f"garantia_{numero_garantia}.pdf",
        )

        try:
            with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=30) as servidor:
                servidor.ehlo()
                servidor.starttls()
                servidor.ehlo()
                servidor.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
                servidor.send_message(mensaje)
        except smtplib.SMTPAuthenticationError as e:
            raise RuntimeError("No se pudo autenticar con el servidor de correo") from e
        except smtplib.SMTPException as e:
            raise RuntimeError(f"Error enviando el correo: {e}") from e
