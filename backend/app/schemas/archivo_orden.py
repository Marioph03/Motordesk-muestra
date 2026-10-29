from datetime import datetime

from pydantic import BaseModel


class ArchivoOrdenResponse(BaseModel):

    id: int
    orden_id: int

    nombre_original: str
    nombre_archivo: str

    tipo_mime: str
    categoria: str

    tamano: int

    created_at: datetime

    model_config = {
        "from_attributes": True
    }
"""Representación API de archivos adjuntos asociados a órdenes."""
