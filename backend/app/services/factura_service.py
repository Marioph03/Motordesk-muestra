"""Servicio fiscal de facturas: borradores, emisión, cobros y VERI*FACTU.

Los cambios aquí deben preservar reglas fiscales; el importe de una orden no es
facturación oficial hasta que exista una factura válida emitida.
"""

from datetime import datetime
from decimal import Decimal
import zlib

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload
from sqlalchemy import text

from app.models.factura import (
    EstadoFactura,
    Factura,
    TipoDocumento,
    TipoFactura,
)
from app.models.factura_linea import FacturaLinea
from app.models.albaran_venta import AlbaranVenta
from app.models.factura_albaran_venta import FacturaAlbaranVenta
from app.models.factura_orden_reparacion import FacturaOrdenReparacion
from app.models.orden_reparacion import EstadoReparacion
from app.repositories.cliente_repository import ClienteRepository
from app.repositories.vehiculo_repository import VehiculoRepository
from app.repositories.orden_reparacion_repository import OrdenReparacionRepository
from app.repositories.factura_repository import FacturaRepository
from app.repositories.factura_linea_repository import FacturaLineaRepository
from app.schemas.factura import (
    FacturaCreate,
    FacturaUpdate
)
from app.services.pdf_service import PdfService
from app.services.facturae_service import FacturaeService
from app.services.facturae_xml_service import FacturaeXmlService
from app.services.configuracion_taller_service import ConfiguracionTallerService
from app.services.configuracion_documentos_service import ConfiguracionDocumentosService
from app.services.configuracion_facturacion_service import ConfiguracionFacturacionService
from app.services.verifactu_service import VerifactuService
from app.services.verifactu_aeat_service import VerifactuAeatService
from app.services.email_service import EmailService
from app.services.whatsapp_service import WhatsAppService
from app.services.whatsapp_config_service import WhatsAppConfigService
from app.repositories.empresa_repository import EmpresaRepository
from app.repositories.registro_verifactu_repository import RegistroVerifactuRepository
from app.models.registro_verifactu import (
    EstadoRegistroVerifactu,
    TipoRegistroVerifactu,
)

from app.schemas.pagination import PaginationParams
from app.schemas.paginated_response import PaginatedResponse
from app.schemas.factura import FacturaResponse
from app.schemas.factura_filtro import FacturaFiltro

