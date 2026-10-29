"""Configuración WhatsApp Business aislada por empresa autenticada."""

from io import BytesIO

from fastapi import APIRouter, Depends, HTTPException, Response, status
from reportlab.pdfgen import canvas
from sqlalchemy.orm import Session

from app.core.permissions import require_permission
from app.database.database import get_db
from app.models.usuario import Usuario
from app.schemas.configuracion_whatsapp import (
    ConfiguracionWhatsAppGuardar,
    ConfiguracionWhatsAppResponse,
    EstadoWhatsAppResponse,
    WhatsAppPlantillasResponse,
)
from app.services.whatsapp_config_service import WhatsAppConfigService
from app.services.whatsapp_plantillas_service import WhatsAppPlantillasService


router = APIRouter(
    prefix="/configuracion/whatsapp",
    tags=["Configuración WhatsApp"],
)


def _empresa_id_usuario(current_user: Usuario) -> int:
    """Obtiene la empresa del JWT y bloquea usuarios sin empresa asociada."""

    if current_user.empresa_id is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="El usuario autenticado no tiene una empresa asignada.",
        )

    return current_user.empresa_id


def _crear_response(config) -> ConfiguracionWhatsAppResponse:
    """Serializa la configuración sin exponer jamás el token cifrado."""

    return ConfiguracionWhatsAppResponse(
        id=config.id,
        empresa_id=config.empresa_id,
        activo=config.activo,
        whatsapp_business_account_id=config.whatsapp_business_account_id,
        phone_number_id=config.phone_number_id,
        numero_whatsapp=config.numero_whatsapp,
        token_configurado=bool(config.access_token_cifrado),
    )


def generar_pdf_ejemplo_whatsapp() -> bytes:
    """
    Genera en memoria un PDF neutro para usar como documento
    de ejemplo al crear plantillas de WhatsApp en Meta.

    No contiene datos reales de clientes.
    """

    buffer = BytesIO()

    pdf = canvas.Canvas(buffer)

    pdf.setFont("Helvetica-Bold", 18)
    pdf.drawString(
        72,
        750,
        "MotorDesk",
    )

    pdf.setFont("Helvetica", 12)
    pdf.drawString(
        72,
        720,
        "Documento de ejemplo para plantilla de WhatsApp",
    )

    pdf.drawString(
        72,
        700,
        "Este documento no contiene datos reales de clientes.",
    )

    pdf.save()

    buffer.seek(0)

    return buffer.read()


@router.get(
    "/plantillas",
    response_model=WhatsAppPlantillasResponse,
)
def obtener_plantillas(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(
        require_permission("permisos.gestionar")
    ),
):
    """Inicializa y devuelve el catálogo local; no contacta con Meta."""

    empresa_id = _empresa_id_usuario(current_user)

    if not WhatsAppConfigService.esta_configurado(
        db,
        empresa_id,
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="WhatsApp no está configurado para esta empresa.",
        )

    plantillas = WhatsAppPlantillasService.inicializar_catalogo(
        db,
        empresa_id,
    )

    return WhatsAppPlantillasResponse(
        plantillas=plantillas,
    )


@router.post(
    "/plantillas/sincronizar",
    response_model=WhatsAppPlantillasResponse,
)
def sincronizar_plantillas_whatsapp(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(
        require_permission("permisos.gestionar")
    ),
):
    """Sincroniza bajo demanda los estados locales desde Meta Graph API."""

    empresa_id = _empresa_id_usuario(current_user)

    try:
        plantillas = WhatsAppPlantillasService.sincronizar_con_meta(
            db,
            empresa_id,
        )

        return WhatsAppPlantillasResponse(
            plantillas=plantillas,
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    except RuntimeError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(exc),
        ) from exc


@router.get(
    "",
    response_model=ConfiguracionWhatsAppResponse,
)
def obtener_configuracion(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(
        require_permission("permisos.gestionar")
    ),
):
    """Devuelve únicamente la configuración de la empresa del usuario actual."""

    empresa_id = _empresa_id_usuario(current_user)

    config = WhatsAppConfigService.obtener(
        db,
        empresa_id,
    )

    if config is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="WhatsApp no está configurado para esta empresa.",
        )

    return _crear_response(config)


