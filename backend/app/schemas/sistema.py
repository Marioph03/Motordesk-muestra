from pydantic import BaseModel


class EstadoServicioResponse(BaseModel):
    nombre: str
    estado: str
    detalle: str | None = None


class EstadoSistemaResponse(BaseModel):
    version: str
    backend: EstadoServicioResponse
    base_datos: EstadoServicioResponse
    whatsapp: EstadoServicioResponse
    verifactu: EstadoServicioResponse


class BackupInfoResponse(BaseModel):
    disponible: bool
    nombre_archivo: str | None = None
    fecha: str | None = None
    tamano_bytes: int | None = None


class RestablecerDatosRequest(BaseModel):
    confirmacion: str
"""Contratos de mantenimiento y copias de seguridad del sistema."""
