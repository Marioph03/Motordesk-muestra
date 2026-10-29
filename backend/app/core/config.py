from pathlib import Path

from dotenv import load_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict


# El servidor puede heredar variables antiguas de una terminal o servicio.
# Cargamos siempre el .env del backend antes de crear Settings para que la
# configuración SMTP usada por Uvicorn coincida con la del proyecto.
# ``backend/.env`` conserva las credenciales de desarrollo históricas. El
# ``.env`` raíz guarda los secretos propios de la instalación Docker, incluida
# ENCRYPTION_KEY. Cargamos primero el general y luego el específico del backend
# para mantener la compatibilidad con ambos modos de ejecución.
ROOT_ENV_FILE = Path(__file__).resolve().parents[3] / ".env"
ENV_FILE = Path(__file__).resolve().parents[2] / ".env"
load_dotenv(ROOT_ENV_FILE, override=False)
load_dotenv(ENV_FILE, override=False)


class Settings(BaseSettings):

    # =====================================================
    # BASE DE DATOS
    # =====================================================

    database_url: str

    # =====================================================
    # JWT / SEGURIDAD
    # =====================================================

    secret_key: str
    # Clave Fernet propia de cada instalación para cifrar secretos persistidos.
    # Nunca debe incluirse en código ni en copias de base de datos sin proteger.
    encryption_key: str
    algorithm: str = "HS256"
    # Seis horas por defecto. El valor puede ajustarse por entorno mediante .env.
    access_token_expire_minutes: int = 360

    # =====================================================
    # COPIAS DE SEGURIDAD
    # =====================================================

    pg_dump_path: str = ""
    backup_auto_enabled: bool = True
    backup_interval_hours: int = 24
    # Se comprueba cada quince minutos para no retrasar hasta una hora una
    # copia que ya ha cumplido el intervalo de veinticuatro horas.
    backup_check_minutes: int = 15

    # =====================================================
    # EMAIL
    # =====================================================

    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587

    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""

    EMAIL_FROM: str = ""
    # Identificador público del cliente OAuth de escritorio de MotorDesk.
    # PKCE evita necesitar (o distribuir) una contraseña de aplicación.
    GOOGLE_OAUTH_CLIENT_ID: str = "30971929626-cmojruh4slfdeq8totovq694eaai0ccp.apps.googleusercontent.com"
    GOOGLE_OAUTH_CLIENT_SECRET: str = ""
    # Identificador público de la aplicación Microsoft Entra usada para Outlook.
    # Es un cliente de escritorio con PKCE: no se distribuyen secretos.
    MICROSOFT_OAUTH_CLIENT_ID: str = "e4c343d0-3dd2-4aec-8367-47a0c4979eeb"

    # =====================================================
    # WHATSAPP
    # =====================================================

    WHATSAPP_SYSTEM_TOKEN: str = ""
    WHATSAPP_PHONE_NUMBER_ID: str = ""
    WHATSAPP_FACTURA_TEMPLATE_NAME: str = "factura"
    # Debe coincidir con una plantilla aprobada en Meta para presupuestos.
    WHATSAPP_PRESUPUESTO_TEMPLATE_NAME: str = "presupuesto"
    # Debe coincidir con una plantilla aprobada en Meta para garantías.
    WHATSAPP_GARANTIA_TEMPLATE_NAME: str = "garantia"

    # =====================================================
    # META
    # =====================================================

    META_APP_ID: str = ""
    META_APP_SECRET: str = ""
    # Es público y se comparte con el navegador para abrir Embedded Signup.
    # La clave privada de la aplicación nunca se devuelve al frontend.
    META_CONFIG_ID: str = "1547065099596140"
    # Página pública estática usada únicamente para iniciar WhatsApp Embedded
    # Signup. Meta ya no admite localhost como dominio de una aplicación.
    # No contiene secretos ni accede a datos de los talleres.
    META_EMBEDDED_SIGNUP_BRIDGE_URL: str = (
        "https://marioph03.github.io/motordesk-legal/motordesk-connect/"
    )

    # =====================================================
    # CONFIGURACIÓN
    # =====================================================

    model_config = SettingsConfigDict(
        env_file=ENV_FILE,
        env_file_encoding="utf-8",
        extra="ignore"
    )


settings = Settings()
"""Parámetros de aplicación utilizados por la capa core y seguridad."""
