"""Auditoría de MotorDesk AI con filtrado preventivo de información sensible."""

from enum import Enum
from typing import Any

from sqlalchemy.orm import Session

from app.models.ai_auditoria import (
    AIAuditoria
)


CAMPOS_SENSIBLES = {
    "password",
    "contraseña",
    "token",
    "access_token",
    "refresh_token",
    "api_key",
    "authorization"
}


def sanitizar_auditoria(
    valor: Any
) -> Any:
    """Elimina secretos de datos estructurados antes de guardarlos."""

    if isinstance(valor, dict):
        limpio = {}

        for clave, contenido in valor.items():
            if str(clave).lower() in CAMPOS_SENSIBLES:
                limpio[clave] = "[OCULTO]"
            else:
                limpio[clave] = sanitizar_auditoria(contenido)

        return limpio

    if isinstance(valor, list):
        return [
            sanitizar_auditoria(item)
            for item in valor
        ]

    return valor


class TipoEventoAI(str, Enum):
    """Eventos auditables del chat, las herramientas y las acciones IA."""


    CHAT = "CHAT"

    TOOL_CALL = "TOOL_CALL"
    TOOL_OK = "TOOL_OK"
    TOOL_ERROR = "TOOL_ERROR"

    ACTION_PROPUESTA = "ACTION_PROPUESTA"
    ACTION_CONFIRMADA = "ACTION_CONFIRMADA"
    ACTION_CANCELADA = "ACTION_CANCELADA"

    WORKFLOW_PROPUESTO = "WORKFLOW_PROPUESTO"
    WORKFLOW_CONFIRMADO = "WORKFLOW_CONFIRMADO"
    WORKFLOW_CANCELADO = "WORKFLOW_CANCELADO"

    PERMISO_DENEGADO = "PERMISO_DENEGADO"

    ERROR = "ERROR"


def registrar_evento_ai(
    db: Session,
    usuario_id: int,
    tipo_evento: TipoEventoAI | str,
    recurso: str | None = None,
    referencia_id: str | None = None,
    descripcion: str | None = None,
    datos: dict[str, Any] | None = None,
    resultado: dict[str, Any] | None = None,
    exitoso: bool = True,
    error: str | None = None,
    commit: bool = True
) -> AIAuditoria:
    """Persiste un evento IA saneado; nunca debe almacenar claves ni contraseñas."""


    evento = AIAuditoria(

        usuario_id=
            usuario_id,

        tipo_evento=(
            tipo_evento.value
            if isinstance(
                tipo_evento,
                TipoEventoAI
            )
            else str(tipo_evento)
        ),

        recurso=
            recurso,

        referencia_id=
            referencia_id,

        descripcion=
            descripcion,

        datos=
            sanitizar_auditoria(datos),

        resultado=
            sanitizar_auditoria(resultado),

        exitoso=
            exitoso,

        error=
            error
    )

    db.add(evento)

    if commit:

        db.commit()
        db.refresh(evento)

    else:

        db.flush()

    return evento

