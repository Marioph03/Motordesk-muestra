from pydantic import BaseModel


class DisponibilidadPersonalResponse(BaseModel):
    usuario_id: int
    nombre: str
    apellidos: str
    rol: str
    disponible: bool
    motivo: str | None = None
    conflicto_tipo: str | None = None
    conflicto_id: int | None = None
    conflicto_referencia: str | None = None
"""Respuesta de disponibilidad de cada usuario para un rango de tiempo."""
