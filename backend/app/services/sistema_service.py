from datetime import datetime
import os
from pathlib import Path
import shutil
import subprocess
from threading import Lock

from sqlalchemy import text
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session

from app.core.config import settings
from app.database.database import Base


class SistemaService:
    VERSION = "1.0.0"
    # En Docker/desarrollo conservamos la carpeta historica del proyecto. La
    # instalacion nativa la define explicitamente en ProgramData para que una
    # actualizacion del ejecutable nunca borre ni esconda las copias.
    BACKUP_DIR = Path(
        os.getenv(
            "MOTORDESK_BACKUP_DIR",
            str(Path(__file__).resolve().parents[2] / "backups"),
        )
    )
    _backup_lock = Lock()
    TABLAS_CONSERVADAS = {
        "empresa", "usuarios", "roles", "permisos", "rol_permisos",
        "configuracion_agenda", "configuracion_documentos", "configuracion_email",
        "configuracion_facturacion", "configuracion_notificaciones", "configuracion_taller",
        "configuracion_whatsapp", "whatsapp_plantillas", "certificados_electronicos",
        "facturae_organismos",
    }

    @staticmethod
    def restablecer_datos_prueba(db: Session) -> int:
        """Borra únicamente datos operativos y conserva identidad y configuración."""
        tablas = [
            tabla for tabla in reversed(Base.metadata.sorted_tables)
            if tabla.name not in SistemaService.TABLAS_CONSERVADAS
        ]
        try:
            if db.bind and db.bind.dialect.name == "postgresql":
                nombres = ", ".join(f'"{tabla.name}"' for tabla in tablas)
                if nombres:
                    db.execute(text(f"TRUNCATE TABLE {nombres} RESTART IDENTITY"))
            else:
                for tabla in tablas:
                    db.execute(tabla.delete())
            db.commit()
            return len(tablas)
        except Exception as error:
            db.rollback()
            raise ValueError("No se pudieron restablecer los datos. La base de datos no se ha modificado.") from error

    @staticmethod
    def estado_sistema(db: Session) -> dict:
        backend = {"nombre": "Backend", "estado": "OPERATIVO", "detalle": None}
        try:
            db.execute(text("SELECT 1"))
            base_datos = {"nombre": "Base de datos", "estado": "OPERATIVO", "detalle": None}
        except Exception as error:
            base_datos = {"nombre": "Base de datos", "estado": "ERROR", "detalle": str(error)}

        return {
            "version": SistemaService.VERSION,
            "backend": backend,
            "base_datos": base_datos,
            "whatsapp": {"nombre": "WhatsApp", "estado": "CONFIGURADO", "detalle": None},
            "verifactu": {"nombre": "VERI*FACTU", "estado": "CONFIGURADO", "detalle": None},
        }

    @staticmethod
    def crear_backup() -> Path:
        """Crea una copia coherente con el motor de base de datos configurado."""
        if not SistemaService._backup_lock.acquire(blocking=False):
            raise ValueError("Ya hay una copia de seguridad en curso")

        try:
            url = make_url(settings.database_url)
            motor = url.get_backend_name()
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            SistemaService.BACKUP_DIR.mkdir(parents=True, exist_ok=True)

            if motor == "postgresql":
                destino = SistemaService.BACKUP_DIR / f"motordesk_{timestamp}.dump"
                SistemaService._crear_backup_postgresql(url, destino)
                return destino

            if motor == "sqlite":
                if not url.database or url.database == ":memory:":
                    raise ValueError("No se puede copiar una base de datos SQLite en memoria")
                origen = Path(url.database).expanduser()
                if not origen.is_file():
                    raise ValueError("No se ha encontrado la base de datos SQLite")
                destino = SistemaService.BACKUP_DIR / f"motordesk_{timestamp}.db"
                shutil.copy2(origen, destino)
                return destino

            raise ValueError(f"No hay soporte de copia automática para {motor}")
        finally:
            SistemaService._backup_lock.release()

    @staticmethod
    def _crear_backup_postgresql(url, destino: Path) -> None:
        ejecutable = SistemaService._obtener_pg_dump()
        if ejecutable is None:
            raise ValueError(
                "No se ha encontrado pg_dump. Instala las herramientas de PostgreSQL "
                "o configura PG_DUMP_PATH."
            )
        if not url.database or not url.username:
            raise ValueError("La URL de PostgreSQL no contiene base de datos o usuario")

        entorno = os.environ.copy()
        if url.password:
            entorno["PGPASSWORD"] = url.password

        comando = [
            ejecutable,
            "--format=custom",
            "--file", str(destino),
            "--host", url.host or "localhost",
            "--port", str(url.port or 5432),
            "--username", url.username,
            "--no-owner",
            "--no-privileges",
            url.database,
        ]
        try:
            resultado = subprocess.run(
                comando,
                env=entorno,
                capture_output=True,
                text=True,
                timeout=600,
                check=False,
            )
        except OSError as error:
            raise ValueError(f"No se pudo ejecutar pg_dump: {error}") from error
        except subprocess.TimeoutExpired as error:
            raise ValueError("La copia de PostgreSQL superó el límite de 10 minutos") from error

        if resultado.returncode != 0:
            if destino.exists():
                destino.unlink()
            lineas = (resultado.stderr or "").strip().splitlines()
            detalle = lineas[-1] if lineas else "Error desconocido de pg_dump"
            raise ValueError(f"No se pudo crear la copia de PostgreSQL: {detalle}")

    @staticmethod
    def _obtener_pg_dump() -> str | None:
        configurado = settings.pg_dump_path.strip()
        if configurado and SistemaService._es_pg_dump_funcional(configurado):
            return configurado
        encontrado = shutil.which("pg_dump")
        if encontrado and SistemaService._es_pg_dump_funcional(encontrado):
            return encontrado

        carpeta_postgres = Path("C:/Program Files/PostgreSQL")
        if carpeta_postgres.is_dir():
            for ruta in sorted(carpeta_postgres.glob("*/bin/pg_dump.exe"), reverse=True):
                if SistemaService._es_pg_dump_funcional(str(ruta)):
                    return str(ruta)
        return None

    @staticmethod
    def _es_pg_dump_funcional(ejecutable: str) -> bool:
        """Evita seleccionar instalaciones de PostgreSQL incompletas en Windows."""
        ruta = Path(ejecutable)
        if not ruta.is_file():
            return False
        try:
            resultado = subprocess.run(
                [str(ruta), "--version"],
                capture_output=True,
                text=True,
                timeout=10,
                check=False,
            )
        except (OSError, subprocess.TimeoutExpired):
            return False
        return resultado.returncode == 0

    @staticmethod
    def ultima_copia() -> dict:
        carpeta = SistemaService.BACKUP_DIR
        if not carpeta.exists():
            return {"disponible": False}

        archivos = sorted(
            (
                archivo
                for archivo in carpeta.glob("motordesk_*")
                if archivo.suffix in {".db", ".dump"}
            ),
            key=lambda archivo: archivo.stat().st_mtime,
            reverse=True,
        )
        if not archivos:
            return {"disponible": False}

        archivo = archivos[0]
        return {
            "disponible": True,
            "nombre_archivo": archivo.name,
            "fecha": datetime.fromtimestamp(archivo.stat().st_mtime).isoformat(),
            "tamano_bytes": archivo.stat().st_size,
        }
