from datetime import datetime, timedelta

from fastapi import (
    APIRouter,
    Depends,
    HTTPException
)
from fastapi.responses import StreamingResponse

from sqlalchemy.orm import Session

from app.database.database import get_db
from app.core.permissions import require_permission
from app.schemas.informe import ResumenGeneralInforme
from app.repositories.empresa_repository import EmpresaRepository
from app.services.informes_service import InformesService
from app.services.pdf_service import PdfService
from app.services.excel_export_service import ExcelExportService


router = APIRouter(
    prefix="/informes",
    tags=["Informes"]
)


@router.get(
    "/resumen-general",
    response_model=ResumenGeneralInforme
)
def resumen_general(
    fecha_inicio: datetime,
    fecha_fin: datetime,
    cliente_id: int | None = None,
    proveedor_id: int | None = None,
    gasto_id: int | None = None,
    db: Session = Depends(get_db),
    usuario_actual=Depends(require_permission("informes.ver")),
):

    try:

        return InformesService.resumen_general(
            db,
            fecha_inicio,
            fecha_fin,
            cliente_id,
            proveedor_id,
            gasto_id,
        )

    except ValueError as e:

        raise HTTPException(
            status_code=400,
            detail=str(e)
        )


@router.get("/resumen-general/pdf")
def pdf_resumen_general(
    fecha_inicio: datetime,
    fecha_fin: datetime,
    db: Session = Depends(get_db),
    usuario_actual=Depends(require_permission("informes.ver")),
):
    try:
        informe = InformesService.resumen_general(db, fecha_inicio, fecha_fin)
        empresa = EmpresaRepository.get_first(db)
        pdf = PdfService.generar_informe_general(informe, empresa)

        # La API trabaja con una fecha final exclusiva para incluir el día
        # seleccionado completo. El archivo, sin embargo, usa el último día
        # que el usuario ve en pantalla.
        fecha_fin_mostrada = fecha_fin - timedelta(days=1)
        nombre = (
            f"informe_{fecha_inicio:%Y%m%d}_"
            f"{fecha_fin_mostrada:%Y%m%d}.pdf"
        )

        return StreamingResponse(
            pdf,
            media_type="application/pdf",
            headers={"Content-Disposition": f'inline; filename="{nombre}"'},
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


def _respuesta_pdf_economico(titulo, informe, empresa, fecha_inicio, fecha_fin, nombre):
    pdf = PdfService.generar_informe_economico(titulo, informe, empresa)
    fecha_fin_mostrada = fecha_fin - timedelta(days=1)
    return StreamingResponse(
        pdf,
        media_type="application/pdf",
        headers={
            "Content-Disposition": (
                f'inline; filename="{nombre}_{fecha_inicio:%Y%m%d}_{fecha_fin_mostrada:%Y%m%d}.pdf"'
            )
        },
    )


def _respuesta_excel_economico(titulo, informe, empresa, fecha_inicio, fecha_fin, nombre):
    excel = ExcelExportService.generar_informe_economico(titulo, informe, empresa)
    fecha_fin_mostrada = fecha_fin - timedelta(days=1)
    return StreamingResponse(
        excel,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={
            "Content-Disposition": (
                f'attachment; filename="{nombre}_{fecha_inicio:%Y%m%d}_{fecha_fin_mostrada:%Y%m%d}.xlsx"'
            )
        },
    )


@router.get("/facturacion/pdf")
def pdf_facturacion(fecha_inicio: datetime, fecha_fin: datetime, cliente_id: int | None = None, db: Session = Depends(get_db), usuario_actual=Depends(require_permission("informes.ver"))):
    try:
        return _respuesta_pdf_economico("FACTURACIÓN", InformesService.informe_facturacion(db, fecha_inicio, fecha_fin, cliente_id), EmpresaRepository.get_first(db), fecha_inicio, fecha_fin, "facturacion")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/clientes/pdf")
def pdf_clientes(fecha_inicio: datetime, fecha_fin: datetime, cliente_id: int | None = None, db: Session = Depends(get_db), usuario_actual=Depends(require_permission("informes.ver"))):
    try:
        return _respuesta_pdf_economico("RESUMEN ECONÓMICO POR CLIENTE", InformesService.informe_clientes(db, fecha_inicio, fecha_fin, cliente_id), EmpresaRepository.get_first(db), fecha_inicio, fecha_fin, "clientes")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/compras-gastos/pdf")
def pdf_compras_gastos(fecha_inicio: datetime, fecha_fin: datetime, proveedor_id: int | None = None, gasto_id: int | None = None, db: Session = Depends(get_db), usuario_actual=Depends(require_permission("informes.ver"))):
    try:
        return _respuesta_pdf_economico("COMPRAS Y GASTOS", InformesService.informe_compras_gastos(db, fecha_inicio, fecha_fin, proveedor_id, gasto_id), EmpresaRepository.get_first(db), fecha_inicio, fecha_fin, "compras_gastos")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/facturacion/excel")
def excel_facturacion(fecha_inicio: datetime, fecha_fin: datetime, cliente_id: int | None = None, db: Session = Depends(get_db), usuario_actual=Depends(require_permission("informes.ver"))):
    try:
        return _respuesta_excel_economico("FACTURACION", InformesService.informe_facturacion(db, fecha_inicio, fecha_fin, cliente_id), EmpresaRepository.get_first(db), fecha_inicio, fecha_fin, "facturacion")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/clientes/excel")
def excel_clientes(fecha_inicio: datetime, fecha_fin: datetime, cliente_id: int | None = None, db: Session = Depends(get_db), usuario_actual=Depends(require_permission("informes.ver"))):
    try:
        return _respuesta_excel_economico("RESUMEN ECONOMICO POR CLIENTE", InformesService.informe_clientes(db, fecha_inicio, fecha_fin, cliente_id), EmpresaRepository.get_first(db), fecha_inicio, fecha_fin, "clientes")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/compras-gastos/excel")
def excel_compras_gastos(fecha_inicio: datetime, fecha_fin: datetime, proveedor_id: int | None = None, gasto_id: int | None = None, db: Session = Depends(get_db), usuario_actual=Depends(require_permission("informes.ver"))):
    try:
        return _respuesta_excel_economico("COMPRAS Y GASTOS", InformesService.informe_compras_gastos(db, fecha_inicio, fecha_fin, proveedor_id, gasto_id), EmpresaRepository.get_first(db), fecha_inicio, fecha_fin, "compras_gastos")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
"""API de informes agregados y exportación del resumen a PDF."""
