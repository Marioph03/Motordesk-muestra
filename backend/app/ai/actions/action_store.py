import os
from datetime import datetime, timedelta, timezone
from threading import Lock

from app.ai.actions.action_models import (
    AccionPendiente,
    EstadoAccion
)


class ActionStore:

    def __init__(self):

        self._acciones: dict[
            str,
            AccionPendiente
        ] = {}

        self._lock = Lock()

    @staticmethod
    def _expirar_si_corresponde(
        accion: AccionPendiente
    ) -> None:
        """Evita confirmar una propuesta antigua tras cambios de contexto."""
        if accion.estado != EstadoAccion.PENDIENTE:
            return

        try:
            creada_en = datetime.fromisoformat(
                accion.creada_en.replace("Z", "+00:00")
            )
        except (AttributeError, ValueError):
            accion.estado = EstadoAccion.EXPIRADA
            return

        if creada_en.tzinfo is not None:
            creada_en = (
                creada_en.astimezone(timezone.utc)
                .replace(tzinfo=None)
            )

        try:
            minutos = int(
                os.getenv(
                    "MOTOR_AI_ACTION_TTL_MINUTES",
                    "15",
                )
            )
        except ValueError:
            minutos = 15

        if datetime.utcnow() >= creada_en + timedelta(
            minutes=max(1, minutos)
        ):
            accion.estado = EstadoAccion.EXPIRADA


    # =====================================================
    # GUARDAR
    # =====================================================

    def guardar(
        self,
        accion: AccionPendiente
    ) -> AccionPendiente:

        with self._lock:

            self._acciones[
                accion.id
            ] = accion

        return accion


    # =====================================================
    # OBTENER
    # =====================================================

    def obtener(
        self,
        accion_id: str
    ) -> AccionPendiente | None:

        with self._lock:

            accion = self._acciones.get(accion_id)
            if accion is not None:
                self._expirar_si_corresponde(accion)
            return accion


    # =====================================================
    # PENDIENTE DE UN USUARIO
    # =====================================================

    def obtener_pendiente_usuario(
        self,
        usuario_id: int
    ) -> AccionPendiente | None:

        with self._lock:

            pendientes = [

                accion

                for accion
                in self._acciones.values()

                if (
                    accion.usuario_id
                    == usuario_id

                    and

                    accion.estado
                    == EstadoAccion.PENDIENTE
                )
            ]


            for accion in pendientes:
                self._expirar_si_corresponde(accion)

            pendientes = [
                accion
                for accion in pendientes
                if accion.estado == EstadoAccion.PENDIENTE
            ]

            if not pendientes:
                return None


            return max(
                pendientes,
                key=lambda accion:
                    accion.creada_en
            )


    # =====================================================
    # ELIMINAR
    # =====================================================

    def eliminar(
        self,
        accion_id: str
    ) -> bool:

        with self._lock:

            if accion_id not in self._acciones:
                return False

            del self._acciones[
                accion_id
            ]

            return True


action_store = ActionStore()
"""Almacén temporal de acciones IA pendientes por usuario autenticado."""
