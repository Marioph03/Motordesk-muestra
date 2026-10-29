from datetime import datetime

from pydantic import BaseModel

from app.schemas.usuario_simple import UsuarioSimpleResponse


class ActividadCreate(BaseModel):

    empresa_id: int

    usuario_id: int

    modulo: str

    accion: str

    registro_id: int | None = None

    descripcion: str

    ip: str | None = None


class ActividadResponse(BaseModel):

    id: int

    empresa_id: int

    usuario_id: int

    modulo: str

    accion: str

    registro_id: int | None

    descripcion: str

    ip: str | None

    created_at: datetime

    usuario: UsuarioSimpleResponse

    class Config:
        from_attributes = True
"""Contrato de eventos mostrados en la auditoría funcional."""
