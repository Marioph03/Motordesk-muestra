from datetime import datetime
from uuid import uuid4

from app.ai.workflows.workflow_models import (
    EstadoPasoWorkflow,
    EstadoWorkflow,
    PasoWorkflow,
    TipoPasoWorkflow,
    TipoWorkflow,
    WorkflowPendiente
)

from app.ai.workflows.workflow_store import (
    workflow_store
)


# =========================================================
# CREAR WORKFLOW
# =========================================================

def crear_workflow(
    tipo: TipoWorkflow,
    usuario_id: int,
    resumen: str,
    pasos: list[PasoWorkflow]
) -> WorkflowPendiente:

    anterior = (
        workflow_store
        .obtener_pendiente_usuario(
            usuario_id
        )
    )


    if anterior:

        anterior.estado = (
            EstadoWorkflow.CANCELADO
        )

        workflow_store.guardar(
            anterior
        )


    workflow = WorkflowPendiente(

        id=str(
            uuid4()
        ),

        tipo=tipo,

        estado=
            EstadoWorkflow.PENDIENTE,

        usuario_id=
            usuario_id,

        resumen=
            resumen,

        pasos=
            pasos,

        creada_en=
            datetime.utcnow()
            .isoformat()

    )


    return workflow_store.guardar(
        workflow
    )


# =========================================================
# CANCELAR
# =========================================================

def cancelar_workflow(
    workflow_id: str,
    usuario_id: int
) -> WorkflowPendiente:

    workflow = workflow_store.obtener(
        workflow_id
    )


    if workflow is None:

        raise ValueError(
            "El workflow no existe."
        )


    if workflow.usuario_id != usuario_id:

        raise PermissionError(
            "El workflow pertenece a otro usuario."
        )


    if (
        workflow.estado
        != EstadoWorkflow.PENDIENTE
    ):

        raise ValueError(
            "El workflow ya no está pendiente."
        )


    workflow.estado = (
        EstadoWorkflow.CANCELADO
    )


    for paso in workflow.pasos:

        if (
            paso.estado
            == EstadoPasoWorkflow.PENDIENTE
        ):

            paso.estado = (
                EstadoPasoWorkflow.OMITIDO
            )


    workflow_store.guardar(
        workflow
    )


    return workflow
"""Operaciones de consulta y cancelación de workflows IA pendientes."""
