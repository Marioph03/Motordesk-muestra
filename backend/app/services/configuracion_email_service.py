import smtplib
import ssl
import base64
import requests
from email.message import EmailMessage

from sqlalchemy.orm import Session

from app.models.configuracion_email import ConfiguracionEmail
from app.services.secretos_service import SecretosService


class ConfiguracionEmailService:
    @staticmethod
    def obtener(db: Session, empresa_id: int) -> ConfiguracionEmail | None:
        return db.query(ConfiguracionEmail).filter(ConfiguracionEmail.empresa_id == empresa_id).first()

    @classmethod
    def guardar(cls, db: Session, empresa_id: int, datos) -> ConfiguracionEmail:
        config = cls.obtener(db, empresa_id)
        if config is None:
            config = ConfiguracionEmail(empresa_id=empresa_id)
            db.add(config)
        for campo in ("proveedor", "host", "puerto", "seguridad", "usuario", "remitente", "activo"):
            setattr(config, campo, getattr(datos, campo))
        if datos.password:
            config.password_cifrada = SecretosService.cifrar(datos.password)
            config.metodo_autenticacion = "password"
        elif not config.password_cifrada:
            raise ValueError("Introduce la contraseña de aplicación del correo.")
        db.commit(); db.refresh(config)
        return config

    @staticmethod
    def respuesta(config: ConfiguracionEmail | None) -> dict:
        if config is None:
            return {"configurado": False}
        return {"configurado": True, "activo": config.activo, "proveedor": config.proveedor, "host": config.host, "puerto": config.puerto, "seguridad": config.seguridad, "usuario": config.usuario, "remitente": config.remitente, "metodo_autenticacion": config.metodo_autenticacion}

    @classmethod
    def enviar_prueba(cls, db: Session, empresa_id: int, destinatario: str) -> None:
        config = cls.obtener(db, empresa_id)
        if config is None or not config.activo:
            raise ValueError("Configura y activa el correo electrónico antes de enviar una prueba.")
        mensaje = EmailMessage()
        mensaje["From"] = config.remitente or config.usuario
        mensaje["To"] = destinatario
        mensaje["Subject"] = "Prueba de correo - MotorDesk"
        mensaje.set_content("La integración de correo electrónico de MotorDesk funciona correctamente.")
        if config.metodo_autenticacion == "google_oauth":
            from app.core.config import settings
            datos_token = {"client_id": settings.GOOGLE_OAUTH_CLIENT_ID, "refresh_token": SecretosService.descifrar(config.google_refresh_token_cifrada), "grant_type": "refresh_token"}
            if settings.GOOGLE_OAUTH_CLIENT_SECRET:
                datos_token["client_secret"] = settings.GOOGLE_OAUTH_CLIENT_SECRET
            token = requests.post("https://oauth2.googleapis.com/token", data=datos_token, timeout=20)
            if not token.ok:
                raise RuntimeError("Google revocó la autorización. Vuelve a conectar el correo.")
            raw = base64.urlsafe_b64encode(mensaje.as_bytes()).decode().rstrip("=")
            envio = requests.post("https://gmail.googleapis.com/gmail/v1/users/me/messages/send", headers={"Authorization": f"Bearer {token.json()['access_token']}"}, json={"raw": raw}, timeout=30)
            if not envio.ok:
                raise RuntimeError("Google no pudo enviar el correo de prueba.")
            return
        if config.metodo_autenticacion == "microsoft_oauth":
            from app.services.microsoft_email_oauth_service import MicrosoftEmailOAuthService
            MicrosoftEmailOAuthService.enviar_mensaje(config, mensaje)
            return
        password = SecretosService.descifrar(config.password_cifrada)
        try:
            if config.seguridad == "ssl":
                with smtplib.SMTP_SSL(config.host, config.puerto, timeout=30, context=ssl.create_default_context()) as servidor:
                    servidor.login(config.usuario, password); servidor.send_message(mensaje)
            else:
                with smtplib.SMTP(config.host, config.puerto, timeout=30) as servidor:
                    servidor.ehlo(); servidor.starttls(context=ssl.create_default_context()); servidor.ehlo(); servidor.login(config.usuario, password); servidor.send_message(mensaje)
        except smtplib.SMTPAuthenticationError as exc:
            raise RuntimeError("No se pudo autenticar. En Gmail usa una contraseña de aplicación.") from exc
        except (smtplib.SMTPException, OSError) as exc:
            raise RuntimeError(f"No se pudo conectar con el servidor SMTP: {exc}") from exc
