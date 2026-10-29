"""Endpoints compatibles para conectar y diagnosticar WhatsApp Business.

La configuración persistente vive exclusivamente en ``ConfiguracionWhatsApp``.
Los campos ``whatsapp_*`` de Empresa se mantienen temporalmente solo para
migraciones y rollback; este router no los lee ni los escribe.
"""

from fastapi import APIRouter, Depends, HTTPException, status
import requests
from sqlalchemy.orm import Session

from app.core.permissions import require_permission
from app.core.config import settings
from app.database.database import get_db
from app.models.usuario import Usuario
from app.schemas.whatsapp import WhatsAppConnectRequest, WhatsAppConnectResponse
from app.services.whatsapp_config_service import WhatsAppConfigService
from app.services.whatsapp_service import WhatsAppService


router = APIRouter(prefix="/whatsapp", tags=["WhatsApp"])


def _empresa_id_usuario(current_user: Usuario) -> int:
    """Obtiene la empresa del JWT sin aceptar identificadores desde el cliente."""
    if current_user.empresa_id is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="El usuario autenticado no tiene una empresa asignada.",
        )
    return current_user.empresa_id


def _meta_embedded_signup_disponible() -> bool:
    """Indica si esta instalación puede completar OAuth de Meta.

    Una instalación nueva no debe aparentar que WhatsApp está disponible si
    aún no se han provisionado las credenciales de la aplicación MotorDesk.
    """
    return bool(
        settings.META_APP_ID
        and settings.META_APP_SECRET
        and settings.META_CONFIG_ID
    )


def _configuracion_meta_pendiente() -> list[str]:
    """Devuelve solo los nombres de ajustes de Meta que faltan.

    Es intencionadamente un diagnóstico no sensible: ayuda a soporte a
    comprobar una actualización sin revelar ningún identificador, secreto o
    token al navegador.
    """
    valores = {
        "META_APP_ID": settings.META_APP_ID,
        "META_APP_SECRET": settings.META_APP_SECRET,
        "META_CONFIG_ID": settings.META_CONFIG_ID,
    }
    return [nombre for nombre, valor in valores.items() if not valor]


@router.post("/conectar", response_model=WhatsAppConnectResponse)
def conectar_whatsapp(
    request: WhatsAppConnectRequest,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_permission("permisos.gestionar")),
):
    """Intercambia OAuth de Meta y guarda sus credenciales cifradas.

    Los IDs de WABA y Phone Number proceden del flujo Embedded Signup y se
    validan frente a Meta antes de persistirse. No se registran tokens ni la
    respuesta OAuth completa en los logs.
    """
    if not _meta_embedded_signup_disponible():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=(
                "WhatsApp Business no está habilitado en esta instalación. "
                "Contacta con el administrador de MotorDesk para configurar "
                "la integración de Meta."
            ),
        )

    try:
        empresa_id = _empresa_id_usuario(current_user)
        resultado = WhatsAppService.intercambiar_codigo(
            code=request.code,
            redirect_uri=request.redirect_uri,
        )
        access_token = resultado.get("access_token")

        if not access_token:
            raise RuntimeError("Meta no devolvió un access token.")

        numero_whatsapp = WhatsAppService.obtener_numero_whatsapp(
            access_token=access_token,
            waba_id=request.waba_id,
            phone_number_id=request.phone_number_id,
        )

        WhatsAppConfigService.guardar(
            db=db,
            empresa_id=empresa_id,
            whatsapp_business_account_id=request.waba_id,
            phone_number_id=request.phone_number_id,
            numero_whatsapp=numero_whatsapp,
            access_token=access_token,
            activo=True,
        )
        return {"message": "WhatsApp Business conectado correctamente."}
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc


@router.get("/estado")
def obtener_estado_whatsapp(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_permission("permisos.gestionar")),
):
    """Endpoint compatible; la fuente de verdad es la configuración cifrada."""
    empresa_id = _empresa_id_usuario(current_user)
    config = WhatsAppConfigService.obtener(db, empresa_id)
    return {
        "conectado": WhatsAppConfigService.esta_configurado(db, empresa_id),
        "numero_whatsapp": config.numero_whatsapp if config else None,
        "embedded_signup_disponible": _meta_embedded_signup_disponible(),
        "meta_config_id": (
            settings.META_CONFIG_ID
            if _meta_embedded_signup_disponible()
            else None
        ),
        # El identificador de aplicación es público y el SDK lo necesita para
        # inicializarse. El secreto nunca abandona el backend.
        "meta_app_id": (
            settings.META_APP_ID
            if _meta_embedded_signup_disponible()
            else None
        ),
        # Origen público aprobado por Meta para Embedded Signup. Es una página
        # estática; el secreto de Meta y el intercambio del código permanecen
        # exclusivamente en el backend local.
        "meta_signup_bridge_url": (
            settings.META_EMBEDDED_SIGNUP_BRIDGE_URL
            if _meta_embedded_signup_disponible()
            else None
        ),
        # No contiene valores: solo permite identificar de forma segura una
        # instalación antigua cuyo .env no se actualizó correctamente.
        "configuracion_meta_pendiente": _configuracion_meta_pendiente(),
    }


@router.get("/debug")
def debug_whatsapp(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_permission("permisos.gestionar")),
):
    """Comprueba el perfil del número configurado sin exponer secretos."""
    empresa_id = _empresa_id_usuario(current_user)
    config = WhatsAppConfigService.obtener(db, empresa_id)
    if config is None or not config.phone_number_id:
        raise HTTPException(status_code=400, detail="WhatsApp no está configurado.")

    token = WhatsAppConfigService.obtener_token(db, empresa_id)
    try:
        response = requests.get(
            f"https://graph.facebook.com/{WhatsAppService.API_VERSION}/"
            f"{config.phone_number_id}",
            headers={"Authorization": f"Bearer {token}"},
            params={"fields": "id,display_phone_number,verified_name"},
            timeout=30,
        )
    except requests.RequestException as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="No se pudo conectar con Meta.",
        ) from exc

    if not response.ok:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Meta no pudo consultar el perfil de WhatsApp.",
        )

    perfil = response.json()
    return {
        "conectado": True,
        "id": perfil.get("id"),
        "numero_whatsapp": perfil.get("display_phone_number"),
        "nombre_verificado": perfil.get("verified_name"),
    }
