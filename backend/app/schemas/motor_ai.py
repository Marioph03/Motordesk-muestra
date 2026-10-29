from typing import Any

from pydantic import BaseModel, Field


class MotorAIChatRequest(BaseModel):

    mensaje: str = Field(
        ...,
        min_length=1,
        max_length=4000
    )


class MotorAIAccionResponse(BaseModel):

    id: str
    tipo: str
    resumen: str
    datos: dict[str, Any]


class MotorAIWorkflowPasoResponse(BaseModel):

    orden: int
    tipo: str
    resumen: str


class MotorAIWorkflowResponse(BaseModel):

    id: str
    tipo: str
    resumen: str
    pasos: list[MotorAIWorkflowPasoResponse]


class MotorAIChatResponse(BaseModel):

    respuesta: str

    herramientas_usadas: list[str] = []

    accion_pendiente: MotorAIAccionResponse | None = None

    workflow_pendiente: MotorAIWorkflowResponse | None = None


class MotorAIAccionResultadoResponse(BaseModel):

    ok: bool
    mensaje: str
    resultado: dict[str, Any] | None = None
"""Contrato del chat IA y propuestas de acciones o workflows confirmables."""
