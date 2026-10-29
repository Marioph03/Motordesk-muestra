"""Gestión segura de adjuntos asociados a órdenes de reparación."""

from pathlib import Path
from uuid import uuid4

from fastapi import UploadFile
from sqlalchemy.orm import Session

from app.repositories.archivo_orden_repository import (
    ArchivoOrdenRepository
)
from app.repositories.orden_reparacion_repository import (
    OrdenReparacionRepository
)
from app.models.orden_reparacion import EstadoReparacion


class ArchivoOrdenService:
    """Valida y almacena ficheros bajo rutas controladas del backend."""


    UPLOAD_DIR = Path("uploads") / "ordenes"

    MAX_FILE_SIZE = 10 * 1024 * 1024

    TIPOS_PERMITIDOS = {
        "application/pdf",
        "image/jpeg",
        "image/png",
        "image/webp"
    }

    CATEGORIAS_PERMITIDAS = {
        "Foto del vehículo",
        "Documento del cliente",
        "Informe",
        "Presupuesto",
        "Peritaje",
        "Factura externa",
        "Otro"
    }

    @staticmethod
    def _validar_orden_editable(orden) -> None:
        if orden.tipo == "PR" and orden.estado != EstadoReparacion.BORRADOR.value:
            raise ValueError(
                "No se pueden modificar los archivos de un presupuesto que no está en borrador"
            )

    @staticmethod
    def get_by_orden(
        db: Session,
        orden_id: int
    ):
        orden = OrdenReparacionRepository.get_by_id(
            db,
            orden_id
        )

        if orden is None:
            raise ValueError(
                "Orden de reparación no encontrada"
            )

        return ArchivoOrdenRepository.get_by_orden(
            db,
            orden_id
        )

    @staticmethod
    async def subir(
        db: Session,
        orden_id: int,
        archivo: UploadFile,
        categoria: str
    ):
        orden = OrdenReparacionRepository.get_by_id(
            db,
            orden_id
        )

        if orden is None:
            raise ValueError(
                "Orden de reparación no encontrada"
            )

        ArchivoOrdenService._validar_orden_editable(orden)

        if categoria not in ArchivoOrdenService.CATEGORIAS_PERMITIDAS:
            raise ValueError(
                "Categoría de archivo no válida"
            )

        if archivo.content_type not in ArchivoOrdenService.TIPOS_PERMITIDOS:
            raise ValueError(
                "Tipo de archivo no permitido. "
                "Solo se permiten PDF, JPG, JPEG, PNG y WEBP."
            )

        contenido = await archivo.read()

        if not contenido:
            raise ValueError(
                "El archivo está vacío"
            )

        if len(contenido) > ArchivoOrdenService.MAX_FILE_SIZE:
            raise ValueError(
                "El archivo no puede superar los 10 MB"
            )

        carpeta_orden = (
            ArchivoOrdenService.UPLOAD_DIR
            / str(orden_id)
        )

        carpeta_orden.mkdir(
            parents=True,
            exist_ok=True
        )

        nombre_original = (
            Path(archivo.filename).name
            if archivo.filename
            else "archivo"
        )

        extension = Path(nombre_original).suffix.lower()

        nombre_archivo = (
            f"{uuid4().hex}{extension}"
        )

        ruta = carpeta_orden / nombre_archivo

        try:
            ruta.write_bytes(contenido)

            archivo_db = ArchivoOrdenRepository.create(
                db=db,
                orden_id=orden_id,
                nombre_original=nombre_original,
                nombre_archivo=nombre_archivo,
                tipo_mime=archivo.content_type,
                categoria=categoria,
                ruta=str(ruta),
                tamano=len(contenido)
            )

            return archivo_db

        except Exception:

            if ruta.exists():
                ruta.unlink()

            raise

    @staticmethod
    def get_by_id(
        db: Session,
        orden_id: int,
        archivo_id: int
    ):
        archivo = ArchivoOrdenRepository.get_by_id(
            db,
            archivo_id
        )

        if (
            archivo is None
            or archivo.orden_id != orden_id
        ):
            raise ValueError(
                "Archivo no encontrado"
            )

        return archivo

    @staticmethod
    def delete(
        db: Session,
        orden_id: int,
        archivo_id: int
    ):
        archivo = ArchivoOrdenService.get_by_id(
            db,
            orden_id,
            archivo_id
        )

        orden = OrdenReparacionRepository.get_by_id(db, orden_id)
        if orden is None:
            raise ValueError("Orden de reparación no encontrada")
        ArchivoOrdenService._validar_orden_editable(orden)

        ruta = Path(archivo.ruta)

        ArchivoOrdenRepository.delete(
            db,
            archivo
        )

        if ruta.exists():
            ruta.unlink()
