"""Endpoints autenticados para el parque de vehículos de los clientes."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.schemas.vehiculo import (
    VehiculoCreate,
    VehiculoResponse
)
from app.services.vehiculo_service import VehiculoService
from app.core.security import get_current_user
from app.schemas.pagination import PaginationParams
from app.schemas.paginated_response import PaginatedResponse
from app.schemas.vehiculo import VehiculoUpdate
from app.schemas.vehiculo import VehiculoSelect
from typing import Annotated
from fastapi import Query

router = APIRouter(
    prefix="/vehiculos",
    tags=["Vehículos"],
    dependencies=[Depends(get_current_user)]
)


@router.get("/", response_model=PaginatedResponse[VehiculoResponse])
def get_vehiculos(
    pagination: PaginationParams = Depends(),
    q: Annotated[str | None, Query()] = None,
    db: Session = Depends(get_db)
):
    return VehiculoService.get_paginated(
        db,
        pagination,
        q
    )

@router.get("/buscar", response_model=list[VehiculoResponse])
def buscar_vehiculos(
    q: str,
    db: Session = Depends(get_db)
):
    return VehiculoService.search(db, q)

@router.get(
    "/select",
    response_model=list[VehiculoSelect]
)
def get_vehiculos_select(
    db: Session = Depends(get_db)
):

    return VehiculoService.get_select(db)

@router.get("/{vehiculo_id}", response_model=VehiculoResponse)
def get_vehiculo(
    vehiculo_id: int,
    db: Session = Depends(get_db)
):
    try:
        return VehiculoService.get_by_id(db, vehiculo_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/matricula/{matricula}", response_model=VehiculoResponse)
def get_by_matricula(
    matricula: str,
    db: Session = Depends(get_db)
):
    vehiculo = VehiculoService.get_by_matricula(db, matricula)

    if vehiculo is None:
        raise HTTPException(
            status_code=404,
            detail="Vehículo no encontrado"
        )

    return vehiculo


@router.get("/cliente/{cliente_id}", response_model=list[VehiculoResponse])
def get_by_cliente(
    cliente_id: int,
    db: Session = Depends(get_db)
):
    return VehiculoService.get_by_cliente(db, cliente_id)


@router.post("/", response_model=VehiculoResponse, status_code=201)
def create_vehiculo(
    vehiculo: VehiculoCreate,
    db: Session = Depends(get_db)
):
    try:
        return VehiculoService.create(db, vehiculo)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="Ya existe un vehículo con esa matrícula o bastidor.",
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
@router.put("/{vehiculo_id}", response_model=VehiculoResponse)
def update_vehiculo(
    vehiculo_id: int,
    vehiculo: VehiculoUpdate,
    db: Session = Depends(get_db)
):
    try:
        return VehiculoService.update(
            db,
            vehiculo_id,
            vehiculo.model_dump()
        )
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="Ya existe un vehículo con esa matrícula o bastidor.",
        )
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )
        
@router.delete("/{vehiculo_id}", status_code=204)
def delete_vehiculo(
    vehiculo_id: int,
    db: Session = Depends(get_db)
):
    try:
        VehiculoService.delete(db, vehiculo_id)
    except ValueError as e:
        raise HTTPException(
            status_code=404,
            detail=str(e)
        )
