from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status
)

from sqlalchemy.orm import Session

from app.database.database import get_db

from app.schemas.pago_factura import (
    PagoFacturaCreate,
    PagoFacturaResponse
)

from app.services.pago_factura_service import (
    PagoFacturaService
)
from app.core.security import get_current_user


router = APIRouter(
    prefix="/pagos-factura",
    tags=["Pagos factura"],
    dependencies=[Depends(get_current_user)]
)


@router.get(
    "/factura/{factura_id}",
    response_model=list[PagoFacturaResponse]
)
def get_pagos_factura(
    factura_id: int,
    db: Session = Depends(get_db)
):

    try:

        return PagoFacturaService.get_by_factura(
            db,
            factura_id
        )

    except ValueError as e:

        raise HTTPException(
            status_code=400,
            detail=str(e)
        )


@router.get(
    "/factura/{factura_id}/resumen"
)
def get_resumen_pago(
    factura_id: int,
    db: Session = Depends(get_db)
):

    try:

        return PagoFacturaService.calcular_importes(
            db,
            factura_id
        )

    except ValueError as e:

        raise HTTPException(
            status_code=400,
            detail=str(e)
        )


@router.post(
    "/factura/{factura_id}",
    response_model=PagoFacturaResponse,
    status_code=status.HTTP_201_CREATED
)
def crear_pago(
    factura_id: int,
    pago: PagoFacturaCreate,
    db: Session = Depends(get_db)
):

    try:

        return PagoFacturaService.create(
            db,
            factura_id,
            pago
        )

    except ValueError as e:

        raise HTTPException(
            status_code=400,
            detail=str(e)
        )


@router.delete(
    "/{pago_id}",
    status_code=status.HTTP_204_NO_CONTENT
)
def eliminar_pago(
    pago_id: int,
    db: Session = Depends(get_db)
):

    try:

        PagoFacturaService.delete(
            db,
            pago_id
        )

    except ValueError as e:

        raise HTTPException(
            status_code=400,
            detail=str(e)
        )
"""API de pagos de facturas, base para cobros y saldo pendiente exacto."""
