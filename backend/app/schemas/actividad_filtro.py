from datetime import date

from pydantic import BaseModel


class ActividadFiltro(BaseModel):

    usuario_id: int | None = None

    modulo: str | None = None

    accion: str | None = None

    fecha_desde: date | None = None

    fecha_hasta: date | None = None
"""Filtros admitidos para consultar actividad y auditoría paginada."""
