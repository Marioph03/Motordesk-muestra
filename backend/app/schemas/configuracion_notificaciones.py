from pydantic import (
    BaseModel,
    ConfigDict
)


class ConfiguracionNotificacionesUpdate(
    BaseModel
):

    stock_bajo: bool = True

    pedidos_pendientes: bool = True

    garantias_pendientes: bool = True

    presupuestos_pendientes: bool = True

    citas_proximas: bool = True

    ausencias_personal: bool = True


class ConfiguracionNotificacionesResponse(
    ConfiguracionNotificacionesUpdate
):

    id: int

    model_config = ConfigDict(
        from_attributes=True
    )
"""Contrato de preferencias que activan o silencian categorías de avisos."""
