"""OAuth de Gmail para la aplicación de escritorio usando PKCE."""

import base64
import hashlib
import secrets
import time
from urllib.parse import urlencode

import requests
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.configuracion_email import ConfiguracionEmail
from app.services.secretos_service import SecretosService


class GoogleEmailOAuthService:
    _sesiones: dict[str, dict] = {}
    # Cliente OAuth de tipo escritorio: Google autoriza callbacks loopback HTTP.
    _redirect_uri = "http://127.0.0.1:8000/configuracion/email/google/callback"
    _scope = "openid email https://www.googleapis.com/auth/gmail.send"

    @classmethod
    def iniciar(cls, empresa_id: int) -> dict:
        estado = secrets.token_urlsafe(32)
        verificador = secrets.token_urlsafe(64)
        reto = base64.urlsafe_b64encode(hashlib.sha256(verificador.encode()).digest()).decode().rstrip("=")
        cls._sesiones[estado] = {"empresa_id": empresa_id, "verificador": verificador, "creada": time.time(), "estado": "PENDIENTE"}
        params = {"client_id": settings.GOOGLE_OAUTH_CLIENT_ID, "redirect_uri": cls._redirect_uri, "response_type": "code", "scope": cls._scope, "state": estado, "code_challenge": reto, "code_challenge_method": "S256", "access_type": "offline", "prompt": "consent"}
        return {"url": "https://accounts.google.com/o/oauth2/v2/auth?" + urlencode(params), "estado": estado}

    @classmethod
    def completar(cls, db: Session, codigo: str, estado: str) -> None:
        sesion = cls._sesiones.get(estado)
        if not sesion or time.time() - sesion["creada"] > 600:
            raise ValueError("La solicitud de Google ha caducado. Vuelve a iniciar la conexión.")
        datos_solicitud = {"client_id": settings.GOOGLE_OAUTH_CLIENT_ID, "code": codigo, "code_verifier": sesion["verificador"], "grant_type": "authorization_code", "redirect_uri": cls._redirect_uri}
        if settings.GOOGLE_OAUTH_CLIENT_SECRET:
            datos_solicitud["client_secret"] = settings.GOOGLE_OAUTH_CLIENT_SECRET
        respuesta = requests.post("https://oauth2.googleapis.com/token", data=datos_solicitud, timeout=20)
        if not respuesta.ok:
            try:
                detalle = respuesta.json()
            except ValueError:
                detalle = {}
            codigo_error = str(detalle.get("error") or f"HTTP {respuesta.status_code}")
            descripcion = str(detalle.get("error_description") or "")
            mensaje = f"Google rechazó la autorización ({codigo_error})."
            if descripcion:
                mensaje += f" {descripcion}"
            # No se registra ni el código de autorización ni ningún token.
            print(f"MotorDesk: {mensaje}")
            sesion["estado"] = "ERROR"
            sesion["error"] = mensaje
            raise RuntimeError(mensaje)
        datos = respuesta.json()
        refresh_token = datos.get("refresh_token")
        if not refresh_token:
            raise RuntimeError("Google no entregó la autorización permanente. Inténtalo de nuevo.")
        config = db.query(ConfiguracionEmail).filter(ConfiguracionEmail.empresa_id == sesion["empresa_id"]).first()
        if config is None:
            config = ConfiguracionEmail(empresa_id=sesion["empresa_id"], proveedor="gmail", host="smtp.gmail.com", puerto=587, seguridad="starttls", usuario="", activo=True)
            db.add(config)
        payload = datos.get("id_token", "").split(".")
        if len(payload) == 3:
            decoded = base64.urlsafe_b64decode(payload[1] + "==")
            import json
            config.usuario = json.loads(decoded).get("email", config.usuario)
        config.metodo_autenticacion = "google_oauth"
        config.google_refresh_token_cifrada = SecretosService.cifrar(refresh_token)
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
    def detalle_estado(cls, estado: str, empresa_id: int) -> str | None:
        sesion = cls._sesiones.get(estado)
        if not sesion or sesion["empresa_id"] != empresa_id:
            return None
        return sesion.get("error")
