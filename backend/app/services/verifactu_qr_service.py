"""Generación del QR fiscal incluido en documentos VERI*FACTU."""

from io import BytesIO
from urllib.parse import urlencode

import qrcode
from qrcode.constants import ERROR_CORRECT_M

from app.config.verifactu_config import VerifactuConfig


class VerifactuQrService:
    """Construye la URL de consulta y su imagen QR en memoria."""


    TEST_BASE_URL = (
        "https://prewww2.aeat.es/"
        "wlpl/TIKE-CONT/ValidarQR"
    )

    PROD_BASE_URL = (
        "https://www2.agenciatributaria.gob.es/"
        "wlpl/TIKE-CONT/ValidarQR"
    )

    @staticmethod
    def generar_url(
        factura,
        empresa
    ) -> str:

        if not empresa:
            raise ValueError(
                "No hay datos de empresa configurados"
            )

        if not getattr(
            empresa,
            "nif",
            None
        ):
            raise ValueError(
                "La empresa no tiene NIF configurado"
            )

        if not factura.numero:
            raise ValueError(
                "La factura no tiene número"
            )

        if not factura.fecha_emision:
            raise ValueError(
                "La factura no tiene fecha de emisión"
            )

        if factura.total is None:
            raise ValueError(
                "La factura no tiene importe total"
            )

        entorno = (
            VerifactuConfig
            .ENVIRONMENT
            .upper()
        )

        if entorno == "TEST":
            base_url = (
                VerifactuQrService
                .TEST_BASE_URL
            )
        elif entorno in (
            "PROD",
            "PRODUCTION"
        ):
            base_url = (
                VerifactuQrService
                .PROD_BASE_URL
            )
        else:
            raise ValueError(
                "Entorno VERI*FACTU no válido"
            )

        parametros = {
            "nif": empresa.nif,
            "numserie": factura.numero,
            "fecha":
                factura.fecha_emision.strftime(
                    "%d-%m-%Y"
                ),
            "importe":
                VerifactuQrService
                ._formatear_importe(
                    factura.total
                )
        }

        return (
            f"{base_url}?"
            f"{urlencode(parametros)}"
        )

    @staticmethod
    def _formatear_importe(
        importe
    ) -> str:

        valor = format(
            float(importe),
            ".2f"
        )

        # AEAT admite decimales sin necesidad
        # de conservar ceros finales.
        return (
            valor
            .rstrip("0")
            .rstrip(".")
        )

    @staticmethod
    def generar_qr(
        factura,
        empresa
    ) -> BytesIO:

        url = (
            VerifactuQrService.generar_url(
                factura,
                empresa
            )
        )

        qr = qrcode.QRCode(
            version=None,
            error_correction=ERROR_CORRECT_M,
            box_size=10,
            border=4
        )

        qr.add_data(url)

        qr.make(
            fit=True
        )

        imagen = qr.make_image(
            fill_color="black",
            back_color="white"
        )

        buffer = BytesIO()

        imagen.save(
            buffer,
            format="PNG"
        )

        buffer.seek(0)

        return buffer
