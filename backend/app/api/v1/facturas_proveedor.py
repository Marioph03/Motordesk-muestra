from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.core.permissions import require_permission
from app.database.database import get_db
from app.models.usuario import Usuario
from app.schemas.factura_proveedor import FacturaProveedorCreate, FacturaProveedorResponse, MarcarFacturaProveedorPagadaRequest
from app.services.factura_proveedor_service import FacturaProveedorService


router = APIRouter(prefix="/facturas-proveedor", tags=["Facturas proveedor"])


@router.get("", response_model=list[FacturaProveedorResponse])
def listar(db: Session = Depends(get_db)):
    return FacturaProveedorService.listar(db)


@router.get("/{factura_id}", response_model=FacturaProveedorResponse)
def obtener(factura_id: int, db: Session = Depends(get_db)):
    try:
        return FacturaProveedorService.obtener(db, factura_id)
    except ValueError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error


@router.post("", response_model=FacturaProveedorResponse, status_code=201)
def crear(datos: FacturaProveedorCreate, db: Session = Depends(get_db), usuario: Usuario = Depends(require_permission("compras.crear"))):
    try:
        return FacturaProveedorService.crear(db, datos)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error


@router.post("/{factura_id}/pagar", response_model=FacturaProveedorResponse)
def marcar_pagada(factura_id: int, datos: MarcarFacturaProveedorPagadaRequest, db: Session = Depends(get_db), usuario: Usuario = Depends(require_permission("compras.crear"))):
    try:
        return FacturaProveedorService.marcar_pagada(db, factura_id, datos.fecha_pago)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error


@router.post("/{factura_id}/pdf", response_model=FacturaProveedorResponse)
def subir_pdf(factura_id: int, archivo: UploadFile = File(...), db: Session = Depends(get_db), usuario: Usuario = Depends(require_permission("compras.crear"))):
    try:
        return FacturaProveedorService.guardar_pdf(db, factura_id, archivo)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error


@router.get("/{factura_id}/pdf")
def descargar_pdf(factura_id: int, db: Session = Depends(get_db)):
    try:
        ruta = FacturaProveedorService.obtener_ruta_pdf(db, factura_id)
        return FileResponse(ruta, media_type="application/pdf", filename=ruta.name)
    except ValueError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
"""API de facturas recibidas de proveedor, adjuntos y estado de pago."""
