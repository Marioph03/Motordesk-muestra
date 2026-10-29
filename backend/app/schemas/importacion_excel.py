from typing import Any

from pydantic import (
    BaseModel,
    Field
)


class ColumnaExcelResponse(BaseModel):
    indice: int
    nombre: str


class HojaExcelResponse(BaseModel):
    nombre: str
    filas: int
    columnas: int


class AnalisisExcelResponse(BaseModel):
    archivo: str

    hojas: list[HojaExcelResponse]

    hoja_activa: str

    columnas: list[ColumnaExcelResponse]

    total_filas: int

    muestra: list[dict[str, Any]]


class MapeoCampoRequest(BaseModel):
    campo_motordesk: str
    columna_excel: str | None = None


class PreviewImportacionRequest(BaseModel):
    archivo_temporal: str

    hoja: str

    mapeo: list[MapeoCampoRequest]


class FilaPreviewResponse(BaseModel):
    numero_fila: int

    datos: dict[str, Any]

    valida: bool

    duplicado: bool = False

    errores: list[str] = []

    advertencias: list[str] = []


class PreviewImportacionResponse(BaseModel):
    total: int

    validas: int

    errores: int

    advertencias: int

    duplicados: int

    filas: list[FilaPreviewResponse]


class ConfirmarImportacionRequest(BaseModel):
    archivo_temporal: str

    hoja: str

    mapeo: list[MapeoCampoRequest]

    ignorar_duplicados: bool = True


class ResultadoImportacionResponse(BaseModel):
    total: int

    importados: int

    omitidos: int

    errores: int

    detalle_errores: list[str] = []
"""Contratos de análisis, mapeo, vista previa e importación desde Excel."""
