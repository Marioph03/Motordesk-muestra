"""Punto de entrada del ejecutable local de MotorDesk."""

import os
import sys
import ipaddress
import socket
import threading
import traceback
from datetime import datetime, timedelta, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit

import uvicorn
from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import ExtendedKeyUsageOID, NameOID
from dotenv import dotenv_values


def iniciar_puente_oauth_loopback(
    puerto_http: int,
    puerto_https: int,
) -> ThreadingHTTPServer:
    """Recibe callbacks OAuth de escritorio y los pasa a la API HTTPS local.

    Google y Microsoft usan un callback loopback HTTP para clientes de
    escritorio. La API de MotorDesk se sirve exclusivamente por HTTPS, así que
    este puente, limitado a 127.0.0.1, evita exponer otra API HTTP en la red.
    """
    rutas_admitidas = {
        "/configuracion/email/google/callback",
        "/configuracion/email/microsoft/callback",
    }

    class ManejadorPuenteOAuth(BaseHTTPRequestHandler):
        def do_GET(self) -> None:  # noqa: N802 - requerido por BaseHTTPRequestHandler
            solicitud = urlsplit(self.path)
            if solicitud.path not in rutas_admitidas:
                self.send_error(404)
                return

            # En la edición nativa la API está publicada bajo /backend. El
            # listener HTTP solo recibe el callback de Google/Microsoft y lo
            # entrega inmediatamente al único servidor HTTPS de MotorDesk.
            destino = f"https://localhost:{puerto_https}/backend{self.path}"
            self.send_response(302)
            self.send_header("Location", destino)
            self.end_headers()

        def log_message(self, _format: str, *_args) -> None:
            # El callback es interno y no debe ensuciar el registro de inicio.
            return

    class ServidorPuenteOAuth(ThreadingHTTPServer):
        allow_reuse_address = True

    servidor = ServidorPuenteOAuth(("127.0.0.1", puerto_http), ManejadorPuenteOAuth)
    threading.Thread(target=servidor.serve_forever, daemon=True).start()
    print(f"MotorDesk: puente OAuth local activo en 127.0.0.1:{puerto_http}.")
    return servidor


def cargar_configuracion_externa() -> None:
    """Carga secretos externos antes de importar la aplicacion.

    En una instalacion distribuida el archivo ``.env`` vive junto al
    ejecutable, nunca dentro del paquete. Durante el desarrollo se conservan
    tambien las rutas ``backend/.env`` y ``.env`` de la raiz del proyecto.
    Las variables ya presentes en Windows tienen siempre prioridad.
    """
    variables_del_sistema = set(os.environ)

    if getattr(sys, "frozen", False):
        directorio_ejecutable = Path(sys.executable).resolve().parent
        directorio_programdata = Path(
            os.environ.get("PROGRAMDATA", r"C:\ProgramData")
        ) / "MotorDesk"
        archivos_env = [
            directorio_ejecutable.parent.parent.parent / ".env",
            directorio_ejecutable.parent.parent / ".env",
            directorio_ejecutable / ".env",
            # La instalacion de Windows guarda los secretos fuera del paquete
            # para que una actualizacion del ejecutable no los sobrescriba.
            directorio_programdata / ".env",
        ]
    else:
        directorio_backend = Path(__file__).resolve().parent
        archivos_env = [
            directorio_backend.parent / ".env",
            directorio_backend / ".env",
        ]

    valores: dict[str, str] = {}
    archivo_instalacion: Path | None = None

    for archivo_env in archivos_env:
        if archivo_env.is_file():
            try:
                valores.update(
                    {
                        clave: valor
                        for clave, valor in dotenv_values(archivo_env).items()
                        if valor is not None
                    }
                )
                archivo_instalacion = archivo_env
            except PermissionError:
                # Una cuenta sin acceso al secreto de una instalacion ajena no
                # debe impedir que el launcher pueda usar su propia configuracion.
                continue

    for clave, valor in valores.items():
        os.environ.setdefault(clave, valor)

    # Solo se registra un indicador no sensible. Facilita diagnosticar una
    # instalacion nativa sin revelar nunca URL, contrasenas ni claves.
    if archivo_instalacion is not None:
        os.environ["MOTORDESK_EXTERNAL_CONFIG_LOADED"] = "true"

    # En el ejecutable distribuido la configuracion de ProgramData es la
    # autoridad de la instalacion. Un .env residual junto al binario nunca
    # debe convertir accidentalmente la API nativa en modo desarrollo.
    if getattr(sys, "frozen", False):
        archivo_nativo = directorio_programdata / ".env"
        if archivo_nativo.is_file():
            try:
                for clave, valor in dotenv_values(archivo_nativo).items():
                    # La configuracion de la instalacion prevalece sobre
                    # cualquier .env empaquetado, pero nunca sobre una
                    # variable definida expresamente en Windows.
                    if valor is not None and clave not in variables_del_sistema:
                        os.environ[clave] = valor
                os.environ["MOTORDESK_NATIVE_CONFIG_LOADED"] = "true"
            except PermissionError:
                # El servicio instalado recibe permiso de lectura. Este caso
                # solo cubre ejecuciones de diagnostico desde otra cuenta.
                pass


