from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.core.permissions import require_permission
from app.database.database import get_db
from app.models.usuario import Usuario
from app.models.albaran_proveedor import AlbaranProveedor
from app.schemas.albaran_proveedor import (
    AlbaranProveedorCreate,
    AlbaranProveedorResponse,
)
from app.services.albaran_proveedor_service import AlbaranProveedorService
from app.repositories.empresa_repository import EmpresaRepository
from app.services.configuracion_taller_service import ConfiguracionTallerService
from app.services.configuracion_documentos_service import ConfiguracionDocumentosService
from app.services.pdf_service import PdfService


router = APIRouter(
    prefix="/albaranes-proveedor",
    tags=["Albaranes de proveedor"],
)


@router.post(
    "",
    response_model=AlbaranProveedorResponse,
    status_code=201,
)
def crear_albaran(
    datos: AlbaranProveedorCreate,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_permission("compras.crear")),
):
    try:
        return AlbaranProveedorService.crear(db, datos)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error


@router.get("", response_model=list[AlbaranProveedorResponse])
def listar_albaranes(db: Session = Depends(get_db)):
    return (
        db.query(AlbaranProveedor)
        .order_by(AlbaranProveedor.fecha.desc(), AlbaranProveedor.id.desc())
        .all()
    )


@router.get("/{albaran_id}/lineas-devolvibles")
def lineas_devolvibles(
    albaran_id: int,
    db: Session = Depends(get_db),
):
    try:
        return AlbaranProveedorService.obtener_lineas_devolvibles(
            db,
            albaran_id,
        )
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error


@router.get("/{albaran_id}", response_model=AlbaranProveedorResponse)
def obtener_albaran(albaran_id: int, db: Session = Depends(get_db)):
    albaran = (
        db.query(AlbaranProveedor)
        .filter(AlbaranProveedor.id == albaran_id)
        .first()
    )
    if albaran is None:
        raise HTTPException(status_code=404, detail="Albarán no encontrado")
    return albaran


@router.get("/{albaran_id}/pdf")
def generar_pdf_albaran(albaran_id: int, db: Session = Depends(get_db)):
    albaran = db.query(AlbaranProveedor).filter(AlbaranProveedor.id == albaran_id).first()
    if albaran is None:
        raise HTTPException(status_code=404, detail="Albarán no encontrado")
    return StreamingResponse(
        PdfService.generar_albaran_proveedor(
            albaran, EmpresaRepository.get_first(db),
            ConfiguracionTallerService.obtener(db),
            ConfiguracionDocumentosService.obtener(db),
        ),
        media_type="application/pdf",
        headers={"Content-Disposition": f'inline; filename="{albaran.numero_interno}.pdf"'},
    )


@router.post(
    "/{albaran_id}/confirmar",
    response_model=AlbaranProveedorResponse,
)
def confirmar_albaran(
    albaran_id: int,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_permission("compras.recibir")),
):
    try:
        return AlbaranProveedorService.confirmar(db, albaran_id)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error


@router.post(
    "/{albaran_id}/anular",
    response_model=AlbaranProveedorResponse,
)
def anular_albaran(
    albaran_id: int,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_permission("compras.crear")),
):
    try:
        return AlbaranProveedorService.anular(db, albaran_id)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
"""API del ciclo de albaranes de proveedor y su confirmación de mercancía."""
