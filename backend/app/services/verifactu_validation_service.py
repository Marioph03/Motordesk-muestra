"""Validación local de XML VERI*FACTU contra los esquemas XSD distribuidos."""

from pathlib import Path

from lxml import etree


class VerifactuValidationService:
    """Aísla la comprobación de estructura antes de cualquier envío fiscal."""


    XSD_DIR = (
        Path(__file__).resolve().parent.parent
        / "verifactu"
        / "xsd"
    )

    @staticmethod
    def validar_xml(
        xml_content: str
    ) -> None:

        xsd_path = (
            VerifactuValidationService.XSD_DIR
            / "SuministroLR.xsd"
        )

        if not xsd_path.exists():
            raise ValueError(
                "No se encuentra el esquema "
                "SuministroLR.xsd"
            )

        try:

            xml_document = etree.fromstring(
                xml_content.encode("utf-8")
            )

            with open(
                xsd_path,
                "rb"
            ) as xsd_file:

                xsd_document = etree.parse(
                    xsd_file
                )

            schema = etree.XMLSchema(
                xsd_document
            )

            schema.assertValid(
                xml_document
            )

        except etree.DocumentInvalid as e:

            errores = [
                error.message
                for error
                in e.error_log
            ]

            raise ValueError(
                "XML VERI*FACTU no válido: "
                + " | ".join(errores)
            )

        except etree.XMLSyntaxError as e:

            raise ValueError(
                f"XML VERI*FACTU mal formado: {e}"
            )