cargar_configuracion_externa()


def rutas_tls_local() -> tuple[Path, Path]:
    """Devuelve las rutas persistentes del certificado local del servidor."""
    directorio = Path(os.environ.get("PROGRAMDATA", r"C:\ProgramData")) / "MotorDesk" / "tls"
    return directorio / "motordesk-local-cert.pem", directorio / "motordesk-local-key.pem"


def rutas_ca_local() -> tuple[Path, Path]:
    """Devuelve el certificado público y la clave privada de la CA local."""
    directorio = Path(os.environ.get("PROGRAMDATA", r"C:\ProgramData")) / "MotorDesk" / "tls"
    return directorio / "motordesk-local-ca.cer", directorio / "motordesk-local-ca-key.pem"


def _direcciones_ip_lan() -> list[ipaddress.IPv4Address]:
    """Obtiene IPv4 privadas candidatas para el certificado del servidor."""
    candidatas: set[str] = set()

    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as conexion:
            # No se envía tráfico: connect solo deja que Windows seleccione la
            # interfaz de red principal.
            conexion.connect(("192.0.2.1", 1))
            candidatas.add(conexion.getsockname()[0])
    except OSError:
        pass

    try:
        candidatas.update(socket.gethostbyname_ex(socket.gethostname())[2])
    except OSError:
        pass

    resultado: list[ipaddress.IPv4Address] = []
    for direccion in candidatas:
        try:
            ip = ipaddress.ip_address(direccion)
        except ValueError:
            continue
        if isinstance(ip, ipaddress.IPv4Address) and ip.is_private and not ip.is_loopback:
            resultado.append(ip)
    return resultado


