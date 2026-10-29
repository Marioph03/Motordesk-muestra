"""Punto de entrada de la API FastAPI de MotorDesk.

Este módulo concentra infraestructura transversal (CORS, estáticos, routers,
auditoría HTTP y tareas de mantenimiento). Las reglas de negocio deben vivir en
servicios, no en este archivo.
"""

import asyncio
from datetime import datetime
import logging
import os
import sys
from threading import Lock
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse
from sqlalchemy import text

from app.database.database import SessionLocal, engine
from app.database.bootstrap import inicializar_base_datos
import app.models
from app.services.actividad_service import ActividadService
from app.services.cita_service import CitaService
from app.services.sistema_service import SistemaService
from app.services.certificado_electronico_service import (
    CertificadoElectronicoService,
)
from app.core.config import settings

logger = logging.getLogger(__name__)

# El ejecutable nativo publica HTTP:8000 para la red local y HTTPS:8443 para
# el propio equipo/Meta. Ambos servidores comparten este proceso y FastAPI
# ejecuta el evento startup por cada uno. Sin este bloqueo podían intentar
# inicializar Alembic simultáneamente: HTTPS quedaba disponible, pero HTTP
# terminaba antes de abrir el puerto para los demás puestos del taller.
_ESQUEMA_INICIAL_LOCK = Lock()
_ESQUEMA_INICIAL_PREPARADO = False
from app.api.v1.vehiculos import router as vehiculos_router
from app.api.v1.ordenes_reparacion import router as ordenes_router
from app.api.v1.ordenes_internas import router as ordenes_internas_router
from app.api.v1.mano_obra import router as mano_obra_router
from app.api.v1.piezas import router as piezas_router
from app.api.v1.usuarios import router as usuarios_router
from app.api.v1.auth import router as auth_router
from app.api.v1.bootstrap import router as bootstrap_router
from app.api.v1.proveedores import router as proveedores_router
from app.api.v1.facturas import router as facturas_router
from app.api.v1.factura_lineas import router as factura_lineas_router
from app.api.v1.empresa import router as empresa_router
from app.api.v1.dashboard import router as dashboard_router
from app.api.v1.archivos_orden import router as archivos_orden_router
from app.api.v1.whatsapp import router as whatsapp_router
from app.api.v1.actividad import router as actividad_router
from app.api.v1.webhooks import router as webhook_router
from app.api.v1.pago_factura import router as pago_factura_router
from app.api.v1.verifactu import router as verifactu_router
from app.api.v1 import clientes
from app.api.v1.cita import router as cita_router
from app.api.v1.stock import router as stock_router
from app.api.v1.pedido_compra import router as pedidos_compra_router
from app.api.v1.permisos import router as permisos_router
from app.api.v1.ausencia_personal import router as ausencias_personal_router
from app.api.v1.personal import router as personal_router
from app.api.v1.informe import router as informes_router
from app.api.v1.configuracion_taller import router as configuracion_taller_router
from app.api.v1.configuracion_agenda import router as configuracion_agenda_router
from app.api.v1.configuracion_documentos import router as configuracion_documentos_router
from app.api.v1.configuracion_notificaciones import (
    router as configuracion_notificaciones_router,
)
from app.api.v1.configuracion_facturacion import (
    router as configuracion_facturacion_router,
)
from app.api.v1.certificado_electronico import (
    router as certificado_electronico_router
)
from app.api.v1.configuracion_whatsapp import router as configuracion_whatsapp_router
from app.api.v1.configuracion_email import router as configuracion_email_router
from app.api.v1.seguridad import router as seguridad_router
from app.api.v1.sistema import router as sistema_router
from app.api.v1.albaran_proveedor import router as albaranes_proveedor_router
from app.api.v1.albaranes_venta import router as albaranes_venta_router
from app.api.v1.devoluciones_proveedor import router as devoluciones_proveedor_router
from app.api.v1.facturas_proveedor import router as facturas_proveedor_router
from app.api.v1.compras_dashboard import router as compras_dashboard_router
from app.api.v1.importaciones_excel import router as importaciones_excel_router
from app.api.v1.motor_ai import router as motor_ai_router

from fastapi.staticfiles import StaticFiles

app = FastAPI(
    title="MotorDesk API",
    version="1.0.0"
)

# El ejecutable nativo sirve Angular y agrupa la API bajo /backend. Docker y
# desarrollo mantienen las rutas historicas para no romper el proxy de Nginx.
MODO_NATIVO = os.getenv(
    "MOTORDESK_NATIVE_FRONTEND",
    "false",
).strip().lower() in {"1", "true", "yes", "si", "sí"}

