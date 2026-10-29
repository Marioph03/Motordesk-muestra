from pydantic import BaseModel, ConfigDict


class PermisoResponse(BaseModel):

    id: int
    codigo: str
    nombre: str
    modulo: str
    descripcion: str | None = None

    model_config = ConfigDict(
        from_attributes=True
    )
"""Contrato de permiso y sus atributos visibles en administración de roles."""
