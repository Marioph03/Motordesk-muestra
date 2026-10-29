"""API autenticada de MotorDesk AI y confirmación controlada de acciones."""

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status
)

from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.database.database import get_db
from app.core.security import get_current_user
from app.models.usuario import Usuario

from app.ai.motor_ai_service import (
    MotorAIService
)

from app.ai.groq_provider import (
    AIProviderBusyError,
    AIProviderError,
    AIProviderRateLimitError,
)

from app.schemas.motor_ai import (
    MotorAIChatRequest,
    MotorAIChatResponse,
    MotorAIAccionResultadoResponse,
)
from app.ai.actions.action_models import EstadoAccion, TipoAccion
from app.ai.actions.action_store import action_store
from app.ai.actions.cita_action import ejecutar_crear_cita
from app.ai.actions.orden_action import ejecutar_crear_orden
from app.ai.actions.cliente_action import ejecutar_crear_cliente
from app.ai.actions.vehiculo_action import ejecutar_crear_vehiculo
from app.ai.workflows.workflow_models import EstadoWorkflow, TipoWorkflow
from app.ai.workflows.workflow_store import workflow_store
from app.ai.workflows.workflow_service import cancelar_workflow
from app.ai.workflows.alta_cliente_vehiculo_cita import (
    ejecutar_alta_cliente_vehiculo_cita,
)
from app.ai.workflows.alta_cliente_vehiculo_orden import (
    ejecutar_alta_cliente_vehiculo_orden,
)
from app.ai.memory.context_extractor import extraer_contexto
from app.ai.memory.conversation_store import conversation_store
from app.ai.security.ai_permissions import (
    AIPermissionError,
    comprobar_permiso_action,
    comprobar_permiso_tipo_workflow,
)
from app.ai.audit.audit_service import TipoEventoAI, registrar_evento_ai


router = APIRouter(
    prefix="/ai",
    tags=["MotorDesk AI"]
)


@router.post(
    "/chat",
    response_model=MotorAIChatResponse
)
def chat_motor_ai(
    datos: MotorAIChatRequest,
    db: Session = Depends(get_db),
    usuario_actual: Usuario = Depends(
        get_current_user
    )
):

    try:

        service = MotorAIService()

        resultado = service.chat(
            db=db,
            mensaje=datos.mensaje,
            usuario=usuario_actual,
        )

        accion = action_store.obtener_pendiente_usuario(usuario_actual.id)
        workflow = workflow_store.obtener_pendiente_usuario(usuario_actual.id)

        return MotorAIChatResponse(
            respuesta=resultado["respuesta"],
            herramientas_usadas=resultado[
                "herramientas_usadas"
            ],
            accion_pendiente=(
                {
                    "id": accion.id,
                    "tipo": accion.tipo.value,
                    "resumen": accion.resumen,
                    "datos": accion.datos,
                }
                if accion and accion.estado == EstadoAccion.PENDIENTE
                else None
            ),
            workflow_pendiente=(
                {
                    "id": workflow.id,
                    "tipo": workflow.tipo.value,
                    "resumen": workflow.resumen,
                    "pasos": [
                        {
                            "orden": paso.orden,
                            "tipo": paso.tipo.value,
                            "resumen": paso.resumen,
                        }
                        for paso in workflow.pasos
                    ],
                }
                if workflow and workflow.estado == EstadoWorkflow.PENDIENTE
                else None
            ),
        )


    except ValueError as error:

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error)
        )


    except AIProviderRateLimitError as error:

        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=str(error),
        ) from error


    except AIProviderBusyError:

        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=(
                "MotorDesk AI está temporalmente "
                "ocupado. Inténtalo de nuevo "
                "en unos segundos."
            )
        )


    except AIProviderError as error:

        print(
            "Error proveedor MotorDesk AI:",
            repr(error)
        )

        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=(
                "MotorDesk AI no está disponible "
                "en este momento."
            )
        )


    except Exception as error:

        print(
            "Error inesperado MotorDesk AI:",
            repr(error)
        )

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=(
                "Se ha producido un error "
                "procesando la solicitud."
            )
        )


@router.delete(
    "/conversation",
)
def limpiar_conversacion_motor_ai(
    usuario_actual: Usuario = Depends(get_current_user),
):
    conversation_store.limpiar(usuario_actual.id)
    return {"ok": True, "mensaje": "Conversación reiniciada."}


