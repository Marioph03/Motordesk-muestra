from datetime import date

from pydantic import (
    BaseModel,
    ConfigDict,
    Field
)


class ConfiguracionAgendaUpdate(BaseModel):

    duracion_cita_minutos: int = Field(
        ge=5,
        le=480
    )

    lunes_activo: bool
    lunes_inicio: str
    lunes_fin: str

    martes_activo: bool
    martes_inicio: str
    martes_fin: str

    miercoles_activo: bool
    miercoles_inicio: str
    miercoles_fin: str

    jueves_activo: bool
    jueves_inicio: str
    jueves_fin: str

    viernes_activo: bool
    viernes_inicio: str
    viernes_fin: str

    sabado_activo: bool
    sabado_inicio: str
    sabado_fin: str

    domingo_activo: bool
    domingo_inicio: str
    domingo_fin: str


class ConfiguracionAgendaResponse(
    ConfiguracionAgendaUpdate
):

    id: int

    model_config = ConfigDict(
        from_attributes=True
    )


class CierreAgendaCreate(BaseModel):

    fecha: date

    motivo: str

    observaciones: str | None = None


class CierreAgendaResponse(
    CierreAgendaCreate
):

    id: int

    model_config = ConfigDict(
        from_attributes=True
    )
"""Contratos de configuración de horarios y cierres de agenda."""
