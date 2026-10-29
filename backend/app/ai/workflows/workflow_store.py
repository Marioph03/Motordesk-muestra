"""Almacén temporal en memoria de workflows IA para el entorno actual."""

import os
from datetime import datetime, timedelta, timezone
from threading import Lock

from app.ai.workflows.workflow_models import (
    EstadoWorkflow,
    WorkflowPendiente
)


class WorkflowStore:
    """Protege el acceso concurrente a workflows; debe migrar a persistencia en producción."""


    def __init__(self):

        self._workflows: dict[
            str,
            WorkflowPendiente
        ] = {}

        self._lock = Lock()

    @staticmethod
    def _expirar_si_corresponde(workflow: WorkflowPendiente) -> None:
        """Marca propuestas vencidas para evitar ejecutar datos antiguos."""

        if workflow.estado != EstadoWorkflow.PENDIENTE:
            return
        try:
            creada_en = datetime.fromisoformat(
                workflow.creada_en.replace("Z", "+00:00")
            )
        except (AttributeError, ValueError):
            workflow.estado = EstadoWorkflow.EXPIRADO
            return
        if creada_en.tzinfo is not None:
            creada_en = creada_en.astimezone(timezone.utc).replace(tzinfo=None)
        try:
            minutos = int(os.getenv("MOTOR_AI_WORKFLOW_TTL_MINUTES", "15"))
        except ValueError:
            minutos = 15
        if datetime.utcnow() >= creada_en + timedelta(minutes=max(1, minutos)):
            workflow.estado = EstadoWorkflow.EXPIRADO


    def guardar(
        self,
        workflow: WorkflowPendiente
    ) -> WorkflowPendiente:

        with self._lock:

            self._workflows[
                workflow.id
            ] = workflow

        return workflow


    def obtener(
        self,
        workflow_id: str
    ) -> WorkflowPendiente | None:

        with self._lock:

            workflow = self._workflows.get(workflow_id)
            if workflow is not None:
                self._expirar_si_corresponde(workflow)
            return workflow


    def obtener_pendiente_usuario(
        self,
        usuario_id: int
    ) -> WorkflowPendiente | None:

        with self._lock:

            workflows = [

                workflow

                for workflow
                in self._workflows.values()

                if (
                    workflow.usuario_id
                    == usuario_id

                    and

                    workflow.estado
                    == EstadoWorkflow.PENDIENTE
                )
            ]

            for workflow in workflows:
                self._expirar_si_corresponde(workflow)

            workflows = [
                workflow
                for workflow in workflows
                if workflow.estado == EstadoWorkflow.PENDIENTE
            ]


            if not workflows:

                return None


            return max(
                workflows,
                key=lambda item:
                    item.creada_en
            )


workflow_store = WorkflowStore()
