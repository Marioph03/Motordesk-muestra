from datetime import datetime
from uuid import uuid4

from app.ai.actions.action_models import (
    AccionPendiente,
    EstadoAccion,
    TipoAccion
)

from app.ai.actions.action_store import (
    action_store
)


# =========================================================
# CREAR PROPUESTA
# =========================================================

def crear_propuesta_accion(
    tipo: TipoAccion,
    datos: dict,
    resumen: str,
    usuario_id: int
) -> AccionPendiente:

    ahora = datetime.utcnow().isoformat()


    accion = AccionPendiente(

        id=str(
            uuid4()
        ),

        tipo=tipo,

        estado=EstadoAccion.PENDIENTE,

        datos=datos,

        resumen=resumen,

        usuario_id=usuario_id,

        creada_en=ahora
    )


    return action_store.guardar(
        accion
    )


# =========================================================
# OBTENER ACCIÓN
# =========================================================

def obtener_accion(
    accion_id: str
) -> AccionPendiente | None:

    return action_store.obtener(
        accion_id
    )


# =========================================================
# OBTENER PENDIENTE
# =========================================================

def obtener_accion_pendiente(
    usuario_id: int
) -> AccionPendiente | None:

    return (
        action_store
        .obtener_pendiente_usuario(
            usuario_id
        )
    )


# =========================================================
# CANCELAR
# =========================================================

def cancelar_accion(
    accion_id: str,
    usuario_id: int
) -> AccionPendiente:

    accion = action_store.obtener(
        accion_id
    )


    if not accion:

        raise ValueError(
            "La acción pendiente no existe."
        )


    if accion.usuario_id != usuario_id:

        raise PermissionError(
            "La acción no pertenece al usuario actual."
        )


    if (
        accion.estado
        != EstadoAccion.PENDIENTE
    ):

        raise ValueError(
            "La acción ya no está pendiente."
        )


    accion.estado = (
        EstadoAccion.CANCELADA
    )


    action_store.guardar(
        accion
    )


    return accion
"""Confirmación y ejecución segura de acciones IA de un solo efecto."""
