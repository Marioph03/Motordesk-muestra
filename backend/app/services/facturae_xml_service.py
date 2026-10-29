"""Genera XML Facturae sin firmar para AutoFirma."""

from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path
from xml.etree import ElementTree as ET

from app.core.storage_paths import directorio_datos


class FacturaeXmlService:
    NS = "http://www.facturae.es/Facturae/2014/v3.2.2/Facturae"

    @classmethod
    def generar(cls, factura, empresa, destino) -> Path:
        cls.validar_destino(destino)

        ET.register_namespace("", cls.NS)
        raiz = ET.Element(cls.q("Facturae"))
        cabecera = ET.SubElement(raiz, cls.q("FileHeader"))
        cls.texto(cabecera, "SchemaVersion", "3.2.2")
        cls.texto(cabecera, "Modality", "I")
        cls.texto(cabecera, "InvoiceIssuerType", "EM")
        lote = ET.SubElement(cabecera, cls.q("Batch"))
        cls.texto(lote, "BatchIdentifier", f"{empresa.nif}{factura.numero}".replace("/", ""))
        cls.texto(lote, "InvoicesCount", "1")
        for nombre in ("TotalInvoicesAmount", "TotalOutstandingAmount", "TotalExecutableAmount"):
            cls.importe(lote, nombre, factura.total)
        cls.texto(lote, "InvoiceCurrencyCode", "EUR")

        partes = ET.SubElement(raiz, cls.q("Parties"))
        cls.parte(partes, "SellerParty", empresa.nombre, empresa.nif, empresa.direccion, empresa.codigo_postal, empresa.ciudad, empresa.provincia)
        comprador = cls.parte(partes, "BuyerParty", destino.nombre, destino.nif, destino.direccion, destino.codigo_postal, destino.ciudad, destino.provincia)
        centros = ET.SubElement(comprador, cls.q("AdministrativeCentres"))
        for rol, codigo, nombre in (("01", destino.oficina_contable, "Oficina contable"), ("02", destino.organo_gestor, "Órgano gestor"), ("03", destino.unidad_tramitadora, "Unidad tramitadora")):
            centro = ET.SubElement(centros, cls.q("AdministrativeCentre"))
            cls.texto(centro, "CentreCode", codigo)
            cls.texto(centro, "RoleTypeCode", rol)
            cls.texto(centro, "Name", nombre)
            cls.direccion(centro, destino.direccion, destino.codigo_postal, destino.ciudad, destino.provincia)

        facturas = ET.SubElement(raiz, cls.q("Invoices"))
        nodo = ET.SubElement(facturas, cls.q("Invoice"))
        encabezado = ET.SubElement(nodo, cls.q("InvoiceHeader"))
        cls.texto(encabezado, "InvoiceNumber", factura.numero)
        cls.texto(encabezado, "InvoiceDocumentType", "FC")
        cls.texto(encabezado, "InvoiceClass", "OO")
        emision = ET.SubElement(nodo, cls.q("InvoiceIssueData"))
        cls.texto(emision, "IssueDate", factura.fecha_emision.date().isoformat())
        cls.texto(emision, "InvoiceCurrencyCode", "EUR")
        cls.texto(emision, "TaxCurrencyCode", "EUR")
        cls.texto(emision, "LanguageName", "es")

        impuestos = ET.SubElement(nodo, cls.q("TaxesOutputs"))
        impuesto = ET.SubElement(impuestos, cls.q("Tax"))
        cls.texto(impuesto, "TaxTypeCode", "01")
        cls.texto(impuesto, "TaxRate", cls.numero(factura.iva))
        cls.importe(impuesto, "TaxableBase", factura.base_imponible)
        cls.importe(impuesto, "TaxAmount", factura.cuota_iva)
        totales = ET.SubElement(nodo, cls.q("InvoiceTotals"))
        for nombre, valor in (("TotalGrossAmount", factura.base_imponible), ("TotalGrossAmountBeforeTaxes", factura.base_imponible), ("TotalTaxOutputs", factura.cuota_iva), ("InvoiceTotal", factura.total), ("TotalOutstandingAmount", factura.total), ("TotalExecutableAmount", factura.total)):
            cls.importe(totales, nombre, valor)

        items = ET.SubElement(nodo, cls.q("Items"))
        for linea in factura.lineas:
            item = ET.SubElement(items, cls.q("InvoiceLine"))
            cls.texto(item, "ItemDescription", linea.descripcion)
            cls.texto(item, "Quantity", cls.numero(linea.cantidad))
            cls.texto(item, "UnitOfMeasure", "01")
            cls.texto(item, "UnitPriceWithoutTax", cls.numero(linea.precio_unitario))
            cls.texto(item, "TotalCost", cls.numero(Decimal(linea.precio_unitario) * Decimal(linea.cantidad)))
            cls.texto(item, "GrossAmount", cls.numero(linea.subtotal))
            linea_impuestos = ET.SubElement(item, cls.q("TaxesOutputs"))
            linea_impuesto = ET.SubElement(linea_impuestos, cls.q("Tax"))
            cls.texto(linea_impuesto, "TaxTypeCode", "01")
            cls.texto(linea_impuesto, "TaxRate", cls.numero(linea.iva))
            cls.importe(linea_impuesto, "TaxableBase", linea.subtotal)
            iva = Decimal(linea.subtotal) * Decimal(linea.iva) / Decimal("100")
            cls.importe(linea_impuesto, "TaxAmount", iva)
            cls.importe(item, "TotalItemAmount", Decimal(linea.subtotal) + iva)

        ET.indent(raiz, space="  ")
        carpeta = directorio_datos() / "FE"
        carpeta.mkdir(parents=True, exist_ok=True)
        seguro = "".join(c if c.isalnum() or c in "-_." else "_" for c in factura.numero)
        archivo = carpeta / f"Facturae_{seguro}.xml"
        temporal = carpeta / f".{seguro}.tmp"
        ET.ElementTree(raiz).write(temporal, encoding="utf-8", xml_declaration=True)
        temporal.replace(archivo)
        return archivo

    @staticmethod
    def validar_destino(destino) -> None:
        obligatorios = (destino.direccion, destino.codigo_postal, destino.ciudad, destino.provincia)
        if not all(valor and valor.strip() for valor in obligatorios):
            raise ValueError("Completa la dirección del organismo Facturae antes de emitir la factura")

    @classmethod
    def q(cls, nombre): return f"{{{cls.NS}}}{nombre}"

    @classmethod
    def texto(cls, padre, nombre, valor): ET.SubElement(padre, cls.q(nombre)).text = str(valor)

    @staticmethod
    def numero(valor): return format(Decimal(valor).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP), "f")

    @classmethod
    def importe(cls, padre, nombre, valor):
        nodo = ET.SubElement(padre, cls.q(nombre)); cls.texto(nodo, "TotalAmount", cls.numero(valor))

    @classmethod
    def direccion(cls, padre, direccion, codigo_postal, ciudad, provincia):
        nodo = ET.SubElement(padre, cls.q("AddressInSpain"))
        for nombre, valor in (("Address", direccion), ("PostCode", codigo_postal), ("Town", ciudad), ("Province", provincia), ("CountryCode", "ESP")):
            cls.texto(nodo, nombre, valor)

    @classmethod
    def parte(cls, padre, etiqueta, nombre, nif, direccion, codigo_postal, ciudad, provincia):
        parte = ET.SubElement(padre, cls.q(etiqueta))
        identificacion = ET.SubElement(parte, cls.q("TaxIdentification"))
        for campo, valor in (("PersonTypeCode", "J"), ("ResidenceTypeCode", "R"), ("TaxIdentificationNumber", nif)):
            cls.texto(identificacion, campo, valor)
        entidad = ET.SubElement(parte, cls.q("LegalEntity"))
        cls.texto(entidad, "CorporateName", nombre)
        cls.direccion(entidad, direccion, codigo_postal, ciudad, provincia)
        return parte
