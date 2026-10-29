from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, Field, field_validator


class ManoObraBase(BaseModel):
    concepto: str
    codigo_mano_obra: Optional[str] = Field(default=None, max_length=100)
    horas: Decimal
    precio_hora: Decimal
    descuento_porcentaje: Decimal = Decimal("0")
    cubierto_garantia: bool = False

    @field_validator("codigo_mano_obra", mode="before")
    @classmethod
    def codigo_vacio_es_nulo(cls, valor):
        """Evita persistir cadenas vacías como códigos de garantía."""
        if valor is None:
            return None
        codigo = str(valor).strip()
        return codigo.upper() or None


class ManoObraCreate(ManoObraBase):
    pass


class ManoObraUpdate(BaseModel):
    concepto: Optional[str] = None
    codigo_mano_obra: Optional[str] = Field(default=None, max_length=100)
    horas: Optional[Decimal] = None
    precio_hora: Optional[Decimal] = None
    descuento_porcentaje: Optional[Decimal] = None
    cubierto_garantia: Optional[bool] = None

    @field_validator("codigo_mano_obra", mode="before")
    @classmethod
    def codigo_vacio_es_nulo(cls, valor):
        if valor is None:
            return None
        codigo = str(valor).strip()
        return codigo.upper() or None


class ManoObraResponse(ManoObraBase):
    id: int
    orden_id: int
    total: Decimal

    model_config = {
        "from_attributes": True
    }
"""Contratos de alta y edición de mano de obra de una orden."""
