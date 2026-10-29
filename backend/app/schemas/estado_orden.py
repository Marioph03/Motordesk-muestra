from pydantic import BaseModel


class EstadoOrdenUpdate(BaseModel):
    estado: str
"""Contrato específico de transiciones de estado para órdenes."""
