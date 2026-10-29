from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session, joinedload

from app.core.permissions import require_permission
from app.database.database import get_db
from app.models.articulo_stock import ArticuloStock
from app.models.cliente import Cliente
from app.models.proveedor import Proveedor
from app.models.vehiculo import Vehiculo
from app.schemas.importacion_excel import ConfirmarImportacionRequest, PreviewImportacionRequest, PreviewImportacionResponse, ResultadoImportacionResponse
from app.services.excel_campos_service import ExcelCamposService
from app.services.excel_export_service import ExcelExportService
from app.services.excel_import_service import ExcelImportService

router = APIRouter(prefix="/configuracion/importaciones", tags=["Configuracion - Importaciones"], dependencies=[Depends(require_permission("permisos.gestionar"))])


def _bad_request(error: ValueError):
    raise HTTPException(status_code=400, detail=str(error)) from error


@router.get("/campos/{tipo}")
def obtener_campos(tipo: str):
    try:
        return {"tipo": tipo, "campos": ExcelCamposService.obtener_campos(tipo)}
    except ValueError as error:
        _bad_request(error)


@router.post("/analizar")
async def analizar_excel(archivo: UploadFile = File(...)):
    try:
        return ExcelImportService.analizar(await ExcelImportService.guardar_temporal(archivo))
    except ValueError as error:
        _bad_request(error)


@router.get("/analizar/{archivo_temporal}")
def analizar_hoja(archivo_temporal: str, hoja: str | None = None):
    try:
        return ExcelImportService.analizar(ExcelImportService.obtener_ruta_temporal(archivo_temporal), hoja)
    except ValueError as error:
        _bad_request(error)


@router.post("/{tipo}/preview", response_model=PreviewImportacionResponse)
def preview_importacion(tipo: str, datos: PreviewImportacionRequest, db: Session = Depends(get_db)):
    try:
        return ExcelImportService.preview(db, tipo, datos.archivo_temporal, datos.hoja, datos.mapeo)
    except ValueError as error:
        _bad_request(error)


@router.post("/{tipo}/confirmar", response_model=ResultadoImportacionResponse)
def confirmar_importacion(tipo: str, datos: ConfirmarImportacionRequest, db: Session = Depends(get_db)):
    try:
        return ExcelImportService.importar(db, tipo, datos.archivo_temporal, datos.hoja, datos.mapeo, datos.ignorar_duplicados)
    except ValueError as error:
        _bad_request(error)
    except Exception as error:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"No se pudo completar la importacion: {error}") from error


@router.get("/exportar/{tipo}")
def exportar_datos(tipo: str, db: Session = Depends(get_db)):
    tipo = tipo.lower().strip()
    if tipo == "clientes":
        cabecera = ["Codigo", "Nombre", "Apellidos", "NIF/CIF", "Telefono", "Email", "Direccion", "Codigo postal", "Localidad", "Provincia", "Observaciones"]
        filas = [[x.codigo, x.nombre, x.apellidos, x.dni, x.telefono, x.email, x.direccion, x.codigo_postal, x.ciudad, x.provincia, x.observaciones] for x in db.query(Cliente).order_by(Cliente.apellidos, Cliente.nombre).all()]
    elif tipo == "vehiculos":
        cabecera = ["Codigo", "Matricula", "Marca", "Modelo", "Version", "Bastidor", "Kilometros", "Combustible", "NIF/CIF propietario"]
        registros = db.query(Vehiculo).options(joinedload(Vehiculo.cliente)).order_by(Vehiculo.matricula).all()
        filas = [[x.codigo, x.matricula, x.marca, x.modelo, x.version, x.bastidor, x.kilometros, x.combustible, x.cliente.dni if x.cliente else None] for x in registros]
    elif tipo == "proveedores":
        cabecera = ["Codigo", "Nombre", "NIF/CIF", "Telefono", "Email", "Direccion", "Localidad", "Provincia", "Codigo postal", "Observaciones"]
        filas = [[x.codigo, x.nombre, x.cif, x.telefono, x.email, x.direccion, x.ciudad, x.provincia, x.codigo_postal, x.observaciones] for x in db.query(Proveedor).order_by(Proveedor.nombre).all()]
    elif tipo == "articulos":
        cabecera = ["Referencia", "Nombre", "Descripcion", "Stock actual", "Stock minimo", "Coste unitario"]
        filas = [[x.referencia, x.nombre, x.descripcion, x.stock_actual, x.stock_minimo, x.coste] for x in db.query(ArticuloStock).order_by(ArticuloStock.referencia).all()]
    else:
        _bad_request(ValueError("Tipo de importacion no valido"))

    salida = ExcelExportService.generar_listado(tipo.title(), cabecera, filas, [18, 28] + [18] * (len(cabecera) - 2))
    return StreamingResponse(salida, media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", headers={"Content-Disposition": f'attachment; filename="motordesk_{tipo}.xlsx"'})