def _crear_ca_local(certificado_ca: Path, clave_ca: Path):
    """Crea una CA privada exclusiva de esta instalación MotorDesk."""
    privada = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    ahora = datetime.now(timezone.utc)
    sujeto = x509.Name([
        x509.NameAttribute(NameOID.COMMON_NAME, "MotorDesk Local CA"),
    ])
    certificado = (
        x509.CertificateBuilder()
        .subject_name(sujeto)
        .issuer_name(sujeto)
        .public_key(privada.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(ahora - timedelta(minutes=1))
        .not_valid_after(ahora + timedelta(days=3650))
        .add_extension(x509.BasicConstraints(ca=True, path_length=0), critical=True)
        .add_extension(
            x509.KeyUsage(
                digital_signature=False,
                content_commitment=False,
                key_encipherment=False,
                data_encipherment=False,
                key_agreement=False,
                key_cert_sign=True,
                crl_sign=True,
                encipher_only=False,
                decipher_only=False,
            ),
            critical=True,
        )
        .sign(privada, hashes.SHA256())
    )
    clave_ca.write_bytes(
        privada.private_bytes(
            serialization.Encoding.PEM,
            serialization.PrivateFormat.TraditionalOpenSSL,
            serialization.NoEncryption(),
        )
    )
    certificado_ca.write_bytes(certificado.public_bytes(serialization.Encoding.DER))
    return certificado, privada


def asegurar_certificado_tls_local() -> tuple[Path, Path]:
    """Crea un certificado local para localhost solo cuando no existe.

    El instalador añade la parte pública al almacén de confianza de Windows.
    Así Meta puede usar HTTPS en el propio PC servidor sin depender de una
    URL externa ni exponer PostgreSQL a Internet.
    """
    certificado, clave = rutas_tls_local()
    certificado_ca, clave_ca = rutas_ca_local()
    certificado.parent.mkdir(parents=True, exist_ok=True)

    if certificado_ca.is_file() and clave_ca.is_file():
        ca = x509.load_der_x509_certificate(certificado_ca.read_bytes())
        privada_ca = serialization.load_pem_private_key(
            clave_ca.read_bytes(),
            password=None,
        )
        if certificado.is_file() and clave.is_file():
            certificado_existente = x509.load_pem_x509_certificate(
                certificado.read_bytes()
            )
            if certificado_existente.issuer == ca.subject:
                return certificado, clave
    else:
        ca, privada_ca = _crear_ca_local(certificado_ca, clave_ca)

    privada = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    sujeto = x509.Name([
        x509.NameAttribute(NameOID.COMMON_NAME, "motordesk.lan"),
    ])
    ahora = datetime.now(timezone.utc)
    nombres_alternativos = [
        x509.DNSName("localhost"),
        x509.DNSName("motordesk.lan"),
        x509.IPAddress(ipaddress.ip_address("127.0.0.1")),
    ]
    nombres_alternativos.extend(
        x509.IPAddress(direccion)
        for direccion in _direcciones_ip_lan()
    )
    cert = (
        x509.CertificateBuilder()
        .subject_name(sujeto)
        .issuer_name(ca.subject)
        .public_key(privada.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(ahora - timedelta(minutes=1))
        .not_valid_after(ahora + timedelta(days=3650))
        .add_extension(x509.SubjectAlternativeName(nombres_alternativos), critical=False)
        .add_extension(x509.BasicConstraints(ca=False, path_length=None), critical=True)
        .add_extension(
            x509.ExtendedKeyUsage([ExtendedKeyUsageOID.SERVER_AUTH]),
            critical=False,
        )
        .sign(privada_ca, hashes.SHA256())
    )
    clave.write_bytes(
        privada.private_bytes(
            serialization.Encoding.PEM,
            serialization.PrivateFormat.TraditionalOpenSSL,
            serialization.NoEncryption(),
        )
    )
    certificado.write_bytes(cert.public_bytes(serialization.Encoding.PEM))
    return certificado, clave


if "--generate-local-tls-certificate" in sys.argv:
    cert_path, _ = asegurar_certificado_tls_local()
    print(f"MotorDesk: certificado TLS local creado en {cert_path}")
    raise SystemExit(0)


def preparar_directorio_datos_nativo() -> None:
    """Separa los datos modificables del ejecutable empaquetado.

    Un servicio de Windows no tiene como directorio de trabajo fiable la
    carpeta del programa. Los adjuntos, logos y copias se guardan por tanto en
    ProgramData, que sobrevive a las actualizaciones de MotorDesk.
    """
    if not getattr(sys, "frozen", False):
        return

    directorio_datos = Path(
        os.environ.get("PROGRAMDATA", r"C:\ProgramData")
    ) / "MotorDesk"

    for ruta in (
        directorio_datos / "uploads" / "ordenes",
        directorio_datos / "uploads" / "avatars",
        directorio_datos / "static" / "uploads" / "taller",
        directorio_datos / "FE",
        directorio_datos / "backups",
    ):
        ruta.mkdir(parents=True, exist_ok=True)

    os.chdir(directorio_datos)


preparar_directorio_datos_nativo()


def ejecutar_migraciones() -> int:
    """Actualiza la base de datos como paso controlado del instalador."""
    try:
        from app.database.bootstrap import inicializar_base_datos

        print("MotorDesk: iniciando actualización del esquema de datos.")
        inicializar_base_datos()
        print("MotorDesk: actualización del esquema completada.")
        return 0
    except Exception:
        print("MotorDesk: la actualización del esquema ha fallado.")
        traceback.print_exc()
        return 1


if "--migrate-only" in sys.argv:
    raise SystemExit(ejecutar_migraciones())


from app.main import app


def main() -> None:
    """Inicia la API del servidor MotorDesk.

    La base PostgreSQL sigue ligada a ``127.0.0.1``. Solo la interfaz web y
    la API se exponen en la LAN, para que los demás equipos del taller usen el
    mismo servidor sin acceder nunca directamente a la base de datos.
    """
    puerto = int(os.getenv("MOTORDESK_BACKEND_PORT", "8000"))
    tls_activo = os.getenv("MOTORDESK_HTTPS_ENABLED", "false").strip().lower() in {"1", "true", "yes", "si", "sí"}
    puerto_https = int(os.getenv("MOTORDESK_HTTPS_PORT", "8443"))
    host_predeterminado = "0.0.0.0" if getattr(sys, "frozen", False) else "127.0.0.1"
    host = os.getenv("MOTORDESK_BIND_HOST", host_predeterminado).strip()

    if not 1 <= puerto <= 65535 or not 1 <= puerto_https <= 65535:
        raise ValueError("MOTORDESK_BACKEND_PORT no contiene un puerto valido.")

    if host not in {"127.0.0.1", "0.0.0.0", "::1", "::"}:
        raise ValueError("MOTORDESK_BIND_HOST contiene una direccion no admitida.")

    print(
        "MotorDesk: configuracion nativa cargada="
        f"{os.getenv('MOTORDESK_NATIVE_CONFIG_LOADED') == 'true'}; "
        "interfaz nativa="
        f"{os.getenv('MOTORDESK_NATIVE_FRONTEND') == 'true'}; "
        f"red local={'activa' if host in {'0.0.0.0', '::'} else 'desactivada'}"
    )
    if not tls_activo:
        uvicorn.run(app, host=host, port=puerto, log_level="info")
        return

    cert_path, key_path = asegurar_certificado_tls_local()

    try:
        iniciar_puente_oauth_loopback(puerto, puerto_https)
    except OSError as exc:
        raise RuntimeError(
            "No se pudo abrir el puente local de correo en el puerto "
            f"{puerto}. Cierra la aplicación que lo esté usando y vuelve a intentarlo."
        ) from exc

    # La edicion nativa publica una unica instancia Uvicorn en HTTPS. Antes se
    # iniciaban HTTP y HTTPS en dos hilos con la misma aplicacion FastAPI: cada
    # uno disparaba el evento ``startup`` y podia intentar preparar Alembic al
    # mismo tiempo. Eso dejaba algunas instalaciones esperando sin llegar a
    # abrir el puerto seguro. Los puestos de la red deben usar HTTPS:8443.
    #
    # ``puerto`` se conserva en la configuracion por compatibilidad con .env
    # anteriores, pero no se expone HTTP sin cifrar en una instalacion nativa.
    print(
        "MotorDesk: iniciando un unico servidor HTTPS en "
        f"{host}:{puerto_https}."
    )
    uvicorn.run(
        app,
        host=host,
        port=puerto_https,
        log_level="info",
        ssl_certfile=str(cert_path),
        ssl_keyfile=str(key_path),
    )


if __name__ == "__main__":
    main()
