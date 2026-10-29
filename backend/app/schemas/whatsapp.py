from pydantic import BaseModel, Field


class WhatsAppConnectRequest(BaseModel):

    code: str

    # El flujo moderno de Embedded Signup se abre en un popup del SDK de Meta,
    # por lo que no necesita una redirección OAuth propia.
    redirect_uri: str | None = None

    # Estos identificadores los entrega Meta durante Embedded Signup; nunca
    # deben sustituirse por valores fijos de otra instalación.
    waba_id: str = Field(min_length=1, max_length=100)

    phone_number_id: str = Field(min_length=1, max_length=100)


class WhatsAppConnectResponse(BaseModel):

    message: str
"""Contratos de solicitudes y resultados de comunicaciones WhatsApp."""