API_PREFIX = "/backend" if MODO_NATIVO else ""

from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:4200",
        "https://gmt-sampling-lounge-medicare.trycloudflare.com",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Mapeo de prefijos HTTP a nombres funcionales. Permite que el historial de
# actividad sea entendible para usuarios sin acoplar cada router al middleware.
_MODULOS_AUDITORIA = {
    "clientes": "CLIENTES",
    "vehiculos": "VEHICULOS",
    "proveedores": "PROVEEDORES",
    "pedidos-compra": "COMPRAS",
    "albaranes-proveedor": "COMPRAS",
    "devoluciones-proveedor": "COMPRAS",
    "facturas-proveedor": "COMPRAS",
    "usuarios": "USUARIOS",
    "ausencias-personal": "PERSONAL",
    "personal": "PERSONAL",
    "empresa": "EMPRESA",
    "configuracion": "CONFIGURACION",
    "ordenes-reparacion": "ORDENES",
    "mano-obra": "MANO_OBRA",
    "piezas": "PIEZAS",
    "archivos-orden": "ARCHIVOS_ORDEN",
    "facturas": "FACTURAS",
    "factura-lineas": "LINEAS_FACTURA",
    "pagos-factura": "COBROS",
    "verifactu": "VERIFACTU",
    "whatsapp": "WHATSAPP",
}


def _datos_auditoria(method: str, path: str) -> tuple[str, str, int | None]:
    """Convierte una petición API en un evento de auditoría legible."""
    segmentos = [segmento for segmento in path.split("/") if segmento]
    modulo = _MODULOS_AUDITORIA.get(segmentos[0], "SISTEMA") if segmentos else "SISTEMA"
    if "archivos" in segmentos:
        modulo = "ARCHIVOS_ORDEN"
    registro_id = next((int(segmento) for segmento in segmentos[1:] if segmento.isdigit()), None)
    ruta = path.lower()

    acciones_especiales = (
        ("enviar-email", "ENVIAR_EMAIL"),
        ("enviar-whatsapp", "ENVIAR_WHATSAPP"),
        ("generar-anulacion", "GENERAR_ANULACION_VERIFACTU"),
        ("/generar", "GENERAR_VERIFACTU"),
        ("enviar-test", "ENVIAR_AEAT_TEST"),
        ("crear-garantia", "CREAR_GARANTIA"),
        ("garantias/desde-factura", "CREAR_GARANTIA"),
        ("iniciar-revision", "INICIAR_REVISION"),
        ("iniciar-reparacion", "INICIAR_REPARACION"),
        ("/garantia/aprobar", "APROBAR_GARANTIA"),
        ("/garantia/rechazar", "RECHAZAR_GARANTIA"),
        ("/garantia/resolver", "RESOLVER_GARANTIA"),
        ("convertir-en-orden", "CONVERTIR_EN_ORDEN"),
        ("/aceptar", "ACEPTAR_PRESUPUESTO"),
        ("/rechazar", "RECHAZAR_PRESUPUESTO"),
        ("/enviar", "ENVIAR_PRESUPUESTO"),
        ("/emitir", "EMITIR_FACTURA"),
        ("/anular", "ANULAR_FACTURA"),
        ("actualizar-desde-orden", "ACTUALIZAR_DESDE_ORDEN"),
        ("reset-password", "RESTABLECER_CONTRASENA"),
        ("desactivar", "DESACTIVAR"),
    )
    accion = next((accion for fragmento, accion in acciones_especiales if fragmento in ruta), None)
    if accion is None:
        accion = {
            "POST": "CREAR",
            "PUT": "ACTUALIZAR",
            "PATCH": "ACTUALIZAR",
            "DELETE": "ELIMINAR",
        }.get(method, method)
    return modulo, accion, registro_id


@app.middleware("http")
async def registrar_auditoria_peticion(request: Request, call_next):
    response = await call_next(request)

    # Las consultas no modifican información. Se guardan todas las acciones
    # autenticadas de escritura, incluidas las rechazadas, salvo la propia
    # auditoría y el login (que se registra en AuthService).
    if (
        request.method not in {"POST", "PUT", "PATCH", "DELETE"}
        or request.url.path.startswith("/actividad")
        or request.url.path == "/auth/login"
    ):
        return response

    usuario = getattr(request.state, "audit_user", None)
    if usuario is None:
        return response

    modulo, accion, registro_id = _datos_auditoria(request.method, request.url.path)
    correcto = 200 <= response.status_code < 300
    accion_registrada = accion if correcto else f"FALLO_{accion}"
    resultado = "correctamente" if correcto else f"con error HTTP {response.status_code}"
    descripcion = f"{accion.replace('_', ' ').title()} {resultado} ({request.method} {request.url.path})"

    db_auditoria = SessionLocal()
    try:
        ActividadService.registrar_evento(
            db_auditoria,
            empresa_id=usuario["empresa_id"],
            usuario_id=usuario["id"],
            modulo=modulo,
            accion=accion_registrada[:50],
            registro_id=registro_id,
            descripcion=descripcion,
            ip=request.client.host if request.client else None,
        )
    except Exception:
        # Una auditoría no puede convertir una acción ya resuelta en un fallo.
        db_auditoria.rollback()
    finally:
        db_auditoria.close()

    return response

