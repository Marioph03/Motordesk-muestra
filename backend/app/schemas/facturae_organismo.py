"""Contratos del directorio de organismos Facturae."""

from datetime import datetime

from pydantic import ConfigDict

from app.schemas.facturae import FacturaeDestinoUpdate


class FacturaeOrganismoUpdate(FacturaeDestinoUpdate):
    pass


class FacturaeOrganismoResponse(FacturaeOrganismoUpdate):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
