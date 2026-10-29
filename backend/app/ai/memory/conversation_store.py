from datetime import datetime
from threading import Lock

from app.ai.memory.memory_models import (
    ContextoConversacion,
    MensajeMemoria
)


MAX_MENSAJES = 12


class ConversationStore:

    def __init__(self):

        self._conversaciones: dict[
            int,
            ContextoConversacion
        ] = {}

        self._lock = Lock()


    # =====================================================
    # OBTENER
    # =====================================================

    def obtener(
        self,
        usuario_id: int
    ) -> ContextoConversacion:

        with self._lock:

            contexto = (
                self._conversaciones.get(
                    usuario_id
                )
            )


            if contexto is None:

                contexto = ContextoConversacion(
                    usuario_id=usuario_id
                )

                self._conversaciones[
                    usuario_id
                ] = contexto


            return contexto


    # =====================================================
    # AÑADIR MENSAJE
    # =====================================================

    def agregar_mensaje(
        self,
        usuario_id: int,
        rol: str,
        contenido: str
    ) -> None:

        with self._lock:

            contexto = (
                self._conversaciones.get(
                    usuario_id
                )
            )


            if contexto is None:

                contexto = ContextoConversacion(
                    usuario_id=usuario_id
                )

                self._conversaciones[
                    usuario_id
                ] = contexto


            contexto.mensajes.append(

                MensajeMemoria(
                    rol=rol,
                    contenido=contenido
                )

            )


            # Solo conservamos los últimos
            # mensajes necesarios.

            contexto.mensajes = (
                contexto.mensajes[
                    -MAX_MENSAJES:
                ]
            )


            contexto.actualizado_en = (
                datetime.utcnow()
                .isoformat()
            )


    # =====================================================
    # ACTUALIZAR CONTEXTO
    # =====================================================

    def actualizar_contexto(
        self,
        usuario_id: int,
        cliente_id: int | None = None,
        vehiculo_id: int | None = None,
        orden_id: int | None = None,
        factura_id: int | None = None,
        cita_id: int | None = None,
        matricula: str | None = None
    ) -> None:

        with self._lock:

            contexto = (
                self._conversaciones.get(
                    usuario_id
                )
            )


            if contexto is None:

                contexto = ContextoConversacion(
                    usuario_id=usuario_id
                )

                self._conversaciones[
                    usuario_id
                ] = contexto


            if cliente_id is not None:
                contexto.cliente_id = cliente_id

            if vehiculo_id is not None:
                contexto.vehiculo_id = vehiculo_id

            if orden_id is not None:
                contexto.orden_id = orden_id

            if factura_id is not None:
                contexto.factura_id = factura_id

            if cita_id is not None:
                contexto.cita_id = cita_id

            if matricula is not None:

                contexto.matricula = (
                    matricula
                    .replace(" ", "")
                    .replace("-", "")
                    .upper()
                )


            contexto.actualizado_en = (
                datetime.utcnow()
                .isoformat()
            )


    # =====================================================
    # LIMPIAR
    # =====================================================

    def limpiar(
        self,
        usuario_id: int
    ) -> None:

        with self._lock:

            self._conversaciones.pop(
                usuario_id,
                None
            )


conversation_store = ConversationStore()
"""Memoria temporal acotada de conversación por usuario para MotorDesk AI."""
