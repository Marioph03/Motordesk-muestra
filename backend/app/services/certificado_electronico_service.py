import os
import re
import shutil
import sys

from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from cryptography.hazmat.primitives.serialization.pkcs12 import (
    load_key_and_certificates,
)
from cryptography.x509.oid import (
    NameOID,
    ObjectIdentifier,
)
from sqlalchemy.orm import Session

from app.repositories.certificado_electronico_repository import (
    CertificadoElectronicoRepository,
)
from app.repositories.empresa_repository import EmpresaRepository
from app.services.secretos_service import SecretosService


class CertificadoElectronicoService:

    EXTENSIONES_PERMITIDAS = {
        ".p12",
        ".pfx",
    }

    TAMANO_MAXIMO = 10 * 1024 * 1024

    # backend/
    BACKEND_DIR = Path(__file__).resolve().parents[2]

    # Los certificados PKCS#12 contienen una clave privada. Nunca pueden vivir
    # bajo ``uploads`` porque ese directorio se expone mediante StaticFiles.
    DIRECTORIO_RELATIVO = Path("storage") / "certificados"
    DIRECTORIO_LEGACY_RELATIVO = Path("uploads") / "certificados"

    # organizationIdentifier.
    OID_ORGANIZATION_IDENTIFIER = ObjectIdentifier(
        "2.5.4.97"
    )

    PATRON_NIF = re.compile(
        r"\b("
        r"[XYZ]\d{7}[A-Z]"
        r"|"
        r"\d{8}[A-Z]"
        r"|"
        r"[ABCDEFGHJNPQRSUVW]\d{7}[0-9A-J]"
        r")\b",
        re.IGNORECASE,
    )

    # =========================================================
    # UTILIDADES
    # =========================================================

    @classmethod
    def _raiz_almacen_privado(cls) -> Path:
        """Devuelve una ubicación escribible para secretos de la instalación."""
        if getattr(sys, "frozen", False) or os.getenv(
            "MOTORDESK_NATIVE_FRONTEND"
        ) == "true":
            return Path(
                os.environ.get("PROGRAMDATA", r"C:\ProgramData")
            ) / "MotorDesk"

        return cls.BACKEND_DIR

    @classmethod
    def _directorio_absoluto(cls) -> Path:

        directorio = (
            cls._raiz_almacen_privado()
            / cls.DIRECTORIO_RELATIVO
        )

        directorio.mkdir(
            parents=True,
            exist_ok=True,
        )

        return directorio

    @classmethod
    def _ruta_absoluta(
        cls,
        ruta: str,
    ) -> Path:
        """Resuelve únicamente rutas dentro del almacén privado.

        La ruta viene de la base de datos; validar su contención evita que un
        dato corrupto convierta la sustitución o el borrado en acceso a otros
        ficheros del backend.
        """
        directorio = cls._directorio_absoluto().resolve()
        ruta_path = Path(ruta)
        ruta_absoluta = (
            ruta_path.resolve()
            if ruta_path.is_absolute()
            else (cls._raiz_almacen_privado() / ruta_path).resolve()
        )

        try:
            ruta_absoluta.relative_to(directorio)
        except ValueError as exc:
            raise RuntimeError(
                "La ruta del certificado no es válida."
            ) from exc

        return ruta_absoluta

    @staticmethod
    def _obtener_atributo(
        nombre,
        oid,
    ) -> str | None:

        atributos = nombre.get_attributes_for_oid(
            oid
        )

        if not atributos:
            return None

        return atributos[0].value

    # =========================================================
    # DATOS DEL CERTIFICADO
    # =========================================================

    @classmethod
    def _extraer_titular(
        cls,
        certificado,
    ) -> str | None:

        titular = cls._obtener_atributo(
            certificado.subject,
            NameOID.COMMON_NAME,
        )

        if titular:
            return titular

        organizacion = cls._obtener_atributo(
            certificado.subject,
            NameOID.ORGANIZATION_NAME,
        )

        if organizacion:
            return organizacion

        return certificado.subject.rfc4514_string()

    @classmethod
    def _extraer_emisor(
        cls,
        certificado,
    ) -> str | None:

        emisor = cls._obtener_atributo(
            certificado.issuer,
            NameOID.COMMON_NAME,
        )

        if emisor:
            return emisor

        organizacion = cls._obtener_atributo(
            certificado.issuer,
            NameOID.ORGANIZATION_NAME,
        )

        if organizacion:
            return organizacion

        return certificado.issuer.rfc4514_string()

    @classmethod
    def _extraer_nif(
        cls,
        certificado,
    ) -> str | None:

        candidatos = []

        # Muchos certificados españoles incluyen el NIF aquí.
        for oid in (
            cls.OID_ORGANIZATION_IDENTIFIER,
            NameOID.SERIAL_NUMBER,
        ):

            atributos = (
                certificado.subject
                .get_attributes_for_oid(oid)
            )

            for atributo in atributos:
                candidatos.append(
                    atributo.value
                )

        # Fallback sobre el subject completo.
        candidatos.append(
            certificado.subject.rfc4514_string()
        )

        for candidato in candidatos:

            coincidencia = cls.PATRON_NIF.search(
                candidato.upper()
            )

            if coincidencia:
                return coincidencia.group(1).upper()

        return None

    # =========================================================
    # VALIDACIÓN PKCS#12
    # =========================================================

    @classmethod
    def _analizar_certificado(
        cls,
        contenido: bytes,
        password: str,
    ) -> dict:

        if not contenido:
            raise ValueError(
                "El certificado está vacío."
            )

        if len(contenido) > cls.TAMANO_MAXIMO:
            raise ValueError(
                "El certificado supera el tamaño máximo permitido de 10 MB."
            )

        if not password:
            raise ValueError(
                "Debes introducir la contraseña del certificado."
            )

        try:

            clave_privada, certificado, _ = (
                load_key_and_certificates(
                    contenido,
                    password.encode("utf-8"),
                )
            )

        except (ValueError, TypeError) as exc:

            raise ValueError(
                "No se ha podido abrir el certificado. "
                "Comprueba que el archivo sea un .p12/.pfx válido "
                "y que la contraseña sea correcta."
            ) from exc

        if certificado is None:
            raise ValueError(
                "El archivo no contiene un certificado válido."
            )

        if clave_privada is None:
            raise ValueError(
                "El certificado no contiene una clave privada."
            )

        # cryptography moderno proporciona propiedades UTC.
        if hasattr(
            certificado,
            "not_valid_before_utc",
        ):
            fecha_desde = (
                certificado
                .not_valid_before_utc
            )
        else:
            fecha_desde = (
                certificado
                .not_valid_before
                .replace(
                    tzinfo=timezone.utc
                )
            )

        if hasattr(
            certificado,
            "not_valid_after_utc",
        ):
            fecha_hasta = (
                certificado
                .not_valid_after_utc
            )
        else:
            fecha_hasta = (
                certificado
                .not_valid_after
                .replace(
                    tzinfo=timezone.utc
                )
            )

        ahora = datetime.now(
            timezone.utc
        )

        if ahora < fecha_desde:
            raise ValueError(
                "El certificado todavía no es válido."
            )

        if ahora >= fecha_hasta:
            raise ValueError(
                "El certificado electrónico está caducado."
            )

        return {
            "titular":
                cls._extraer_titular(
                    certificado
                ),

            "nif_titular":
                cls._extraer_nif(
                    certificado
                ),

            "emisor":
                cls._extraer_emisor(
                    certificado
                ),

            # La BD utiliza DateTime sin timezone.
            "fecha_validez_desde":
                fecha_desde
                .astimezone(timezone.utc)
                .replace(tzinfo=None),

            "fecha_caducidad":
                fecha_hasta
                .astimezone(timezone.utc)
                .replace(tzinfo=None),
        }

    @staticmethod
    def _normalizar_nif(nif: str | None) -> str:
        """Normaliza el NIF/CIF para comparaciones no sensibles al formato."""
        return re.sub(r"[^A-Z0-9]", "", (nif or "").upper())

    # =========================================================
    # CONSULTA
    # =========================================================

    @staticmethod
    def obtener(
        db: Session,
        empresa_id: int,
    ):

        return (
            CertificadoElectronicoRepository
            .get_by_empresa(
                db,
                empresa_id,
            )
        )

    @staticmethod
    def esta_caducado(
        certificado,
    ) -> bool:

        if (
            certificado is None
            or certificado.fecha_caducidad is None
        ):
            return False

        fecha = certificado.fecha_caducidad

        if fecha.tzinfo is None:
            fecha = fecha.replace(
                tzinfo=timezone.utc
            )

        return (
            fecha
            <= datetime.now(timezone.utc)
        )

    @classmethod
    def archivo_disponible(cls, certificado) -> bool:
        """Indica si el certificado conserva un fichero privado utilizable."""
        if certificado is None:
            return False
        try:
            ruta = cls._ruta_absoluta(certificado.ruta_archivo)
        except RuntimeError:
            return False
        return ruta.is_file()

    @classmethod
    def migrar_desde_directorio_publico(cls, db: Session) -> int:
        """Retira certificados heredados del directorio servido por HTTP.

        Solo procesa rutas con el prefijo histórico exacto; una referencia
        anómala se deja intacta y será rechazada posteriormente por
        ``_ruta_absoluta``.
        """
        migrados = 0
        raiz_almacen = cls._raiz_almacen_privado()
        directorio_legacy = (
            raiz_almacen / cls.DIRECTORIO_LEGACY_RELATIVO
        ).resolve()
        directorio_privado = cls._directorio_absoluto()

        for certificado in CertificadoElectronicoRepository.get_all(db):
            ruta_relativa = Path(certificado.ruta_archivo)
            try:
                ruta_relativa.relative_to(cls.DIRECTORIO_LEGACY_RELATIVO)
            except ValueError:
                continue

            ruta_legacy = (raiz_almacen / ruta_relativa).resolve()
            try:
                ruta_legacy.relative_to(directorio_legacy)
            except ValueError:
                continue

            if not ruta_legacy.is_file():
                continue

            ruta_nueva = directorio_privado / ruta_legacy.name
            if ruta_nueva.exists():
                raise RuntimeError(
                    "Ya existe un certificado privado con el mismo nombre."
                )

            try:
                shutil.copy2(ruta_legacy, ruta_nueva)
                try:
                    os.chmod(ruta_nueva, 0o600)
                except OSError:
                    pass
                certificado.ruta_archivo = (
                    cls.DIRECTORIO_RELATIVO / ruta_nueva.name
                ).as_posix()
                db.commit()
            except Exception:
                db.rollback()
                if ruta_nueva.exists():
                    ruta_nueva.unlink()
                raise

            ruta_legacy.unlink()
            migrados += 1

        return migrados

    # =========================================================
    # GUARDAR / REEMPLAZAR
    # =========================================================

    @classmethod
    def guardar(
        cls,
        db: Session,
        empresa_id: int,
        nombre_archivo: str,
        contenido: bytes,
        password: str,
    ):

        empresa = EmpresaRepository.get_by_id(
            db,
            empresa_id,
        )

        if empresa is None:
            raise ValueError(
                "Empresa no encontrada."
            )

        extension = (
            Path(nombre_archivo)
            .suffix
            .lower()
        )

        if (
            extension
            not in cls.EXTENSIONES_PERMITIDAS
        ):
            raise ValueError(
                "El certificado debe ser un archivo .p12 o .pfx."
            )

        datos_certificado = (
            cls._analizar_certificado(
                contenido,
                password,
            )
        )

        nif_empresa = cls._normalizar_nif(empresa.nif)
        nif_certificado = cls._normalizar_nif(
            datos_certificado["nif_titular"]
        )
        if not nif_certificado:
            raise ValueError(
                "No se ha podido identificar el NIF del titular del certificado."
            )
        if nif_certificado != nif_empresa:
            raise ValueError(
                "El NIF del certificado no coincide con el NIF de la empresa."
            )

        password_cifrada = (
            SecretosService.cifrar(
                password
            )
        )

        directorio = (
            cls._directorio_absoluto()
        )

        nombre_interno = (
            f"empresa_{empresa_id}_"
            f"{uuid4().hex}"
            f"{extension}"
        )

        ruta_relativa = (
            cls.DIRECTORIO_RELATIVO
            / nombre_interno
        )

        ruta_absoluta = (
            directorio
            / nombre_interno
        )

        certificado_actual = (
            CertificadoElectronicoRepository
            .get_by_empresa(
                db,
                empresa_id,
            )
        )

        ruta_anterior = None

        if certificado_actual is not None:
            # Una instalación antigua puede conservar una fila cuyo fichero
            # ya no exista bajo uploads/. No impedimos subir un reemplazo
            # válido; la referencia heredada nunca se elimina por ruta.
            try:
                ruta_anterior = cls._ruta_absoluta(
                    certificado_actual.ruta_archivo
                )
            except RuntimeError:
                ruta_anterior = None

        try:

            ruta_absoluta.write_bytes(
                contenido
            )

            # En sistemas compatibles restringimos
            # los permisos del fichero.
            try:
                os.chmod(
                    ruta_absoluta,
                    0o600,
                )
            except OSError:
                pass

            datos = {
                "empresa_id":
                    empresa_id,

                "nombre_archivo":
                    Path(
                        nombre_archivo
                    ).name,

                "ruta_archivo":
                    ruta_relativa.as_posix(),

                "password_cifrada":
                    password_cifrada,

                "titular":
                    datos_certificado[
                        "titular"
                    ],

                "nif_titular":
                    datos_certificado[
                        "nif_titular"
                    ],

                "emisor":
                    datos_certificado[
                        "emisor"
                    ],

                "fecha_validez_desde":
                    datos_certificado[
                        "fecha_validez_desde"
                    ],

                "fecha_caducidad":
                    datos_certificado[
                        "fecha_caducidad"
                    ],

                "activo":
                    True,
            }

            if certificado_actual is None:

                certificado = (
                    CertificadoElectronicoRepository
                    .create(
                        db,
                        datos,
                    )
                )

            else:

                # empresa_id no cambia.
                datos.pop(
                    "empresa_id",
                    None,
                )

                certificado = (
                    CertificadoElectronicoRepository
                    .update(
                        db,
                        certificado_actual,
                        datos,
                    )
                )

        except Exception:

            db.rollback()

            if ruta_absoluta.exists():

                try:
                    ruta_absoluta.unlink()
                except OSError:
                    pass

            raise

        # Eliminamos el certificado antiguo
        # solamente después de guardar correctamente
        # el nuevo.
        if (
            ruta_anterior is not None
            and ruta_anterior != ruta_absoluta
            and ruta_anterior.exists()
        ):

            try:
                ruta_anterior.unlink()
            except OSError:
                pass

        return certificado

    # =========================================================
    # ELIMINAR
    # =========================================================

    @classmethod
    def eliminar(
        cls,
        db: Session,
        empresa_id: int,
    ) -> None:

        certificado = (
            CertificadoElectronicoRepository
            .get_by_empresa(
                db,
                empresa_id,
            )
        )

        if certificado is None:
            raise ValueError(
                "No hay ningún certificado configurado."
            )

        try:
            ruta = cls._ruta_absoluta(certificado.ruta_archivo)
        except RuntimeError:
            ruta = None

        CertificadoElectronicoRepository.delete(
            db,
            certificado,
        )

        if ruta is not None and ruta.exists():

            try:
                ruta.unlink()
            except OSError:
                pass

    # =========================================================
    # USO INTERNO VERI*FACTU
    # =========================================================

    @classmethod
    def obtener_credenciales_envio(
        cls,
        db: Session,
        empresa_id: int,
    ) -> tuple[str, str]:

        certificado = (
            CertificadoElectronicoRepository
            .get_by_empresa(
                db,
                empresa_id,
            )
        )

        if certificado is None:
            raise ValueError(
                "El taller no tiene un certificado electrónico configurado."
            )

        if not certificado.activo:
            raise ValueError(
                "El certificado electrónico está desactivado."
            )

        if cls.esta_caducado(
            certificado
        ):
            raise ValueError(
                "El certificado electrónico está caducado."
            )

        ruta = cls._ruta_absoluta(
            certificado.ruta_archivo
        )

        if not ruta.exists():
            raise ValueError(
                "No se encuentra el archivo del certificado electrónico."
            )

        password = (
            SecretosService.descifrar(
                certificado.password_cifrada
            )
        )

        return (
            str(ruta),
            password,
        )