app.include_router(clientes.router, prefix=API_PREFIX)
app.include_router(vehiculos_router, prefix=API_PREFIX)
app.include_router(ordenes_router, prefix=API_PREFIX)
app.include_router(ordenes_internas_router, prefix=API_PREFIX)
app.include_router(mano_obra_router, prefix=API_PREFIX)
app.include_router(piezas_router, prefix=API_PREFIX)
app.include_router(usuarios_router, prefix=API_PREFIX)
app.include_router(auth_router, prefix=API_PREFIX)
app.include_router(bootstrap_router, prefix=API_PREFIX)
app.include_router(proveedores_router, prefix=API_PREFIX)
app.include_router(facturas_router, prefix=API_PREFIX)
app.include_router(factura_lineas_router, prefix=API_PREFIX)
app.include_router(empresa_router, prefix=API_PREFIX)
app.include_router(dashboard_router, prefix=API_PREFIX)
app.include_router(archivos_orden_router, prefix=API_PREFIX)
app.include_router(whatsapp_router, prefix=API_PREFIX)
app.include_router(actividad_router, prefix=API_PREFIX)
app.include_router(webhook_router, prefix=API_PREFIX)
app.include_router(pago_factura_router, prefix=API_PREFIX)
app.include_router(verifactu_router, prefix=API_PREFIX)
app.include_router(cita_router, prefix=API_PREFIX)
app.include_router(pedidos_compra_router, prefix=API_PREFIX)
app.include_router(stock_router, prefix=API_PREFIX)
app.include_router(permisos_router, prefix=API_PREFIX)
app.include_router(ausencias_personal_router, prefix=API_PREFIX)
app.include_router(personal_router, prefix=API_PREFIX)
app.include_router(informes_router, prefix=API_PREFIX)
app.include_router(configuracion_taller_router, prefix=API_PREFIX)
app.include_router(configuracion_agenda_router, prefix=API_PREFIX)
app.include_router(configuracion_documentos_router, prefix=API_PREFIX)
app.include_router(configuracion_notificaciones_router, prefix=API_PREFIX)
app.include_router(configuracion_facturacion_router, prefix=API_PREFIX)
app.include_router(certificado_electronico_router, prefix=API_PREFIX)
app.include_router(configuracion_whatsapp_router, prefix=API_PREFIX)
app.include_router(configuracion_email_router, prefix=API_PREFIX)
app.include_router(seguridad_router, prefix=API_PREFIX)
app.include_router(sistema_router, prefix=API_PREFIX)
app.include_router(albaranes_proveedor_router, prefix=API_PREFIX)
app.include_router(albaranes_venta_router, prefix=API_PREFIX)
app.include_router(devoluciones_proveedor_router, prefix=API_PREFIX)
app.include_router(facturas_proveedor_router, prefix=API_PREFIX)
app.include_router(compras_dashboard_router, prefix=API_PREFIX)
app.include_router(importaciones_excel_router, prefix=API_PREFIX)
app.include_router(motor_ai_router, prefix=API_PREFIX)

os.makedirs(
    "uploads/logos",
    exist_ok=True
)
os.makedirs(
    "uploads/avatars",
    exist_ok=True
)
os.makedirs(
    "static/uploads/taller",
    exist_ok=True
)

app.mount(
    "/static",
    StaticFiles(directory="static"),
    name="static"
)

app.mount(
    "/uploads",
    StaticFiles(directory="uploads"),
    name="uploads"
)


def _obtener_directorio_frontend() -> Path:
    """Localiza el build Angular utilizado por la instalacion nativa."""
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent / "frontend"

    return (
        Path(__file__).resolve().parents[2]
        / "frontend"
        / "dist"
        / "frontend"
        / "browser"
    )


FRONTEND_DIR = _obtener_directorio_frontend()


