from typing import Optional

from pydantic import (
    BaseModel,
    ConfigDict,
    EmailStr,
    Field
)


class ConfiguracionTallerBase(BaseModel):

    nombre_comercial: Optional[str] = Field(
        default=None,
        max_length=150
    )

    razon_social: Optional[str] = Field(
        default=None,
        max_length=150
    )

    nif_cif: Optional[str] = Field(
        default=None,
        max_length=20
    )

    telefono: Optional[str] = Field(
        default=None,
        max_length=30
    )

    email: Optional[EmailStr] = None

    web: Optional[str] = Field(
        default=None,
        max_length=200
    )

    direccion: Optional[str] = Field(
        default=None,
        max_length=250
    )

    codigo_postal: Optional[str] = Field(
        default=None,
        max_length=10
    )

    localidad: Optional[str] = Field(
        default=None,
        max_length=100
    )

    provincia: Optional[str] = Field(
        default=None,
        max_length=100
    )

    pais: Optional[str] = Field(
        default="España",
        max_length=100
    )


class ConfiguracionTallerUpdate(
    ConfiguracionTallerBase
):
    pass


class ConfiguracionTallerResponse(
    ConfiguracionTallerBase
):

    id: int

    logo_url: Optional[str] = None

    model_config = ConfigDict(
        from_attributes=True
    )
"""Contrato de identidad, contacto y logo corporativo del taller."""
