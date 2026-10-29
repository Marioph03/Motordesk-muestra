from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.core.permissions import require_permission
from app.database.database import get_db
from app.models.usuario import Usuario
from app.schemas.albaran_venta import AlbaranVentaCreate, AlbaranVentaResponse
from app.services.albaran_venta_service import AlbaranVentaService
from app.repositories.empresa_repository import EmpresaRepository
from app.services.configuracion_taller_service import ConfiguracionTallerService
from app.services.configuracion_documentos_service import ConfiguracionDocumentosService
from app.services.pdf_service import PdfService


router = APIRouter(prefix="/albaranes-venta", tags=["Albaranes de venta"])


@router.get("", response_model=list[AlbaranVentaResponse])
def listar(db: Session = Depends(get_db), usuario: Usuario = Depends(require_permission("stock.ver"))):
    return AlbaranVentaService.listar(db)


@router.get("/{albaran_id}", response_model=AlbaranVentaResponse)
def obtener(albaran_id: int, db: Session = Depends(get_db), usuario: Usuario = Depends(require_permission("stock.ver"))):
    albaran = AlbaranVentaService.obtener(db, albaran_id)
    if albaran is None:
        raise HTTPException(status_code=404, detail="Albarán de venta no encontrado")
    return albaran


@router.get("/{albaran_id}/pdf")
def descargar_pdf(albaran_id: int, db: Session = Depends(get_db), usuario: Usuario = Depends(require_permission("stock.ver"))):
    albaran = AlbaranVentaService.obtener(db, albaran_id)
    if albaran is None:
        raise HTTPException(status_code=404, detail="Albarán de venta no encontrado")
    pdf = PdfService.generar_albaran_venta(
        albaran,
        EmpresaRepository.get_first(db),
        ConfiguracionTallerService.obtener(db),
        ConfiguracionDocumentosService.obtener(db),
    )
    return StreamingResponse(pdf, media_type="application/pdf", headers={"Content-Disposition": f'inline; filename="albaran_{albaran.numero}.pdf"'})


@router.post("", response_model=AlbaranVentaResponse, status_code=status.HTTP_201_CREATED)
def crear(datos: AlbaranVentaCreate, db: Session = Depends(get_db), usuario: Usuario = Depends(require_permission("stock.editar"))):
    try:
        return AlbaranVentaService.crear(db, datos)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error


@router.post("/{albaran_id}/confirmar", response_model=AlbaranVentaResponse)
def confirmar(albaran_id: int, db: Session = Depends(get_db), usuario: Usuario = Depends(require_permission("stock.editar"))):
    try:
        return AlbaranVentaService.confirmar(db, albaran_id)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error


@router.post("/{albaran_id}/anular", response_model=AlbaranVentaResponse)
def anular(albaran_id: int, db: Session = Depends(get_db), usuario: Usuario = Depends(require_permission("stock.editar"))):
    try:
        return AlbaranVentaService.anular(db, albaran_id)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
