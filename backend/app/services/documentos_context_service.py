from pathlib import Path

from sqlalchemy.orm import Session

from app.services.configuracion_taller_service import (
    ConfiguracionTallerService
)

from app.services.configuracion_documentos_service import (
    ConfiguracionDocumentosService
)
from app.core.storage_paths import directorio_logos_taller


class DocumentosContextService:
    """
    Centraliza la configuración utilizada por los
    documentos y PDFs generados por MotorDesk.

    De esta forma evitamos repetir lógica en:
    - Facturas
    - Presupuestos
    - Órdenes
    - Pedidos de compra
    """

    @staticmethod
    def obtener_ruta_logo(
        db: Session
    ) -> str | None:
        """Obtiene una ruta local verificable para imágenes de ReportLab.

        En base de datos se almacena una URL pública ``/static/...``. Esta
        función la traduce a un fichero dentro del backend y rechaza cualquier
        ruta fuera de la carpeta de logos del taller.
        """

        taller = ConfiguracionTallerService.obtener(db)

        if not taller.logo_url:
            return None

        prefijo_publico = "/static/uploads/taller/"
        if not taller.logo_url.startswith(prefijo_publico):
            return None

        carpeta_logos = directorio_logos_taller().resolve()
        archivo = (carpeta_logos / taller.logo_url.removeprefix(prefijo_publico)).resolve()

        if carpeta_logos not in archivo.parents:
            return None

        if not archivo.is_file():
            return None

        return str(archivo)

    @staticmethod
    def obtener_contexto(
        db: Session
    ) -> dict:

        taller = (
            ConfiguracionTallerService
            .obtener(db)
        )

        documentos = (
            ConfiguracionDocumentosService
            .obtener(db)
        )

        return {

            # =============================================
            # IDENTIDAD DEL TALLER
            # =============================================

            "nombre_comercial":
                taller.nombre_comercial,

            "razon_social":
                taller.razon_social,

            "nif_cif":
                taller.nif_cif,

            "telefono":
                taller.telefono,

            "email":
                taller.email,

            "web":
                taller.web,

            "direccion":
                taller.direccion,

            "codigo_postal":
                taller.codigo_postal,

            "localidad":
                taller.localidad,

            "provincia":
                taller.provincia,

            "pais":
                taller.pais,

            "logo_url":
                taller.logo_url,


            # =============================================
            # VISIBILIDAD
            # =============================================

            "mostrar_telefono":
                documentos.mostrar_telefono,

            "mostrar_email":
                documentos.mostrar_email,

            "mostrar_direccion":
                documentos.mostrar_direccion,

            "mostrar_nif_cif":
                documentos.mostrar_nif_cif,

            "mostrar_web":
                documentos.mostrar_web,


            # =============================================
            # PRESUPUESTOS
            # =============================================

            "validez_presupuesto_dias":
                documentos.validez_presupuesto_dias,

            "observaciones_presupuesto":
                documentos.observaciones_presupuesto,


            # =============================================
            # ÓRDENES
            # =============================================

            "observaciones_orden":
                documentos.observaciones_orden,


            # =============================================
            # PEDIDOS
            # =============================================

            "observaciones_pedido_compra":
                documentos.observaciones_pedido_compra,


            # =============================================
            # GENERAL
            # =============================================

            "pie_documentos":
                documentos.pie_documentos

        }


    @staticmethod
    def obtener_datos_taller_visibles(
        db: Session
    ) -> dict:

        contexto = (
            DocumentosContextService
            .obtener_contexto(db)
        )

        datos = {

            "nombre_comercial":
                contexto[
                    "nombre_comercial"
                ],

            "razon_social":
                contexto[
                    "razon_social"
                ],

            "logo_url":
                contexto[
                    "logo_url"
                ],

            "codigo_postal":
                contexto[
                    "codigo_postal"
                ],

            "localidad":
                contexto[
                    "localidad"
                ],

            "provincia":
                contexto[
                    "provincia"
                ],

            "pais":
                contexto[
                    "pais"
                ]

        }


        datos["nif_cif"] = (
            contexto["nif_cif"]
            if contexto["mostrar_nif_cif"]
            else None
        )


        datos["telefono"] = (
            contexto["telefono"]
            if contexto["mostrar_telefono"]
            else None
        )


        datos["email"] = (
            contexto["email"]
            if contexto["mostrar_email"]
            else None
        )


        datos["web"] = (
            contexto["web"]
            if contexto["mostrar_web"]
            else None
        )


        datos["direccion"] = (
            contexto["direccion"]
            if contexto["mostrar_direccion"]
            else None
        )


        return datos
