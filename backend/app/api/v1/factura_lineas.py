from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.schemas.factura_linea import (
    FacturaLineaCreate,
    FacturaLineaUpdate,
    FacturaLineaResponse
)
from app.services.factura_linea_service import FacturaLineaService
from app.core.security import get_current_user

router = APIRouter(
    prefix="/factura-lineas",
    tags=["Líneas de Factura"],
    dependencies=[Depends(get_current_user)]
)


@router.get(
    "/factura/{factura_id}",
    response_model=list[FacturaLineaResponse]
)
def get_lineas(
    factura_id: int,
    db: Session = Depends(get_db)
):
    try:
        return FacturaLineaService.get_by_factura(
            db,
            factura_id
        )

    except ValueError as e:
        raise HTTPException(
            status_code=404,
            detail=str(e)
        )


@router.post(
    "/factura/{factura_id}",
    response_model=FacturaLineaResponse,
    status_code=201
)
def create_linea(
    factura_id: int,
    linea: FacturaLineaCreate,
    db: Session = Depends(get_db)
):
    try:
        return FacturaLineaService.create(
            db,
            factura_id,
            linea
        )

    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )


@router.patch(
    "/{linea_id}",
    response_model=FacturaLineaResponse
)
def update_linea(
    linea_id: int,
    datos: FacturaLineaUpdate,
    db: Session = Depends(get_db)
):
    try:
        return FacturaLineaService.update(
            db,
            linea_id,
            datos
        )

    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )


@router.delete("/{linea_id}")
def delete_linea(
    linea_id: int,
    db: Session = Depends(get_db)
):
    try:
        FacturaLineaService.delete(
            db,
            linea_id
        )

        return {
            "mensaje": "Línea eliminada correctamente"
        }

    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )
"""Endpoints de edición de líneas que conforman una factura en borrador."""
