from datetime import datetime

from pydantic import BaseModel


class BloquePlanificacionResponse(BaseModel):
    tipo: str
    inicio: datetime
    fin: datetime
    referencia: str
    id: int


class UsuarioPlanificacionResponse(BaseModel):
    usuario_id: int
    nombre: str
    apellidos: str
    rol: str
    bloques: list[BloquePlanificacionResponse]
"""Contrato de planificación semanal del equipo y sus asignaciones."""
