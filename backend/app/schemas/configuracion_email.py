from typing import Literal

from pydantic import BaseModel, EmailStr, Field, model_validator


class ConfiguracionEmailGuardar(BaseModel):
    proveedor: Literal["gmail", "outlook", "personalizado"] = "gmail"
    host: str = "smtp.gmail.com"
    puerto: int = Field(default=587, ge=1, le=65535)
    seguridad: Literal["starttls", "ssl"] = "starttls"
    usuario: EmailStr
    remitente: EmailStr | None = None
    password: str | None = Field(default=None, max_length=500)
    activo: bool = True

    @model_validator(mode="after")
    def gmail_seguro(self):
        if self.proveedor == "gmail":
            self.host, self.puerto, self.seguridad = "smtp.gmail.com", 587, "starttls"
        elif self.proveedor == "outlook":
            self.host, self.puerto, self.seguridad = "smtp.office365.com", 587, "starttls"
        return self


class ConfiguracionEmailResponse(BaseModel):
    configurado: bool
    activo: bool = False
    proveedor: str = "gmail"
    host: str = "smtp.gmail.com"
    puerto: int = 587
    seguridad: str = "starttls"
    usuario: str | None = None
    remitente: str | None = None
    metodo_autenticacion: str = "password"


class PruebaEmailRequest(BaseModel):
    destinatario: EmailStr
