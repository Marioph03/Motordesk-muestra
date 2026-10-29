"""Generación de documentos PDF con la configuración central del taller."""

from io import BytesIO
import os
from datetime import timedelta
from decimal import Decimal
from pathlib import Path
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.enums import TA_JUSTIFY
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.utils import ImageReader
from PIL import Image as PILImage, ImageDraw
from reportlab.platypus import (
    Image,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
    PageBreak
)

from app.services.verifactu_qr_service import VerifactuQrService
from app.core.storage_paths import directorio_datos


class PdfService:

    @staticmethod
    def generar_orden_interna(orden):
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=40, leftMargin=40, topMargin=36, bottomMargin=36)
        estilos = getSampleStyleSheet()
        titulo = ParagraphStyle("OrdenInternaTitulo", parent=estilos["Title"], fontName="Helvetica-Bold", fontSize=19, alignment=1, spaceAfter=14)
        normal = ParagraphStyle("OrdenInternaNormal", parent=estilos["Normal"], fontSize=9, leading=12)
        elementos = [Paragraph("ORDEN INTERNA", titulo), Paragraph(f"<b>Número:</b> {escape(orden.numero)} &nbsp;&nbsp; <b>Estado:</b> {escape(orden.estado)}", normal), Spacer(1, 10), Paragraph(f"<b>Trabajo:</b> {escape(orden.titulo)}", normal), Paragraph(f"<b>Categoría:</b> {escape(orden.categoria)}", normal)]
        if orden.referencia_activo: elementos.append(Paragraph(f"<b>Vehículo / activo:</b> {escape(orden.referencia_activo)}", normal))
        elementos.extend([Spacer(1, 8), Paragraph(f"<b>Descripción:</b><br/>{escape(orden.descripcion).replace(chr(10), '<br/>')}", normal), Spacer(1, 12)])
        filas = [["Tipo", "Referencia", "Descripción", "Cantidad", "Coste"]]
        for linea in orden.lineas:
            filas.append([linea.tipo.title(), linea.referencia or "-", Paragraph(escape(linea.descripcion), normal), str(linea.cantidad), f"{float(linea.cantidad * linea.coste_unitario):.2f} €"])
        tabla = Table(filas, colWidths=[65, 90, 210, 60, 75], repeatRows=1)
        tabla.setStyle(TableStyle([("BACKGROUND", (0,0), (-1,0), colors.HexColor("#123A63")), ("TEXTCOLOR", (0,0), (-1,0), colors.white), ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"), ("GRID", (0,0), (-1,-1), .35, colors.HexColor("#C7D1DB")), ("FONTSIZE", (0,0), (-1,-1), 8), ("ALIGN", (3,1), (-1,-1), "RIGHT"), ("VALIGN", (0,0), (-1,-1), "MIDDLE"), ("TOPPADDING", (0,0), (-1,-1), 6), ("BOTTOMPADDING", (0,0), (-1,-1), 6)]))
        total = Table([["COSTE INTERNO TOTAL", f"{float(orden.coste_total):.2f} €"]], colWidths=[180, 100], hAlign="RIGHT")
        total.setStyle(TableStyle([("FONTNAME", (0,0), (-1,-1), "Helvetica-Bold"), ("LINEABOVE", (0,0), (-1,-1), .8, colors.HexColor("#123A63")), ("ALIGN", (0,0), (-1,-1), "RIGHT"), ("TOPPADDING", (0,0), (-1,-1), 8)]))
        elementos.extend([tabla, Spacer(1, 14), total, Spacer(1, 18), Paragraph("Documento interno. No constituye factura ni genera ingresos.", normal)])
        doc.build(elementos); buffer.seek(0); return buffer

    @staticmethod
    def generar_registro_jornada(registros, mes, empresa):
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=32, leftMargin=32, topMargin=32, bottomMargin=32)
        estilos = getSampleStyleSheet()
        titulo = ParagraphStyle("RegistroJornadaTitulo", parent=estilos["Title"], fontName="Helvetica-Bold", fontSize=18, alignment=1, spaceAfter=12)
        texto = ParagraphStyle("RegistroJornadaTexto", parent=estilos["Normal"], fontSize=8, leading=10)
        nombre_empresa = escape(str(getattr(empresa, "nombre", None) or "MotorDesk"))
        elementos = [Paragraph(nombre_empresa, ParagraphStyle("RegistroJornadaEmpresa", parent=texto, alignment=1, fontName="Helvetica-Bold", fontSize=11)), Spacer(1, 8), Paragraph("REGISTRO DE JORNADA LABORAL", titulo), Paragraph(f"Mes: {escape(mes)}", texto), Spacer(1, 10)]
        por_usuario = {}
        for registro in registros:
            por_usuario.setdefault((registro["usuario_id"], registro["nombre"], registro["apellidos"]), []).append(registro)
        for (_, nombre, apellidos), filas_usuario in por_usuario.items():
            nombre_mostrado = ", ".join(parte for parte in [escape(apellidos), escape(nombre)] if parte)
            elementos.append(Paragraph(f"<b>{nombre_mostrado}</b>", ParagraphStyle("RegistroJornadaNombre", parent=texto, fontSize=10, spaceBefore=10, spaceAfter=4)))
            filas = [["Fecha", "Presente", "Entrada", "Salida", "Firma"]]
            for fila in filas_usuario:
                entrada = fila["hora_entrada"].strftime("%H:%M") if fila["hora_entrada"] else "-"
                salida = fila["hora_salida"].strftime("%H:%M") if fila["hora_salida"] else "-"
                filas.append([fila["fecha"].strftime("%d/%m/%Y"), "Sí" if fila["presente"] else "No", entrada, salida, ""])
            tabla = Table(filas, colWidths=[90, 70, 80, 80, 170], repeatRows=1)
            tabla.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#123A63")), ("TEXTCOLOR", (0, 0), (-1, 0), colors.white), ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"), ("GRID", (0, 0), (-1, -1), .35, colors.HexColor("#C7D1DB")), ("FONTSIZE", (0, 0), (-1, -1), 8), ("ALIGN", (1, 1), (3, -1), "CENTER"), ("VALIGN", (0, 0), (-1, -1), "MIDDLE"), ("TOPPADDING", (0, 0), (-1, -1), 5), ("BOTTOMPADDING", (0, 0), (-1, -1), 5)]))
            elementos.extend([tabla, Spacer(1, 5)])
        doc.build(elementos)
        buffer.seek(0)
        return buffer

    @staticmethod
    def generar_albaran_venta(albaran, empresa, configuracion_taller=None, configuracion_documentos=None):
        """Documento de entrega de recambios, independiente de su factura."""
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=40, leftMargin=40, topMargin=36, bottomMargin=36)
        estilos = getSampleStyleSheet()
        titulo = ParagraphStyle("AlbaranVentaTitulo", parent=estilos["Title"], fontName="Helvetica-Bold", fontSize=22, leading=26, alignment=1, spaceAfter=14)
        seccion = ParagraphStyle("AlbaranVentaSeccion", parent=estilos["Heading2"], fontName="Helvetica-Bold", fontSize=11, textColor=colors.HexColor("#123A63"), spaceBefore=14, spaceAfter=6)
        texto = ParagraphStyle("AlbaranVentaTexto", parent=estilos["Normal"], fontSize=9, leading=12)
        texto_tabla = ParagraphStyle(
            "AlbaranVentaTabla",
            parent=texto,
            fontSize=7.5,
            leading=9,
            wordWrap="CJK",
            splitLongWords=True,
        )

        def valor(objeto, atributo, defecto="-"):
            dato = getattr(objeto, atributo, None) if objeto else None
            return escape(str(dato)) if dato not in (None, "") else defecto

        def importe(numero):
            return f"{float(numero or 0):,.2f} €".replace(",", "X").replace(".", ",").replace("X", ".")

        datos_taller = PdfService._datos_taller_documento(empresa, configuracion_taller, configuracion_documentos)
        ruta_logo = PdfService._ruta_logo_documento(empresa, configuracion_taller)
        logo = None
        if ruta_logo:
            try:
                lector = ImageReader(ruta_logo)
                ancho, alto = lector.getSize()
                escala = min(180 / ancho, 70 / alto)
                logo = Image(ruta_logo, width=ancho * escala, height=alto * escala)
                logo.hAlign = "LEFT"
            except Exception:
                logo = None

        cliente = getattr(albaran, "cliente", None)
        direccion_cliente = "<br/>".join(parte for parte in [
            valor(cliente, "direccion", ""),
            " ".join(parte for parte in [valor(cliente, "codigo_postal", ""), valor(cliente, "ciudad", "")] if parte),
            valor(cliente, "provincia", ""),
        ] if parte)
        bloque_cliente = (
            f"<b>DATOS DEL CLIENTE</b><br/><br/><b>{valor(cliente, 'apellidos', '')}{', ' if getattr(cliente, 'apellidos', None) else ''}{valor(cliente, 'nombre')}</b>"
            + (f"<br/>{direccion_cliente}" if direccion_cliente else "")
            + f"<br/><br/><b>NIF/CIF:</b> {valor(cliente, 'dni')}"
            + f"<br/><b>Teléfono:</b> {valor(cliente, 'telefono')}"
            + f"<br/><b>Email:</b> {valor(cliente, 'email')}"
        )
        bloque_taller = Paragraph(PdfService._bloque_datos_taller(datos_taller), texto)
        if logo:
            bloque_taller = Table([[logo], [bloque_taller]], colWidths=[250])
            bloque_taller.setStyle(TableStyle([("LEFTPADDING", (0, 0), (-1, -1), 0), ("RIGHTPADDING", (0, 0), (-1, -1), 0), ("BOTTOMPADDING", (0, 0), (-1, -1), 5)]))

        cabecera = Table([[bloque_taller, Paragraph(bloque_cliente, texto)]], colWidths=[258, 258])
        cabecera.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "TOP"), ("LINEBEFORE", (1, 0), (1, -1), 0.5, colors.HexColor("#B8C4D0")),
            ("LEFTPADDING", (0, 0), (-1, -1), 10), ("RIGHTPADDING", (0, 0), (-1, -1), 10), ("TOPPADDING", (0, 0), (-1, -1), 8), ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ]))
        fecha = getattr(albaran, "fecha", None)
        fecha_texto = fecha.strftime("%d/%m/%Y") if fecha else "-"
        resumen = Table([["N.º ALBARÁN", "FECHA", "ESTADO"], [getattr(albaran, "numero", "-"), fecha_texto, getattr(albaran, "estado", "-")]], colWidths=[172, 172, 172])
        resumen.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#E6E6E6")), ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#B8C4D0")), ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("LEFTPADDING", (0, 0), (-1, -1), 8), ("TOPPADDING", (0, 0), (-1, -1), 8), ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ]))
        filas = [["Ref.", "Descripción", "Cant.", "Precio", "Dto.", "Importe"]]
        for linea in getattr(albaran, "lineas", []):
            filas.append([
                Paragraph(valor(linea, "referencia"), texto_tabla),
                Paragraph(valor(linea, "descripcion"), texto_tabla),
                str(linea.cantidad),
                importe(linea.precio_unitario),
                f"{float(linea.descuento_porcentaje or 0):.2f}%",
                importe(linea.total),
            ])
        tabla = Table(filas, colWidths=[70, 210, 48, 70, 48, 70], repeatRows=1)
        tabla.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#123A63")), ("TEXTCOLOR", (0, 0), (-1, 0), colors.white), ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#D9E0E6")), ("FONTSIZE", (0, 0), (-1, -1), 8), ("ALIGN", (2, 1), (-1, -1), "RIGHT"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"), ("TOPPADDING", (0, 0), (-1, -1), 6), ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ]))
        total = Table([["TOTAL SIN IVA", importe(getattr(albaran, "total", 0))]], colWidths=[130, 110], hAlign="RIGHT")
        total.setStyle(TableStyle([("FONTNAME", (0, 0), (-1, -1), "Helvetica-Bold"), ("FONTSIZE", (0, 0), (-1, -1), 11), ("LINEABOVE", (0, 0), (-1, -1), 0.8, colors.HexColor("#123A63")), ("ALIGN", (0, 0), (-1, -1), "RIGHT"), ("TOPPADDING", (0, 0), (-1, -1), 7)]))
        elementos = [cabecera, Spacer(1, 18), Paragraph("ALBARÁN", titulo), resumen, Paragraph("PIEZAS / RECAMBIOS", seccion), tabla, Spacer(1, 12), total]
        if getattr(albaran, "observaciones", None):
            elementos.extend([Paragraph("OBSERVACIONES", seccion), Paragraph(escape(albaran.observaciones).replace("\n", "<br/>"), texto)])
        PdfService._agregar_pie_configurable(elementos, configuracion_documentos, texto)
        doc.build(elementos)
        buffer.seek(0)
        return buffer

    @staticmethod
    def _datos_taller_documento(
        empresa,
        configuracion_taller=None,
        configuracion_documentos=None,
    ) -> dict[str, str]:
        """Normaliza los datos configurables del taller para los PDFs."""

        def obtener(objeto, atributo: str) -> str:
            valor = getattr(objeto, atributo, None) if objeto else None
            return str(valor) if valor not in (None, "") else ""

        def visible(atributo: str, por_defecto: bool = True) -> bool:
            return bool(
                getattr(configuracion_documentos, atributo, por_defecto)
                if configuracion_documentos is not None
                else por_defecto
            )

        # Los documentos oficiales deben identificar al emisor por su
        # denominación fiscal. El nombre comercial queda únicamente como
        # compatibilidad para instalaciones antiguas que aún no tengan
        # configurada la razón social.
        nombre = (
            obtener(configuracion_taller, "razon_social")
            or obtener(empresa, "nombre")
            or obtener(configuracion_taller, "nombre_comercial")
            or obtener(empresa, "nombre_comercial")
            or "MotorDesk"
        )
        direccion = obtener(configuracion_taller, "direccion") or obtener(empresa, "direccion")
        codigo_postal = obtener(configuracion_taller, "codigo_postal") or obtener(empresa, "codigo_postal")
        localidad = (
            obtener(configuracion_taller, "localidad")
            or obtener(empresa, "ciudad")
            or obtener(empresa, "localidad")
        )
        provincia = obtener(configuracion_taller, "provincia") or obtener(empresa, "provincia")
        localidad_completa = " ".join(parte for parte in (codigo_postal, localidad) if parte)
        if provincia:
            localidad_completa = (
                f"{localidad_completa} ({provincia})"
                if localidad_completa else provincia
            )

        return {
            "nombre": nombre,
            "nif": (
                obtener(configuracion_taller, "nif_cif")
                or obtener(empresa, "nif")
                or obtener(empresa, "cif")
            ) if visible("mostrar_nif_cif") else "",
            "direccion": direccion if visible("mostrar_direccion") else "",
            "localidad": localidad_completa if visible("mostrar_direccion") else "",
            "telefono": (
                obtener(configuracion_taller, "telefono") or obtener(empresa, "telefono")
            ) if visible("mostrar_telefono") else "",
            "email": (
                obtener(configuracion_taller, "email") or obtener(empresa, "email")
            ) if visible("mostrar_email") else "",
            "web": (
                obtener(configuracion_taller, "web") or obtener(empresa, "web")
            ) if visible("mostrar_web", False) else "",
        }

    @staticmethod
    def _bloque_datos_taller(datos: dict[str, str]) -> str:
        lineas = [f"<b>{escape(datos['nombre'])}</b>"]
        if datos["direccion"]:
            lineas.append(escape(datos["direccion"]))
        if datos["localidad"]:
            lineas.append(escape(datos["localidad"]))
        if datos["nif"]:
            lineas.append(f"<b>NIF:</b> {escape(datos['nif'])}")
        if datos["telefono"]:
            lineas.append(f"<b>Teléfono:</b> {escape(datos['telefono'])}")
        if datos["email"]:
            lineas.append(escape(datos["email"]))
        if datos["web"]:
            lineas.append(f"<b>Web:</b> {escape(datos['web'])}")
        return "<br/>".join(lineas)

    @staticmethod
    def _ruta_logo_documento(
        empresa=None,
        configuracion_taller=None,
        ruta_logo=None,
    ) -> str | None:
        """Resuelve el logo local con prioridad a Configuración > Taller."""

        candidatos = [
            ruta_logo,
            getattr(configuracion_taller, "logo_url", None),
            getattr(empresa, "logo", None),
        ]
        # En el ejecutable los logos se guardan en ProgramData, mientras que
        # ``__file__`` apunta al paquete interno de Program Files. Probamos
        # primero la raíz de datos activa y mantenemos la raíz del backend como
        # respaldo para instalaciones antiguas.
        raices = [directorio_datos(), Path(__file__).resolve().parents[2]]

        for candidato in candidatos:
            if not candidato:
                continue
            texto_ruta = str(candidato).strip()
            if texto_ruta.startswith(("http://", "https://")):
                continue
            if texto_ruta.startswith("/static/"):
                texto_ruta = texto_ruta.lstrip("/")

            ruta_original = Path(texto_ruta)
            rutas = [ruta_original] if ruta_original.is_absolute() else [
                raiz / ruta_original for raiz in raices
            ]
            for ruta in rutas:
                try:
                    ruta = ruta.resolve()
                except OSError:
                    continue
                if ruta.is_file():
                    return str(ruta)

        return None

    @staticmethod
    def _agregar_pie_configurable(elementos, configuracion_documentos, estilo):
        pie = (
            configuracion_documentos.get("pie_documentos")
            if isinstance(configuracion_documentos, dict)
            else getattr(configuracion_documentos, "pie_documentos", None)
        )
        if pie:
            elementos.extend([
                Spacer(1, 14),
                Paragraph(escape(str(pie)).replace("\n", "<br/>"), estilo),
            ])

    @staticmethod
    def generar_albaran_proveedor(albaran, empresa, configuracion_taller=None, configuracion_documentos=None):
        """Genera el PDF imprimible de un albarán recibido de proveedor."""
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=40, leftMargin=40, topMargin=40, bottomMargin=40)
        estilos = getSampleStyleSheet()
        titulo = ParagraphStyle("AlbaranProveedorTitulo", parent=estilos["Title"], fontName="Helvetica-Bold", fontSize=20, textColor=colors.HexColor("#123A63"), spaceAfter=14)
        texto = ParagraphStyle("AlbaranProveedorTexto", parent=estilos["Normal"], fontSize=9, leading=12)
        tabla_texto = ParagraphStyle("AlbaranProveedorTabla", parent=texto, fontSize=8, leading=10, wordWrap="CJK")
        datos_taller = PdfService._datos_taller_documento(empresa, configuracion_taller, configuracion_documentos)
        proveedor = getattr(albaran, "proveedor", None)
        fecha = getattr(albaran, "fecha", None)
        fecha_texto = fecha.strftime("%d/%m/%Y") if fecha else "-"
        cabecera = Table([[Paragraph(PdfService._bloque_datos_taller(datos_taller), texto), Paragraph(
            f"<b>DATOS DEL PROVEEDOR</b><br/><br/><b>{escape(str(getattr(proveedor, 'nombre', '-') or '-'))}</b><br/>"
            f"<b>NIF/CIF:</b> {escape(str(getattr(proveedor, 'cif', '-') or '-'))}<br/>"
            f"<b>Teléfono:</b> {escape(str(getattr(proveedor, 'telefono', '-') or '-'))}<br/>"
            f"<b>Email:</b> {escape(str(getattr(proveedor, 'email', '-') or '-'))}", texto)]], colWidths=[258, 258])
        cabecera.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP"), ("LINEBEFORE", (1, 0), (1, -1), .5, colors.HexColor("#B8C4D0")), ("LEFTPADDING", (0, 0), (-1, -1), 10), ("RIGHTPADDING", (0, 0), (-1, -1), 10)]))
        resumen = Table([["N.º INTERNO", "N.º PROVEEDOR", "FECHA", "ESTADO"], [albaran.numero_interno, albaran.numero_proveedor or "-", fecha_texto, albaran.estado]], colWidths=[130, 130, 120, 136])
        resumen.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#E6E6E6")), ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"), ("GRID", (0, 0), (-1, -1), .5, colors.HexColor("#B8C4D0")), ("FONTSIZE", (0, 0), (-1, -1), 8), ("PADDING", (0, 0), (-1, -1), 7)]))
        filas = [["Ref.", "Descripción", "Cant.", "Coste unit.", "Importe"]]
        total = Decimal("0")
        for linea in getattr(albaran, "lineas", []):
            articulo = getattr(linea, "articulo", None)
            coste = Decimal(linea.coste_unitario or 0)
            importe_linea = Decimal(linea.cantidad_recibida or 0) * coste
            total += importe_linea
            filas.append([Paragraph(escape(str(getattr(articulo, "referencia", "-") or "-")), tabla_texto), Paragraph(escape(str(getattr(articulo, "nombre", "-") or "-")), tabla_texto), str(linea.cantidad_recibida), f"{coste:.2f} €", f"{importe_linea:.2f} €"])
        tabla = Table(filas, colWidths=[90, 230, 55, 75, 66], repeatRows=1)
        tabla.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#123A63")), ("TEXTCOLOR", (0, 0), (-1, 0), colors.white), ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"), ("GRID", (0, 0), (-1, -1), .35, colors.HexColor("#D9E0E6")), ("FONTSIZE", (0, 0), (-1, -1), 8), ("ALIGN", (2, 1), (-1, -1), "RIGHT"), ("VALIGN", (0, 0), (-1, -1), "MIDDLE"), ("TOPPADDING", (0, 0), (-1, -1), 6), ("BOTTOMPADDING", (0, 0), (-1, -1), 6)]))
        total_tabla = Table([["TOTAL SIN IVA", f"{total:.2f} €"]], colWidths=[130, 110], hAlign="RIGHT")
        total_tabla.setStyle(TableStyle([("FONTNAME", (0, 0), (-1, -1), "Helvetica-Bold"), ("LINEABOVE", (0, 0), (-1, -1), .8, colors.HexColor("#123A63")), ("ALIGN", (0, 0), (-1, -1), "RIGHT"), ("TOPPADDING", (0, 0), (-1, -1), 7)]))
        elementos = [cabecera, Spacer(1, 18), Paragraph("ALBARÁN DE COMPRA", titulo), resumen, Spacer(1, 14), tabla, Spacer(1, 12), total_tabla]
        if getattr(albaran, "observaciones", None):
            elementos.extend([Spacer(1, 12), Paragraph("OBSERVACIONES", texto), Paragraph(escape(albaran.observaciones).replace("\n", "<br/>"), texto)])
        PdfService._agregar_pie_configurable(elementos, configuracion_documentos, texto)
        doc.build(elementos)
        buffer.seek(0)
        return buffer

    @staticmethod
    def generar_pedido_compra(
        pedido,
        empresa,
        configuracion_taller=None,
        configuracion_documentos=None,
    ):
        """Genera el documento imprimible de un pedido de compra."""

        buffer = BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=40,
            leftMargin=40,
            topMargin=40,
            bottomMargin=40,
        )

        estilos = getSampleStyleSheet()
        titulo = ParagraphStyle(
            "PedidoCompraTitulo",
            parent=estilos["Title"],
            fontName="Helvetica-Bold",
            fontSize=20,
            leading=24,
            textColor=colors.HexColor("#123A63"),
            spaceAfter=4,
        )
        subtitulo = ParagraphStyle(
            "PedidoCompraSubtitulo",
            parent=estilos["Normal"],
            fontName="Helvetica-Bold",
            fontSize=11,
            leading=14,
            textColor=colors.HexColor("#555555"),
            spaceAfter=16,
        )
        seccion = ParagraphStyle(
            "PedidoCompraSeccion",
            parent=estilos["Heading2"],
            fontName="Helvetica-Bold",
            fontSize=10,
            leading=13,
            textColor=colors.HexColor("#123A63"),
            spaceBefore=14,
            spaceAfter=6,
        )
        texto = ParagraphStyle(
            "PedidoCompraTexto",
            parent=estilos["Normal"],
            fontName="Helvetica",
            fontSize=9,
            leading=12,
        )

        def importe(valor) -> str:
            return f"{float(valor or 0):,.2f} €".replace(
                ",",
                "X",
            ).replace(
                ".",
                ",",
            ).replace(
                "X",
                ".",
            )

        def valor(objeto, atributo: str, defecto: str = "-") -> str:
            dato = getattr(objeto, atributo, None) if objeto else None
            return str(dato) if dato not in (None, "") else defecto

        fecha = getattr(pedido, "fecha", None)
        fecha_texto = fecha.strftime("%d/%m/%Y") if fecha else "-"
        datos_taller = PdfService._datos_taller_documento(
            empresa,
            configuracion_taller,
            configuracion_documentos,
        )
        nombre_empresa = datos_taller["nombre"]
        ruta_logo_pdf = PdfService._ruta_logo_documento(
            empresa=empresa,
            configuracion_taller=configuracion_taller,
        )
        logo = None
        if ruta_logo_pdf:
            try:
                imagen_logo = ImageReader(ruta_logo_pdf)
                ancho_original, alto_original = imagen_logo.getSize()
                escala = min(72 / ancho_original, 48 / alto_original)
                logo = Image(
                    ruta_logo_pdf,
                    width=ancho_original * escala,
                    height=alto_original * escala,
                )
                logo.hAlign = "LEFT"
            except Exception:
                logo = None

        elementos = [
            Paragraph("PEDIDO DE COMPRA", titulo),
            Paragraph(valor(pedido, "numero"), subtitulo),
        ]

        datos_cabecera = [
            [
                Paragraph("<b>EMPRESA</b><br/>" + nombre_empresa, texto),
                Paragraph(
                    "<b>FECHA</b><br/>" + fecha_texto
                    + "<br/><br/><b>ESTADO</b><br/>"
                    + valor(pedido, "estado"),
                    texto,
                ),
            ],
            [
                Paragraph(
                    "<b>NIF</b>: " + valor(empresa, "nif")
                    + "<br/><b>Teléfono</b>: " + valor(empresa, "telefono")
                    + "<br/><b>Email</b>: " + valor(empresa, "email"),
                    texto,
                ),
                Paragraph(
                    "<b>Proveedor</b><br/>"
                    + valor(getattr(pedido, "proveedor", None), "nombre")
                    + "<br/><b>CIF</b>: "
                    + valor(getattr(pedido, "proveedor", None), "cif")
                    + "<br/><b>Teléfono</b>: "
                    + valor(getattr(pedido, "proveedor", None), "telefono")
                    + "<br/><b>Email</b>: "
                    + valor(getattr(pedido, "proveedor", None), "email"),
                    texto,
                ),
            ],
        ]
        # Sustituye el bloque histórico por los datos y visibilidad configurados.
        datos_cabecera[1][0] = Paragraph(
            PdfService._bloque_datos_taller(datos_taller),
            texto,
        )
        if logo is not None:
            datos_cabecera[0][0] = Table(
                [[logo, Paragraph("<b>EMPRESA</b><br/>" + escape(nombre_empresa), texto)]],
                colWidths=[82, 155],
            )
            datos_cabecera[0][0].setStyle(TableStyle([
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                ("TOPPADDING", (0, 0), (-1, -1), 0),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
            ]))
        cabecera = Table(datos_cabecera, colWidths=[257, 257])
        cabecera.setStyle(TableStyle([
            ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#B8C4D0")),
            ("INNERGRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#D9E0E6")),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#F3F7FA")),
            ("LEFTPADDING", (0, 0), (-1, -1), 10),
            ("RIGHTPADDING", (0, 0), (-1, -1), 10),
            ("TOPPADDING", (0, 0), (-1, -1), 8),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ]))
        elementos.extend([cabecera, Paragraph("ARTÍCULOS", seccion)])

        filas = [[
            "Ref.", "Descripción", "Cant.", "Coste", "IVA", "Total"
        ]]
        for linea in getattr(pedido, "lineas", []):
            filas.append([
                valor(linea, "referencia"),
                valor(linea, "descripcion"),
                str(getattr(linea, "cantidad_pedida", 0)),
                importe(getattr(linea, "coste_unitario", 0)),
                f"{float(getattr(linea, 'iva', 0)):.0f}%",
                importe(getattr(linea, "total", 0)),
            ])

        tabla_lineas = Table(
            filas,
            colWidths=[66, 202, 49, 66, 40, 92],
            repeatRows=1,
        )
        tabla_lineas.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#123A63")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 8),
            ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#D9E0E6")),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("ALIGN", (2, 1), (-1, -1), "RIGHT"),
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ("RIGHTPADDING", (0, 0), (-1, -1), 6),
            ("TOPPADDING", (0, 0), (-1, -1), 7),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
        ]))
        elementos.extend([tabla_lineas, Spacer(1, 14)])

        totales = Table([
            ["Subtotal", importe(getattr(pedido, "subtotal", 0))],
            ["IVA", importe(getattr(pedido, "iva_total", 0))],
            ["TOTAL", importe(getattr(pedido, "total", 0))],
        ], colWidths=[130, 100], hAlign="RIGHT")
        totales.setStyle(TableStyle([
            ("ALIGN", (0, 0), (-1, -1), "RIGHT"),
            ("FONTNAME", (0, 0), (-1, -2), "Helvetica"),
            ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
            ("FONTSIZE", (0, -1), (-1, -1), 12),
            ("LINEABOVE", (0, -1), (-1, -1), 0.8, colors.HexColor("#123A63")),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ]))
        elementos.append(totales)

        observaciones = getattr(pedido, "observaciones", None)
        if not (observaciones and str(observaciones).strip()):
            observaciones = (
                configuracion_documentos.get("observaciones_pedido_compra")
                if isinstance(configuracion_documentos, dict)
                else getattr(
                    configuracion_documentos,
                    "observaciones_pedido_compra",
                    None,
                )
            )
        if observaciones:
            elementos.extend([
                Paragraph("OBSERVACIONES", seccion),
                Paragraph(escape(str(observaciones)).replace("\n", "<br/>"), texto),
            ])

        PdfService._agregar_pie_configurable(
            elementos,
            configuracion_documentos,
            texto,
        )

        doc.build(elementos)
        buffer.seek(0)
        return buffer

    @staticmethod
    def generar_informe_general(informe, empresa):
        """Genera un PDF del mismo resumen que se muestra en Informes."""

        buffer = BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=40,
            leftMargin=40,
            topMargin=40,
            bottomMargin=40,
        )
        estilos = getSampleStyleSheet()
        titulo = ParagraphStyle(
            "InformeGeneralTitulo",
            parent=estilos["Title"],
            fontName="Helvetica-Bold",
            fontSize=20,
            leading=24,
            textColor=colors.HexColor("#123A63"),
            spaceAfter=4,
        )
        subtitulo = ParagraphStyle(
            "InformeGeneralSubtitulo",
            parent=estilos["Normal"],
            fontSize=10,
            leading=13,
            textColor=colors.HexColor("#5B6470"),
            spaceAfter=14,
        )
        seccion = ParagraphStyle(
            "InformeGeneralSeccion",
            parent=estilos["Heading2"],
            fontName="Helvetica-Bold",
            fontSize=11,
            leading=14,
            textColor=colors.HexColor("#123A63"),
            spaceBefore=14,
            spaceAfter=6,
        )
        texto = ParagraphStyle(
            "InformeGeneralTexto",
            parent=estilos["Normal"],
            fontSize=9,
            leading=12,
        )

        def dato(clave, defecto=None):
            if isinstance(informe, dict):
                return informe.get(clave, defecto)
            return getattr(informe, clave, defecto)

        def bloque(clave):
            return dato(clave, {}) or {}

        def valor(objeto, clave, defecto=0):
            if isinstance(objeto, dict):
                return objeto.get(clave, defecto)
            return getattr(objeto, clave, defecto)

        def texto_seguro(valor_texto) -> str:
            return escape(str(valor_texto if valor_texto not in (None, "") else "-"))

        def importe(numero) -> str:
            return (
                f"{float(numero or 0):,.2f} €"
                .replace(",", "X")
                .replace(".", ",")
                .replace("X", ".")
            )

        def numero(numero_valor) -> str:
            return f"{float(numero_valor or 0):,.2f}".replace(".", ",")

        def fecha_texto(fecha) -> str:
            return fecha.strftime("%d/%m/%Y") if fecha else "-"

        def tabla_resumen(filas, anchos=(310, 170)):
            tabla = Table(
                [[texto_seguro(etiqueta), texto_seguro(dato_fila)] for etiqueta, dato_fila in filas],
                colWidths=list(anchos),
            )
            tabla.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, -1), colors.white),
                ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#D9E0E6")),
                ("FONTNAME", (1, 0), (1, -1), "Helvetica-Bold"),
                ("ALIGN", (1, 0), (1, -1), "RIGHT"),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
                ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ]))
            return tabla

        fecha_inicio = dato("fecha_inicio")
        fecha_fin_exclusiva = dato("fecha_fin")
        fecha_fin = (
            fecha_fin_exclusiva - timedelta(days=1)
            if fecha_fin_exclusiva else None
        )
        ordenes = bloque("ordenes")
        facturacion = bloque("facturacion")
        stock = bloque("stock")
        compras = bloque("compras")
        garantias = bloque("garantias")
        personal = bloque("personal")

        # El informe también es un documento corporativo: se muestra la
        # denominación fiscal del emisor antes que su marca comercial.
        nombre_empresa = getattr(empresa, "nombre", None) or getattr(
            empresa,
            "nombre_comercial",
            "MotorDesk",
        )
        direccion = " · ".join(
            str(item) for item in [
                getattr(empresa, "direccion", None),
                getattr(empresa, "codigo_postal", None),
                getattr(empresa, "ciudad", None),
            ] if item
        ) or "-"

        elementos = [
            Paragraph("INFORME DEL TALLER", titulo),
            Paragraph(
                f"Periodo: {fecha_texto(fecha_inicio)} - {fecha_texto(fecha_fin)}",
                subtitulo,
            ),
            Paragraph("EMPRESA", seccion),
            Paragraph(
                f"<b>{texto_seguro(nombre_empresa)}</b><br/>"
                f"NIF: {texto_seguro(getattr(empresa, 'nif', None))}<br/>"
                f"{texto_seguro(direccion)}",
                texto,
            ),
            Paragraph("RESUMEN", seccion),
            tabla_resumen([
                ("Órdenes", valor(ordenes, "total")),
                ("Facturación", importe(valor(facturacion, "total_facturado"))),
                ("Ticket medio", importe(valor(facturacion, "ticket_medio"))),
                ("Compras", importe(valor(compras, "total_compras"))),
                ("Garantías", valor(garantias, "total")),
                ("Personal activo", valor(personal, "usuarios_activos")),
            ]),
            Paragraph("ÓRDENES", seccion),
            tabla_resumen([
                ("Total", valor(ordenes, "total")),
                ("Cerradas", valor(ordenes, "cerradas")),
                ("Facturadas", valor(ordenes, "facturadas")),
                ("En curso", valor(ordenes, "en_curso")),
                ("Presupuestos", valor(ordenes, "presupuestos")),
                ("Garantías", valor(ordenes, "garantias")),
            ]),
        ]

        trabajos = valor(ordenes, "trabajos_frecuentes", []) or []
        if trabajos:
            elementos.append(Paragraph("Trabajos más frecuentes", seccion))
            filas_trabajos = [["#", "Trabajo", "N.º órdenes"]]
            for posicion, trabajo in enumerate(trabajos, start=1):
                filas_trabajos.append([
                    str(posicion),
                    str(valor(trabajo, "descripcion", "-")),
                    str(valor(trabajo, "total", 0)),
                ])
            tabla_trabajos = Table(filas_trabajos, colWidths=[35, 350, 95], repeatRows=1)
            tabla_trabajos.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#123A63")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#D9E0E6")),
                ("ALIGN", (0, 1), (0, -1), "CENTER"),
                ("ALIGN", (2, 1), (2, -1), "RIGHT"),
                ("LEFTPADDING", (0, 0), (-1, -1), 7),
                ("RIGHTPADDING", (0, 0), (-1, -1), 7),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ]))
            elementos.append(tabla_trabajos)

        elementos.extend([
            Paragraph("FACTURACIÓN", seccion),
            tabla_resumen([
                ("Facturas emitidas", valor(facturacion, "facturas_emitidas")),
                ("Facturas anuladas", valor(facturacion, "facturas_anuladas")),
                ("Total facturado", importe(valor(facturacion, "total_facturado"))),
                ("Ticket medio", importe(valor(facturacion, "ticket_medio"))),
            ]),
            Paragraph("STOCK", seccion),
            tabla_resumen([
                ("Movimientos", valor(stock, "movimientos")),
                ("Consumo", numero(valor(stock, "unidades_consumidas"))),
                ("Entradas por compra", numero(valor(stock, "entradas_compra"))),
                ("Ajustes positivos", numero(valor(stock, "ajustes_positivos"))),
                ("Ajustes negativos", numero(valor(stock, "ajustes_negativos"))),
            ]),
            Paragraph("COMPRAS", seccion),
            tabla_resumen([
                ("Pedidos", valor(compras, "pedidos")),
                ("Recibidos", valor(compras, "recibidos")),
                ("Parciales", valor(compras, "recibidos_parciales")),
                ("Cancelados", valor(compras, "cancelados")),
                ("Total compras", importe(valor(compras, "total_compras"))),
                ("Ticket medio", importe(valor(compras, "ticket_medio"))),
            ]),
            Paragraph("GARANTÍAS", seccion),
            tabla_resumen([
                ("Total", valor(garantias, "total")),
                ("Abiertas", valor(garantias, "abiertas")),
                ("En revisión", valor(garantias, "en_revision")),
                ("Aprobadas", valor(garantias, "aprobadas")),
                ("Rechazadas", valor(garantias, "rechazadas")),
                ("En reparación", valor(garantias, "en_reparacion")),
                ("Resueltas", valor(garantias, "resueltas")),
                ("Tiempo medio", f"{numero(valor(garantias, 'tiempo_medio_resolucion_dias'))} días"),
            ]),
            Paragraph("PERSONAL", seccion),
        ])

        detalle_personal = valor(personal, "detalle", []) or []
        if detalle_personal:
            filas_personal = [["Personal", "Rol", "Órdenes", "Citas", "Ausencias", "Días"]]
            for persona in detalle_personal:
                filas_personal.append([
                    str(valor(persona, "nombre", "-")),
                    str(valor(persona, "rol", "-")),
                    str(valor(persona, "ordenes_asignadas", 0)),
                    str(valor(persona, "citas_asignadas", 0)),
                    str(valor(persona, "ausencias", 0)),
                    numero(valor(persona, "dias_ausencia", 0)),
                ])
            tabla_personal = Table(
                filas_personal,
                colWidths=[140, 90, 60, 50, 70, 60],
                repeatRows=1,
            )
            tabla_personal.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#123A63")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#D9E0E6")),
                ("ALIGN", (2, 1), (-1, -1), "RIGHT"),
                ("FONTSIZE", (0, 0), (-1, -1), 8),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ]))
            elementos.append(tabla_personal)
        else:
            elementos.append(Paragraph("No hay actividad de personal en este periodo.", texto))

        doc.build(elementos)
        buffer.seek(0)
        return buffer

    @staticmethod
    def generar_informe_economico(titulo_informe, informe, empresa):
        """PDF tabular para facturación, clientes y compras/gastos."""
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=28, leftMargin=28, topMargin=34, bottomMargin=34)
        estilos = getSampleStyleSheet()
        titulo = ParagraphStyle("InformeEconomicoTitulo", parent=estilos["Title"], fontName="Helvetica-Bold", fontSize=18, leading=22, textColor=colors.HexColor("#123A63"), spaceAfter=4)
        subtitulo = ParagraphStyle("InformeEconomicoSubtitulo", parent=estilos["Normal"], fontSize=9, leading=12, textColor=colors.HexColor("#5B6470"), spaceAfter=12)
        celda = ParagraphStyle("InformeEconomicoCelda", parent=estilos["Normal"], fontSize=7.2, leading=8.5, wordWrap="CJK")

        def importe(valor):
            return f"{float(valor or 0):,.2f} €".replace(",", "X").replace(".", ",").replace("X", ".")

        def fecha_texto(fecha):
            return fecha.strftime("%d/%m/%Y") if fecha else "-"

        fecha_fin = informe["fecha_fin"] - timedelta(days=1)
        nombre_empresa = getattr(empresa, "nombre", None) or getattr(empresa, "nombre_comercial", None) or "MotorDesk"
        es_clientes = titulo_informe == "RESUMEN ECONÓMICO POR CLIENTE"
        es_compras = titulo_informe == "COMPRAS Y GASTOS"
        es_facturacion = not es_clientes and not es_compras
        if es_clientes:
            cabecera = ["Cliente", "NIF/CIF", "Facturas", "Base", "IVA", "Total"]
            anchos = [150, 88, 52, 70, 60, 70]
        elif es_compras:
            cabecera = ["Fecha", "Factura", "Tipo", "Proveedor", "NIF/CIF", "Base", "IVA", "Total"]
            anchos = [45, 66, 59, 107, 61, 49, 42, 58]
        else:
            cabecera = ["Fecha", "Factura", "Cliente", "NIF/CIF", "Base", "IVA", "Total", "Método de pago"]
            anchos = [45, 73, 112, 66, 57, 45, 55, 83]
        datos = [cabecera]
        for fila in informe["filas"]:
            if es_clientes:
                valores = [fila["tercero"], fila["nif"], str(fila["documentos"]), importe(fila["base"]), importe(fila["iva"]), importe(fila["total"])]
            elif es_compras:
                valores = [fecha_texto(fila["fecha"]), fila["numero"], fila.get("tipo_gasto", "COMPRA").title(), fila["tercero"], fila["nif"], importe(fila["base"]), importe(fila["iva"]), importe(fila["total"])]
            else:
                valores = [fecha_texto(fila["fecha"]), fila["numero"], fila["tercero"], fila["nif"], importe(fila["base"]), importe(fila["iva"]), importe(fila["total"]), fila.get("metodo_pago", "Pendiente")]
            datos.append([Paragraph(escape(str(valor or "-")), celda) for valor in valores])
        if len(datos) == 1:
            datos.append([Paragraph("No hay datos en el periodo seleccionado.", celda)] + [""] * (len(cabecera) - 1))

        tabla = Table(datos, colWidths=anchos, repeatRows=1)
        tabla.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#123A63")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, 0), 7.5),
            ("GRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#D9E0E6")),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("ALIGN", (4, 1) if es_facturacion else (-3, 1), (6, -1) if es_facturacion else (-1, -1), "RIGHT"),
            ("ALIGN", (2, 1), (2, -1), "RIGHT" if es_clientes else "LEFT"),
            ("LEFTPADDING", (0, 0), (-1, -1), 5), ("RIGHTPADDING", (0, 0), (-1, -1), 5),
            ("TOPPADDING", (0, 0), (-1, -1), 5), ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ]))
        totales = informe["totales"]
        resumen = Table([
            ["Documentos" if not es_clientes else "Clientes", str(totales["documentos"])],
            ["Base imponible", importe(totales["base"])], ["IVA", importe(totales["iva"])], ["TOTAL", importe(totales["total"])],
        ], colWidths=[130, 100], hAlign="RIGHT")
        resumen.setStyle(TableStyle([
            ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#D9E0E6")),
            ("ALIGN", (1, 0), (1, -1), "RIGHT"), ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
            ("BACKGROUND", (0, -1), (-1, -1), colors.HexColor("#E8F0F8")),
            ("LEFTPADDING", (0, 0), (-1, -1), 7), ("RIGHTPADDING", (0, 0), (-1, -1), 7),
            ("TOPPADDING", (0, 0), (-1, -1), 5), ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ]))
        elementos = [
            Paragraph(titulo_informe, titulo),
            Paragraph(f"{escape(str(nombre_empresa))} · Periodo: {fecha_texto(informe['fecha_inicio'])} - {fecha_texto(fecha_fin)}", subtitulo),
            tabla, Spacer(1, 16), resumen,
        ]
        doc.build(elementos)
        buffer.seek(0)
        return buffer

    @staticmethod
    def generar_factura(
        factura,
        empresa,
        configuracion_taller=None,
        configuracion_documentos=None,
    ):

        buffer = BytesIO()

        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=40,
            leftMargin=40,
            topMargin=40,
            bottomMargin=105,
        )

        styles = getSampleStyleSheet()
        datos_taller = PdfService._datos_taller_documento(
            empresa,
            configuracion_taller,
            configuracion_documentos,
        )
        elementos = []

        def dibujar_pie_pagina(canvas, doc):

            canvas.saveState()

            ancho_pagina, _ = A4

            canvas.setStrokeColor(
                colors.HexColor("#BDBDBD")
            )
            canvas.setLineWidth(0.5)
            canvas.line(
                40,
                92,
                ancho_pagina - 40,
                92
            )

            texto_legal = (
                "En cumplimiento con la Ley Orgánica 15/1999, de 13 de diciembre, "
                "de Protección de Datos de Carácter Personal, le informamos de que "
                "los datos facilitados serán incluidos en el fichero de clientes "
                "de la empresa, con la finalidad de gestionar la relación comercial "
                "y administrativa. Asimismo, podrá ejercer sus derechos de acceso, "
                "rectificación, cancelación y oposición dirigiéndose a la empresa."
            )

            estilo_legal = ParagraphStyle(
                name="TextoLegal",
                fontName="Helvetica",
                fontSize=6.5,
                leading=7.5,
                alignment=TA_JUSTIFY,
                textColor=colors.HexColor("#444444"),
            )

            parrafo_legal = Paragraph(
                texto_legal,
                estilo_legal
            )

            ancho_texto = ancho_pagina - 80

            _, alto_texto = parrafo_legal.wrap(
                ancho_texto,
                55
            )

            parrafo_legal.drawOn(
                canvas,
                40,
                82 - alto_texto
            )

            canvas.setFont(
                "Helvetica-Bold",
                7
            )
            canvas.setFillColor(
                colors.HexColor("#222222")
            )

            aviso = (
                "LA TENENCIA DE ESTA FACTURA NO ACREDITA SU PAGO "
                "SI NO VA ACOMPAÑADA DEL CORRESPONDIENTE RECIBO "
                "O TÍTULO DE PAGO"
            )

            canvas.drawCentredString(
                ancho_pagina / 2,
                30,
                aviso
            )

            canvas.setFont(
                "Helvetica",
                7
            )
            canvas.setFillColor(
                colors.HexColor("#666666")
            )

            nombre_empresa_pie = datos_taller["nombre"]

            canvas.drawString(
                40,
                16,
                nombre_empresa_pie
            )

            canvas.drawRightString(
                ancho_pagina - 40,
                16,
                f"Página {doc.page}"
            )

            canvas.restoreState()

        # -------------------------------------------------
        # Logo
        # -------------------------------------------------

        logo = Spacer(
            250,
            145
        )

        ruta_logo_pdf = PdfService._ruta_logo_documento(
            empresa=empresa,
            configuracion_taller=configuracion_taller,
        )

        if (
            ruta_logo_pdf
            and os.path.exists(ruta_logo_pdf)
        ):

            try:

                imagen = ImageReader(
                    ruta_logo_pdf
                )

                ancho_original, alto_original = imagen.getSize()

                ancho_maximo = 250
                alto_maximo = 145

                escala = min(
                    ancho_maximo / ancho_original,
                    alto_maximo / alto_original
                )

                logo = Image(
                    ruta_logo_pdf,
                    width=ancho_original * escala,
                    height=alto_original * escala
                )

                logo.hAlign = "LEFT"

            except Exception:

                pass

        # -------------------------------------------------
        # Datos del cliente
        # -------------------------------------------------

        cliente = factura.cliente

        nombre_cliente = ", ".join(
            filter(
                None,
                [
                    getattr(cliente, "apellidos", None),
                    getattr(cliente, "nombre", None),
                ]
            )
        )

        direccion_cliente = (
            getattr(cliente, "direccion", None)
            or ""
        )

        codigo_postal_cliente = (
            getattr(cliente, "codigo_postal", None)
            or ""
        )

        ciudad_cliente = (
            getattr(cliente, "ciudad", None)
            or ""
        )

        provincia_cliente = (
            getattr(cliente, "provincia", None)
            or ""
        )

        nif_cliente = (
            getattr(cliente, "dni", None)
            or ""
        )

        email_cliente = (
            getattr(cliente, "email", None)
            or "-"
        )

        telefono_cliente = (
            getattr(cliente, "telefono", None)
            or "-"
        )

        # -------------------------------------------------
        # Cabecera principal
        # -------------------------------------------------

        tipo_factura_mostrado = (
            "FACTURA DE VENTAS Y COMISIONES"
            if factura.tipo_factura == "VENTAS_COMISIONES"
            else factura.tipo_documento
        )

        datos_cliente = Paragraph(
            f"""
            <font size="12">
                <b>DATOS DEL CLIENTE</b>
            </font>

            <br/><br/>

            <b>{nombre_cliente}</b>

            <br/>

            {direccion_cliente}

            <br/>

            {codigo_postal_cliente}
            {ciudad_cliente}
            {f"({provincia_cliente})" if provincia_cliente else ""}

            <br/><br/>

            <b>NIF/CIF:</b>
            {nif_cliente or "-"}

            <br/>

            <b>Teléfono:</b>
            {telefono_cliente}

            <br/>

            <b>Correo electrónico:</b>
            {email_cliente}

            <br/><br/>

            <font size="11">
                <b>DATOS DE FACTURACIÓN</b>
            </font>

            <br/><br/>

            <b>Fecha:</b>
            {factura.fecha_emision.strftime("%d/%m/%Y")}

            <br/>

            <b>N.º documento:</b>
            {factura.numero}

            <br/>

            <b>Tipo:</b>
            {tipo_factura_mostrado}

            <br/>

            <b>Estado:</b>
            {factura.estado}
            """,
            styles["BodyText"]
        )

        # -------------------------------------------------
        # Datos del taller
        # -------------------------------------------------

        nombre_empresa = (
            empresa.nombre
            or empresa.nombre_comercial
        )

        web_empresa = (
            getattr(
                empresa,
                "web",
                None
            )
            or ""
        )

        datos_empresa = Paragraph(
            f"""
            <b>{nombre_empresa}</b>

            <br/>

            {empresa.direccion}

            <br/>

            {empresa.codigo_postal}
            {empresa.ciudad}
            ({empresa.provincia})

            <br/>

            Teléfono: {empresa.telefono}

            <br/>

            {empresa.email}

            {
                f"<br/>{web_empresa}"
                if web_empresa
                else ""
            }
            """,
            styles["BodyText"]
        )

        # La configuración decide qué datos de contacto se muestran.
        datos_empresa = Paragraph(
            PdfService._bloque_datos_taller(datos_taller),
            styles["BodyText"],
        )

        # -------------------------------------------------
        # Columna izquierda: logo y datos del taller
        # -------------------------------------------------

        columna_empresa = Table(
            [
                [
                    Table(
                        [
                            [logo],
                            [Spacer(1, 8)],
                            [datos_empresa]
                        ],
                        colWidths=[250]
                    )
                ]
            ],
            colWidths=[250]
        )

        columna_empresa.setStyle(
            TableStyle(
                [
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 0),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                    ("TOPPADDING", (0, 0), (-1, -1), 0),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
                ]
            )
        )

        # -------------------------------------------------
        # Cabecera completa
        # -------------------------------------------------

        cabecera_principal = Table(
            [
                [
                    columna_empresa,
                    datos_cliente
                ]
            ],
            colWidths=[
                270,
                225
            ]
        )

        cabecera_principal.setStyle(
            TableStyle(
                [
                    (
                        "VALIGN",
                        (0, 0),
                        (0, 0),
                        "TOP"
                    ),

                    (
                        "VALIGN",
                        (1, 0),
                        (1, 0),
                        "MIDDLE"
                    ),

                    (
                        "LEFTPADDING",
                        (0, 0),
                        (-1, -1),
                        0
                    ),

                    (
                        "RIGHTPADDING",
                        (0, 0),
                        (-1, -1),
                        0
                    ),

                    (
                        "TOPPADDING",
                        (0, 0),
                        (-1, -1),
                        0
                    ),

                    (
                        "BOTTOMPADDING",
                        (0, 0),
                        (-1, -1),
                        0
                    ),
                ]
            )
        )

        elementos.append(
            cabecera_principal
        )

        elementos.append(
            Spacer(
                1,
                18
            )
        )

        # -------------------------------------------------
        # Datos del vehículo y orden
        # -------------------------------------------------

        # Una factura de recambio puede agrupar albaranes de venta directa y
        # no tiene por qué estar vinculada a un vehículo.
        if factura.vehiculo and factura.tipo_factura != "RECAMBIO":

            vehiculo = factura.vehiculo

            matricula = (
                getattr(vehiculo, "matricula", None)
                or "-"
            )

            marca = (
                getattr(vehiculo, "marca", None)
                or ""
            )

            modelo = (
                getattr(vehiculo, "modelo", None)
                or ""
            )

            kilometros = (
                getattr(vehiculo, "kilometros", None)
                or "-"
            )

            numero_bastidor = (
                getattr(vehiculo, "bastidor", None)
                or "-"
            )

            numero_orden = "-"

            if factura.orden:

                numero_orden = (
                    getattr(factura.orden, "numero", None)
                    or str(factura.orden.id)
                )

            datos_vehiculo = [
                [
                    Paragraph(
                        "<b>VEHÍCULO</b>",
                        styles["BodyText"]
                    ),
                    Paragraph(
                        "<b>MATRÍCULA</b>",
                        styles["BodyText"]
                    ),
                    Paragraph(
                        "<b>KILÓMETROS</b>",
                        styles["BodyText"]
                    ),
                    Paragraph(
                        "<b>N.º ORDEN</b>",
                        styles["BodyText"]
                    ),
                ],
                [
                    f"{marca} {modelo}".strip() or "-",
                    matricula,
                    str(kilometros),
                    numero_orden,
                ],
                [
                    Paragraph(
                        "<b>N.º BASTIDOR</b>",
                        styles["BodyText"]
                    ),
                    numero_bastidor,
                    "",
                    "",
                ],
            ]

            tabla_vehiculo = Table(
                datos_vehiculo,
                colWidths=[
                    210,
                    100,
                    90,
                    95,
                ]
            )

            tabla_vehiculo.setStyle(
                TableStyle(
                    [
                        (
                            "BACKGROUND",
                            (0, 0),
                            (-1, 0),
                            colors.HexColor("#E6E6E6")
                        ),
                        (
                            "FONTNAME",
                            (0, 0),
                            (-1, 0),
                            "Helvetica-Bold"
                        ),
                        (
                            "BOX",
                            (0, 0),
                            (-1, -1),
                            0.7,
                            colors.HexColor("#808080")
                        ),
                        (
                            "INNERGRID",
                            (0, 0),
                            (-1, -1),
                            0.4,
                            colors.HexColor("#BDBDBD")
                        ),
                        (
                            "VALIGN",
                            (0, 0),
                            (-1, -1),
                            "MIDDLE"
                        ),
                        (
                            "LEFTPADDING",
                            (0, 0),
                            (-1, -1),
                            7
                        ),
                        (
                            "RIGHTPADDING",
                            (0, 0),
                            (-1, -1),
                            7
                        ),
                        (
                            "TOPPADDING",
                            (0, 0),
                            (-1, -1),
                            6
                        ),
                        (
                            "SPAN",
                            (1, 2),
                            (3, 2)
                        ),
                        (
                            "BOTTOMPADDING",
                            (0, 0),
                            (-1, -1),
                            6
                        ),
                    ]
                )
            )

            elementos.append(
                tabla_vehiculo
            )

            elementos.append(
                Spacer(
                    1,
                    18
                )
            )

        # -------------------------------------------------
        # Líneas de factura
        # -------------------------------------------------

        datos_lineas = [
            [
                "CANT.",
                "CONCEPTO",
                "PRECIO",
                "DTO.",
                "IMPORTE SIN IVA",
            ]
        ]

        filas_cabecera_albaran = []
        ultimo_albaran_id = None

        for linea in factura.lineas:

            albaran = getattr(linea, "albaran_venta", None)
            albaran_id = getattr(linea, "albaran_venta_id", None)
            if albaran_id and albaran_id != ultimo_albaran_id:
                numero_albaran = getattr(albaran, "numero", None) or "-"
                fecha_albaran = getattr(albaran, "fecha", None)
                fecha_texto = (
                    fecha_albaran.strftime("%d/%m/%Y")
                    if fecha_albaran is not None
                    else "-"
                )
                filas_cabecera_albaran.append(len(datos_lineas))
                datos_lineas.append(
                    [
                        Paragraph(
                            f"<b>Albarán {escape(str(numero_albaran))}"
                            f" · Fecha {fecha_texto}</b>",
                            styles["BodyText"],
                        ),
                        "",
                        "",
                        "",
                        "",
                    ]
                )
                ultimo_albaran_id = albaran_id

            descripcion_linea = escape(str(linea.descripcion))
            if factura.tipo_factura == "VENTAS_COMISIONES":
                categoria = getattr(linea, "categoria_fiscal", "VENTA_SERVICIO")
                etiqueta_categoria = {
                    "VENTA_SERVICIO": "VENTA O SERVICIO",
                    "COMISION_SUJETA": "COMISION SUJETA",
                    "COMISION_EXENTA": "COMISION EXENTA",
                }.get(categoria, categoria)
                descripcion_linea = (
                    f"<b>{etiqueta_categoria}</b><br/>{descripcion_linea}"
                )

            datos_lineas.append(
                [
                    f"{linea.cantidad:.2f}",
                    Paragraph(
                        descripcion_linea,
                        styles["BodyText"]
                    ),
                    f"{linea.precio_unitario:.2f} €",
                    f"{linea.descuento_porcentaje:.2f} %",
                    # El importe de cada concepto corresponde siempre a su
                    # base tras el descuento. El IVA se muestra únicamente
                    # en el resumen fiscal final de la factura.
                    f"{linea.subtotal:.2f} €",
                ]
            )

        tabla_lineas = Table(
            datos_lineas,
            colWidths=[
                50,
                240,
                70,
                55,
                80,
            ],
            repeatRows=1
        )

        estilo_tabla_lineas = [
                    (
                        "BACKGROUND",
                        (0, 0),
                        (-1, 0),
                        colors.HexColor("#D9D9D9")
                    ),
                    (
                        "TEXTCOLOR",
                        (0, 0),
                        (-1, 0),
                        colors.black
                    ),
                    (
                        "FONTNAME",
                        (0, 0),
                        (-1, 0),
                        "Helvetica-Bold"
                    ),
                    (
                        "FONTSIZE",
                        (0, 0),
                        (-1, 0),
                        9
                    ),
                    (
                        "ALIGN",
                        (0, 0),
                        (0, -1),
                        "CENTER"
                    ),
                    (
                        "ALIGN",
                        (2, 0),
                        (-1, -1),
                        "RIGHT"
                    ),
                    (
                        "VALIGN",
                        (0, 0),
                        (-1, -1),
                        "MIDDLE"
                    ),
                    (
                        "BOX",
                        (0, 0),
                        (-1, -1),
                        0.7,
                        colors.HexColor("#707070")
                    ),
                    (
                        "INNERGRID",
                        (0, 0),
                        (-1, -1),
                        0.35,
                        colors.HexColor("#B0B0B0")
                    ),
                    (
                        "TOPPADDING",
                        (0, 0),
                        (-1, 0),
                        7
                    ),
                    (
                        "BOTTOMPADDING",
                        (0, 0),
                        (-1, 0),
                        7
                    ),
                    (
                        "TOPPADDING",
                        (0, 1),
                        (-1, -1),
                        6
                    ),
                    (
                        "BOTTOMPADDING",
                        (0, 1),
                        (-1, -1),
                        6
                    ),
                    (
                        "LEFTPADDING",
                        (0, 0),
                        (-1, -1),
                        6
                    ),
                    (
                        "RIGHTPADDING",
                        (0, 0),
                        (-1, -1),
                        6
                    ),
        ]

        for fila in filas_cabecera_albaran:
            estilo_tabla_lineas.extend(
                [
                    ("SPAN", (0, fila), (-1, fila)),
                    ("BACKGROUND", (0, fila), (-1, fila), colors.HexColor("#F0F4F7")),
                    ("FONTNAME", (0, fila), (-1, fila), "Helvetica-Bold"),
                    ("TEXTCOLOR", (0, fila), (-1, fila), colors.HexColor("#243447")),
                    ("TOPPADDING", (0, fila), (-1, fila), 6),
                    ("BOTTOMPADDING", (0, fila), (-1, fila), 6),
                ]
            )

        tabla_lineas.setStyle(TableStyle(estilo_tabla_lineas))

        elementos.append(
            tabla_lineas
        )

        elementos.append(
            Spacer(
                1,
                18
            )
        )

        # -------------------------------------------------
        # Importes finales
        # -------------------------------------------------

        datos_totales = [
            [
                "BASE IMPONIBLE",
                "IVA",
                "CUOTA IVA",
                "TOTAL",
            ],
            [
                f"{factura.base_imponible:.2f} €",
                f"{factura.iva:.2f} %",
                f"{factura.cuota_iva:.2f} €",
                f"{factura.total:.2f} €",
            ],
        ]

        motivos_exencion = []
        if factura.tipo_factura == "VENTAS_COMISIONES":
            subtotal_lineas = sum(
                (Decimal(linea.subtotal) for linea in factura.lineas),
                Decimal("0.00"),
            )
            descuento_global = (
                subtotal_lineas
                * Decimal(factura.descuento_porcentaje)
                / Decimal("100")
            )
            desglose = {}

            for linea in factura.lineas:
                base_linea = Decimal(linea.subtotal)
                if subtotal_lineas:
                    base_linea -= (
                        descuento_global
                        * Decimal(linea.subtotal)
                        / subtotal_lineas
                    )

                categoria = getattr(linea, "categoria_fiscal", "VENTA_SERVICIO")
                motivo = getattr(linea, "motivo_exencion", None)
                clave = (Decimal(linea.iva), categoria, motivo)
                grupo = desglose.setdefault(
                    clave,
                    {"base": Decimal("0.00"), "cuota": Decimal("0.00")},
                )
                grupo["base"] += base_linea
                grupo["cuota"] += base_linea * Decimal(linea.iva) / Decimal("100")

                if categoria == "COMISION_EXENTA" and motivo:
                    motivos_exencion.append(motivo)

            datos_totales = [["BASE IMPONIBLE", "IVA", "CUOTA IVA", "TOTAL"]]
            for (iva, categoria, _motivo), grupo in desglose.items():
                etiqueta_iva = {
                    "VENTA_SERVICIO": f"VENTA {iva:.2f} %",
                    "COMISION_SUJETA": f"COMISION {iva:.2f} %",
                    "COMISION_EXENTA": "COMISION EXENTA",
                }.get(categoria, f"{iva:.2f} %")
                datos_totales.append(
                    [
                        f"{grupo['base']:.2f} €",
                        etiqueta_iva,
                        f"{grupo['cuota']:.2f} €",
                        "",
                    ]
                )

            datos_totales.append(
                ["", "", "TOTAL", f"{factura.total:.2f} €"]
            )

        tabla_totales = Table(
            datos_totales,
            colWidths=[
                125,
                100,
                120,
                150,
            ]
        )

        tabla_totales.setStyle(
            TableStyle(
                [
                    (
                        "BACKGROUND",
                        (0, 0),
                        (-1, 0),
                        colors.HexColor("#D9D9D9")
                    ),
                    (
                        "FONTNAME",
                        (0, 0),
                        (-1, 0),
                        "Helvetica-Bold"
                    ),
                    (
                        "FONTSIZE",
                        (0, 0),
                        (-1, 0),
                        9
                    ),
                    (
                        "ALIGN",
                        (0, 0),
                        (-1, -1),
                        "CENTER"
                    ),
                    (
                        "FONTNAME",
                        (0, 1),
                        (-1, 1),
                        "Helvetica"
                    ),
                    (
                        "FONTSIZE",
                        (0, 1),
                        (-1, 1),
                        10
                    ),
                    (
                        "BACKGROUND",
                        (3, 0),
                        (3, -1),
                        colors.HexColor("#E2F0D9")
                    ),
                    (
                        "FONTNAME",
                        (3, 0),
                        (3, -1),
                        "Helvetica-Bold"
                    ),
                    (
                        "FONTSIZE",
                        (3, 1),
                        (3, 1),
                        13
                    ),
                    (
                        "BOX",
                        (0, 0),
                        (-1, -1),
                        0.8,
                        colors.HexColor("#707070")
                    ),
                    (
                        "INNERGRID",
                        (0, 0),
                        (-1, -1),
                        0.4,
                        colors.HexColor("#A0A0A0")
                    ),
                    (
                        "VALIGN",
                        (0, 0),
                        (-1, -1),
                        "MIDDLE"
                    ),
                    (
                        "TOPPADDING",
                        (0, 0),
                        (-1, 0),
                        7
                    ),
                    (
                        "BOTTOMPADDING",
                        (0, 0),
                        (-1, 0),
                        7
                    ),
                    (
                        "TOPPADDING",
                        (0, 1),
                        (-1, 1),
                        10
                    ),
                    (
                        "BOTTOMPADDING",
                        (0, 1),
                        (-1, 1),
                        10
                    ),
                ]
            )
        )

        elementos.append(
            tabla_totales
        )

        if motivos_exencion:
            motivos = "; ".join(dict.fromkeys(motivos_exencion))
            elementos.append(Spacer(1, 8))
            elementos.append(
                Paragraph(
                    f"<b>Comisiones exentas de IVA:</b> {escape(motivos)}",
                    styles["BodyText"],
                )
            )

        # -------------------------------------------------
        # QR tributario VERI*FACTU
        # -------------------------------------------------

        # Un borrador no es una factura expedida. El QR se incorpora al
        # documento definitivo, una vez emitida la factura.
        if factura.estado == "EMITIDA":
            qr_buffer = VerifactuQrService.generar_qr(
                factura,
                empresa
            )

            imagen_qr = Image(
                qr_buffer,
                width=82,
                height=82
            )

            texto_qr = Paragraph(
                """
                <b>VERI*FACTU</b><br/>
                <font size="8">
                Escanee este código QR para cotejar la factura
                en la Agencia Tributaria.
                </font>
                """,
                ParagraphStyle(
                    name="VerifactuQr",
                    parent=styles["BodyText"],
                    leading=10,
                    textColor=colors.HexColor("#1F3D72")
                )
            )

            tabla_qr = Table(
                [[imagen_qr, texto_qr]],
                colWidths=[94, 401]
            )

            tabla_qr.setStyle(
                TableStyle(
                    [
                        ("BOX", (0, 0), (-1, -1), 0.6, colors.HexColor("#B8C6D9")),
                        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F5F8FC")),
                        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                        ("LEFTPADDING", (0, 0), (-1, -1), 8),
                        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                        ("TOPPADDING", (0, 0), (-1, -1), 8),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
                    ]
                )
            )

            elementos.append(Spacer(1, 18))
            elementos.append(tabla_qr)

        # -------------------------------------------------
        # Observaciones
        # -------------------------------------------------

        if (
            factura.observaciones
            and factura.observaciones.strip()
        ):

            elementos.append(
                Spacer(
                    1,
                    18
                )
            )

            texto_observaciones = Paragraph(
                f"""
                <b>OBSERVACIONES</b>

                <br/><br/>

                {factura.observaciones}
                """,
                styles["BodyText"]
            )

            tabla_observaciones = Table(
                [
                    [
                        texto_observaciones
                    ]
                ],
                colWidths=[
                    495
                ]
            )

            tabla_observaciones.setStyle(
                TableStyle(
                    [
                        (
                            "BOX",
                            (0, 0),
                            (-1, -1),
                            0.6,
                            colors.HexColor("#A0A0A0")
                        ),
                        (
                            "BACKGROUND",
                            (0, 0),
                            (-1, -1),
                            colors.HexColor("#F7F7F7")
                        ),
                        (
                            "LEFTPADDING",
                            (0, 0),
                            (-1, -1),
                            10
                        ),
                        (
                            "RIGHTPADDING",
                            (0, 0),
                            (-1, -1),
                            10
                        ),
                        (
                            "TOPPADDING",
                            (0, 0),
                            (-1, -1),
                            8
                        ),
                        (
                            "BOTTOMPADDING",
                            (0, 0),
                            (-1, -1),
                            8
                        ),
                    ]
                )
            )

            elementos.append(
                tabla_observaciones
            )

        # -------------------------------------------------
        # Generar PDF
        # -------------------------------------------------

        doc.build(
            elementos,
            onFirstPage=dibujar_pie_pagina,
            onLaterPages=dibujar_pie_pagina
        )

        buffer.seek(0)

        return buffer
    
    @staticmethod
    def generar_orden(
        orden,
        empresa,
        configuracion_taller=None,
        configuracion_documentos=None,
        taller_visible=None,
        ruta_logo=None,
        contexto_documentos=None,
    ):

        buffer = BytesIO()

        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=40,
            leftMargin=40,
            topMargin=40,
            bottomMargin=40,
        )

        styles = getSampleStyleSheet()
        elementos = []

        datos_taller = PdfService._datos_taller_documento(
            empresa,
            configuracion_taller,
            configuracion_documentos,
        )
        if taller_visible is not None:
            datos_taller = {
                "nombre": (
                    taller_visible.get("razon_social")
                    or taller_visible.get("nombre_comercial")
                    or datos_taller["nombre"]
                ),
                "nif": taller_visible.get("nif_cif") or "",
                "direccion": taller_visible.get("direccion") or "",
                "localidad": " ".join(
                    parte for parte in (
                        taller_visible.get("codigo_postal"),
                        taller_visible.get("localidad"),
                        taller_visible.get("provincia"),
                    ) if parte
                ),
                "telefono": taller_visible.get("telefono") or "",
                "email": taller_visible.get("email") or "",
                "web": taller_visible.get("web") or "",
            }
        nombre_empresa = datos_taller["nombre"]

        es_presupuesto = getattr(orden, "tipo", "OR") == "PR"
        es_garantia = getattr(orden, "tipo", "OR") == "GA"
        fuente_documentos = contexto_documentos or configuracion_documentos
        titulo_documento = (
            "PRESUPUESTO"
            if es_presupuesto
            else "GARANTÍA" if es_garantia else "ORDEN DE REPARACIÓN"
        )
        etiqueta_numero = (
            "N.º PRESUPUESTO"
            if es_presupuesto
            else "N.º GARANTÍA" if es_garantia else "N.º ORDEN"
        )
        etiqueta_fecha = (
            "FECHA"
            if es_presupuesto
            else "FECHA DE APERTURA" if es_garantia else "FECHA DE ENTRADA"
        )
        titulo_firma_cliente = (
            "ACEPTACIÓN DEL PRESUPUESTO / FIRMA DEL CLIENTE"
            if es_presupuesto
            else "CONFORMIDAD DEL CLIENTE" if es_garantia else "FIRMA DEL CLIENTE"
        )
        titulo_trabajos = (
            "TRABAJOS Y MATERIALES PRESUPUESTADOS"
            if es_presupuesto
            else "MOTIVO DE GARANTÍA" if es_garantia else "AVERÍA / TRABAJOS SOLICITADOS"
        )

    # =====================================================
    # ESTILOS
    # =====================================================

        estilo_titulo = ParagraphStyle(
            name="TituloOrden",
            parent=styles["Heading1"],
            fontName="Helvetica-Bold",
            fontSize=18,
            leading=22,
            alignment=1,
            spaceAfter=15,
        )

        estilo_subtitulo = ParagraphStyle(
            name="SubtituloOrden",
            parent=styles["Heading2"],
            fontName="Helvetica-Bold",
            fontSize=13,
            leading=16,
            spaceAfter=10,
            textColor=colors.HexColor("#162B49"),
        )

        estilo_texto = ParagraphStyle(
            name="TextoOrden",
            parent=styles["BodyText"],
            fontName="Helvetica",
            fontSize=9,
            leading=12,
        )

        estilo_dano = ParagraphStyle(
            name="DanoOrden",
            parent=styles["BodyText"],
            fontName="Helvetica",
            fontSize=9,
            leading=13,
            leftIndent=5,
        )

        estilo_condiciones = ParagraphStyle(
            name="CondicionesOrden",
            parent=styles["BodyText"],
            fontName="Helvetica",
            fontSize=7.5,
            leading=9.5,
        )

    # =====================================================
    # HELPERS
    # =====================================================

        def valor(objeto, atributo, defecto="-"):
            resultado = getattr(
                objeto,
                atributo,
                None
            )

            if resultado is None or resultado == "":
                return defecto

            return resultado

        def crear_seccion(titulo, contenido):

            texto = Paragraph(
                f"""
                <b>{titulo}</b>
                <br/><br/>
                {contenido or "-"}
                """,
                estilo_texto
            )

            tabla = Table(
                [[texto]],
                colWidths=[515]
            )

            tabla.setStyle(
                TableStyle(
                    [
                        (
                            "BOX",
                            (0, 0),
                            (-1, -1),
                            0.6,
                            colors.HexColor("#A0A0A0")
                        ),
                        (
                            "LEFTPADDING",
                            (0, 0),
                            (-1, -1),
                            8
                        ),
                        (
                            "RIGHTPADDING",
                            (0, 0),
                            (-1, -1),
                            8
                        ),
                        (
                            "TOPPADDING",
                            (0, 0),
                            (-1, -1),
                            8
                        ),
                        (
                            "BOTTOMPADDING",
                            (0, 0),
                            (-1, -1),
                            8
                        ),
                    ]
                )
            )

            return tabla

    # =====================================================
    # TRADUCCIÓN DE PIEZAS
    # =====================================================

        NOMBRES_PIEZAS = {

            "hood_60":
                "Capó",

            "trunk_99":
                "Maletero",

            "bumper-front_8":
                "Paragolpes delantero",

            "bumper-rear_10":
                "Paragolpes trasero",

            "door-front-l_16":
                "Puerta delantera izquierda",

            "door-front-r_17":
                "Puerta delantera derecha",

            "door-rear-l_22":
                "Puerta trasera izquierda",

            "door-rear-r_23":
                "Puerta trasera derecha",

            "fender-front-l_32":
                "Aleta delantera izquierda",

            "fender-front-r_33":
                "Aleta delantera derecha",

            "side-mirror-l_70":
                "Retrovisor izquierdo",

            "side-mirror-r_71":
                "Retrovisor derecho",

            "windshield_102":
                "Parabrisas",

            "glass-rear_42":
                "Luna trasera",

            "wheel-fender-l_100":
                "Paso de rueda izquierdo",

            "wheel-fender-r_101":
                "Paso de rueda derecho",

            "headlights-cover-l_47":
                "Faro delantero izquierdo",

            "headlights-cover-r_48":
                "Faro delantero derecho",

            "taillight-lens-l_92":
                "Piloto trasero izquierdo",

            "taillight-lens-r_89":
                "Piloto trasero derecho",
        }

        TIPOS_DANO = {
            "scratch": "Arañazo",
            "dent": "Golpe / abolladura",
            "broken": "Roto / fisurado",
            "missing": "Falta / pieza ausente",
            "replace": "Sustituir",
        }

        COLORES_DANO = {
            "scratch": "#FFD600",
            "dent": "#FF8C00",
            "broken": "#E61919",
            "missing": "#3F7FC4",
            "replace": "#55AD37",
        }

        # Coordenadas sobre la plantilla original de 1536 x 1024.
        # Una misma pieza puede marcarse en la vista superior y en su lateral.
        POSICIONES_PIEZAS = {
            "hood_60": [(485, 275)],
            "trunk_99": [(1080, 275)],
            "bumper-front_8": [(350, 280), (75, 670), (825, 670)],
            "bumper-rear_10": [(1180, 280), (675, 665), (1435, 665)],

            "door-front-l_16": [(650, 405), (350, 640)],
            "door-rear-l_22": [(875, 405), (500, 640)],
            "door-front-r_17": [(650, 150), (1100, 640)],
            "door-rear-r_23": [(875, 150), (1250, 640)],

            "fender-front-l_32": [(440, 400), (205, 650)],
            "fender-front-r_33": [(440, 155), (955, 650)],

            "side-mirror-l_70": [(625, 425), (235, 610)],
            "side-mirror-r_71": [(625, 125), (985, 610)],

            "windshield_102": [(610, 280)],
            "glass-rear_42": [(1025, 280)],

            "wheel-fender-l_100": [(505, 410), (550, 690)],
            "wheel-fender-r_101": [(505, 145), (1300, 690)],

            "headlights-cover-l_47": [(370, 355), (100, 650)],
            "headlights-cover-r_48": [(370, 200), (850, 650)],

            "taillight-lens-l_92": [(1160, 350), (650, 650)],
            "taillight-lens-r_89": [(1160, 205), (1400, 650)],
        }

        def crear_plantilla_marcada(ruta, danos_vehiculo):
            """
            Devuelve un BytesIO con una copia de la plantilla y los daños
            dibujados encima. La plantilla original nunca se modifica.
            """
            imagen = PILImage.open(ruta).convert("RGBA")
            dibujo = ImageDraw.Draw(imagen, "RGBA")

            ancho, alto = imagen.size
            escala_x = ancho / 1536
            escala_y = alto / 1024
            radio = max(8, int(min(escala_x, escala_y) * 15))
            borde = max(2, int(min(escala_x, escala_y) * 3))

            for pieza, tipos in (danos_vehiculo or {}).items():

                if not tipos:
                    continue

                posiciones = POSICIONES_PIEZAS.get(pieza)

                # Si todavía no hemos mapeado visualmente una pieza,
                # seguirá apareciendo en el listado textual.
                if not posiciones:
                    continue

                for tipo_dano, activo in tipos.items():

                    if not activo:
                        continue

                    color_hex = COLORES_DANO.get(tipo_dano, "#777777")
                    color_hex = color_hex.lstrip("#")

                    rojo = int(color_hex[0:2], 16)
                    verde = int(color_hex[2:4], 16)
                    azul = int(color_hex[4:6], 16)

                    for x_original, y_original in posiciones:

                        x = int(x_original * escala_x)
                        y = int(y_original * escala_y)

                        dibujo.ellipse(
                            (
                                x - radio,
                                y - radio,
                                x + radio,
                                y + radio
                            ),
                            fill=(rojo, verde, azul, 225),
                            outline=(20, 20, 20, 255),
                            width=borde
                        )

            salida = BytesIO()
            imagen.convert("RGB").save(
                salida,
                format="PNG"
            )
            salida.seek(0)

            return salida

    # =====================================================
    # PIE DE PÁGINA
    # =====================================================

        def dibujar_pie_pagina(canvas, doc):

            canvas.saveState()

            ancho_pagina, _ = A4

            canvas.setStrokeColor(
                colors.HexColor("#BDBDBD")
            )

            canvas.setLineWidth(0.5)

            canvas.line(
                40,
                25,
                ancho_pagina - 40,
                25
            )

            canvas.setFont(
                "Helvetica",
                7
            )

            canvas.setFillColor(
                colors.HexColor("#666666")
            )

            canvas.drawString(
                40,
                13,
                nombre_empresa
            )

            canvas.drawRightString(
                ancho_pagina - 40,
                13,
                f"Página {doc.page}"
            )

            canvas.restoreState()

    # =====================================================
    # PÁGINA 1
    # ORDEN DE REPARACIÓN
    # =====================================================

        # =====================================================
        # CABECERA: EMPRESA + CLIENTE
        # =====================================================

        vehiculo = getattr(
            orden,
            "vehiculo",
            None
        )

        cliente = (
            getattr(vehiculo, "cliente", None)
            if vehiculo
            else None
        )

        # -------------------------------------------------
        # Logo
        # -------------------------------------------------

        logo = Spacer(
            245,
            75
        )

        ruta_logo_pdf = PdfService._ruta_logo_documento(
            empresa=empresa,
            configuracion_taller=configuracion_taller,
            ruta_logo=ruta_logo,
        )

        if (
            ruta_logo_pdf
            and os.path.exists(ruta_logo_pdf)
        ):
            try:

                imagen_logo = ImageReader(
                    ruta_logo_pdf
                )

                ancho_original, alto_original = (
                    imagen_logo.getSize()
                )

                ancho_maximo = 220
                alto_maximo = 75

                escala = min(
                    ancho_maximo / ancho_original,
                    alto_maximo / alto_original
                )

                logo = Image(
                    ruta_logo_pdf,
                    width=ancho_original * escala,
                    height=alto_original * escala
                )

                logo.hAlign = "LEFT"

            except Exception:
                pass

        # -------------------------------------------------
        # Datos empresa
        # -------------------------------------------------

        if empresa:

            direccion_empresa = (
                f"{valor(empresa, 'direccion', '')}<br/>"
                f"{valor(empresa, 'codigo_postal', '')} "
                f"{valor(empresa, 'ciudad', '')} "
                f"({valor(empresa, 'provincia', '')})"
            )

            web_empresa = getattr(
                empresa,
                "web",
                None
            )

            datos_empresa = Paragraph(
                f"""
                <b>{nombre_empresa}</b><br/>
                {direccion_empresa}<br/>
                <b>NIF:</b> {valor(empresa, "nif")}<br/>
                <b>Teléfono:</b> {valor(empresa, "telefono")}<br/>
                <b>Email:</b> {valor(empresa, "email")}
                {
                    f'<br/><b>Web:</b> {web_empresa}'
                    if web_empresa
                    else ''
                }
                """,
                estilo_texto
            )

        else:

            datos_empresa = Paragraph(
                "<b>MotorDesk</b>",
                estilo_texto
            )

        datos_empresa = Paragraph(
            PdfService._bloque_datos_taller(datos_taller),
            estilo_texto,
        )

        columna_empresa = Table(
            [
                [logo],
                [Spacer(1, 5)],
                [datos_empresa]
            ],
            colWidths=[250]
        )

        columna_empresa.setStyle(
            TableStyle(
                [
                    (
                        "VALIGN",
                        (0, 0),
                        (-1, -1),
                        "TOP"
                    ),
                    (
                        "LEFTPADDING",
                        (0, 0),
                        (-1, -1),
                        0
                    ),
                    (
                        "RIGHTPADDING",
                        (0, 0),
                        (-1, -1),
                        0
                    ),
                    (
                        "TOPPADDING",
                        (0, 0),
                        (-1, -1),
                        0
                    ),
                    (
                        "BOTTOMPADDING",
                        (0, 0),
                        (-1, -1),
                        0
                    ),
                ]
            )
        )

        # -------------------------------------------------
        # Datos cliente
        # -------------------------------------------------

        if cliente:

            nombre_cliente = ", ".join(
                filter(
                    None,
                    [
                        getattr(cliente, "apellidos", None),
                        getattr(cliente, "nombre", None)
                    ]
                )
            )

            direccion_cliente = (
                getattr(cliente, "direccion", None)
                or "-"
            )

            cp_cliente = (
                getattr(cliente, "codigo_postal", None)
                or ""
            )

            ciudad_cliente = (
                getattr(cliente, "ciudad", None)
                or ""
            )

            datos_cliente = Paragraph(
                f"""
                <br/><br/><br/><br/><br/>
                <font size="12">
                    <b>DATOS DEL CLIENTE</b>
                </font>

                <br/><br/>

                <b>{nombre_cliente or "-"}</b><br/>
                {direccion_cliente}<br/>
                {cp_cliente} {ciudad_cliente}

                <br/><br/>

                <b>NIF/CIF:</b>
                {valor(cliente, "dni")}<br/>

                <b>Teléfono:</b>
                {valor(cliente, "telefono")}<br/>

                <b>Email:</b>
                {valor(cliente, "email")}
                """,
                estilo_texto
            )

        else:

            datos_cliente = Paragraph(
                """
                <font size="12">
                    <b>DATOS DEL CLIENTE</b>
                </font>
                <br/><br/>
                -
                """,
                estilo_texto
            )

        # -------------------------------------------------
        # Montar cabecera
        # -------------------------------------------------

        cabecera = Table(
            [
                [
                    columna_empresa,
                    datos_cliente
                ]
            ],
            colWidths=[
                265,
                250
            ]
        )

        cabecera.setStyle(
            TableStyle(
                [
                    (
                        "VALIGN",
                        (0, 0),
                        (-1, -1),
                        "TOP"
                    ),
                    (
                        "LEFTPADDING",
                        (0, 0),
                        (0, 0),
                        0
                    ),
                    (
                        "RIGHTPADDING",
                        (0, 0),
                        (0, 0),
                        12
                    ),
                    (
                        "LEFTPADDING",
                        (1, 0),
                        (1, 0),
                        12
                    ),
                    (
                        "RIGHTPADDING",
                        (1, 0),
                        (1, 0),
                        0
                    ),
                    (
                        "LINEBEFORE",
                        (1, 0),
                        (1, 0),
                        0.5,
                        colors.HexColor("#D0D0D0")
                    ),
                ]
            )
        )

        elementos.append(
            cabecera
        )

        elementos.append(
            Spacer(
                1,
                18
            )
        )

        elementos.append(
            Paragraph(
                titulo_documento,
                estilo_titulo
            )
        )

        fecha_documento = getattr(
            orden,
            "fecha_entrada",
            None
        )
        fecha_entrada = fecha_documento

        if fecha_entrada:

            fecha_entrada = (
                fecha_entrada.strftime(
                    "%d/%m/%Y %H:%M"
                )
            )

        else:

            fecha_entrada = "-"

        datos_orden = Table(
            [
                [
                    Paragraph(
                        f"<b>{etiqueta_numero}</b>",
                        estilo_texto
                    ),
                    Paragraph(
                        f"<b>{etiqueta_fecha}</b>",
                        estilo_texto
                    ),
                    Paragraph(
                        "<b>ESTADO</b>",
                        estilo_texto
                    ),
                ],
                [
                    str(
                        valor(
                            orden,
                            "numero"
                        )
                    ),
                    fecha_entrada,
                    str(
                        valor(
                            orden,
                            "estado"
                        )
                    ),
                ]
            ],
            colWidths=[
                170,
                175,
                170
            ]
        )

        datos_orden.setStyle(
            TableStyle(
                [
                    (
                        "BACKGROUND",
                        (0, 0),
                        (-1, 0),
                        colors.HexColor("#E6E6E6")
                    ),
                    (
                        "BOX",
                        (0, 0),
                        (-1, -1),
                        0.7,
                        colors.HexColor("#808080")
                    ),
                    (
                        "INNERGRID",
                        (0, 0),
                        (-1, -1),
                        0.4,
                        colors.HexColor("#BDBDBD")
                    ),
                    (
                        "VALIGN",
                        (0, 0),
                        (-1, -1),
                        "MIDDLE"
                    ),
                    (
                        "LEFTPADDING",
                        (0, 0),
                        (-1, -1),
                        7
                    ),
                    (
                        "RIGHTPADDING",
                        (0, 0),
                        (-1, -1),
                        7
                    ),
                    (
                        "TOPPADDING",
                        (0, 0),
                        (-1, -1),
                        6
                    ),
                    (
                        "BOTTOMPADDING",
                        (0, 0),
                        (-1, -1),
                        6
                    ),
                ]
            )
        )

        elementos.append(
            datos_orden
        )

        if es_presupuesto and fecha_documento and fuente_documentos is not None:
            dias_validez = (
                fuente_documentos.get("validez_presupuesto_dias")
                if isinstance(fuente_documentos, dict)
                else getattr(fuente_documentos, "validez_presupuesto_dias", None)
            ) or 30
            fecha_validez = fecha_documento + timedelta(days=int(dias_validez))
            elementos.extend([
                Spacer(1, 8),
                Paragraph(
                    f"Válido hasta: {fecha_validez.strftime('%d/%m/%Y')}",
                    estilo_texto,
                ),
            ])

        elementos.append(
            Spacer(
                1,
                15
            )
        )

    # =====================================================
    # VEHÍCULO
    # =====================================================

        if vehiculo:

            # -------------------------------------------------
            # Preparar valores
            # -------------------------------------------------

            marca = valor(
                vehiculo,
                "marca",
                ""
            )

            modelo = valor(
                vehiculo,
                "modelo",
                ""
            )

            version = valor(
                vehiculo,
                "version"
            )

            matricula = valor(
                vehiculo,
                "matricula"
            )

            bastidor = valor(
                vehiculo,
                "bastidor"
            )

            anio = valor(
                vehiculo,
                "anio"
            )

            color = valor(
                vehiculo,
                "color"
            )

            combustible = valor(
                vehiculo,
                "combustible"
            )

            transmision = valor(
                vehiculo,
                "transmision"
            )

            kilometros = getattr(
                vehiculo,
                "kilometros",
                None
            )

            nombre_vehiculo = (
                f"{marca} {modelo}"
            ).strip() or "-"

            if kilometros is not None:

                kilometros_texto = (
                    f"{kilometros:,}"
                    .replace(",", ".")
                    + " km"
                )

            else:

                kilometros_texto = "-"

            # -------------------------------------------------
            # Título
            # -------------------------------------------------

            titulo_vehiculo = Table(
                [
                    [
                        Paragraph(
                            "<b>DATOS DEL VEHÍCULO</b>",
                            estilo_texto
                        )
                    ]
                ],
                colWidths=[515]
            )

            titulo_vehiculo.setStyle(
                TableStyle(
                    [
                        (
                            "BACKGROUND",
                            (0, 0),
                            (-1, -1),
                            colors.HexColor("#E6E6E6")
                        ),
                        (
                            "BOX",
                            (0, 0),
                            (-1, -1),
                            0.7,
                            colors.HexColor("#808080")
                        ),
                        (
                            "LEFTPADDING",
                            (0, 0),
                            (-1, -1),
                            7
                        ),
                        (
                            "RIGHTPADDING",
                            (0, 0),
                            (-1, -1),
                            7
                        ),
                        (
                            "TOPPADDING",
                            (0, 0),
                            (-1, -1),
                            6
                        ),
                        (
                            "BOTTOMPADDING",
                            (0, 0),
                            (-1, -1),
                            6
                        ),
                    ]
                )
            )

            elementos.append(
                titulo_vehiculo
            )

            # -------------------------------------------------
            # Datos principales
            # -------------------------------------------------

            tabla_vehiculo = Table(
                [
                    [
                        Paragraph(
                            "<b>MARCA / MODELO</b>",
                            estilo_texto
                        ),
                        Paragraph(
                            "<b>VERSIÓN</b>",
                            estilo_texto
                        ),
                        Paragraph(
                            "<b>MATRÍCULA</b>",
                            estilo_texto
                        ),
                    ],
                    [
                        nombre_vehiculo,
                        str(version),
                        str(matricula),
                    ],

                    [
                        Paragraph(
                            "<b>BASTIDOR</b>",
                            estilo_texto
                        ),
                        Paragraph(
                            "<b>AÑO</b>",
                            estilo_texto
                        ),
                        Paragraph(
                            "<b>KILÓMETROS</b>",
                            estilo_texto
                        ),
                    ],
                    [
                        str(bastidor),
                        str(anio),
                        kilometros_texto,
                    ],

                    [
                        Paragraph(
                            "<b>COMBUSTIBLE</b>",
                            estilo_texto
                        ),
                        Paragraph(
                            "<b>TRANSMISIÓN</b>",
                            estilo_texto
                        ),
                        Paragraph(
                            "<b>COLOR</b>",
                            estilo_texto
                        ),
                    ],
                    [
                        str(combustible),
                        str(transmision),
                        str(color),
                    ],
                ],
                colWidths=[
                    200,
                    170,
                    145
                ]
            )

            tabla_vehiculo.setStyle(
                TableStyle(
                    [
                        # Fondos de las filas de títulos
                        (
                            "BACKGROUND",
                            (0, 0),
                            (-1, 0),
                            colors.HexColor("#F2F2F2")
                        ),
                        (
                            "BACKGROUND",
                            (0, 2),
                            (-1, 2),
                            colors.HexColor("#F2F2F2")
                        ),
                        (
                            "BACKGROUND",
                            (0, 4),
                            (-1, 4),
                            colors.HexColor("#F2F2F2")
                        ),

                        # Bordes
                        (
                            "BOX",
                            (0, 0),
                            (-1, -1),
                            0.7,
                            colors.HexColor("#808080")
                        ),
                        (
                            "INNERGRID",
                            (0, 0),
                            (-1, -1),
                            0.4,
                            colors.HexColor("#BDBDBD")
                        ),

                        # Alineación
                        (
                            "VALIGN",
                            (0, 0),
                            (-1, -1),
                            "MIDDLE"
                        ),

                        # Espaciado
                        (
                            "LEFTPADDING",
                            (0, 0),
                            (-1, -1),
                            7
                        ),
                        (
                            "RIGHTPADDING",
                            (0, 0),
                            (-1, -1),
                            7
                        ),
                        (
                            "TOPPADDING",
                            (0, 0),
                            (-1, -1),
                            6
                        ),
                        (
                            "BOTTOMPADDING",
                            (0, 0),
                            (-1, -1),
                            6
                        ),
                    ]
                )
            )

            elementos.append(
                tabla_vehiculo
            )

            elementos.append(
                Spacer(
                    1,
                    15
                )
            )

    # =====================================================
    # ORIGEN DE LA GARANTÍA
    # =====================================================

        if es_garantia:
            orden_origen = getattr(orden, "orden_origen_garantia", None)
            factura_origen = getattr(orden, "factura_origen_garantia", None)
            numero_orden_origen = (
                getattr(orden_origen, "numero", None)
                or (
                    f"#{getattr(orden, 'orden_origen_garantia_id', '')}"
                    if getattr(orden, "orden_origen_garantia_id", None)
                    else "-"
                )
            )
            numero_factura_origen = (
                getattr(factura_origen, "numero", None)
                or (
                    f"#{getattr(orden, 'factura_origen_garantia_id', '')}"
                    if getattr(orden, "factura_origen_garantia_id", None)
                    else "-"
                )
            )

            elementos.append(
                crear_seccion(
                    "ORIGEN DE LA GARANTÍA",
                    "<b>Orden original:</b> " + str(numero_orden_origen)
                    + "<br/><b>Factura original:</b> " + str(numero_factura_origen),
                )
            )
            elementos.append(Spacer(1, 10))

    # =====================================================
    # AVERÍA
    # =====================================================

        elementos.append(
            crear_seccion(
                titulo_trabajos,
                valor(
                    orden,
                    "descripcion_averia"
                )
            )
        )

        diagnostico = getattr(
            orden,
            "diagnostico",
            None
        )

        if diagnostico:

            elementos.append(
                Spacer(
                    1,
                    10
                )
            )

            elementos.append(
                crear_seccion(
                    "DIAGNÓSTICO",
                    diagnostico
                )
            )

        observaciones_propias = getattr(
            orden,
            "observaciones",
            None
        )

        clave_observaciones = (
            "observaciones_presupuesto" if es_presupuesto else "observaciones_orden"
        )
        observaciones_configuradas = (
            fuente_documentos.get(clave_observaciones)
            if isinstance(fuente_documentos, dict)
            else getattr(fuente_documentos, clave_observaciones, None)
        )
        observaciones = (
            observaciones_propias
            if observaciones_propias and str(observaciones_propias).strip()
            else observaciones_configuradas
        )

        if observaciones and str(observaciones).strip():

            elementos.append(
                Spacer(
                    1,
                    10
                )
            )

            elementos.append(
                crear_seccion("OBSERVACIONES", escape(str(observaciones)).replace("\n", "<br/>"))
            )

    # =====================================================
    # TRABAJOS REALIZADOS EN GARANTÍA
    # =====================================================

        if es_garantia:
            filas_cobertura = [
                [
                    Paragraph("<b>CONCEPTO</b>", estilo_texto),
                    Paragraph("<b>CÓDIGO M. O.</b>", estilo_texto),
                    Paragraph("<b>COBERTURA</b>", estilo_texto),
                ]
            ]

            for linea in getattr(orden, "mano_obra", []) or []:
                filas_cobertura.append([
                    str(getattr(linea, "concepto", "-")),
                    str(getattr(linea, "codigo_mano_obra", None) or "-"),
                    "Garantía" if getattr(linea, "cubierto_garantia", False) else "Cliente",
                ])

            for pieza in getattr(orden, "piezas", []) or []:
                descripcion = str(getattr(pieza, "descripcion", "-"))
                referencia = getattr(pieza, "referencia", None)
                if referencia:
                    descripcion += f" ({referencia})"
                filas_cobertura.append([
                    descripcion,
                    "-",
                    "Garantía" if getattr(pieza, "cubierto_garantia", False) else "Cliente",
                ])

            if len(filas_cobertura) == 1:
                filas_cobertura.append(["No se han registrado trabajos ni materiales.", "-", "-"])

            tabla_cobertura = Table(filas_cobertura, colWidths=[295, 105, 115])
            tabla_cobertura.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#E6E6E6")),
                ("BOX", (0, 0), (-1, -1), 0.7, colors.HexColor("#808080")),
                ("INNERGRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#BDBDBD")),
                ("ALIGN", (1, 1), (-1, -1), "CENTER"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("LEFTPADDING", (0, 0), (-1, -1), 7),
                ("RIGHTPADDING", (0, 0), (-1, -1), 7),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ]))
            elementos.append(Spacer(1, 12))
            elementos.append(Paragraph("TRABAJOS REALIZADOS", estilo_subtitulo))
            elementos.append(tabla_cobertura)

    # =====================================================
    # RESUMEN ECONÓMICO
    # =====================================================

        def formatear_importe(importe):
            valor_numerico = float(importe or 0)
            return (
                f"{valor_numerico:,.2f}"
                .replace(",", "_")
                .replace(".", ",")
                .replace("_", ".")
                + " €"
            )

        if es_garantia:
            filas_resumen = [
                [Paragraph("<b>RESUMEN ECONÓMICO</b>", estilo_texto), ""],
                [
                    "Asumido por garantía",
                    formatear_importe(getattr(orden, "coste_asumido_taller", 0)),
                ],
                [
                    "A cargo del cliente",
                    formatear_importe(getattr(orden, "trabajos_no_cubiertos", 0)),
                ],
                [
                    "IVA cliente",
                    formatear_importe(getattr(orden, "iva_cliente_garantia", 0)),
                ],
                [
                    Paragraph("<b>Total cliente</b>", estilo_texto),
                    Paragraph(
                        f"<b>{formatear_importe(getattr(orden, 'total_cliente_garantia', 0))}</b>",
                        estilo_texto,
                    ),
                ],
            ]
        else:
            total_mano_obra = getattr(orden, "total_mano_obra", 0)
            total_piezas = getattr(orden, "total_piezas", 0)
            importe_total = getattr(orden, "importe_total", 0)
            filas_resumen = [
                [Paragraph("<b>RESUMEN ECONÓMICO</b>", estilo_texto), ""],
                ["Mano de obra", formatear_importe(total_mano_obra)],
                ["Piezas", formatear_importe(total_piezas)],
                [
                    Paragraph("<b>TOTAL</b>", estilo_texto),
                    Paragraph(f"<b>{formatear_importe(importe_total)}</b>", estilo_texto),
                ],
            ]

        resumen_economico = Table(filas_resumen, colWidths=[350, 165])

        resumen_economico.setStyle(
            TableStyle([
                ("SPAN", (0, 0), (1, 0)),
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#E6E6E6")),
                ("BACKGROUND", (0, -1), (-1, -1), colors.HexColor("#DCE8F5")),
                ("BOX", (0, 0), (-1, -1), 0.7, colors.HexColor("#808080")),
                ("INNERGRID", (0, 1), (-1, -1), 0.4, colors.HexColor("#BDBDBD")),
                ("ALIGN", (1, 1), (1, -1), "RIGHT"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("LEFTPADDING", (0, 0), (-1, -1), 7),
                ("RIGHTPADDING", (0, 0), (-1, -1), 7),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ])
        )

        elementos.append(Spacer(1, 12))
        elementos.append(resumen_economico)

        if es_garantia and getattr(orden, "resolucion_garantia", None):
            fecha_resolucion = getattr(orden, "fecha_salida", None)
            fecha_resolucion_texto = (
                fecha_resolucion.strftime("%d/%m/%Y %H:%M")
                if fecha_resolucion
                else "-"
            )
            elementos.append(Spacer(1, 12))
            elementos.append(
                crear_seccion(
                    "RESOLUCIÓN",
                    str(getattr(orden, "resolucion_garantia"))
                    + "<br/><br/><b>Estado:</b> " + str(getattr(orden, "estado", "-"))
                    + "<br/><b>Fecha de resolución:</b> " + fecha_resolucion_texto,
                )
            )

    # =====================================================
    # CONDICIONES
    # =====================================================

        if es_presupuesto:
            condiciones = """
        <b>CONDICIONES DEL PRESUPUESTO</b>

        <br/><br/>

        1. El presente documento constituye una estimación
        de los trabajos y materiales indicados y no supone
        por sí mismo la autorización para iniciar la reparación.

        <br/><br/>

        2. La reparación se realizará una vez que el cliente
        haya aceptado el presupuesto.

        <br/><br/>

        3. Si durante los trabajos fuese necesario realizar
        operaciones adicionales no contempladas en este
        presupuesto, se informará al cliente antes de
        realizarlas cuando impliquen una modificación
        del importe previsto.

        <br/><br/>

        4. Los precios indicados corresponden a los trabajos
        y materiales incluidos en el presente presupuesto.

        <br/><br/>

        5. La aceptación del presente presupuesto autoriza
        al taller a generar la correspondiente orden de
        reparación.
            """

        elif es_garantia:
            condiciones = """
    <b>INFORMACIÓN DE LA GARANTÍA</b>

    <br/><br/>

    Este documento identifica el origen de la garantía, las operaciones
    realizadas y los conceptos cubiertos por el taller o a cargo del cliente.
    Los importes a cargo del cliente, si los hubiera, se facturarán por
    separado tras la resolución de la garantía.
            """

        else:
            condiciones = """
    <b>CONDICIONES DE REPARACIÓN Y DEPÓSITO DEL VEHÍCULO</b>

    <br/><br/>

    1. El taller no se responsabiliza de objetos personales
    depositados en el interior del vehículo que no hayan sido
    expresamente declarados en el momento de su recepción.

    <br/><br/>

    2. El cliente autoriza al taller a realizar las operaciones
    necesarias para el diagnóstico, comprobación y reparación
    descritas en esta orden.

    <br/><br/>

    3. Cualquier trabajo adicional que no figure en esta orden
    deberá ser comunicado al cliente cuando suponga una modificación
    sustancial del presupuesto inicialmente previsto.

    <br/><br/>

    4. El cliente declara haber sido informado del estado del vehículo
    en el momento de su recepción y de los daños reflejados en esta
    orden de reparación.

    <br/><br/>

    5. La firma de la presente orden acredita la recepción del vehículo
    por parte del taller y la autorización del cliente para efectuar
    los trabajos indicados.
            """

        tabla_condiciones = Table(
            [
                [
                    Paragraph(
                        condiciones,
                        estilo_condiciones
                    )
                ]
            ],
            colWidths=[
                515
            ]
        )

        tabla_condiciones.setStyle(
            TableStyle(
                [
                    (
                        "BOX",
                        (0, 0),
                        (-1, -1),
                        0.6,
                        colors.HexColor("#A0A0A0")
                    ),
                    (
                        "BACKGROUND",
                        (0, 0),
                        (-1, -1),
                        colors.HexColor("#F7F7F7")
                    ),
                    (
                        "LEFTPADDING",
                        (0, 0),
                        (-1, -1),
                        10
                    ),
                    (
                        "RIGHTPADDING",
                        (0, 0),
                        (-1, -1),
                        10
                    ),
                    (
                        "TOPPADDING",
                        (0, 0),
                        (-1, -1),
                        8
                    ),
                    (
                        "BOTTOMPADDING",
                        (0, 0),
                        (-1, -1),
                        8
                    ),
                ]
            )
        )

        elementos.append(
            tabla_condiciones
        )

        elementos.append(
            Spacer(
                1,
                15
            )
        )

    # =====================================================
    # FIRMA
    # =====================================================

        firma_cliente = Paragraph(
            """
            <b>FIRMA DEL CLIENTE</b>
            <br/><br/><br/><br/>
            ______________________________________
            """,
            estilo_texto
        )

        firma_taller = Paragraph(
            """
            <b>FIRMA / SELLO DEL TALLER</b>
            <br/><br/><br/><br/>
            ______________________________________
            """,
            estilo_texto
        )

        tabla_firmas = Table(
    [
        [
            Paragraph(
                f"<b>{titulo_firma_cliente}</b>",
                estilo_texto
            ),
            Paragraph(
                "<b>FIRMA / SELLO DEL TALLER</b>",
                estilo_texto
            )
        ],
        [
            "",
            ""
        ]
    ],
    colWidths=[
        257.5,
        257.5
    ],
    rowHeights=[
        22,
        45
    ]
)

        elementos.append(
            tabla_firmas
        )

        elementos.append(
            Spacer(
                1,
                15
            )
        )

    # =====================================================
    # PÁGINA 2
    # ESTADO REGISTRADO
    # =====================================================

        elementos.append(
            Paragraph(
                "ESTADO REGISTRADO DEL VEHÍCULO",
                estilo_titulo
            )
        )

        elementos.append(
            Paragraph(
                (
                    f"Orden: <b>{valor(orden, 'numero')}</b>"
                    + (
                        f" &nbsp;&nbsp;&nbsp; Matrícula: "
                        f"<b>{valor(vehiculo, 'matricula')}</b>"
                        if vehiculo
                        else ""
                    )
                ),
                estilo_texto
            )
        )

        elementos.append(
            Spacer(
                1,
                15
            )
        )

    # =====================================================
    # IMAGEN DEL VEHÍCULO
    # =====================================================

        ruta_plantilla = os.path.join(
            os.path.dirname(__file__),
            "..",
            "assets",
            "pdf",
            "vehicle_damage_template.png"
        )

        ruta_plantilla = os.path.abspath(
            ruta_plantilla
        )

        vehicle_damage = (
            getattr(
                orden,
                "vehicle_damage",
                None
            )
            or {}
        )

        if os.path.exists(ruta_plantilla):

            try:

                plantilla_marcada = crear_plantilla_marcada(
                    ruta_plantilla,
                    vehicle_damage
                )

                imagen_reader = ImageReader(
                    plantilla_marcada
                )

                ancho_original, alto_original = (
                    imagen_reader.getSize()
                )

                ancho_maximo = 515
                alto_maximo = 340

                escala = min(
                    ancho_maximo / ancho_original,
                    alto_maximo / alto_original
                )

                plantilla_marcada.seek(0)

                imagen_estado = Image(
                    plantilla_marcada,
                    width=ancho_original * escala,
                    height=alto_original * escala
                )

                imagen_estado.hAlign = "CENTER"

                elementos.append(
                    imagen_estado
                )

            except Exception as error:

                elementos.append(
                    Paragraph(
                        f"No se pudo cargar la plantilla: {error}",
                        estilo_texto
                    )
                )

        else:

            elementos.append(
                Paragraph(
                    "No se encontró la plantilla de inspección del vehículo.",
                    estilo_texto
                )
            )

        elementos.append(
            Spacer(
                1,
                15
            )
        )

    # =====================================================
    # DAÑOS REGISTRADOS
    # =====================================================

        elementos.append(
            Paragraph(
                "DAÑOS REGISTRADOS",
                estilo_subtitulo
            )
        )

        hay_danos = False

        for pieza, danos in vehicle_damage.items():

            if not danos:
                continue

            nombre_pieza = NOMBRES_PIEZAS.get(
                pieza,
                pieza
            )

            for tipo_dano, activo in danos.items():

                if not activo:
                    continue

                hay_danos = True

                nombre_dano = TIPOS_DANO.get(
                    tipo_dano,
                    tipo_dano
                )

                color = COLORES_DANO.get(
                    tipo_dano,
                    "#777777"
                )

                elementos.append(
                    Paragraph(
                        (
                            f'<font color="{color}">'
                            f'<b>●</b>'
                            f'</font>'
                            f' &nbsp; '
                            f'<b>{nombre_pieza}</b>'
                            f' — {nombre_dano}'
                        ),
                        estilo_dano
                    )
                )

                elementos.append(
                    Spacer(
                        1,
                        4
                    )
                )

        if not hay_danos:

            elementos.append(
                Paragraph(
                    "No hay daños registrados en el vehículo.",
                    estilo_texto
                )
            )

    # =====================================================
    # PÁGINA 3
    # INSPECCIÓN MANUAL
    # =====================================================

        elementos.append(
            PageBreak()
        )

        elementos.append(
            Paragraph(
                "INSPECCIÓN MANUAL DEL VEHÍCULO",
                estilo_titulo
            )
        )

        elementos.append(
            Paragraph(
                (
                    "Plantilla destinada a la comprobación manual "
                    "del estado del vehículo en recepción o entrega."
                ),
                estilo_texto
            )
        )

        elementos.append(
            Spacer(
                1,
                15
            )
        )

        if os.path.exists(ruta_plantilla):

            try:

                imagen_reader = ImageReader(
                    ruta_plantilla
                )

                ancho_original, alto_original = (
                    imagen_reader.getSize()
                )

                ancho_maximo = 515
                alto_maximo = 520

                escala = min(
                    ancho_maximo / ancho_original,
                    alto_maximo / alto_original
                )

                imagen_manual = Image(
                    ruta_plantilla,
                    width=ancho_original * escala,
                    height=alto_original * escala
                )

                imagen_manual.hAlign = "CENTER"

                elementos.append(
                    imagen_manual
                )

            except Exception as error:

                elementos.append(
                    Paragraph(
                        f"No se pudo cargar la plantilla: {error}",
                        estilo_texto
                    )
                )

        elementos.append(
            Spacer(
                1,
                20
            )
        )

        firma_inspeccion_cliente = Paragraph(
            f"<b>{titulo_firma_cliente}</b>",
            estilo_texto
        )

        firma_inspeccion_taller = Paragraph(
            """
            <b>FIRMA DEL TALLER</b>
            <br/><br/><br/>
            __________________________________
            """,
            estilo_texto
        )

        tabla_firmas_inspeccion = Table(
            [
                [
                    firma_inspeccion_cliente,
                    firma_inspeccion_taller
                ]
            ],
            colWidths=[
                257.5,
                257.5
            ]
        )

        tabla_firmas_inspeccion.setStyle(
            TableStyle(
                [
                    (
                        "BOX",
                        (0, 0),
                        (-1, -1),
                        0.6,
                        colors.HexColor("#A0A0A0")
                    ),
                    (
                        "INNERGRID",
                        (0, 0),
                        (-1, -1),
                        0.4,
                        colors.HexColor("#BDBDBD")
                    ),
                    (
                        "LEFTPADDING",
                        (0, 0),
                        (-1, -1),
                        10
                    ),
                    (
                        "TOPPADDING",
                        (0, 0),
                        (-1, -1),
                        10
                    ),
                    (
                        "BOTTOMPADDING",
                        (0, 0),
                        (-1, -1),
                        10
                    ),
                ]
            )
        )

        elementos.append(
            tabla_firmas_inspeccion
        )

    # =====================================================
    # CONFIGURACIÓN DEL DOCUMENTO
    # =====================================================

        fuente_documentos = contexto_documentos or configuracion_documentos

        if False:  # Compatibilidad: la fecha de validez ya se muestra en cabecera.
            validez = (
                fuente_documentos.get("validez_presupuesto_dias")
                if isinstance(fuente_documentos, dict)
                else getattr(fuente_documentos, "validez_presupuesto_dias", None)
            )
            if validez:
                elementos.extend([
                    Spacer(1, 12),
                    Paragraph(
                        f"Validez del presupuesto: {validez} días.",
                        estilo_texto,
                    ),
                ])

        clave_observaciones = (
            "observaciones_presupuesto" if es_presupuesto else "observaciones_orden"
        )
        observaciones_configuradas = (
            fuente_documentos.get(clave_observaciones)
            if isinstance(fuente_documentos, dict)
            else getattr(fuente_documentos, clave_observaciones, None)
        )
        observaciones_propias = getattr(orden, "observaciones", None)
        usar_observaciones_predeterminadas = not (
            observaciones_propias and str(observaciones_propias).strip()
        )
        if False and usar_observaciones_predeterminadas and observaciones_configuradas:
            elementos.extend([
                Spacer(1, 10),
                Paragraph(escape(str(observaciones_configuradas)).replace("\n", "<br/>"), estilo_texto),
            ])

        PdfService._agregar_pie_configurable(
            elementos,
            fuente_documentos,
            estilo_texto,
        )

    # =====================================================
    # GENERAR
    # =====================================================

        doc.build(
            elementos,
            onFirstPage=dibujar_pie_pagina,
            onLaterPages=dibujar_pie_pagina
        )

        buffer.seek(0)

        return buffer
