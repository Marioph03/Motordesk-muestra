from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session

from app.core.security import get_current_user
from app.database.database import get_db
from app.schemas.empresa import (
    EmpresaCreate,
    EmpresaUpdate,
    EmpresaResponse
)
from app.services.empresa_service import EmpresaService

from app.schemas.pagination import PaginationParams
from app.schemas.paginated_response import PaginatedResponse

router = APIRouter(
    prefix="/empresas",
    tags=["Empresas"],
    dependencies=[Depends(get_current_user)]
)


@router.get("/", response_model=PaginatedResponse[EmpresaResponse])
def get_empresas(
    pagination: PaginationParams = Depends(),
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return EmpresaService.get_paginated(
        db,
        pagination
    )


@router.get("/{empresa_id}", response_model=EmpresaResponse)
def get_empresa(
    empresa_id: int,
    db: Session = Depends(get_db)
):
    try:
        return EmpresaService.get_by_id(
            db,
            empresa_id
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.post(
    "/",
    response_model=EmpresaResponse,
    status_code=status.HTTP_201_CREATED
)
def create_empresa(
    empresa: EmpresaCreate,
    db: Session = Depends(get_db)
):
    try:
        return EmpresaService.create(
            db,
            empresa
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.patch("/{empresa_id}", response_model=EmpresaResponse)
def update_empresa(
    empresa_id: int,
    datos: EmpresaUpdate,
    db: Session = Depends(get_db)
):
    try:
        return EmpresaService.update(
            db,
            empresa_id,
            datos
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.delete("/{empresa_id}")
def delete_empresa(
    empresa_id: int,
    db: Session = Depends(get_db)
):
    try:
        EmpresaService.delete(
            db,
            empresa_id
        )

        return {
            "mensaje": "Empresa eliminada correctamente"
        }

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
        
@router.post(
    "/{empresa_id}/logo",
    response_model=EmpresaResponse
)
def subir_logo(
    empresa_id: int,
    logo: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    try:
        return EmpresaService.subir_logo(
            db,
            empresa_id,
            logo
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
"""API de empresa heredada, mantenida por compatibilidad con documentos existentes."""
