from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.core.permissions import require_permission
from app.schemas.configuracion_facturacion import (
    ConfiguracionFacturacionResponse,
    ConfiguracionFacturacionUpdate,
)
from app.services.configuracion_facturacion_service import ConfiguracionFacturacionService


router = APIRouter(
    prefix="/configuracion/facturacion",
    tags=["Configuración - Facturación"],
    dependencies=[Depends(require_permission("permisos.gestionar"))],
)


@router.get("", response_model=ConfiguracionFacturacionResponse)
def obtener_configuracion(db: Session = Depends(get_db)):
    return ConfiguracionFacturacionService.obtener(db)


@router.put("", response_model=ConfiguracionFacturacionResponse)
def actualizar_configuracion(
    datos: ConfiguracionFacturacionUpdate,
    db: Session = Depends(get_db),
):
    try:
        return ConfiguracionFacturacionService.actualizar(db, datos)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
"""Configuración segura de series y modo fiscal de facturación."""
