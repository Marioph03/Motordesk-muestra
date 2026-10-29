from pydantic import BaseModel

class UsuarioSimpleResponse(BaseModel):

    id: int

    nombre: str

    apellidos: str

    class Config:
        from_attributes = True
"""Proyección reducida de usuario para relaciones de agenda y órdenes."""
