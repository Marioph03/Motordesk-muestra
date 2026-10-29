"""Contratos HTTP del vehículo y sus datos identificativos."""

from datetime import date
from typing import Optional

from pydantic import BaseModel, ConfigDict, field_validator


class VehiculoBase(BaseModel):
    cliente_id: int

    matricula: str
    bastidor: Optional[str] = None

    marca: str
    modelo: str
    version: Optional[str] = None

    anio: Optional[int] = None
    fecha_matriculacion: Optional[date] = None
    color: Optional[str] = None

    combustible: Optional[str] = None
    transmision: Optional[str] = None

    kilometros: Optional[int] = None

    observaciones: Optional[str] = None

    @field_validator("fecha_matriculacion", mode="before")
    @classmethod
    def fecha_matriculacion_vacia_es_nula(cls, valor):
        """Acepta el valor vacío que envía un input de fecha sin rellenar."""
        return None if valor == "" else valor


class VehiculoCreate(VehiculoBase):
    pass


class VehiculoUpdate(VehiculoBase):
    pass

class ClienteSimple(BaseModel):
    id: int
    nombre: str
    apellidos: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)
class VehiculoResponse(VehiculoBase):

    id: int
    codigo: Optional[str] = None

    cliente: ClienteSimple

    model_config = ConfigDict(from_attributes=True)
    
class VehiculoSelect(BaseModel):
    id: int
    descripcion: str
    cliente_id: int

    model_config = ConfigDict(
        from_attributes=True
    )
    
class VehiculoSimple(BaseModel):
    id: int
    codigo: Optional[str] = None
    matricula: str
    marca: str
    modelo: str

    model_config = {
        "from_attributes": True
    }
