from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, EmailStr


class EmpresaCreate(BaseModel):

    nombre: str

    nombre_comercial: str

    nif: str

    direccion: str

    codigo_postal: str

    ciudad: str

    provincia: str

    telefono: str

    email: EmailStr

    web: str | None = None
    
    logo: str | None = None

    iban: str | None = None

    bic: str | None = None

    regimen_fiscal: str | None = None

    condiciones_factura: str | None = None

    color_primario: str = "#1F3D72"

    color_secundario: str = "#6C757D"

    iva_defecto: Decimal = Decimal("21")

    moneda: str = "EUR"


class EmpresaUpdate(BaseModel):

    nombre: str | None = None

    nombre_comercial: str | None = None

    nif: str | None = None

    direccion: str | None = None

    codigo_postal: str | None = None

    ciudad: str | None = None

    provincia: str | None = None

    telefono: str | None = None

    email: EmailStr | None = None

    web: str | None = None

    logo: str | None = None

    iban: str | None = None

    bic: str | None = None

    regimen_fiscal: str | None = None

    condiciones_factura: str | None = None

    color_primario: str | None = None

    color_secundario: str | None = None

    iva_defecto: Decimal | None = None

    moneda: str | None = None


class EmpresaResponse(BaseModel):

    id: int

    nombre: str

    nombre_comercial: str

    nif: str

    direccion: str

    codigo_postal: str

    ciudad: str

    provincia: str

    telefono: str

    email: EmailStr

    web: str | None

    logo: str | None

    iban: str | None

    bic: str | None

    regimen_fiscal: str | None

    condiciones_factura: str | None

    color_primario: str

    color_secundario: str

    iva_defecto: Decimal

    moneda: str

    created_at: datetime

    updated_at: datetime

    model_config = {
        "from_attributes": True
    }
"""Contrato de empresa conservado para flujos documentales heredados."""
