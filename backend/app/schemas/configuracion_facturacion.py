"""Contrato de configuración fiscal y validaciones de modo de facturación."""

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ConfiguracionFacturacionUpdate(BaseModel):
    modo_facturacion: str
    serie_pruebas: str = Field(min_length=1, max_length=20)
    serie_facturas: str = Field(min_length=1, max_length=20)
    permitir_envio_aeat: bool = False

    @field_validator("modo_facturacion")
    @classmethod
    def validar_modo(cls, valor: str) -> str:
        valor = valor.strip().upper()
        if valor not in {"PRUEBAS", "VERIFACTU"}:
            raise ValueError("Modo de facturación no válido")
        return valor

    @field_validator("serie_pruebas", "serie_facturas")
    @classmethod
    def limpiar_serie(cls, valor: str) -> str:
        valor = valor.strip().upper()
        if not valor:
            raise ValueError("La serie no puede estar vacía")
        return valor


class ConfiguracionFacturacionResponse(ConfiguracionFacturacionUpdate):
    id: int

    model_config = ConfigDict(from_attributes=True)
