from pydantic import (
    BaseModel,
    Field
)


class CambiarPasswordRequest(BaseModel):

    password_actual: str

    password_nueva: str = Field(
        min_length=8,
        max_length=128
    )


class SeguridadUsuarioResponse(BaseModel):

    id: int

    nombre: str
    email: str
    rol: str

    ultimo_acceso: str | None = None
"""Contrato de seguridad de perfil y cambio de contraseña autenticado."""
