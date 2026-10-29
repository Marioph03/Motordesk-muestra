from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from app.core.security import get_current_user
from app.database.database import get_db
from app.schemas.orden_interna import OrdenInternaCreate, OrdenInternaResponse, LineaOrdenInternaCreate, LineaOrdenInternaResponse
from app.services.orden_interna_service import OrdenInternaService
from app.services.pdf_service import PdfService

router = APIRouter(prefix="/ordenes-internas", tags=["Órdenes internas"], dependencies=[Depends(get_current_user)])
@router.get("", response_model=list[OrdenInternaResponse])
def listar(db: Session = Depends(get_db)): return OrdenInternaService.listar(db)
@router.post("", response_model=OrdenInternaResponse)
def crear(datos: OrdenInternaCreate, db: Session = Depends(get_db)):
    try: return OrdenInternaService.crear(db, datos)
    except ValueError as error: raise HTTPException(400, str(error))
@router.get("/{orden_id}", response_model=OrdenInternaResponse)
def obtener(orden_id: int, db: Session = Depends(get_db)):
    try: return OrdenInternaService.obtener(db, orden_id)
    except ValueError as error: raise HTTPException(404, str(error))
@router.post("/{orden_id}/lineas", response_model=LineaOrdenInternaResponse)
def anadir_linea(orden_id: int, datos: LineaOrdenInternaCreate, db: Session = Depends(get_db)):
    try: return OrdenInternaService.anadir_linea(db, orden_id, datos)
    except ValueError as error: raise HTTPException(400, str(error))
@router.delete("/{orden_id}/lineas/{linea_id}")
def borrar_linea(orden_id: int, linea_id: int, db: Session = Depends(get_db)):
    try: OrdenInternaService.borrar_linea(db, orden_id, linea_id); return {"ok": True}
    except ValueError as error: raise HTTPException(400, str(error))
@router.post("/{orden_id}/cerrar", response_model=OrdenInternaResponse)
def cerrar(orden_id: int, db: Session = Depends(get_db)):
    try: return OrdenInternaService.cerrar(db, orden_id)
    except ValueError as error: raise HTTPException(400, str(error))
@router.get("/{orden_id}/pdf")
def pdf(orden_id: int, db: Session = Depends(get_db)):
    try: orden = OrdenInternaService.obtener(db, orden_id); return StreamingResponse(PdfService.generar_orden_interna(orden), media_type="application/pdf", headers={"Content-Disposition": f'inline; filename="{orden.numero}.pdf"'})
    except ValueError as error: raise HTTPException(404, str(error))
