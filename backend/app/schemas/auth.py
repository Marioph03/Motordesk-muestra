from pydantic import BaseModel, EmailStr, Field

from app.schemas.usuario import UsuarioResponse


class LoginRequest(BaseModel):
    email: str
    password: str


class RegisterRequest(BaseModel):
    nombre: str = Field(min_length=1, max_length=100)
    apellidos: str = Field(min_length=1, max_length=150)
    email: EmailStr
    password: str = Field(min_length=6, max_length=100)
    
class Token(BaseModel):
    access_token: str
    token_type: str
    usuario: UsuarioResponse
"""Contratos públicos de registro, login y respuesta de sesión JWT."""
