"""Endpoints autenticados para el catálogo de proveedores."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.security import get_current_user
from app.database.database import get_db
from app.schemas.proveedor import (
    ProveedorCreate,
    ProveedorUpdate,
    ProveedorResponse
)
from app.services.proveedor_service import ProveedorService

router = APIRouter(
    prefix="/proveedores",
    tags=["Proveedores"],
    dependencies=[Depends(get_current_user)]
)


@router.get("/", response_model=list[ProveedorResponse])
def get_proveedores(
    db: Session = Depends(get_db)
):
    return ProveedorService.get_all(db)


@router.get("/{proveedor_id}", response_model=ProveedorResponse)
def get_proveedor(
    proveedor_id: int,
    db: Session = Depends(get_db)
):
    try:
        return ProveedorService.get_by_id(
            db,
            proveedor_id
        )

    except ValueError as e:
        raise HTTPException(
            status_code=404,
            detail=str(e)
        )


@router.post("/", response_model=ProveedorResponse)
def create_proveedor(
    proveedor: ProveedorCreate,
    db: Session = Depends(get_db)
):
    try:
        return ProveedorService.create(
            db,
            proveedor
        )

    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )


@router.patch("/{proveedor_id}", response_model=ProveedorResponse)
def update_proveedor(
    proveedor_id: int,
    proveedor: ProveedorUpdate,
    db: Session = Depends(get_db)
):
    try:
        return ProveedorService.update(
            db,
            proveedor_id,
            proveedor
        )

    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )


@router.delete("/{proveedor_id}")
def delete_proveedor(
    proveedor_id: int,
    db: Session = Depends(get_db)
):
    try:

        ProveedorService.delete(
            db,
            proveedor_id
        )

        return {
            "mensaje": "Proveedor eliminado correctamente"
        }

    except ValueError as e:
        raise HTTPException(
            status_code=409,
            detail=str(e)
        )
