from pydantic import (
    BaseModel,
    ConfigDict,
    Field
)


class ConfiguracionDocumentosUpdate(BaseModel):

    mostrar_telefono: bool = True
    mostrar_email: bool = True
    mostrar_direccion: bool = True
    mostrar_nif_cif: bool = True
    mostrar_web: bool = False

    # IBAN de destino mostrado exclusivamente al registrar transferencias.
    iban_cobros: str | None = Field(
        default=None,
        max_length=34,
    )

    validez_presupuesto_dias: int = Field(
        default=30,
        ge=1,
        le=365
    )

    pie_documentos: str | None = None

    observaciones_presupuesto: str | None = None

    observaciones_orden: str | None = None

    observaciones_pedido_compra: str | None = None


class ConfiguracionDocumentosResponse(
    ConfiguracionDocumentosUpdate
):

    id: int

    model_config = ConfigDict(
        from_attributes=True
    )
"""Contrato de preferencias visibles y textos comunes de documentos PDF."""
