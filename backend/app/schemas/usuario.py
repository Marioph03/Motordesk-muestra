"""Contratos de usuario expuestos por API, sin incluir secretos ni hashes."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field


class UsuarioBase(BaseModel):
    nombre: str
    apellidos: str
    email: EmailStr
    rol: str
    activo: bool = True


class UsuarioCreate(UsuarioBase):
    password: str


class UsuarioUpdate(BaseModel):
    nombre: Optional[str] = None
    apellidos: Optional[str] = None
    email: Optional[EmailStr] = None
    rol: Optional[str] = None
    activo: Optional[bool] = None
    password: Optional[str] = None


class UsuarioResponse(BaseModel):
    id: int
    nombre: str
    apellidos: str
    # La validación de formato se mantiene en UsuarioCreate y UsuarioUpdate.
    # En respuestas usamos str para que una cuenta heredada con un email antiguo
    # no convierta una consulta de Personal en un error 500.
    email: str
    rol: str
    activo: bool = True
    avatar_url: str | None = None
    ultimo_acceso: datetime | None
    created_at: datetime
    updated_at: datetime
    permisos: list[str] = []

    model_config = {
        "from_attributes": True
    }
    
class ResetPasswordRequest(BaseModel):
    password: str = Field(
        ...,
        min_length=6,
        max_length=100
    )
