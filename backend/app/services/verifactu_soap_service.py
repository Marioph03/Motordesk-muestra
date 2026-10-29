"""Construcción del sobre SOAP requerido para remitir registros a AEAT."""

from lxml import etree


class VerifactuSoapService:
    """Encapsula la representación SOAP sin mezclarla con reglas fiscales."""


    NS_SOAP = (
        "http://schemas.xmlsoap.org/soap/envelope/"
    )

    @staticmethod
    def envolver(
        xml_registro: str
    ) -> str:

        envelope = etree.Element(
            f"{{{VerifactuSoapService.NS_SOAP}}}Envelope",
            nsmap={
                "soapenv":
                    VerifactuSoapService.NS_SOAP
            }
        )

        body = etree.SubElement(
            envelope,
            f"{{{VerifactuSoapService.NS_SOAP}}}Body"
        )

        registro = etree.fromstring(
            xml_registro.encode("utf-8")
        )

        body.append(registro)

        return etree.tostring(
            envelope,
            encoding="unicode",
            pretty_print=True,
            xml_declaration=False
        )
