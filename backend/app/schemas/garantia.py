from pydantic import BaseModel, Field


class GarantiaResolverRequest(BaseModel):
    resolucion: str = Field(min_length=1, max_length=2000)
"""Contrato de lectura de garantías gestionadas como órdenes tipo GA."""
