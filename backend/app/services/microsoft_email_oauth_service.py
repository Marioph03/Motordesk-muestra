"""OAuth Microsoft/Outlook para el cliente de escritorio usando PKCE."""

import base64
import hashlib
import json
import secrets
import time
from urllib.parse import urlencode

import requests
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.configuracion_email import ConfiguracionEmail
from app.services.secretos_service import SecretosService


class MicrosoftEmailOAuthService:
    _sesiones: dict[str, dict] = {}
    # Debe coincidir con la URI configurada en Microsoft Entra. El puente
    # loopback local la redirige internamente al servidor HTTPS de MotorDesk.
    _redirect_uri = "http://localhost:8000/configuracion/email/microsoft/callback"
    _scope = "openid profile email offline_access https://graph.microsoft.com/Mail.Send"
    _token_url = "https://login.microsoftonline.com/common/oauth2/v2.0/token"

    @classmethod
    def iniciar(cls, empresa_id: int) -> dict:
        estado = secrets.token_urlsafe(32)
        verificador = secrets.token_urlsafe(64)
        reto = base64.urlsafe_b64encode(hashlib.sha256(verificador.encode()).digest()).decode().rstrip("=")
        cls._sesiones[estado] = {"empresa_id": empresa_id, "verificador": verificador, "creada": time.time(), "estado": "PENDIENTE"}
        params = {
            "client_id": settings.MICROSOFT_OAUTH_CLIENT_ID,
            "response_type": "code",
            "redirect_uri": cls._redirect_uri,
            "response_mode": "query",
            "scope": cls._scope,
            "state": estado,
            "code_challenge": reto,
            "code_challenge_method": "S256",
            "prompt": "select_account",
        }
        return {"url": "https://login.microsoftonline.com/common/oauth2/v2.0/authorize?" + urlencode(params), "estado": estado}

    @classmethod
    def completar(cls, db: Session, codigo: str, estado: str) -> None:
        sesion = cls._sesiones.get(estado)
        if not sesion or time.time() - sesion["creada"] > 600:
            raise ValueError("La solicitud de Microsoft ha caducado. Vuelve a iniciar la conexión.")
        respuesta = requests.post(cls._token_url, data={
            "client_id": settings.MICROSOFT_OAUTH_CLIENT_ID,
            "code": codigo,
            "code_verifier": sesion["verificador"],
            "grant_type": "authorization_code",
            "redirect_uri": cls._redirect_uri,
            "scope": cls._scope,
        }, timeout=20)
        if not respuesta.ok:
            sesion["estado"] = "ERROR"
            raise RuntimeError("Microsoft no pudo autorizar la cuenta de correo.")
        datos = respuesta.json()
        refresh_token = datos.get("refresh_token")
        if not refresh_token:
            sesion["estado"] = "ERROR"
            raise RuntimeError("Microsoft no entregó la autorización permanente. Inténtalo de nuevo.")
        config = db.query(ConfiguracionEmail).filter(ConfiguracionEmail.empresa_id == sesion["empresa_id"]).first()
        if config is None:
            config = ConfiguracionEmail(empresa_id=sesion["empresa_id"], proveedor="outlook", host="smtp.office365.com", puerto=587, seguridad="starttls", usuario="", activo=True)
            db.add(config)
        payload = datos.get("id_token", "").split(".")
        if len(payload) == 3:
            decoded = base64.urlsafe_b64decode(payload[1] + "=" * (-len(payload[1]) % 4))
            config.usuario = json.loads(decoded).get("preferred_username", config.usuario)
        config.proveedor = "outlook"
        config.metodo_autenticacion = "microsoft_oauth"
        config.microsoft_refresh_token_cifrada = SecretosService.cifrar(refresh_token)
        config.activo = True
        db.commit()
        sesion["estado"] = "COMPLETADO"

    @classmethod
    def estado(cls, estado: str, empresa_id: int) -> str:
        sesion = cls._sesiones.get(estado)
        if not sesion or sesion["empresa_id"] != empresa_id:
            return "NO_ENCONTRADO"
        return sesion["estado"]

    @classmethod
    def enviar_mensaje(cls, config: ConfiguracionEmail, mensaje) -> None:
        refresh_token = SecretosService.descifrar(config.microsoft_refresh_token_cifrada)
        token = requests.post(cls._token_url, data={
            "client_id": settings.MICROSOFT_OAUTH_CLIENT_ID,
            "refresh_token": refresh_token,
            "grant_type": "refresh_token",
            "scope": cls._scope,
        }, timeout=20)
        if not token.ok:
            raise RuntimeError("Microsoft revocó la autorización. Vuelve a conectar el correo.")
        contenido_mime = base64.b64encode(mensaje.as_bytes()).decode()
        envio = requests.post(
            "https://graph.microsoft.com/v1.0/me/sendMail",
            headers={"Authorization": f"Bearer {token.json()['access_token']}", "Content-Type": "text/plain"},
            data=contenido_mime,
            timeout=30,
        )
        if not envio.ok:
            raise RuntimeError("Microsoft no pudo enviar el correo.")
