from pydantic import BaseModel, Field


class ConfiguracionWhatsAppGuardar(BaseModel):
    whatsapp_business_account_id: str = Field(
        min_length=1,
        max_length=100,
    )

    phone_number_id: str = Field(
        min_length=1,
        max_length=100,
    )

    numero_whatsapp: str = Field(
        min_length=1,
        max_length=30,
    )

    # Opcional porque al editar la configuración podemos
    # conservar el token que ya existe.
    access_token: str | None = Field(
        default=None,
        min_length=1,
    )

    activo: bool = True


class ConfiguracionWhatsAppResponse(BaseModel):
    id: int
    empresa_id: int

    activo: bool

    whatsapp_business_account_id: str | None = None
    phone_number_id: str | None = None
    numero_whatsapp: str | None = None

    # Solo informamos de si existe.
    # Nunca devolvemos el token.
    token_configurado: bool

    model_config = {
        "from_attributes": True
    }


class EstadoWhatsAppResponse(BaseModel):
    configurado: bool
    activo: bool
    numero_whatsapp: str | None = None


class WhatsAppPlantillaResponse(BaseModel):
    """Estado local de una plantilla Meta para la empresa autenticada."""

    id: int
    tipo: str
    nombre_meta: str
    idioma: str
    estado: str

    model_config = {
        "from_attributes": True,
    }


class WhatsAppPlantillasResponse(BaseModel):
    """Colección de plantillas requeridas por MotorDesk."""

    plantillas: list[WhatsAppPlantillaResponse]
