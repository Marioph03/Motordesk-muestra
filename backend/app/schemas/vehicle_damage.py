from typing import Dict

from pydantic import BaseModel, RootModel


class Damage(BaseModel):
    scratch: bool | None = None
    dent: bool | None = None
    broken: bool | None = None
    replace: bool | None = None


class VehicleDamage(RootModel[Dict[str, Damage]]):
    pass
"""Contrato estructurado de la inspección visual de daños del vehículo."""
