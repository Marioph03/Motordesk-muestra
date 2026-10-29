from pydantic import BaseModel, ConfigDict, Field

from app.schemas.permiso import PermisoResponse


class RolCreate(BaseModel):

    nombre: str
    descripcion: str | None = None
    activo: bool = True

    permisos_ids: list[int] = Field(
        default_factory=list
    )


class RolUpdate(BaseModel):

    nombre: str | None = None
    descripcion: str | None = None
    activo: bool | None = None

    permisos_ids: list[int] | None = None


class RolResponse(BaseModel):

    id: int
    nombre: str
    descripcion: str | None = None
    activo: bool

    permisos: list[PermisoResponse] = Field(
        default_factory=list
    )

    model_config = ConfigDict(
        from_attributes=True
    )
"""Contratos de creación y edición de roles con permisos asociados."""
