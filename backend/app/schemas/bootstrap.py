"""Schemas del asistente de configuracion inicial de MotorDesk."""

from decimal import Decimal

from pydantic import BaseModel, EmailStr, Field, field_validator


class BootstrapInicialRequest(BaseModel):
    """Datos necesarios para completar la primera configuracion."""

    # Empresa / taller
    nombre_empresa: str = Field(min_length=1, max_length=150)
    nombre_comercial: str = Field(min_length=1, max_length=150)
    nif: str = Field(min_length=1, max_length=20)
    direccion: str = Field(min_length=1, max_length=255)
    codigo_postal: str = Field(min_length=1, max_length=10)
    ciudad: str = Field(min_length=1, max_length=100)
    provincia: str = Field(min_length=1, max_length=100)
    telefono: str = Field(min_length=1, max_length=30)
    email_empresa: EmailStr

    # Administrador
    nombre_admin: str = Field(min_length=1, max_length=100)
    apellidos_admin: str = Field(min_length=1, max_length=150)
    email_admin: EmailStr
    password_admin: str = Field(min_length=8, max_length=100)

    # Facturacion. El modo y la moneda no se exponen para que una instalacion
    # nueva nunca pueda empezar enviando informacion fiscal por accidente.
    iva_defecto: Decimal = Field(
        default=Decimal("21"),
        ge=Decimal("0"),
        le=Decimal("100"),
    )
    regimen_fiscal: str | None = Field(default=None, max_length=100)
    serie_facturas: str = Field(default="F", min_length=1, max_length=20)
    serie_pruebas: str = Field(default="TP", min_length=1, max_length=20)

    @field_validator("serie_facturas", "serie_pruebas")
    @classmethod
    def limpiar_serie(cls, valor: str) -> str:
        serie = valor.strip().upper()
        if not serie:
            raise ValueError("La serie de facturacion no puede estar vacia.")
        return serie

    @field_validator("regimen_fiscal")
    @classmethod
    def limpiar_regimen_fiscal(cls, valor: str | None) -> str | None:
        if valor is None:
            return None
        return valor.strip() or None
