"""Pruebas de seguridad y aislamiento del certificado electrónico."""

import asyncio
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import ANY, patch

from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives.serialization import pkcs12
from cryptography.x509.oid import NameOID
from starlette.datastructures import UploadFile

from app.api.v1.certificado_electronico import _leer_certificado
from app.services.certificado_electronico_service import (
    CertificadoElectronicoService,
)
from app.services.verifactu_aeat_service import VerifactuAeatService


PASSWORD = "clave-prueba"
NIF_EMPRESA = "B12345674"


def crear_pkcs12(nif: str = NIF_EMPRESA) -> bytes:
    clave = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    ahora = datetime.now(timezone.utc)
    sujeto = x509.Name([
        x509.NameAttribute(NameOID.COMMON_NAME, "Taller de prueba"),
        x509.NameAttribute(NameOID.SERIAL_NUMBER, nif),
    ])
    certificado = (
        x509.CertificateBuilder()
        .subject_name(sujeto)
        .issuer_name(sujeto)
        .public_key(clave.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(ahora - timedelta(days=1))
        .not_valid_after(ahora + timedelta(days=30))
        .sign(clave, hashes.SHA256())
    )
    return pkcs12.serialize_key_and_certificates(
        b"certificado-prueba",
        clave,
        certificado,
        None,
        serialization.BestAvailableEncryption(PASSWORD.encode()),
    )


class CertificadoElectronicoServiceTests(unittest.TestCase):
    def test_guarda_en_almacen_privado_y_vinculado_al_nif_empresa(self):
        empresa = SimpleNamespace(id=7, nif=NIF_EMPRESA)
        creado = []
        directorio_privado = (
            CertificadoElectronicoService.BACKEND_DIR
            / "storage"
            / "certificados"
        )

        def crear(_db, datos):
            creado.append(datos)
            return SimpleNamespace(**datos)

        with (
            patch.object(CertificadoElectronicoService, "_directorio_absoluto", return_value=directorio_privado),
            patch("app.services.certificado_electronico_service.Path.write_bytes"),
            patch("app.services.certificado_electronico_service.EmpresaRepository.get_by_id", return_value=empresa),
            patch("app.services.certificado_electronico_service.CertificadoElectronicoRepository.get_by_empresa", return_value=None),
            patch("app.services.certificado_electronico_service.CertificadoElectronicoRepository.create", side_effect=crear),
            patch("app.services.certificado_electronico_service.SecretosService.cifrar", return_value="secreto-cifrado"),
        ):
            certificado = CertificadoElectronicoService.guardar(
                db=SimpleNamespace(),
                empresa_id=7,
                nombre_archivo="certificado.pfx",
                contenido=crear_pkcs12(),
                password=PASSWORD,
            )

        ruta = Path(certificado.ruta_archivo)
        self.assertEqual(ruta.parent, Path("storage") / "certificados")
        self.assertNotIn("uploads", certificado.ruta_archivo)
        self.assertEqual(creado[0]["nif_titular"], NIF_EMPRESA)

    def test_rechaza_un_certificado_de_otro_titular(self):
        empresa = SimpleNamespace(id=7, nif=NIF_EMPRESA)
        with patch(
            "app.services.certificado_electronico_service.EmpresaRepository.get_by_id",
            return_value=empresa,
        ):
            with self.assertRaisesRegex(ValueError, "no coincide"):
                CertificadoElectronicoService.guardar(
                    db=SimpleNamespace(),
                    empresa_id=7,
                    nombre_archivo="certificado.p12",
                    contenido=crear_pkcs12("A12345678"),
                    password=PASSWORD,
                )

    def test_no_resuelve_rutas_fuera_del_almacen_privado(self):
        with self.assertRaisesRegex(RuntimeError, "ruta del certificado"):
            CertificadoElectronicoService._ruta_absoluta("uploads/../.env")

    def test_aeat_usa_la_empresa_solicitada(self):
        with patch(
            "app.services.verifactu_aeat_service.CertificadoElectronicoService.obtener_credenciales_envio",
            return_value=("/privado/cert.p12", "clave"),
        ) as obtener:
            resultado = VerifactuAeatService._obtener_certificado_taller(
                SimpleNamespace(),
                23,
            )

        self.assertEqual(resultado, ("/privado/cert.p12", "clave"))
        obtener.assert_called_once_with(ANY, 23)


class LecturaCertificadoTests(unittest.TestCase):
    def test_rechaza_archivo_mayor_que_el_limite_al_leerlo(self):
        archivo = UploadFile(
            filename="demasiado-grande.p12",
            file=__import__("io").BytesIO(
                b"x" * (CertificadoElectronicoService.TAMANO_MAXIMO + 1)
            ),
        )
        with self.assertRaisesRegex(ValueError, "10 MB"):
            asyncio.run(_leer_certificado(archivo))