if MODO_NATIVO:

    @app.get("/motordesk-ca.cer", include_in_schema=False)
    async def descargar_certificado_ca_motordesk():
        """Entrega solo la CA pública para configurar puestos cliente.

        La clave privada nunca sale de ``ProgramData``; esta descarga sirve
        únicamente para que Windows confíe en el certificado HTTPS local.
        """
        certificado = (
            Path(os.environ.get("PROGRAMDATA", r"C:\\ProgramData"))
            / "MotorDesk"
            / "tls"
            / "motordesk-local-ca.cer"
        )

        if not certificado.is_file():
            raise HTTPException(
                status_code=404,
                detail="El certificado local de MotorDesk no está disponible.",
            )

        return FileResponse(
            certificado,
            media_type="application/pkix-cert",
            filename="motordesk-local-ca.cer",
        )

    @app.get("/", include_in_schema=False)
    async def frontend_inicio():
        """Entrega el punto de entrada de Angular en modo nativo."""
        index = FRONTEND_DIR / "index.html"

        if not index.is_file():
            raise HTTPException(
                status_code=404,
                detail="Frontend de MotorDesk no encontrado",
            )

        return FileResponse(index)


    @app.get("/{ruta:path}", include_in_schema=False)
    async def frontend_spa(ruta: str):
        """Sirve recursos Angular y usa index.html para Angular Router."""
        archivo = (FRONTEND_DIR / ruta).resolve()

        try:
            archivo.relative_to(FRONTEND_DIR.resolve())
        except ValueError:
            raise HTTPException(status_code=404) from None

        if archivo.is_file():
            return FileResponse(archivo)

        index = FRONTEND_DIR / "index.html"

        if index.is_file():
            return FileResponse(index)

        raise HTTPException(
            status_code=404,
            detail="Frontend de MotorDesk no encontrado",
        )


async def _bucle_recordatorios_citas() -> None:
    """Proceso local: se ejecuta mientras el backend permanezca activo."""
    while True:
        db = SessionLocal()
        try:
            CitaService.procesar_recordatorios_automaticos(db)
        except Exception:
            db.rollback()
        finally:
            db.close()
        await asyncio.sleep(15 * 60)


async def _bucle_copias_seguridad() -> None:
    """Crea copias periódicas mientras el backend esté en ejecución."""
    intervalo = max(settings.backup_interval_hours, 1) * 3600
    comprobacion = max(settings.backup_check_minutes, 1) * 60

    while True:
        try:
            if settings.backup_auto_enabled:
                ultima = SistemaService.ultima_copia()
                necesita_copia = not ultima["disponible"]

                if ultima.get("fecha"):
                    fecha_ultima = datetime.fromisoformat(ultima["fecha"])
                    necesita_copia = (
                        datetime.now() - fecha_ultima
                    ).total_seconds() >= intervalo

                if necesita_copia:
                    SistemaService.crear_backup()
        except Exception:
            # Un fallo de copia no debe impedir que arranque o continúe la API.
            logger.exception("No se pudo completar la copia automática de seguridad")

        await asyncio.sleep(comprobacion)


def _preparar_esquema_inicial() -> None:
    """Inicializa o actualiza el esquema antes de atender peticiones.

    ``create_all()`` no añade columnas nuevas a tablas existentes. Usar el
    historial de Alembic aquí garantiza que una actualización del instalador
    aplica las migraciones incluidas en su propio backend antes de arrancar.
    """
    global _ESQUEMA_INICIAL_PREPARADO

    with _ESQUEMA_INICIAL_LOCK:
        if _ESQUEMA_INICIAL_PREPARADO:
            return

        inicializar_base_datos()
        _ESQUEMA_INICIAL_PREPARADO = True


@app.on_event("startup")
async def iniciar_recordatorios_citas() -> None:
    try:
        _preparar_esquema_inicial()
    except Exception:
        # El ejecutable redirige stdout/stderr a backend-startup.log. Dejar el
        # traceback completo aqui evita que una instalacion parezca bloqueada
        # cuando una migracion concreta ha fallado.
        logger.exception("No se pudo preparar la base de datos al iniciar MotorDesk")
        raise
    db = SessionLocal()
    try:
        migrados = CertificadoElectronicoService.migrar_desde_directorio_publico(db)
        if migrados:
            logger.warning(
                "Se trasladaron %s certificados al almacenamiento privado.",
                migrados,
            )
    finally:
        db.close()
    asyncio.create_task(_bucle_recordatorios_citas())
    asyncio.create_task(_bucle_copias_seguridad())

@app.get("/")
def root():
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))

        return {
            "message": "MotorDesk API funcionando",
            "database": "Conectada correctamente"
        }

    except Exception as e:
        return {
            "message": "Error de conexión",
            "error": str(e)
        }