class FacturaService:

    PREFIJOS_POR_TIPO = {
        TipoFactura.REPARACION.value: "REP",
        TipoFactura.RECAMBIO.value: "REC",
        TipoFactura.VENTAS_COMISIONES.value: "V/C",
        TipoFactura.PRESUPUESTO.value: "PRES",
        TipoFactura.GARANTIA.value: "GAR",
    }

    @staticmethod
    def get_all(
        db: Session
    ):
        return FacturaRepository.get_all(db)

    @staticmethod
    def get_by_id(
        db: Session,
        factura_id: int
    ):

        factura = FacturaRepository.get_by_id(
            db,
            factura_id
        )

        if factura is None:
            raise ValueError(
                "Factura no encontrada"
            )

        return factura

    @staticmethod
    def _generar_numero(
        db: Session,
        tipo_factura: str,
    ):
        """Genera una numeración única por tipo de factura y año."""
        try:
            prefijo = FacturaService.PREFIJOS_POR_TIPO[tipo_factura]
        except KeyError as exc:
            raise ValueError("Tipo de factura no válido para numeración.") from exc

        anio = datetime.now().year
        prefijo_numero = f"{prefijo}-{anio}-"

        # Evita que dos usuarios obtengan el mismo número al facturar a la vez.
        clave_bloqueo = zlib.crc32(
            f"motordesk-factura-{anio}-{tipo_factura}".encode("utf-8")
        ) & 0x7FFFFFFF
        db.execute(
            text("SELECT pg_advisory_xact_lock(:clave)"),
            {"clave": clave_bloqueo},
        )

        numeros = (
            db.query(Factura.numero)
            .filter(
                Factura.tipo_factura == tipo_factura,
                Factura.numero.like(f"{prefijo_numero}%"),
            )
            .all()
        )

        ultima_secuencia = 0
        for (numero,) in numeros:
            try:
                ultima_secuencia = max(
                    ultima_secuencia,
                    int(numero.rsplit("-", 1)[1]),
                )
            except (AttributeError, IndexError, ValueError):
                continue

        return f"{prefijo_numero}{ultima_secuencia + 1:06d}"

    @staticmethod
    def create(
        db: Session,
        factura: FacturaCreate,
        permitir_factura_garantia: bool = False,
    ):

        cliente = ClienteRepository.get_by_id(
            db,
            factura.cliente_id
        )

        if cliente is None:
            raise ValueError(
                "El cliente no existe"
            )

        if factura.vehiculo_id is not None:

            vehiculo = VehiculoRepository.get_by_id(
                db,
                factura.vehiculo_id
            )

            if vehiculo is None:
                raise ValueError(
                    "El vehículo no existe"
                )

        if factura.orden_id is not None:

            orden = OrdenReparacionRepository.get_by_id(
                db,
                factura.orden_id
            )

            if orden is None:
                raise ValueError(
                    "La orden de reparación no existe"
                )

            if orden.tipo == "GA" and not permitir_factura_garantia:
                raise ValueError(
                    "Las facturas de garantía deben generarse desde sus conceptos no cubiertos"
                )

        if factura.orden_id is not None:
            factura_existente = FacturaRepository.get_by_orden(
                db,
                factura.orden_id
            )

            if factura_existente is not None:
                raise ValueError(
                    f"La orden ya tiene asociada la factura {factura_existente.numero}"
                )

        configuracion_facturacion = ConfiguracionFacturacionService.obtener(db)
        es_prueba = configuracion_facturacion.modo_facturacion == "PRUEBAS"
        numero = FacturaService._generar_numero(
            db,
            factura.tipo_factura,
        )

        datos = factura.model_dump()

        datos["numero"] = numero
        datos["estado"] = EstadoFactura.BORRADOR.value
        datos["es_prueba"] = es_prueba
        datos["modo_facturacion"] = configuracion_facturacion.modo_facturacion

        nueva_factura = FacturaRepository.create(
            db,
            datos
        )

        return nueva_factura

    @staticmethod
    def update(
        db: Session,
        factura_id: int,
        datos: FacturaUpdate
    ):

        factura = FacturaRepository.get_by_id(
            db,
            factura_id
        )

        if factura is None:
            raise ValueError(
                "Factura no encontrada"
            )

        if factura.estado != EstadoFactura.BORRADOR.value:
            raise ValueError(
                "Solo se puede modificar una factura en borrador"
            )

        datos_actualizados = datos.model_dump(
            exclude_unset=True
        )

        if "cliente_id" in datos_actualizados:

            cliente = ClienteRepository.get_by_id(
                db,
                datos_actualizados["cliente_id"]
            )

            if cliente is None:
                raise ValueError(
                    "El cliente no existe"
                )

        if (
            "vehiculo_id" in datos_actualizados
            and datos_actualizados["vehiculo_id"] is not None
        ):

            vehiculo = VehiculoRepository.get_by_id(
                db,
                datos_actualizados["vehiculo_id"]
            )

            if vehiculo is None:
                raise ValueError(
                    "El vehículo no existe"
                )

        if (
            "orden_id" in datos_actualizados
            and datos_actualizados["orden_id"] is not None
        ):

            orden = OrdenReparacionRepository.get_by_id(
                db,
                datos_actualizados["orden_id"]
            )

            if orden is None:
                raise ValueError(
                    "La orden no existe"
                )

        return FacturaRepository.update(
            db,
            factura,
            datos_actualizados
        )

    @staticmethod
    def delete(
        db: Session,
        factura_id: int
    ):

        factura = FacturaRepository.get_by_id(
            db,
            factura_id
        )

        if factura is None:
            raise ValueError(
                "Factura no encontrada"
            )

        # Las facturas de pruebas no forman parte de la cadena fiscal ni se
        # comunican a la AEAT. Permitimos eliminarlas para que el entorno de
        # prueba se pueda limpiar sin abrir una rectificativa ficticia.
        es_factura_prueba = (
            factura.es_prueba
            or factura.modo_facturacion == "PRUEBAS"
        )

        if (
            factura.estado != EstadoFactura.BORRADOR.value
            and not es_factura_prueba
        ):
            raise ValueError(
                "Solo se pueden eliminar facturas en borrador. "
                "Las facturas emitidas reales deben anularse."
            )

        FacturaRepository.delete(
            db,
            factura
        )

    @staticmethod
    def emitir(
        db: Session,
        factura_id: int,
        empresa_id: int,
    ):
        """Emite una factura válida y genera su registro VERI*FACTU si corresponde."""


        factura = FacturaRepository.get_by_id(
            db,
            factura_id
        )

        if factura is None:
            raise ValueError(
                "Factura no encontrada"
            )

        if factura.estado != EstadoFactura.BORRADOR.value:
            raise ValueError(
                "Solo se puede emitir una factura en borrador"
            )

        lineas = FacturaLineaRepository.get_by_factura(db, factura.id)
        if not lineas:
            raise ValueError("No se puede emitir una factura sin líneas")

        if Decimal(factura.total or 0) <= Decimal("0.00"):
            raise ValueError("No se puede emitir una factura con total igual o menor que cero")

        destino_facturae = FacturaeService.obtener_destino(db, factura.id)
        if destino_facturae is not None:
            FacturaeXmlService.validar_destino(destino_facturae)

        orden = None
        if factura.orden_id is not None:
            orden = OrdenReparacionRepository.get_by_id(
                db,
                factura.orden_id
            )

            if orden is None:
                raise ValueError(
                    "La orden asociada a la factura no existe"
                )

        configuracion_facturacion = ConfiguracionFacturacionService.obtener(db)
        modo_factura = factura.modo_facturacion or configuracion_facturacion.modo_facturacion
        es_prueba = factura.es_prueba or modo_factura == "PRUEBAS"

        factura.es_prueba = es_prueba
        factura.modo_facturacion = "PRUEBAS" if es_prueba else "VERIFACTU"
        factura.estado = EstadoFactura.EMITIDA.value
        factura.fecha_emision = datetime.utcnow()

        # Una GA conserva su ciclo de vida propio; emitir su factura no la
        # transforma en una orden normal facturada.
        if orden is not None and orden.tipo != "GA":
            orden.estado = EstadoReparacion.FACTURADA.value

        # Una factura comercial y su registro de alta se guardan juntos.
        # Las facturas de prueba nunca generan XML ni llamadas a la AEAT.
        if not es_prueba:
            if configuracion_facturacion.modo_facturacion != "VERIFACTU":
                db.rollback()
                raise ValueError("El modo de facturación actual no permite emitir una factura VERI*FACTU")
            if not configuracion_facturacion.permitir_envio_aeat:
                db.rollback()
                raise ValueError("El envío a AEAT no está habilitado para la facturación VERI*FACTU")
            VerifactuAeatService.validar_configuracion_produccion(
                db,
                empresa_id,
            )
            db.flush()
            registro = VerifactuService.generar_registro_alta(
                db,
                factura.id,
                commit=False,
            )
        else:
            registro = None

        db.commit()
        db.refresh(factura)

        # El envío se intenta inmediatamente una vez persistido el registro.
        # Si falla queda trazado en estado ERROR para reintento; no se pierde la factura.
        if destino_facturae is not None:
            empresa = EmpresaRepository.get_by_id(db, empresa_id)
            if empresa is None:
                raise ValueError("Empresa no encontrada al generar Facturae")
            FacturaeXmlService.generar(factura, empresa, destino_facturae)

        if registro is not None:
            try:
                VerifactuAeatService.enviar_registro_produccion(
                    db,
                    registro.id,
                    empresa_id,
                )
            except ValueError:
                pass

        return factura

    @staticmethod
    def anular(
        db: Session,
        factura_id: int
    ):
        """Anula una factura conservando la trazabilidad fiscal exigida por su modo."""


        factura = FacturaRepository.get_by_id(
            db,
            factura_id
        )

        if factura is None:
            raise ValueError(
                "Factura no encontrada"
            )

        if factura.estado == EstadoFactura.ANULADA.value:
            raise ValueError("La factura ya está anulada")

        registros = RegistroVerifactuRepository.get_by_factura(db, factura.id)
        alta_generada = next(
            (
                registro for registro in registros
                if registro.tipo_registro == TipoRegistroVerifactu.ALTA.value
            ),
            None,
        )
        if alta_generada:
            if alta_generada.estado in (
                EstadoRegistroVerifactu.ACEPTADO.value,
                EstadoRegistroVerifactu.ACEPTADO_CON_ERRORES.value,
            ):
                mensaje = (
                    "La factura tiene un alta VERI*FACTU aceptada. "
                    "Genera y envía su registro de anulación antes de anularla."
                )
            else:
                mensaje = (
                    "La factura ya tiene un registro VERI*FACTU de alta generado. "
                    "No puede anularse directamente mientras ese registro exista."
                )
            raise ValueError(
                mensaje
            )

        factura.estado = EstadoFactura.ANULADA.value

        orden = OrdenReparacionRepository.get_by_id(db, factura.orden_id)
        if (
            orden is not None
            and orden.tipo != "GA"
            and orden.estado == EstadoReparacion.FACTURADA.value
        ):
            orden.estado = EstadoReparacion.CERRADA.value

        db.commit()
        db.refresh(factura)

        return factura

    @staticmethod
    def enviar_email(
        db: Session,
        factura_id: int
    ):

        factura = FacturaRepository.get_by_id(db, factura_id)

        if factura is None:
            raise ValueError("Factura no encontrada")

        if factura.estado != EstadoFactura.EMITIDA.value:
            raise ValueError("Solo se pueden enviar facturas emitidas")

        cliente = factura.cliente
        if cliente is None:
            raise ValueError("La factura no tiene un cliente asociado")

        if not cliente.email:
            raise ValueError(
                "El cliente no tiene un correo electronico registrado"
            )

        empresa = EmpresaRepository.get_first(db)
        pdf_buffer = PdfService.generar_factura(
            factura,
            empresa,
            ConfiguracionTallerService.obtener(db),
            ConfiguracionDocumentosService.obtener(db),
        )
        nombre_cliente = ", ".join(
            filter(None, [cliente.apellidos, cliente.nombre])
        )

        EmailService.enviar_documento_configurado(
            db=db,
            empresa_id=empresa.id,
            destinatario=cliente.email,
            asunto=f"Factura {factura.numero}",
            texto=(
                f"Hola {nombre_cliente},\n\nAdjuntamos la factura "
                f"{factura.numero} en formato PDF.\n\nUn saludo."
            ),
            pdf_buffer=pdf_buffer,
            nombre_archivo=f"factura_{factura.numero}.pdf",
        )

        return {
            "message": "Factura enviada por email correctamente",
            "email": cliente.email
        }

    @staticmethod
    def enviar_whatsapp(
        db: Session,
        factura_id: int,
        empresa_id: int,
    ):
        factura = FacturaRepository.get_by_id(db, factura_id)

        if factura is None:
            raise ValueError("Factura no encontrada")

        if factura.estado != EstadoFactura.EMITIDA.value:
            raise ValueError("Solo se pueden enviar facturas emitidas")

        cliente = factura.cliente
        if cliente is None:
            raise ValueError("La factura no tiene un cliente asociado")

        if not cliente.telefono:
            raise ValueError("El cliente no tiene un teléfono registrado")

        empresa = EmpresaRepository.get_by_id(db, empresa_id)
        if empresa is None:
            raise ValueError("No hay datos del taller configurados")

        # Las credenciales de Meta se resuelven desde la configuración cifrada
        # de la empresa; Empresa solo aporta datos para el documento PDF.
        whatsapp_config = WhatsAppConfigService.obtener(db, empresa_id)
        if whatsapp_config is None:
            raise ValueError("WhatsApp no está configurado para esta empresa")

        if not whatsapp_config.activo:
            raise ValueError("WhatsApp no está conectado para esta empresa")

        access_token = WhatsAppConfigService.obtener_token(db, empresa_id)

        if not whatsapp_config.activo:
            raise ValueError("WhatsApp no está conectado para esta empresa")

        if not access_token:
            raise ValueError(
                "La empresa no tiene un access token de WhatsApp configurado"
            )

        if not whatsapp_config.phone_number_id:
            raise ValueError(
                "La empresa no tiene un Phone Number ID de WhatsApp configurado"
            )

        nombre_cliente = ", ".join(
            filter(None, [cliente.apellidos, cliente.nombre])
        ) or "Cliente"
        vehiculo_factura = factura.vehiculo
        nombre_vehiculo = " ".join(
            filter(
                None,
                [
                    getattr(vehiculo_factura, "marca", None),
                    getattr(vehiculo_factura, "modelo", None),
                ],
            )
        ) or "Vehículo no asociado"
        matricula = (
            getattr(vehiculo_factura, "matricula", None)
            or "No disponible"
        )
        nombre_taller = (
            empresa.nombre_comercial
            or empresa.nombre
            or "MotorDesk"
        )
        pdf_buffer = PdfService.generar_factura(
            factura,
            empresa,
            ConfiguracionTallerService.obtener(db),
            ConfiguracionDocumentosService.obtener(db),
        )

        resultado = WhatsAppService.enviar_factura(
            telefono=cliente.telefono,
            nombre_cliente=nombre_cliente,
            numero_factura=factura.numero,
            vehiculo=nombre_vehiculo,
            matricula=matricula,
            # La plantilla ya incluye el símbolo €, por lo que se envía
            # únicamente el importe numérico como parámetro {{5}}.
            total_factura=f"{factura.total:.2f}",
            nombre_taller=nombre_taller,
            pdf_buffer=pdf_buffer,
            access_token=access_token,
            phone_number_id=whatsapp_config.phone_number_id
        )

        return {
            "message": "Factura enviada por WhatsApp correctamente",
            "telefono": cliente.telefono,
            "whatsapp": resultado
        }

    @staticmethod
    def _recalcular_totales_sin_commit(
        db: Session,
        factura: Factura,
    ) -> None:
        """Actualiza importes sin cerrar la transacción actual."""
        lineas = FacturaLineaRepository.get_by_factura(db, factura.id)
        subtotal = sum((linea.subtotal for linea in lineas), Decimal("0.00"))
        descuento = subtotal * factura.descuento_porcentaje / Decimal("100")
        base_imponible = subtotal - descuento

        # Una factura puede combinar ventas sujetas y comisiones exentas. El
        # descuento global se reparte proporcionalmente entre las líneas antes
        # de calcular la cuota de cada tipo de IVA.
        cuota_iva = Decimal("0.00")
        if subtotal:
            for linea in lineas:
                base_linea = Decimal(linea.subtotal) - (
                    descuento * Decimal(linea.subtotal) / subtotal
                )
                cuota_iva += base_linea * Decimal(linea.iva) / Decimal("100")

        factura.subtotal = subtotal
        factura.base_imponible = base_imponible
        factura.cuota_iva = cuota_iva
        factura.total = base_imponible + cuota_iva

    @staticmethod
    def recalcular_totales(
        db: Session,
        factura_id: int
    ):

        factura = FacturaRepository.get_by_id(
            db,
            factura_id
        )

        if factura is None:
            raise ValueError(
                "Factura no encontrada"
            )

        FacturaService._recalcular_totales_sin_commit(db, factura)

        db.commit()
        db.refresh(factura)

        return factura

    @staticmethod
    def _crear_desde_albaran_venta_legacy(
        db: Session,
        albaran_venta_id: int,
    ):
        """Convierte una venta de almacén confirmada en factura de recambio.

        El albarán ya descontó el stock al confirmarse. Este paso solo crea el
        documento fiscal en borrador y conserva las cantidades, precios y
        descuentos que se guardaron en el momento de la venta.
        """
        albaran = (
            db.query(AlbaranVenta)
            .filter(AlbaranVenta.id == albaran_venta_id)
            .first()
        )
        if albaran is None:
            raise ValueError("Albarán de venta no encontrado")
        if albaran.estado != "CONFIRMADO":
            raise ValueError("Solo se pueden facturar albaranes de venta confirmados")

        factura_existente = FacturaRepository.get_by_albaran_venta(
            db,
            albaran_venta_id,
        )
        if factura_existente is not None:
            raise ValueError(
                f"El albarán ya está facturado con la factura {factura_existente.numero}"
            )

        configuracion = ConfiguracionFacturacionService.obtener(db)
        es_prueba = configuracion.modo_facturacion == "PRUEBAS"
        numero = FacturaService._generar_numero(
            db,
            TipoFactura.RECAMBIO.value,
        )

        try:
            factura = Factura(
                numero=numero,
                tipo_documento=TipoDocumento.FACTURA.value,
                tipo_factura=TipoFactura.RECAMBIO.value,
                cliente_id=albaran.cliente_id,
                orden_id=None,
                albaran_venta_id=albaran.id,
                descuento_porcentaje=Decimal("0"),
                iva=Decimal("21"),
                observaciones=albaran.observaciones,
                estado=EstadoFactura.BORRADOR.value,
                es_prueba=es_prueba,
                modo_facturacion=configuracion.modo_facturacion,
            )
            db.add(factura)
            db.flush()

            for linea in albaran.lineas:
                subtotal = (
                    Decimal(linea.cantidad)
                    * Decimal(linea.precio_unitario)
                    * (
                        Decimal("1")
                        - Decimal(linea.descuento_porcentaje) / Decimal("100")
                    )
                )
                db.add(
                    FacturaLinea(
                        factura_id=factura.id,
                        origen="ALBARAN_VENTA",
                        descripcion=f"{linea.referencia} - {linea.descripcion}",
                        cantidad=linea.cantidad,
                        precio_unitario=linea.precio_unitario,
                        descuento_porcentaje=linea.descuento_porcentaje,
                        subtotal=subtotal,
                        iva=factura.iva,
                        total=subtotal,
                    )
                )

            db.flush()
            FacturaService.recalcular_totales(db, factura.id)
            return FacturaRepository.get_by_id(db, factura.id)
        except Exception:
            db.rollback()
            raise

    @staticmethod
    def crear_desde_albaran_venta(
        db: Session,
        albaran_venta_id: int,
    ):
        """Crea una factura de recambio a partir de un único albarán."""
        return FacturaService.crear_desde_albaranes_venta(
            db,
            [albaran_venta_id],
        )

    @staticmethod
    def crear_desde_albaranes_venta(
        db: Session,
        albaranes_venta_ids: list[int],
    ):
        """Agrupa albaranes confirmados de un cliente en una factura borrador.

        El stock ya se descontó al confirmar cada albarán. Este proceso solo
        copia las líneas a la factura y conserva su origen para el PDF.
        """
        ids = list(dict.fromkeys(albaranes_venta_ids))
        if not ids:
            raise ValueError("Selecciona al menos un albarán de venta")
        if len(ids) != len(albaranes_venta_ids):
            raise ValueError("No se puede incluir el mismo albarán más de una vez")

        albaranes = (
            db.query(AlbaranVenta)
            .options(selectinload(AlbaranVenta.lineas))
            .filter(AlbaranVenta.id.in_(ids))
            .order_by(AlbaranVenta.fecha.asc(), AlbaranVenta.id.asc())
            .all()
        )
        if len(albaranes) != len(ids):
            raise ValueError("Uno de los albaranes de venta no existe")

        clientes_ids = {albaran.cliente_id for albaran in albaranes}
        if len(clientes_ids) != 1:
            raise ValueError(
                "Solo se pueden agrupar albaranes del mismo cliente en una factura"
            )

        for albaran in albaranes:
            if albaran.estado != "CONFIRMADO":
                raise ValueError(
                    f"El albarán {albaran.numero} debe estar confirmado antes de facturarlo"
                )
            factura_existente = FacturaRepository.get_by_albaran_venta(db, albaran.id)
            if factura_existente is not None:
                raise ValueError(
                    f"El albarán {albaran.numero} ya está facturado con la factura "
                    f"{factura_existente.numero}"
                )

        configuracion = ConfiguracionFacturacionService.obtener(db)
        es_prueba = configuracion.modo_facturacion == "PRUEBAS"
        numero = FacturaService._generar_numero(
            db,
            TipoFactura.RECAMBIO.value,
        )
        observaciones = [
            albaran.observaciones.strip()
            for albaran in albaranes
            if albaran.observaciones and albaran.observaciones.strip()
        ]

        try:
            factura = Factura(
                numero=numero,
                tipo_documento=TipoDocumento.FACTURA.value,
                tipo_factura=TipoFactura.RECAMBIO.value,
                cliente_id=albaranes[0].cliente_id,
                orden_id=None,
                descuento_porcentaje=Decimal("0"),
                iva=Decimal("21"),
                observaciones="\n".join(observaciones) or None,
                estado=EstadoFactura.BORRADOR.value,
                es_prueba=es_prueba,
                modo_facturacion=configuracion.modo_facturacion,
            )
            db.add(factura)
            db.flush()

            for albaran in albaranes:
                db.add(
                    FacturaAlbaranVenta(
                        factura_id=factura.id,
                        albaran_venta_id=albaran.id,
                    )
                )
                for linea in albaran.lineas:
                    subtotal = (
                        Decimal(linea.cantidad)
                        * Decimal(linea.precio_unitario)
                        * (
                            Decimal("1")
                            - Decimal(linea.descuento_porcentaje) / Decimal("100")
                        )
                    )
                    db.add(
                        FacturaLinea(
                            factura_id=factura.id,
                            albaran_venta_id=albaran.id,
                            origen="ALBARAN_VENTA",
                            descripcion=f"{linea.referencia} - {linea.descripcion}",
                            cantidad=linea.cantidad,
                            precio_unitario=linea.precio_unitario,
                            descuento_porcentaje=linea.descuento_porcentaje,
                            subtotal=subtotal,
                            iva=factura.iva,
                            total=subtotal,
                        )
                    )

            db.flush()
            FacturaService._recalcular_totales_sin_commit(db, factura)
            db.commit()
            return FacturaRepository.get_by_id(db, factura.id)
        except IntegrityError as error:
            db.rollback()
            raise ValueError(
                "Uno de los albaranes seleccionados ya ha sido facturado"
            ) from error
        except Exception:
            db.rollback()
            raise

    @staticmethod
    def crear_desde_orden(
        db: Session,
        orden_id: int,
        tipo_documento: str,
        cliente_id: int | None = None,
    ):

        orden = OrdenReparacionRepository.get_by_id(
            db,
            orden_id
        )

        if orden is None:
            raise ValueError(
                "Orden de reparación no encontrada"
            )

        if orden.tipo == "GA":
            raise ValueError(
                "Las facturas de garantía se generan desde la garantía resuelta"
            )

        factura_existente = FacturaRepository.get_by_orden(
            db,
            orden_id
        )

        if factura_existente is not None:
            raise ValueError(
                f"La orden ya tiene asociada la factura {factura_existente.numero}"
            )

        # El destinatario fiscal puede ser distinto del propietario del
        # vehículo: por ejemplo, una aseguradora o una empresa de renting.
        # Si no se indica, conservamos el comportamiento histórico y usamos
        # al cliente vinculado al vehículo de la orden.
        destinatario_id = (
            cliente_id
            if cliente_id is not None
            else orden.vehiculo.cliente_id
        )

        factura = FacturaService.create(
            db,
            FacturaCreate(
                tipo_documento=tipo_documento,
                tipo_factura=TipoFactura.REPARACION.value,
                cliente_id=destinatario_id,
                vehiculo_id=orden.vehiculo_id,
                orden_id=orden.id,
                descuento_porcentaje=Decimal("0"),
                iva=Decimal("21"),
                observaciones=orden.observaciones
            )
        )
        
        FacturaService._copiar_lineas_desde_orden(
            db,
            factura,
            orden,
            solo_no_cubiertas=orden.tipo == "GA",
        )

        FacturaService.recalcular_totales(
            db,
            factura.id
        )

        db.refresh(factura)

        return factura

    @staticmethod
    def crear_desde_ordenes(db: Session, ordenes_ids: list[int], tipo_documento: str, cliente_id: int):
        ids = list(dict.fromkeys(ordenes_ids))
        if len(ids) < 2 or len(ids) != len(ordenes_ids):
            raise ValueError("Selecciona dos o más órdenes distintas")
        ordenes = [OrdenReparacionRepository.get_by_id(db, id_) for id_ in ids]
        if any(o is None or o.tipo != "OR" or o.estado != EstadoReparacion.CERRADA.value for o in ordenes):
            raise ValueError("Solo se pueden agrupar órdenes de reparación cerradas")
        if ClienteRepository.get_by_id(db, cliente_id) is None:
            raise ValueError("El destinatario no existe")
        for orden in ordenes:
            if FacturaRepository.get_by_orden(db, orden.id):
                raise ValueError(f"La orden {orden.numero} ya está facturada")
        config = ConfiguracionFacturacionService.obtener(db)
        try:
            factura = Factura(numero=FacturaService._generar_numero(db, TipoFactura.REPARACION.value), tipo_documento=tipo_documento, tipo_factura=TipoFactura.REPARACION.value, cliente_id=cliente_id, vehiculo_id=ordenes[0].vehiculo_id, orden_id=ordenes[0].id, descuento_porcentaje=Decimal("0"), iva=Decimal("21"), estado=EstadoFactura.BORRADOR.value, es_prueba=config.modo_facturacion == "PRUEBAS", modo_facturacion=config.modo_facturacion)
            db.add(factura); db.flush()
            for orden in ordenes:
                db.add(FacturaOrdenReparacion(factura_id=factura.id, orden_id=orden.id))
                FacturaService._copiar_lineas_desde_orden(db, factura, orden)
            db.flush(); FacturaService.recalcular_totales(db, factura.id)
            return FacturaRepository.get_by_id(db, factura.id)
        except Exception:
            db.rollback(); raise

    @staticmethod
    def crear_desde_garantia(
        db: Session,
        garantia_id: int,
    ):
        """Crea un borrador con los únicos conceptos no cubiertos de una GA."""
        garantia = OrdenReparacionRepository.get_by_id(db, garantia_id)

        if garantia is None:
            raise ValueError("Garantía no encontrada")
        if garantia.tipo != "GA":
            raise ValueError("La orden indicada no es una garantía")
        if garantia.estado != EstadoReparacion.GARANTIA_RESUELTA.value:
            raise ValueError(
                "Solo se puede generar una factura cuando la garantía está resuelta"
            )

        factura_existente = FacturaRepository.get_by_orden(db, garantia.id)
        if factura_existente is not None:
            raise ValueError(
                f"La garantía ya tiene asociada la factura {factura_existente.numero}"
            )

        if Decimal(garantia.trabajos_no_cubiertos or 0) <= Decimal("0"):
            raise ValueError(
                "La garantía no tiene conceptos no cubiertos que facturar"
            )

        factura = FacturaService.create(
            db,
            FacturaCreate(
                tipo_documento=TipoDocumento.FACTURA.value,
                tipo_factura=TipoFactura.GARANTIA.value,
                cliente_id=garantia.vehiculo.cliente_id,
                vehiculo_id=garantia.vehiculo_id,
                orden_id=garantia.id,
                descuento_porcentaje=Decimal("0"),
                iva=Decimal("21"),
                observaciones=(
                    "Factura de conceptos no cubiertos de la garantía "
                    f"{garantia.numero}."
                ),
            ),
            permitir_factura_garantia=True,
        )

        FacturaService._copiar_lineas_desde_orden(
            db,
            factura,
            garantia,
            solo_no_cubiertas=True,
        )
        FacturaService.recalcular_totales(db, factura.id)
        db.refresh(factura)

        return factura
    
    @staticmethod
    def actualizar_desde_orden(
        db: Session,
        factura_id: int
    ):

        factura = FacturaRepository.get_by_id(
            db,
            factura_id
        )

        if factura is None:
            raise ValueError(
                "Factura no encontrada"
            )

        if factura.estado != EstadoFactura.BORRADOR.value:
            raise ValueError(
                "Solo se puede actualizar una factura en borrador"
            )

        if factura.orden_id is None:
            raise ValueError(
                "La factura no está asociada a una orden"
            )

        orden = OrdenReparacionRepository.get_by_id(
            db,
            factura.orden_id
        )

        if orden is None:
            raise ValueError(
                "La orden asociada a la factura ya no existe"
            )

        # Actualizar datos generales. El destinatario de facturación pertenece
        # a la factura y no se reemplaza al sincronizar una orden: puede ser
        # una empresa, aseguradora u otro tercero distinto del propietario.
        factura.vehiculo_id = orden.vehiculo_id
        factura.observaciones = (
            f"Factura de conceptos no cubiertos de la garantía {orden.numero}."
            if orden.tipo == "GA"
            else orden.observaciones
        )

        db.commit()
        db.refresh(factura)

        # Eliminar únicamente las líneas provenientes de la orden
        FacturaLineaRepository.delete_by_origen(
            db,
            factura.id,
            [
                "MANO_OBRA",
                "PIEZA"
            ]
        )

        # En una GA solo se sincronizan los conceptos no cubiertos, incluso
        # si el usuario actualiza el borrador desde la orden.
        FacturaService._copiar_lineas_desde_orden(
            db,
            factura,
            orden,
            solo_no_cubiertas=orden.tipo == "GA",
        )

        FacturaService.recalcular_totales(
            db,
            factura.id
        )

        db.refresh(factura)

        return factura
    
    @staticmethod
    def generar_pdf(
            db: Session,
            factura_id: int
        ):

            factura = FacturaRepository.get_by_id(
                db,
                factura_id
            )

            if factura is None:
                raise ValueError(
                    "Factura no encontrada"
                )

            empresa = EmpresaRepository.get_first(db)

            return PdfService.generar_factura(
                factura,
                empresa,
                ConfiguracionTallerService.obtener(db),
                ConfiguracionDocumentosService.obtener(db),
            )
            
    @staticmethod
    def buscar(
        db: Session,
        texto: str
    ):
        return FacturaRepository.buscar(
            db,
            texto
        )
        
    @staticmethod
    def filtrar(
        db: Session,
        filtros
    ):
        return FacturaRepository.filtrar(
            db,
            filtros
        )
        
    @staticmethod
    def get_paginated(
        db: Session,
        pagination: PaginationParams,
        filtros: FacturaFiltro | None = None,
    ):

        items, total = FacturaRepository.get_paginated(
            db,
            pagination,
            filtros,
        )

        return PaginatedResponse[FacturaResponse].create(
            items=items,
            total=total,
            page=pagination.page,
            size=pagination.size
        )
        
    @staticmethod
    def get_by_orden(
        db: Session,
        orden_id: int
    ):

        factura = FacturaRepository.get_by_orden(
            db,
            orden_id
        )

        if factura is None:
            raise ValueError(
                "La orden no tiene una factura asociada"
            )

        return factura

    @staticmethod
    def _copiar_lineas_desde_orden(
        db: Session,
        factura,
        orden,
        solo_no_cubiertas: bool = False,
    ):

        # Se toma una instantánea de los conceptos de la orden. De esta forma
        # la factura conserva el precio, el descuento y el IVA aplicados en
        # el momento de crearla o sincronizarla.
        iva = Decimal("21")

        # Copiar mano de obra
        for linea in orden.mano_obra:

            if solo_no_cubiertas and linea.cubierto_garantia:
                continue

            importe_bruto = (
                linea.horas *
                linea.precio_hora
            )

            descuento_porcentaje = linea.descuento_porcentaje
            subtotal = importe_bruto * (
                Decimal("1") - descuento_porcentaje / Decimal("100")
            )
            total = subtotal

            FacturaLineaRepository.create(
                db,
                {
                    "factura_id": factura.id,
                    "origen": "MANO_OBRA",
                    "descripcion": linea.concepto,
                    "cantidad": linea.horas,
                    "precio_unitario": linea.precio_hora,
                    "descuento_porcentaje": descuento_porcentaje,
                    "subtotal": subtotal,
                    "iva": iva,
                    "total": total
                }
            )

        # Copiar piezas
        for pieza in orden.piezas:

            if solo_no_cubiertas and pieza.cubierto_garantia:
                continue

            importe_bruto = (
                pieza.cantidad *
                pieza.precio_unitario
            )

            descuento_porcentaje = pieza.descuento_porcentaje
            subtotal = importe_bruto * (
                Decimal("1") - descuento_porcentaje / Decimal("100")
            )
            total = subtotal

            descripcion = pieza.descripcion
            if pieza.referencia:
                descripcion = f"{descripcion} ({pieza.referencia})"

            FacturaLineaRepository.create(
                db,
                {
                    "factura_id": factura.id,
                    "origen": "PIEZA",
                    "descripcion": descripcion,
                    "cantidad": pieza.cantidad,
                    "precio_unitario": pieza.precio_unitario,
                    "descuento_porcentaje": descuento_porcentaje,
                    "subtotal": subtotal,
                    "iva": iva,
                    "total": total
                }
            )
