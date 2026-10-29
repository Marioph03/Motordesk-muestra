from datetime import datetime

from pydantic import BaseModel, ConfigDict


class CertificadoElectronicoResponse(BaseModel):
    id: int
    empresa_id: int

    nombre_archivo: str

    titular: str | None = None
    nif_titular: str | None = None
    emisor: str | None = None

    fecha_validez_desde: datetime | None = None
    fecha_caducidad: datetime | None = None

    activo: bool

    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(
        from_attributes=True
    )


class CertificadoElectronicoEstadoResponse(BaseModel):
    configurado: bool
    activo: bool = False

    nombre_archivo: str | None = None
    titular: str | None = None
    nif_titular: str | None = None
    emisor: str | None = None

    fecha_validez_desde: datetime | None = None
    fecha_caducidad: datetime | None = None

    caducado: bool = False