@router.post(
    "/actions/{accion_id}/confirmar",
    response_model=MotorAIAccionResultadoResponse,
)
def confirmar_accion_motor_ai(
    accion_id: str,
    db: Session = Depends(get_db),
    usuario_actual: Usuario = Depends(get_current_user),
):
    accion = action_store.obtener(accion_id)
    if accion is None:
        raise HTTPException(status_code=404, detail="La acción pendiente ya no existe.")
    if accion.usuario_id != usuario_actual.id:
        raise HTTPException(status_code=403, detail="No puedes confirmar esta acción.")
    if accion.estado == EstadoAccion.EXPIRADA:
        raise HTTPException(
            status_code=409,
            detail="La acción pendiente ha caducado. Vuelve a solicitarla.",
        )
    if accion.estado != EstadoAccion.PENDIENTE:
        raise HTTPException(status_code=409, detail="La acción ya no está pendiente.")
    try:
        comprobar_permiso_action(db, usuario_actual, accion.tipo)

        if accion.tipo == TipoAccion.CREAR_CITA:
            resultado = ejecutar_crear_cita(
                db=db,
                accion=accion,
                usuario_id=usuario_actual.id,
            )
            resultado_final = resultado.get("cita")
        elif accion.tipo == TipoAccion.CREAR_ORDEN:
            resultado = ejecutar_crear_orden(
                db=db,
                accion=accion,
                usuario_id=usuario_actual.id,
            )
            resultado_final = resultado.get("orden")
        elif accion.tipo == TipoAccion.CREAR_CLIENTE:
            resultado = ejecutar_crear_cliente(
                db=db,
                accion=accion,
                usuario_id=usuario_actual.id,
            )
            resultado_final = resultado.get("cliente")
        elif accion.tipo == TipoAccion.CREAR_VEHICULO:
            resultado = ejecutar_crear_vehiculo(
                db=db,
                accion=accion,
                usuario_id=usuario_actual.id,
            )
            resultado_final = resultado.get("vehiculo")
        else:
            raise ValueError("Tipo de acción no soportado.")

        contexto_extraido = extraer_contexto(resultado_final)
        if contexto_extraido:
            conversation_store.actualizar_contexto(
                usuario_id=usuario_actual.id,
                **contexto_extraido,
            )

        registrar_evento_ai(
            db=db,
            usuario_id=usuario_actual.id,
            tipo_evento=TipoEventoAI.ACTION_CONFIRMADA,
            recurso=accion.tipo.value,
            referencia_id=accion.id,
            descripcion="El usuario confirmó la acción propuesta por MotorDesk AI.",
            resultado=resultado_final,
        )

        return {
            "ok": True,
            "mensaje": resultado["mensaje"],
            "resultado": resultado_final,
        }
    except AIPermissionError as error:
        raise HTTPException(status_code=403, detail=str(error)) from error
    except PermissionError as error:
        raise HTTPException(status_code=403, detail=str(error)) from error
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    except IntegrityError as error:
        raise HTTPException(
            status_code=409,
            detail=(
                "No se ha podido completar el workflow porque otro registro "
                "con los mismos datos ya existe."
            ),
        ) from error


