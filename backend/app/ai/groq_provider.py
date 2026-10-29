"""Adaptador Groq: límites, errores normalizados y llamada al modelo configurado."""

import os
from typing import Any

from groq import Groq

from app.ai.ai_provider import AIProvider


class AIProviderError(Exception):
    pass


class AIProviderBusyError(AIProviderError):
    pass


class AIProviderRateLimitError(AIProviderError):
    pass


class AIProviderToolUseError(AIProviderError):
    pass


class GroqProvider(AIProvider):
    """Proveedor LLM de MotorDesk AI; no contiene reglas ni acceso directo a datos."""


    def __init__(self):

        api_key = os.getenv(
            "GROQ_API_KEY"
        )

        self.model = os.getenv(
            "GROQ_MODEL",
            "openai/gpt-oss-20b"
        )

        self.max_completion_tokens = int(
            os.getenv(
                "GROQ_MAX_COMPLETION_TOKENS",
                "400"
            )
        )

        self.reasoning_effort = os.getenv(
            "GROQ_REASONING_EFFORT",
            "low"
        )

        self.timeout_seconds = float(
            os.getenv(
                "GROQ_TIMEOUT_SECONDS",
                "15"
            )
        )

        # Un pico puntual de 429/503 no debe interrumpir el chat. Groq aplica
        # una espera compatible con Retry-After para estos reintentos.
        self.max_retries = int(
            os.getenv(
                "GROQ_MAX_RETRIES",
                "2"
            )
        )

        if not api_key:
            raise AIProviderError(
                "GROQ_API_KEY no está configurada."
            )

        self.client = Groq(
            api_key=api_key,
            timeout=self.timeout_seconds,
            max_retries=max(0, min(self.max_retries, 3))
        )


    def chat(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None = None
    ) -> Any:

        try:

            parametros = {
                "model": self.model,
                "messages": messages,
                "temperature": 0.1,
                "max_completion_tokens": (
                    self.max_completion_tokens
                ),
                "reasoning_effort": (
                    self.reasoning_effort
                )
            }


            if tools:

                parametros["tools"] = tools

                parametros[
                    "tool_choice"
                ] = "auto"


            return (
                self.client
                .chat
                .completions
                .create(
                    **parametros
                )
            )


        except Exception as error:

            status_code = getattr(
                error,
                "status_code",
                None
            )

            # Conserva información útil en el log del backend para diagnosticar
            # límites del proveedor sin exponer secretos al cliente.
            print(
                "Error Groq MotorDesk AI:",
                f"status={status_code}",
                repr(error)
            )


            if status_code in (413, 429):

                raise AIProviderRateLimitError(
                    "La consulta supera temporalmente el límite de capacidad de MotorDesk AI."
                ) from error


            if status_code == 400 and "tool_use_failed" in str(error):
                raise AIProviderToolUseError(
                    "El modelo intentó usar una herramienta no habilitada."
                ) from error


            if status_code == 503:

                raise AIProviderBusyError(
                    "MotorDesk AI está "
                    "temporalmente ocupado."
                ) from error


            raise AIProviderError(
                "No se ha podido obtener "
                "una respuesta de MotorDesk AI."
            ) from error
