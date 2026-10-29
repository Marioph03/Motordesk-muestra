"""Endpoints autenticados para consulta y mantenimiento de clientes."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.database.database import get_db
from app.schemas.cliente import ClienteResponse
from app.services.cliente_service import ClienteService
from app.schemas.cliente import ClienteUpdate
from fastapi import Query
from app.core.security import get_current_user
from app.schemas.cliente import ClienteCreate

from app.schemas.pagination import PaginationParams
from app.schemas.paginated_response import PaginatedResponse
from app.schemas.cliente import ClienteSelect

from typing import Annotated
from fastapi import Query

router = APIRouter(
    prefix="/clientes",
    tags=["Clientes"],
    dependencies=[Depends(get_current_user)]
)


@router.get("/", response_model=PaginatedResponse[ClienteResponse])
def get_clientes(
    pagination: PaginationParams = Depends(),
    q: Annotated[str | None, Query()] = None,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return ClienteService.get_paginated(
        db,
        pagination,
        q
    )

@router.post("/", response_model=ClienteResponse)
def create_cliente(
    cliente: ClienteCreate,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return ClienteService.create(
        db,
        cliente,
        current_user
    )

from fastapi import HTTPException

@router.get("/buscar", response_model=list[ClienteResponse])
def buscar_clientes(
    q: str = Query(..., min_length=1),
    db: Session = Depends(get_db)
):
    return ClienteService.buscar(db, q)

@router.get(
    "/select",
    response_model=list[ClienteSelect]
)
def get_clientes_select(
    db: Session = Depends(get_db)
):

    return ClienteService.get_select(db)

@router.get("/{cliente_id}", response_model=ClienteResponse)
def get_cliente(
    cliente_id: int,
    db: Session = Depends(get_db)
):
    cliente = ClienteService.get_by_id(db, cliente_id)

    if cliente is None:
        raise HTTPException(
            status_code=404,
            detail="Cliente no encontrado"
        )

    return cliente

@router.put("/{cliente_id}", response_model=ClienteResponse)
def update_cliente(
    cliente_id: int,
    cliente: ClienteUpdate,
    db: Session = Depends(get_db)
):
    try:
        actualizado = ClienteService.update(
            db,
            cliente_id,
            cliente
        )
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="Ya existe otro cliente con ese NIF/CIF"
        )

    if actualizado is None:
        raise HTTPException(
            status_code=404,
            detail="Cliente no encontrado"
        )

    return actualizado

@router.patch("/{cliente_id}/desactivar", response_model=ClienteResponse)
def desactivar_cliente(
    cliente_id: int,
    db: Session = Depends(get_db)
):
    cliente = ClienteService.desactivar(
        db,
        cliente_id
    )

    if cliente is None:
        raise HTTPException(
            status_code=404,
            detail="Cliente no encontrado"
        )

    return cliente

@router.delete("/{cliente_id}", status_code=204)
def delete_cliente(
    cliente_id: int,
    db: Session = Depends(get_db)
):
    try:
        eliminado = ClienteService.delete(
            db,
            cliente_id
        )
    except ValueError as error:
        raise HTTPException(
            status_code=409,
            detail=str(error)
        ) from error

    if not eliminado:
        raise HTTPException(
            status_code=404,
            detail="Cliente no encontrado"
        )
