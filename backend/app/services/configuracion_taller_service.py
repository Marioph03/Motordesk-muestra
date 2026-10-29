"""Configuración de identidad del taller y almacenamiento seguro de su logo."""

from pathlib import Path
from uuid import uuid4

from fastapi import UploadFile
from sqlalchemy.orm import Session

from app.models.configuracion_taller import (
    ConfiguracionTaller
)

from app.schemas.configuracion_taller import (
    ConfiguracionTallerUpdate
)
from app.core.storage_paths import directorio_logos_taller


class ConfiguracionTallerService:

    _EXTENSIONES_LOGO_VALIDAS = {".png", ".jpg", ".jpeg", ".webp"}
    _TIPOS_LOGO_VALIDOS = {"image/png", "image/jpeg", "image/webp"}
    _TAMANO_MAXIMO_LOGO = 5 * 1024 * 1024

    @staticmethod
    def obtener(
        db: Session
    ) -> ConfiguracionTaller:

        configuracion = (
            db.query(
                ConfiguracionTaller
            )
            .first()
        )

        if configuracion is None:

            configuracion = (
                ConfiguracionTaller(
                    pais="España"
                )
            )

            db.add(
                configuracion
            )

            db.commit()

            db.refresh(
                configuracion
            )

        return configuracion


    @staticmethod
    def actualizar(
        db: Session,
        datos: ConfiguracionTallerUpdate
    ) -> ConfiguracionTaller:

        configuracion = (
            ConfiguracionTallerService
            .obtener(db)
        )

        valores = (
            datos.model_dump(
                exclude_unset=True
            )
        )

        for campo, valor in valores.items():

            setattr(
                configuracion,
                campo,
                valor
            )

        db.commit()

        db.refresh(
            configuracion
        )

        return configuracion


    @staticmethod
    async def actualizar_logo(
        db: Session,
        archivo: UploadFile
    ) -> ConfiguracionTaller:
        """Valida y persiste un logo local sin confiar en el nombre del navegador."""
        nombre_original = archivo.filename or ""
        extension = Path(nombre_original).suffix.lower()

        if (
            extension not in ConfiguracionTallerService._EXTENSIONES_LOGO_VALIDAS
            or archivo.content_type not in ConfiguracionTallerService._TIPOS_LOGO_VALIDOS
        ):
            raise ValueError(
                "Formato de imagen no válido. Usa PNG, JPG, JPEG o WEBP."
            )

        contenido = await archivo.read()
        if not contenido:
            raise ValueError("El archivo de logo está vacío")
        if len(contenido) > ConfiguracionTallerService._TAMANO_MAXIMO_LOGO:
            raise ValueError("El logo no puede superar los 5 MB")

        carpeta = directorio_logos_taller()
        nombre_archivo = f"logo_{uuid4().hex}{extension}"
        ruta_archivo = carpeta / nombre_archivo
        configuracion = ConfiguracionTallerService.obtener(db)
        logo_anterior = configuracion.logo_url

        try:
            ruta_archivo.write_bytes(contenido)
            configuracion.logo_url = f"/static/uploads/taller/{nombre_archivo}"
            db.commit()
            db.refresh(configuracion)
        except Exception:
            db.rollback()
            if ruta_archivo.exists():
                ruta_archivo.unlink()
            raise

        if logo_anterior and logo_anterior.startswith("/static/uploads/taller/"):
            ruta_anterior = (
                directorio_logos_taller()
                / logo_anterior.removeprefix("/static/uploads/taller/")
            )
            if ruta_anterior.exists() and ruta_anterior.is_file():
                try:
                    ruta_anterior.unlink()
                except OSError:
                    pass

        return configuracion