@router.post(
    "/workflows/{workflow_id}/confirmar",
    response_model=MotorAIAccionResultadoResponse,
)
def confirmar_workflow_motor_ai(
    workflow_id: str,
    db: Session = Depends(get_db),
    usuario_actual: Usuario = Depends(get_current_user),
):
    workflow = workflow_store.obtener(workflow_id)
    if workflow is None:
        raise HTTPException(status_code=404, detail="El workflow pendiente ya no existe.")
    if workflow.usuario_id != usuario_actual.id:
        raise HTTPException(status_code=403, detail="No puedes confirmar este workflow.")
    if workflow.estado == EstadoWorkflow.EXPIRADO:
        raise HTTPException(status_code=409, detail="El workflow pendiente ha caducado.")
    if workflow.estado != EstadoWorkflow.PENDIENTE:
        raise HTTPException(status_code=409, detail="El workflow ya no está pendiente.")
    try:
        comprobar_permiso_tipo_workflow(db, usuario_actual, workflow.tipo)

        if workflow.tipo == TipoWorkflow.ALTA_CLIENTE_VEHICULO_CITA:
            resultado = ejecutar_alta_cliente_vehiculo_cita(
                db=db,
                workflow=workflow,
                usuario_id=usuario_actual.id,
            )
        elif workflow.tipo == TipoWorkflow.ALTA_CLIENTE_VEHICULO_ORDEN:
            resultado = ejecutar_alta_cliente_vehiculo_orden(
                db=db,
                workflow=workflow,
                usuario_id=usuario_actual.id,
            )
        else:
            raise ValueError("Tipo de workflow no soportado.")

        contexto_extraido = extraer_contexto(resultado.get("resultado"))
        if contexto_extraido:
            conversation_store.actualizar_contexto(
                usuario_id=usuario_actual.id,
                **contexto_extraido,
            )
        registrar_evento_ai(
            db=db,
            usuario_id=usuario_actual.id,
            tipo_evento=TipoEventoAI.WORKFLOW_CONFIRMADO,
            recurso=workflow.tipo.value,
            referencia_id=workflow.id,
            descripcion="Workflow confirmado y ejecutado correctamente.",
            resultado=workflow.resultado,
        )
        return resultado
    except AIPermissionError as error:
        raise HTTPException(status_code=403, detail=str(error)) from error
    except PermissionError as error:
        raise HTTPException(status_code=403, detail=str(error)) from error
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error

    except IntegrityError as error:
        raise HTTPException(
            status_code=409,
            detail=(
                "No se ha podido completar el workflow porque otro registro "
                "con los mismos datos ya existe."
            ),
        ) from error


@router.post(
    "/workflows/{workflow_id}/cancelar",
    response_model=MotorAIAccionResultadoResponse,
)
def cancelar_workflow_motor_ai(
    workflow_id: str,
    db: Session = Depends(get_db),
    usuario_actual: Usuario = Depends(get_current_user),
):
    workflow = workflow_store.obtener(workflow_id)
    if workflow is None:
        raise HTTPException(status_code=404, detail="Workflow no encontrado.")
    if workflow.usuario_id != usuario_actual.id:
        raise HTTPException(status_code=403, detail="No puedes cancelar este workflow.")
    if workflow.estado == EstadoWorkflow.EXPIRADO:
        raise HTTPException(status_code=409, detail="El workflow pendiente ha caducado.")
    try:
        cancelar_workflow(workflow_id, usuario_actual.id)
        registrar_evento_ai(
            db=db,
            usuario_id=usuario_actual.id,
            tipo_evento=TipoEventoAI.WORKFLOW_CANCELADO,
            recurso=workflow.tipo.value,
            referencia_id=workflow.id,
            descripcion="El usuario canceló el workflow propuesto por MotorDesk AI.",
        )
        return {"ok": True, "mensaje": "Workflow cancelado.", "resultado": None}
    except PermissionError as error:
        raise HTTPException(status_code=403, detail=str(error)) from error
    except ValueError as error:
        raise HTTPException(status_code=409, detail=str(error)) from error


@router.post(
    "/actions/{accion_id}/cancelar",
    response_model=MotorAIAccionResultadoResponse,
)
def cancelar_accion_motor_ai(
    accion_id: str,
    db: Session = Depends(get_db),
    usuario_actual: Usuario = Depends(get_current_user),
):
    accion = action_store.obtener(accion_id)
    if accion is None:
        raise HTTPException(status_code=404, detail="Acción no encontrada.")
    if accion.usuario_id != usuario_actual.id:
        raise HTTPException(status_code=403, detail="No puedes cancelar esta acción.")
    if accion.estado == EstadoAccion.EXPIRADA:
        raise HTTPException(
            status_code=409,
            detail="La acción pendiente ha caducado.",
        )
    if accion.estado != EstadoAccion.PENDIENTE:
        raise HTTPException(status_code=409, detail="La acción ya no está pendiente.")
    accion.estado = EstadoAccion.CANCELADA
    action_store.guardar(accion)
    registrar_evento_ai(
        db=db,
        usuario_id=usuario_actual.id,
        tipo_evento=TipoEventoAI.ACTION_CANCELADA,
        recurso=accion.tipo.value,
        referencia_id=accion.id,
        descripcion="El usuario canceló la acción propuesta por MotorDesk AI.",
    )
    return {"ok": True, "mensaje": "Acción cancelada.", "resultado": None}
