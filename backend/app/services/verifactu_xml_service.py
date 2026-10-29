from lxml import etree

from app.config.verifactu_config import VerifactuConfig


class VerifactuXmlService:

    NS_LR = (
        "https://www2.agenciatributaria.gob.es/"
        "static_files/common/internet/dep/aplicaciones/"
        "es/aeat/tike/cont/ws/SuministroLR.xsd"
    )

    NS_SF = (
        "https://www2.agenciatributaria.gob.es/"
        "static_files/common/internet/dep/aplicaciones/"
        "es/aeat/tike/cont/ws/SuministroInformacion.xsd"
    )

    @staticmethod
    def _sf(nombre: str) -> str:
        return f"{{{VerifactuXmlService.NS_SF}}}{nombre}"

    @staticmethod
    def _lr(nombre: str) -> str:
        return f"{{{VerifactuXmlService.NS_LR}}}{nombre}"

    @staticmethod
    def _anadir_cabecera(root, empresa) -> None:
        cabecera = etree.SubElement(root, VerifactuXmlService._lr("Cabecera"))
        obligado = etree.SubElement(
            cabecera, VerifactuXmlService._sf("ObligadoEmision")
        )
        etree.SubElement(
            obligado, VerifactuXmlService._sf("NombreRazon")
        ).text = (
            getattr(empresa, "razon_social", None)
            or getattr(empresa, "nombre", None)
            or ""
        )
        etree.SubElement(
            obligado, VerifactuXmlService._sf("NIF")
        ).text = empresa.nif

    @staticmethod
    def _anadir_encadenamiento(
        registro_xml,
        empresa,
        hash_anterior: str | None,
        factura_anterior_numero: str | None,
        factura_anterior_fecha: str | None,
    ) -> None:
        encadenamiento = etree.SubElement(
            registro_xml, VerifactuXmlService._sf("Encadenamiento")
        )
        if not hash_anterior:
            etree.SubElement(
                encadenamiento, VerifactuXmlService._sf("PrimerRegistro")
            ).text = "S"
            return

        anterior = etree.SubElement(
            encadenamiento, VerifactuXmlService._sf("RegistroAnterior")
        )
        etree.SubElement(
            anterior, VerifactuXmlService._sf("IDEmisorFactura")
        ).text = empresa.nif
        etree.SubElement(
            anterior, VerifactuXmlService._sf("NumSerieFactura")
        ).text = factura_anterior_numero or ""
        etree.SubElement(
            anterior, VerifactuXmlService._sf("FechaExpedicionFactura")
        ).text = factura_anterior_fecha or ""
        etree.SubElement(
            anterior, VerifactuXmlService._sf("Huella")
        ).text = hash_anterior

    @staticmethod
    def _anadir_sistema_informatico(
        registro_xml,
        nombre_productor: str,
        nif_productor: str,
    ) -> None:
        sistema = etree.SubElement(
            registro_xml, VerifactuXmlService._sf("SistemaInformatico")
        )
        etree.SubElement(
            sistema, VerifactuXmlService._sf("NombreRazon")
        ).text = nombre_productor
        etree.SubElement(
            sistema, VerifactuXmlService._sf("NIF")
        ).text = nif_productor
        etree.SubElement(
            sistema, VerifactuXmlService._sf("NombreSistemaInformatico")
        ).text = VerifactuConfig.NOMBRE_SISTEMA
        etree.SubElement(
            sistema, VerifactuXmlService._sf("IdSistemaInformatico")
        ).text = VerifactuConfig.ID_SISTEMA
        etree.SubElement(
            sistema, VerifactuXmlService._sf("Version")
        ).text = VerifactuConfig.VERSION
        etree.SubElement(
            sistema, VerifactuXmlService._sf("NumeroInstalacion")
        ).text = VerifactuConfig.NUMERO_INSTALACION
        etree.SubElement(
            sistema, VerifactuXmlService._sf("TipoUsoPosibleSoloVerifactu")
        ).text = VerifactuConfig.TIPO_USO_POSIBLE_SOLO_VERIFACTU
        etree.SubElement(
            sistema, VerifactuXmlService._sf("TipoUsoPosibleMultiOT")
        ).text = VerifactuConfig.TIPO_USO_POSIBLE_MULTI_OT
        etree.SubElement(
            sistema, VerifactuXmlService._sf("IndicadorMultiplesOT")
        ).text = VerifactuConfig.INDICADOR_MULTIPLES_OT

    @staticmethod
    def generar_registro_anulacion(
        factura,
        empresa,
        hash_registro: str,
        hash_anterior: str | None,
        factura_anterior_numero: str | None,
        factura_anterior_fecha: str | None,
        fecha_hora_huso: str,
        nombre_productor: str,
        nif_productor: str,
    ) -> str:
        """Construye un RegistroAnulacion conforme a los XSD de la AEAT."""
        root = etree.Element(
            VerifactuXmlService._lr("RegFactuSistemaFacturacion"),
            nsmap={
                "sfLR": VerifactuXmlService.NS_LR,
                "sf": VerifactuXmlService.NS_SF,
            },
        )
        VerifactuXmlService._anadir_cabecera(root, empresa)

        registro_factura = etree.SubElement(
            root, VerifactuXmlService._lr("RegistroFactura")
        )
        anulacion = etree.SubElement(
            registro_factura, VerifactuXmlService._sf("RegistroAnulacion")
        )
        etree.SubElement(
            anulacion, VerifactuXmlService._sf("IDVersion")
        ).text = "1.0"

        id_factura = etree.SubElement(
            anulacion, VerifactuXmlService._sf("IDFactura")
        )
        etree.SubElement(
            id_factura, VerifactuXmlService._sf("IDEmisorFacturaAnulada")
        ).text = empresa.nif
        etree.SubElement(
            id_factura, VerifactuXmlService._sf("NumSerieFacturaAnulada")
        ).text = factura.numero
        etree.SubElement(
            id_factura, VerifactuXmlService._sf("FechaExpedicionFacturaAnulada")
        ).text = factura.fecha_emision.strftime("%d-%m-%Y")

        VerifactuXmlService._anadir_encadenamiento(
            anulacion,
            empresa,
            hash_anterior,
            factura_anterior_numero,
            factura_anterior_fecha,
        )
        VerifactuXmlService._anadir_sistema_informatico(
            anulacion, nombre_productor, nif_productor
        )
        etree.SubElement(
            anulacion, VerifactuXmlService._sf("FechaHoraHusoGenRegistro")
        ).text = fecha_hora_huso
        etree.SubElement(
            anulacion, VerifactuXmlService._sf("TipoHuella")
        ).text = "01"
        etree.SubElement(
            anulacion, VerifactuXmlService._sf("Huella")
        ).text = hash_registro

        return etree.tostring(root, encoding="unicode", pretty_print=True)

    @staticmethod
    def generar_registro_alta(
        factura,
        empresa,
        cliente,
        hash_registro: str,
        hash_anterior: str | None,
        factura_anterior_numero: str | None,
        factura_anterior_fecha: str | None,
        fecha_hora_huso: str,
        nombre_productor: str,
        nif_productor: str
    ) -> str:

        nsmap = {
            "sfLR": VerifactuXmlService.NS_LR,
            "sf": VerifactuXmlService.NS_SF
        }

        root = etree.Element(
            VerifactuXmlService._lr(
                "RegFactuSistemaFacturacion"
            ),
            nsmap=nsmap
        )

        # -------------------------------------------------
        # CABECERA
        # -------------------------------------------------

        cabecera = etree.SubElement(
            root,
            VerifactuXmlService._lr("Cabecera")
        )

        obligado = etree.SubElement(
            cabecera,
            VerifactuXmlService._sf(
                "ObligadoEmision"
            )
        )

        nombre_obligado = etree.SubElement(
            obligado,
            VerifactuXmlService._sf(
                "NombreRazon"
            )
        )

        nombre_obligado.text = (
            getattr(
                empresa,
                "razon_social",
                None
            )
            or getattr(
                empresa,
                "nombre",
                None
            )
            or ""
        )

        nif_obligado = etree.SubElement(
            obligado,
            VerifactuXmlService._sf("NIF")
        )

        nif_obligado.text = empresa.nif

        # -------------------------------------------------
        # REGISTRO FACTURA
        # -------------------------------------------------

        registro_factura = etree.SubElement(
            root,
            VerifactuXmlService._lr(
                "RegistroFactura"
            )
        )

        alta = etree.SubElement(
            registro_factura,
            VerifactuXmlService._sf(
                "RegistroAlta"
            )
        )

        # -------------------------------------------------
        # VERSIÓN
        # -------------------------------------------------

        id_version = etree.SubElement(
            alta,
            VerifactuXmlService._sf(
                "IDVersion"
            )
        )
        id_version.text = "1.0"

        # -------------------------------------------------
        # IDENTIFICACIÓN FACTURA
        # -------------------------------------------------

        id_factura = etree.SubElement(
            alta,
            VerifactuXmlService._sf(
                "IDFactura"
            )
        )

        id_emisor = etree.SubElement(
            id_factura,
            VerifactuXmlService._sf(
                "IDEmisorFactura"
            )
        )
        id_emisor.text = empresa.nif

        numero = etree.SubElement(
            id_factura,
            VerifactuXmlService._sf(
                "NumSerieFactura"
            )
        )
        numero.text = factura.numero

        fecha = etree.SubElement(
            id_factura,
            VerifactuXmlService._sf(
                "FechaExpedicionFactura"
            )
        )
        fecha.text = factura.fecha_emision.strftime(
            "%d-%m-%Y"
        )

        # -------------------------------------------------
        # EMISOR
        # -------------------------------------------------

        nombre_emisor = etree.SubElement(
            alta,
            VerifactuXmlService._sf(
                "NombreRazonEmisor"
            )
        )

        nombre_emisor.text = (
            getattr(
                empresa,
                "razon_social",
                None
            )
            or getattr(
                empresa,
                "nombre",
                None
            )
            or ""
        )

        # -------------------------------------------------
        # TIPO FACTURA
        # -------------------------------------------------

        tipo_factura = etree.SubElement(
            alta,
            VerifactuXmlService._sf(
                "TipoFactura"
            )
        )

        tipo_factura.text = "F1"

        descripcion = etree.SubElement(
            alta,
            VerifactuXmlService._sf(
                "DescripcionOperacion"
            )
        )

        descripcion.text = (
            factura.observaciones
            or "Servicios de reparación"
        )

        # -------------------------------------------------
        # DESTINATARIO
        # -------------------------------------------------

        destinatarios = etree.SubElement(
            alta,
            VerifactuXmlService._sf(
                "Destinatarios"
            )
        )

        destinatario = etree.SubElement(
            destinatarios,
            VerifactuXmlService._sf(
                "IDDestinatario"
            )
        )

        nombre_cliente = etree.SubElement(
            destinatario,
            VerifactuXmlService._sf(
                "NombreRazon"
            )
        )

        nombre_cliente.text = ", ".join(
            parte for parte in [cliente.apellidos or "", cliente.nombre or ""] if parte
        )

        nif_cliente = etree.SubElement(
            destinatario,
            VerifactuXmlService._sf("NIF")
        )

        nif_cliente.text = cliente.dni

        # -------------------------------------------------
        # DESGLOSE IVA
        # -------------------------------------------------

        desglose = etree.SubElement(
            alta,
            VerifactuXmlService._sf(
                "Desglose"
            )
        )

        detalle = etree.SubElement(
            desglose,
            VerifactuXmlService._sf(
                "DetalleDesglose"
            )
        )

        impuesto = etree.SubElement(
            detalle,
            VerifactuXmlService._sf(
                "Impuesto"
            )
        )
        impuesto.text = "01"

        clave_regimen = etree.SubElement(
            detalle,
            VerifactuXmlService._sf(
                "ClaveRegimen"
            )
        )
        clave_regimen.text = "01"

        calificacion = etree.SubElement(
            detalle,
            VerifactuXmlService._sf(
                "CalificacionOperacion"
            )
        )
        calificacion.text = "S1"

        tipo_impositivo = etree.SubElement(
            detalle,
            VerifactuXmlService._sf(
                "TipoImpositivo"
            )
        )
        tipo_impositivo.text = (
            f"{factura.iva:.2f}"
        )

        base = etree.SubElement(
            detalle,
            VerifactuXmlService._sf(
                "BaseImponibleOimporteNoSujeto"
            )
        )
        base.text = (
            f"{factura.base_imponible:.2f}"
        )

        cuota = etree.SubElement(
            detalle,
            VerifactuXmlService._sf(
                "CuotaRepercutida"
            )
        )
        cuota.text = (
            f"{factura.cuota_iva:.2f}"
        )

        # -------------------------------------------------
        # TOTALES
        # -------------------------------------------------

        cuota_total = etree.SubElement(
            alta,
            VerifactuXmlService._sf(
                "CuotaTotal"
            )
        )
        cuota_total.text = (
            f"{factura.cuota_iva:.2f}"
        )

        importe_total = etree.SubElement(
            alta,
            VerifactuXmlService._sf(
                "ImporteTotal"
            )
        )
        importe_total.text = (
            f"{factura.total:.2f}"
        )

        # -------------------------------------------------
        # ENCADENAMIENTO
        # -------------------------------------------------

        encadenamiento = etree.SubElement(
            alta,
            VerifactuXmlService._sf(
                "Encadenamiento"
            )
        )

        if hash_anterior:

            anterior = etree.SubElement(
                encadenamiento,
                VerifactuXmlService._sf(
                    "RegistroAnterior"
                )
            )

            emisor_anterior = etree.SubElement(
                anterior,
                VerifactuXmlService._sf(
                    "IDEmisorFactura"
                )
            )
            emisor_anterior.text = empresa.nif

            num_anterior = etree.SubElement(
                anterior,
                VerifactuXmlService._sf(
                    "NumSerieFactura"
                )
            )
            num_anterior.text = (
                factura_anterior_numero
                or ""
            )

            fecha_anterior = etree.SubElement(
                anterior,
                VerifactuXmlService._sf(
                    "FechaExpedicionFactura"
                )
            )
            fecha_anterior.text = (
                factura_anterior_fecha
                or ""
            )

            huella_anterior_xml = (
                etree.SubElement(
                    anterior,
                    VerifactuXmlService._sf(
                        "Huella"
                    )
                )
            )

            huella_anterior_xml.text = (
                hash_anterior
            )

        else:

            primero = etree.SubElement(
                encadenamiento,
                VerifactuXmlService._sf(
                    "PrimerRegistro"
                )
            )
            primero.text = "S"

        # -------------------------------------------------
        # SISTEMA INFORMÁTICO
        # -------------------------------------------------

        sistema = etree.SubElement(
            alta,
            VerifactuXmlService._sf(
                "SistemaInformatico"
            )
        )

        productor_nombre = etree.SubElement(
            sistema,
            VerifactuXmlService._sf(
                "NombreRazon"
            )
        )
        productor_nombre.text = nombre_productor

        productor_nif = etree.SubElement(
            sistema,
            VerifactuXmlService._sf("NIF")
        )
        productor_nif.text = nif_productor

        nombre_sistema = etree.SubElement(
            sistema,
            VerifactuXmlService._sf(
                "NombreSistemaInformatico"
            )
        )
        nombre_sistema.text = (
            VerifactuConfig.NOMBRE_SISTEMA
        )

        id_sistema = etree.SubElement(
            sistema,
            VerifactuXmlService._sf(
                "IdSistemaInformatico"
            )
        )
        id_sistema.text = (
            VerifactuConfig.ID_SISTEMA
        )

        version = etree.SubElement(
            sistema,
            VerifactuXmlService._sf(
                "Version"
            )
        )
        version.text = VerifactuConfig.VERSION

        instalacion = etree.SubElement(
            sistema,
            VerifactuXmlService._sf(
                "NumeroInstalacion"
            )
        )
        instalacion.text = (
            VerifactuConfig.NUMERO_INSTALACION
        )

        solo_verifactu = etree.SubElement(
            sistema,
            VerifactuXmlService._sf(
                "TipoUsoPosibleSoloVerifactu"
            )
        )
        solo_verifactu.text = (
            VerifactuConfig
            .TIPO_USO_POSIBLE_SOLO_VERIFACTU
        )

        multi_ot = etree.SubElement(
            sistema,
            VerifactuXmlService._sf(
                "TipoUsoPosibleMultiOT"
            )
        )
        multi_ot.text = (
            VerifactuConfig
            .TIPO_USO_POSIBLE_MULTI_OT
        )

        multiples_ot = etree.SubElement(
            sistema,
            VerifactuXmlService._sf(
                "IndicadorMultiplesOT"
            )
        )
        multiples_ot.text = (
            VerifactuConfig
            .INDICADOR_MULTIPLES_OT
        )

        # -------------------------------------------------
        # FECHA + HUELLA
        # -------------------------------------------------

        fecha_hora = etree.SubElement(
            alta,
            VerifactuXmlService._sf(
                "FechaHoraHusoGenRegistro"
            )
        )
        fecha_hora.text = fecha_hora_huso

        tipo_huella = etree.SubElement(
            alta,
            VerifactuXmlService._sf(
                "TipoHuella"
            )
        )
        tipo_huella.text = "01"

        huella = etree.SubElement(
            alta,
            VerifactuXmlService._sf(
                "Huella"
            )
        )
        huella.text = hash_registro

        return etree.tostring(
            root,
            encoding="unicode",
            pretty_print=True
        )
