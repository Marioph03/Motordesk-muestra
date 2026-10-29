"""Inicializa una base de datos Docker vacia de forma segura.

El historial de migraciones heredado contiene revisiones antiguas con varias
raices. En una base nueva esas ramas no pueden ejecutarse en un orden valido.
Por ello, solo en una base sin version Alembic se crea el esquema actual de los
modelos y se marca la revision vigente. Las bases ya versionadas siguen usando
las migraciones normales.
"""

import sys
import logging
import time
from pathlib import Path

from alembic import command
from alembic.config import Config
from alembic.script import ScriptDirectory
from sqlalchemy import Column, inspect, text
from sqlalchemy.schema import CreateColumn

from app.database.database import Base, engine
import app.models  # noqa: F401 - registra todos los modelos en Base.metadata.


logger = logging.getLogger(__name__)

# Las instalaciones nativas pueden iniciar el backend desde el lanzador y,
# durante una actualizacion, desde un servicio anterior que aun este cerrando.
# Un Lock de Python solo protege hilos del mismo proceso; este bloqueo
# transaccional de PostgreSQL protege tambien procesos distintos y se libera
# automaticamente si uno de ellos termina de forma inesperada.
_BLOQUEO_MIGRACIONES = 817354231
_ESPERA_MAXIMA_MIGRACIONES_SEGUNDOS = 90


def _adquirir_bloqueo_migraciones(connection) -> None:
    """Obtiene el bloqueo PostgreSQL que serializa migraciones de MotorDesk."""
    limite = time.monotonic() + _ESPERA_MAXIMA_MIGRACIONES_SEGUNDOS
    aviso_emitido = False

    while True:
        obtenido = connection.execute(
            text("SELECT pg_try_advisory_xact_lock(:clave)"),
            {"clave": _BLOQUEO_MIGRACIONES},
        ).scalar_one()
        if obtenido:
            return

        if not aviso_emitido:
            logger.info(
                "Otra instancia de MotorDesk esta actualizando la base de datos; esperando."
            )
            aviso_emitido = True

        if time.monotonic() >= limite:
            raise RuntimeError(
                "Otra instancia de MotorDesk mantiene bloqueada la actualizacion "
                "de la base de datos durante demasiado tiempo. Cierra las demas "
                "instancias de MotorDesk y vuelve a intentarlo."
            )

        time.sleep(1)


def _base_sin_version() -> bool:
    """Indica si la base no ha sido inicializada ni versionada por Alembic."""
    inspector = inspect(engine)
    if not inspector.has_table("alembic_version"):
        return True

    with engine.connect() as connection:
        version = connection.execute(
            text("SELECT version_num FROM alembic_version LIMIT 1")
        ).scalar_one_or_none()

    return version is None


def _esquema_ya_actualizado(config: Config) -> bool:
    """Evita abrir Alembic durante un arranque si no hay nada que aplicar."""
    revisiones_objetivo = set(ScriptDirectory.from_config(config).get_heads())

    with engine.connect() as connection:
        revisiones_actuales = set(
            connection.execute(
                text("SELECT version_num FROM alembic_version")
            ).scalars()
        )

    return revisiones_actuales == revisiones_objetivo


def _reparar_columnas_heredadas() -> None:
    """Completa columnas ausentes en bases nativas anteriores a Alembic.

    Las primeras versiones instalables creaban tablas con ``create_all`` pero
    no guardaban una revisión de Alembic. Una actualización posterior no puede
    asumir que ese esquema antiguo ya contiene las columnas actuales. Este
    reparador añade exclusivamente columnas que faltan: no elimina tablas,
    registros, índices ni valores existentes.

    Las columnas nuevas se añaden inicialmente como anulables para conservar
    todas las filas históricas. Las reglas de obligatoriedad siguen aplicando
    para los nuevos datos mediante los servicios y schemas de MotorDesk.
    """
    inspector = inspect(engine)
    preparador = engine.dialect.identifier_preparer

    with engine.begin() as connection:
        # No necesitamos un orden de dependencias: solo añadimos columnas a
        # tablas ya existentes. Iterar directamente evita avisos por los ciclos
        # legítimos entre citas, órdenes y facturas.
        for tabla in Base.metadata.tables.values():
            if not inspector.has_table(tabla.name):
                continue

            columnas_existentes = {
                columna["name"]
                for columna in inspector.get_columns(tabla.name)
            }

            for columna_modelo in tabla.columns:
                if columna_modelo.name in columnas_existentes:
                    continue

                # Creamos una definición simple y compatible. No copiamos FK
                # ni restricciones a posteriori porque una instalación vieja
                # puede contener valores históricos que aún no las cumplen.
                columna_nueva = Column(
                    columna_modelo.name,
                    columna_modelo.type,
                    nullable=True,
                    server_default=columna_modelo.server_default,
                )
                definicion = str(
                    CreateColumn(columna_nueva).compile(
                        dialect=engine.dialect
                    )
                )
                nombre_tabla = preparador.quote(tabla.name)

                connection.execute(
                    text(
                        f"ALTER TABLE {nombre_tabla} "
                        f"ADD COLUMN {definicion}"
                    )
                )
                logger.warning(
                    "Se reparó la columna heredada %s.%s durante el arranque.",
                    tabla.name,
                    columna_modelo.name,
                )

        # Una factura histórica sin este estado no debe romper los indicadores
        # de cobros del Dashboard después de recibir la columna nueva.
        if inspector.has_table("facturas"):
            columnas_factura = {
                columna["name"]
                for columna in inspector.get_columns("facturas")
            }
            if "estado_cobro" in columnas_factura:
                connection.execute(
                    text(
                        "UPDATE facturas "
                        "SET estado_cobro = 'PENDIENTE' "
                        "WHERE estado_cobro IS NULL"
                    )
                )


def inicializar_base_datos() -> None:
    """Crea el esquema de una instalación nueva o actualiza una existente.

    En la edición nativa el directorio de trabajo es ``ProgramData`` y no la
    carpeta del ejecutable. Por eso Alembic se localiza explícitamente junto a
    sus migraciones empaquetadas, en vez de depender del directorio actual.
    """
    raiz_distribucion = Path(
        getattr(sys, "_MEIPASS", Path(__file__).resolve().parents[2])
    )
    config = Config(str(raiz_distribucion / "alembic.ini"))

    # El contexto mantiene una transaccion abierta exclusivamente para el
    # advisory lock. Alembic abre sus propias conexiones para el DDL, mientras
    # que este bloqueo permanece activo hasta terminar toda la preparacion.
    with engine.begin() as connection:
        _adquirir_bloqueo_migraciones(connection)
        logger.info("Comprobando y actualizando el esquema de MotorDesk.")

        if _base_sin_version():
            logger.info(
                "La base de datos no tiene historial Alembic; creando el esquema inicial."
            )
            Base.metadata.create_all(bind=engine)
            _reparar_columnas_heredadas()
            command.stamp(config, "head")
            logger.info("Esquema inicial creado y marcado en la revision vigente.")
            return

        if _esquema_ya_actualizado(config):
            logger.info("El esquema de MotorDesk ya está actualizado.")
            _reparar_columnas_heredadas()
            return

        logger.info("Aplicando las migraciones pendientes de MotorDesk.")
        command.upgrade(config, "head")
        logger.info("Migraciones Alembic aplicadas correctamente.")
        _reparar_columnas_heredadas()
        logger.info("Comprobacion del esquema de MotorDesk completada.")


if __name__ == "__main__":
    inicializar_base_datos()