@router.get(
    "/estado",
    response_model=EstadoWhatsAppResponse,
)
def obtener_estado(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(
        require_permission("permisos.gestionar")
    ),
):
    """
    Informa del estado sin devolver secretos
    ni identificadores de otra empresa.
    """

    empresa_id = _empresa_id_usuario(current_user)

    config = WhatsAppConfigService.obtener(
        db,
        empresa_id,
    )

    if config is None:
        return EstadoWhatsAppResponse(
            configurado=False,
            activo=False,
            numero_whatsapp=None,
        )

    return EstadoWhatsAppResponse(
        configurado=WhatsAppConfigService.esta_configurado(
            db,
            empresa_id,
        ),
        activo=config.activo,
        numero_whatsapp=config.numero_whatsapp,
    )


@router.put(
    "",
    response_model=ConfiguracionWhatsAppResponse,
)
def guardar_configuracion(
    datos: ConfiguracionWhatsAppGuardar,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(
        require_permission("permisos.gestionar")
    ),
):
    """Crea o actualiza la configuración propia, cifrando el token recibido."""

    try:
        config = WhatsAppConfigService.guardar(
            db=db,
            empresa_id=_empresa_id_usuario(current_user),
            whatsapp_business_account_id=(
                datos.whatsapp_business_account_id
            ),
            phone_number_id=datos.phone_number_id,
            numero_whatsapp=datos.numero_whatsapp,
            access_token=datos.access_token,
            activo=datos.activo,
        )

        return _crear_response(config)

    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc


@router.delete("", status_code=status.HTTP_204_NO_CONTENT)
def desconectar_configuracion(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(
        require_permission("permisos.gestionar")
    ),
) -> Response:
    """Elimina solo las credenciales locales; no modifica nada en Meta."""

    config = WhatsAppConfigService.obtener(
        db,
        _empresa_id_usuario(current_user),
    )
    if config is not None:
        db.delete(config)
        db.commit()

    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post(
    "/plantillas/{tipo}/crear",
    response_model=dict,
)
def crear_plantilla_whatsapp(
    tipo: str,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(
        require_permission("permisos.gestionar")
    ),
):
    """
    Crea en Meta una plantilla documental que esté realmente
    en estado NO_CREADA.

    Genera un PDF neutro en memoria, lo sube a Meta para obtener
    el header_handle y envía después la plantilla a revisión.
    """

    empresa_id = _empresa_id_usuario(current_user)

    tipo = tipo.upper().strip()

    if not WhatsAppPlantillasService.puede_crearse_automaticamente(
        tipo
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"La plantilla {tipo} no está habilitada "
                "para creación automática."
            ),
        )

    try:
        # El estado local puede estar desactualizado si esta instalacion se
        # conecta a una WABA que ya contenia plantillas. Antes de escribir en
        # Meta, refrescamos siempre el catalogo desde la cuenta real.
        WhatsAppPlantillasService.sincronizar_con_meta(
            db=db,
            empresa_id=empresa_id,
        )

        pendientes = (
            WhatsAppPlantillasService
            .obtener_pendientes_creacion_automatica(
                db=db,
                empresa_id=empresa_id,
            )
        )

        plantilla = next(
            (
                item
                for item in pendientes
                if item.tipo == tipo
            ),
            None,
        )

        if plantilla is None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=(
                    f"La plantilla {tipo} no está en estado "
                    "NO_CREADA."
                ),
            )

        contenido_pdf = generar_pdf_ejemplo_whatsapp()

        resultado = (
            WhatsAppPlantillasService
            .crear_plantilla_meta_con_documento(
                db=db,
                empresa_id=empresa_id,
                tipo=tipo,
                contenido_pdf=contenido_pdf,
                nombre_archivo="motordesk_whatsapp_ejemplo.pdf",
            )
        )

        return {
            "tipo": tipo,
            "estado": resultado["estado"],
            "meta_id": resultado["meta_id"],
            "mensaje": (
                "La plantilla ha sido enviada a Meta para revisión."
            ),
        }

    except HTTPException:
        raise

    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    except RuntimeError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(exc),
        ) from exc
