"""Contratos HTTP para crear, editar y devolver clientes."""

from pydantic import BaseModel, ConfigDict
from typing import Optional


class ClienteBase(BaseModel):
    nombre: str
    apellidos: Optional[str] = None
    dni: Optional[str] = None
    telefono: Optional[str] = None
    email: Optional[str] = None
    direccion: Optional[str] = None
    ciudad: Optional[str] = None
    provincia: Optional[str] = None
    codigo_postal: Optional[str] = None
    observaciones: Optional[str] = None


class ClienteCreate(ClienteBase):
    pass


class ClienteUpdate(ClienteBase):
    activo: Optional[bool] = None


class ClienteResponse(ClienteBase):
    id: int
    codigo: Optional[str] = None
    activo: bool

    model_config = ConfigDict(from_attributes=True)
    
class ClienteSelect(BaseModel):
    """Datos mínimos, pero suficientes, para identificar un cliente en selectores."""
    id: int
    codigo: Optional[str] = None
    nombre: str
    apellidos: Optional[str] = None
    dni: Optional[str] = None

    model_config = ConfigDict(
        from_attributes=True
    )
