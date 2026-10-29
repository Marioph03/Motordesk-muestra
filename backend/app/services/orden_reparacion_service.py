"""Flujo de órdenes de reparación, importes, estados y numeración interna."""

from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from decimal import Decimal

from app.repositories.orden_reparacion_repository import OrdenReparacionRepository
from app.repositories.vehiculo_repository import VehiculoRepository
from app.repositories.usuario_repository import UsuarioRepository
from app.repositories.factura_repository import FacturaRepository
from app.models.orden_reparacion import EstadoReparacion
from app.models.factura import EstadoFactura
from app.schemas.orden_reparacion import OrdenReparacionCreate
from app.repositories.mano_obra_repository import ManoObraRepository
from app.schemas.mano_obra import (
    ManoObraCreate,
    ManoObraUpdate
)
from app.repositories.pieza_repository import PiezaRepository
from app.schemas.orden_reparacion import OrdenReparacionUpdate
from app.repositories.empresa_repository import EmpresaRepository
from app.services.pdf_service import PdfService
from app.services.configuracion_taller_service import ConfiguracionTallerService
from app.services.configuracion_documentos_service import ConfiguracionDocumentosService
from app.services.documentos_context_service import DocumentosContextService
from app.services.email_service import EmailService
from app.services.whatsapp_service import WhatsAppService
from app.services.whatsapp_config_service import WhatsAppConfigService
from app.services.ausencia_personal_service import AusenciaPersonalService
from app.services.stock_service import StockService

from app.schemas.orden_reparacion import OrdenReparacionResponse
from app.schemas.paginated_response import PaginatedResponse
from app.schemas.pagination import PaginationParams


class OrdenReparacionService:

    @staticmethod
    def _registrar_kilometros_entrada(
        vehiculo,
        kilometros_entrada: int | None,
        permitir_lectura_historica: bool = False,
    ) -> None:
        """Valida la lectura de la orden y conserva el máximo del vehículo."""
        if kilometros_entrada is None:
            return

        if kilometros_entrada < 0:
            raise ValueError("Los kilómetros de entrada no pueden ser negativos.")

        if (
            vehiculo.kilometros is not None
            and kilometros_entrada < vehiculo.kilometros
        ):
            if permitir_lectura_historica:
                return

            raise ValueError(
                "Los kilómetros de entrada no pueden ser inferiores "
                "al kilometraje actual del vehículo."
            )

        vehiculo.kilometros = kilometros_entrada

    @staticmethod
    def _obtener_usuarios_asignables(
        db: Session,
        usuarios_ids: list[int],
        fecha_inicio: datetime,
        fecha_fin: datetime,
    ):
        """Valida y devuelve el personal que puede asignarse a una orden."""

        usuarios = []

        # Evita duplicar asociaciones si el cliente repite un identificador.
        for usuario_id in dict.fromkeys(usuarios_ids):
            usuario = UsuarioRepository.get_by_id(db, usuario_id)

            if usuario is None:
                raise ValueError(
                    f"Usuario {usuario_id} no encontrado"
                )

            if not usuario.activo:
                raise ValueError(
                    f"{usuario.nombre} {usuario.apellidos} "
                    "está inactivo"
                )

            disponible = AusenciaPersonalService.usuario_disponible(
                db,
                usuario.id,
                fecha_inicio,
                fecha_fin,
            )

            if not disponible:
                raise ValueError(
                    f"{usuario.nombre} {usuario.apellidos} "
                    "no está disponible"
                )

            usuarios.append(usuario)

        return usuarios

    @staticmethod
    def get_all(db: Session):
        return OrdenReparacionRepository.get_all(db)

    @staticmethod
    def get_by_id(db: Session, orden_id: int):
        orden = OrdenReparacionRepository.get_by_id(db, orden_id)

        if orden is None:
            raise ValueError("Orden de reparación no encontrada")

        return orden

    @staticmethod
    def generar_numero(
        db: Session,
        tipo: str,
    ) -> str:
        """Genera el siguiente número sin confirmar la transacción actual."""

        anio = datetime.now().year
        ultima_orden = OrdenReparacionRepository.get_last_by_tipo(db, tipo)

        if ultima_orden is None:
            siguiente = 1
        else:
            try:
                siguiente = int(
                    ultima_orden.numero.split("-")[-1]
                ) + 1
            except (AttributeError, ValueError) as error:
                raise ValueError(
                    "No se puede calcular el siguiente número de orden."
                ) from error

        return f"{tipo}-{anio}-{siguiente:06d}"

    @staticmethod
    def create(
        db: Session,
        orden: OrdenReparacionCreate
    ):

        if orden.tipo not in {"OR", "PR", "GA"}:
            raise ValueError(
                "El tipo de documento debe ser OR, PR o GA"
            )

        vehiculo = VehiculoRepository.get_by_id(
            db,
            orden.vehiculo_id
        )

        if vehiculo is None:
            raise ValueError(
                "El vehículo no existe"
            )

        OrdenReparacionService._registrar_kilometros_entrada(
            vehiculo,
            orden.kilometros_entrada,
        )

        orden_origen_garantia = None

        if orden.orden_origen_garantia_id is not None:
            orden_origen_garantia = (
                OrdenReparacionRepository.get_by_id(
                    db,
                    orden.orden_origen_garantia_id
                )
            )

            if orden_origen_garantia is None:
                raise ValueError(
                    "La orden original de garantía no existe"
                )

            if (
                orden_origen_garantia.vehiculo_id
                != orden.vehiculo_id
            ):
                raise ValueError(
                    "La orden original de garantía debe pertenecer "
                    "al mismo vehículo"
                )

        factura_origen_garantia = None

        if orden.factura_origen_garantia_id is not None:
            factura_origen_garantia = FacturaRepository.get_by_id(
                db,
                orden.factura_origen_garantia_id
            )

            if factura_origen_garantia is None:
                raise ValueError(
                    "La factura original de garantía no existe"
                )

            if (
                factura_origen_garantia.vehiculo_id
                != orden.vehiculo_id
            ):
                raise ValueError(
                    "La factura original de garantía debe pertenecer "
                    "al mismo vehículo"
                )

        if (
            orden_origen_garantia is not None
            and factura_origen_garantia is not None
            and factura_origen_garantia.orden_id
            != orden_origen_garantia.id
        ):
            raise ValueError(
                "La factura original no pertenece a la "
                "orden original indicada"
            )

        if (
            orden.tipo == "GA"
            and orden.orden_origen_garantia_id is None
            and orden.factura_origen_garantia_id is None
        ):
            raise ValueError(
                "Una garantía debe estar vinculada a una "
                "orden o factura original"
            )

        numero = OrdenReparacionService.generar_numero(
            db,
            orden.tipo,
        )

        usuarios_ids = orden.usuarios_ids

        datos = orden.model_dump(
            exclude={"usuarios_ids"}
        )

        # A falta de una fecha prevista de salida,
        # comprobamos que el personal esté disponible.
        fecha_asignacion = datetime.now()

        usuarios = (
            OrdenReparacionService._obtener_usuarios_asignables(
                db,
                usuarios_ids,
                fecha_asignacion,
                fecha_asignacion + timedelta(minutes=1),
            )
        )

        if (
            orden.orden_origen_garantia_id is not None
            or orden.factura_origen_garantia_id is not None
        ):
            datos["garantia"] = True

        if orden.tipo == "PR":
            datos["estado"] = (
                EstadoReparacion.BORRADOR.value
            )
        elif orden.tipo == "GA":
            datos["estado"] = (
                EstadoReparacion.GARANTIA_ABIERTA.value
            )
        else:
            datos["estado"] = (
                EstadoReparacion.ABIERTA.value
            )

        datos["numero"] = numero

        try:
            nueva_orden = OrdenReparacionRepository.create(
                db,
                numero,
                datos,
                commit=False,
            )

            nueva_orden.usuarios_asignados = usuarios

            OrdenReparacionService.recalcular_totales(
                db,
                nueva_orden.id,
                commit=False,
            )

            db.commit()
            db.refresh(nueva_orden)

            return nueva_orden

        except Exception:
            db.rollback()
            raise

    @staticmethod
    def _cambiar_estado_garantia(
        db: Session,
        garantia_id: int,
        estado_destino: EstadoReparacion,
        datos_extra: dict | None = None
    ):
        garantia = OrdenReparacionRepository.get_by_id(
            db,
            garantia_id
        )

        if garantia is None:
            raise ValueError(
                "Garantía no encontrada"
            )

        if garantia.tipo != "GA":
            raise ValueError(
                "El documento indicado no es una garantía"
            )

        transiciones = {
            EstadoReparacion.GARANTIA_ABIERTA.value: {
                EstadoReparacion.GARANTIA_REVISION
            },
            EstadoReparacion.GARANTIA_REVISION.value: {
                EstadoReparacion.GARANTIA_APROBADA,
                EstadoReparacion.GARANTIA_RECHAZADA,
            },
            EstadoReparacion.GARANTIA_APROBADA.value: {
                EstadoReparacion.GARANTIA_REPARACION
            },
            EstadoReparacion.GARANTIA_REPARACION.value: {
                EstadoReparacion.GARANTIA_RESUELTA
            },
        }

        if estado_destino not in transiciones.get(
            garantia.estado,
            set()
        ):
            raise ValueError(
                f"No se permite pasar de '{garantia.estado}' a "
                f"'{estado_destino.value}' en una garantía"
            )

        datos_actualizados = {
            "estado": estado_destino.value
        }

        if datos_extra:
            datos_actualizados.update(datos_extra)

        return OrdenReparacionRepository.update(
            db,
            garantia,
            datos_actualizados
        )

    @staticmethod
    def iniciar_revision_garantia(
        db: Session,
        garantia_id: int
    ):
        return OrdenReparacionService._cambiar_estado_garantia(
            db,
            garantia_id,
            EstadoReparacion.GARANTIA_REVISION
        )

    @staticmethod
    def crear_garantia_desde_orden(
        db: Session,
        orden_id: int
    ):
        orden_origen = OrdenReparacionRepository.get_by_id(
            db,
            orden_id
        )

        if orden_origen is None:
            raise ValueError(
                "Orden original no encontrada"
            )

        if orden_origen.tipo != "OR":
            raise ValueError(
                "Solo se puede crear una garantía desde "
                "una orden de reparación"
            )

        if orden_origen.estado not in {
            EstadoReparacion.CERRADA.value,
            EstadoReparacion.FACTURADA.value,
        }:
            raise ValueError(
                "La orden original debe estar cerrada o facturada"
            )

        factura_origen = FacturaRepository.get_by_orden(
            db,
            orden_origen.id
        )

        garantia = OrdenReparacionCreate(
            tipo="GA",
            vehiculo_id=orden_origen.vehiculo_id,
            descripcion_averia="Motivo de garantía pendiente",
            garantia=True,
            garantia_meses=orden_origen.garantia_meses,
            orden_origen_garantia_id=orden_origen.id,
            factura_origen_garantia_id=(
                factura_origen.id
                if factura_origen
                else None
            ),
        )

        return OrdenReparacionService.create(
            db,
            garantia
        )

    @staticmethod
    def crear_garantia_desde_factura(
        db: Session,
        factura_id: int
    ):
        factura_origen = FacturaRepository.get_by_id(
            db,
            factura_id
        )

        if factura_origen is None:
            raise ValueError(
                "Factura original no encontrada"
            )

        if factura_origen.estado != EstadoFactura.EMITIDA.value:
            raise ValueError(
                "La factura original debe estar emitida"
            )

        if factura_origen.orden_id is None:
            raise ValueError(
                "La factura original no está asociada a una orden"
            )

        orden_origen = OrdenReparacionRepository.get_by_id(
            db,
            factura_origen.orden_id
        )

        if orden_origen is None:
            raise ValueError(
                "La orden original no encontrada"
            )

        garantia = OrdenReparacionCreate(
            tipo="GA",
            vehiculo_id=factura_origen.vehiculo_id,
            descripcion_averia="Motivo de garantía pendiente",
            garantia=True,
            garantia_meses=orden_origen.garantia_meses,
            orden_origen_garantia_id=orden_origen.id,
            factura_origen_garantia_id=factura_origen.id,
        )

        return OrdenReparacionService.create(
            db,
            garantia
        )

    @staticmethod
    def aprobar_garantia(
        db: Session,
        garantia_id: int
    ):
        return OrdenReparacionService._cambiar_estado_garantia(
            db,
            garantia_id,
            EstadoReparacion.GARANTIA_APROBADA
        )

    @staticmethod
    def rechazar_garantia(
        db: Session,
        garantia_id: int
    ):
        return OrdenReparacionService._cambiar_estado_garantia(
            db,
            garantia_id,
            EstadoReparacion.GARANTIA_RECHAZADA
        )

    @staticmethod
    def iniciar_reparacion_garantia(
        db: Session,
        garantia_id: int
    ):
        return OrdenReparacionService._cambiar_estado_garantia(
            db,
            garantia_id,
            EstadoReparacion.GARANTIA_REPARACION
        )

    @staticmethod
    def resolver_garantia(
        db: Session,
        garantia_id: int,
        resolucion: str
    ):
        resolucion = resolucion.strip()

        if not resolucion:
            raise ValueError(
                "Debes indicar la resolución de la garantía"
            )

        return OrdenReparacionService._cambiar_estado_garantia(
            db,
            garantia_id,
            EstadoReparacion.GARANTIA_RESUELTA,
            {
                "resolucion_garantia": resolucion,
                "fecha_resolucion_garantia": datetime.now(),
                "fecha_salida": datetime.now(),
            }
        )

    @staticmethod
    def cambiar_estado(
        db: Session,
        orden_id: int,
        estado: str
    ):
        orden = OrdenReparacionRepository.get_by_id(
            db,
            orden_id
        )

        if orden is None:
            raise ValueError(
                "Orden de reparación no encontrada"
            )

        if orden.tipo == "PR":
            raise ValueError(
                "El estado de un presupuesto solo puede cambiarse "
                "mediante sus acciones específicas"
            )

        if orden.tipo == "GA":
            raise ValueError(
                "El estado de una garantía solo puede cambiarse "
                "mediante sus acciones específicas"
            )

        estados_orden = {
            EstadoReparacion.ABIERTA.value,
            EstadoReparacion.EN_PROCESO.value,
            EstadoReparacion.CERRADA.value,
            EstadoReparacion.FACTURADA.value,
        }

        if estado not in estados_orden:
            raise ValueError(
                "El estado no es válido para una orden de reparación"
            )

        if orden.estado == EstadoReparacion.FACTURADA.value:
            raise ValueError(
                "No se puede cambiar el estado de una orden facturada"
            )

        datos = {
            "estado": estado
        }

        if estado == EstadoReparacion.FACTURADA.value:
            datos["fecha_salida"] = datetime.now()

        return OrdenReparacionRepository.update(
            db,
            orden,
            datos
        )

    @staticmethod
    def anular(db: Session, orden_id: int):
        """Anula una orden sin perder su número y devuelve las piezas al stock."""
        orden = OrdenReparacionRepository.get_by_id(db, orden_id)
        if orden is None:
            raise ValueError("Orden de reparación no encontrada")
        if orden.tipo != "OR":
            raise ValueError("Solo se pueden anular órdenes de reparación")
        if orden.estado == EstadoReparacion.FACTURADA.value:
            raise ValueError("No se puede anular una orden ya facturada")
        if orden.estado == EstadoReparacion.ANULADA.value:
            return orden

        try:
            for pieza in PiezaRepository.get_by_orden(db, orden.id):
                if pieza.articulo_stock_id is not None:
                    StockService.devolver_desde_orden(
                        db, pieza.articulo_stock_id, Decimal(pieza.cantidad), orden.id, commit=False
                    )
            orden.estado = EstadoReparacion.ANULADA.value
            db.commit()
            db.refresh(orden)
            return orden
        except Exception:
            db.rollback()
            raise

    @staticmethod
    def recalcular_totales(
        db: Session,
        orden_id: int,
        commit: bool = True,
    ):

        orden = OrdenReparacionRepository.get_by_id(
            db,
            orden_id
        )

        if orden is None:
            raise ValueError(
                "Orden de reparación no encontrada"
            )

        total_mano_obra = Decimal("0.00")
        total_piezas = Decimal("0.00")
        coste_asumido_taller = Decimal("0.00")
        trabajos_no_cubiertos = Decimal("0.00")

        for linea in orden.mano_obra:
            total_mano_obra += linea.total

            if orden.tipo == "GA":
                if linea.cubierto_garantia:
                    coste_asumido_taller += linea.total
                else:
                    trabajos_no_cubiertos += linea.total

        for pieza in orden.piezas:
            total_piezas += pieza.total

            if orden.tipo == "GA":
                if pieza.cubierto_garantia:
                    coste_asumido_taller += pieza.total
                else:
                    trabajos_no_cubiertos += pieza.total

        subtotal = (
            total_mano_obra +
            total_piezas
        )

        base_imponible = subtotal

        iva = (
            base_imponible *
            Decimal("21")
        ) / Decimal("100")

        importe_total = (
            base_imponible +
            iva
        )

        orden.total_mano_obra = total_mano_obra
        orden.total_piezas = total_piezas
        orden.subtotal = subtotal
        orden.base_imponible = base_imponible
        orden.iva = iva
        orden.importe_total = importe_total

        if orden.tipo == "GA":
            iva_cliente = (
                trabajos_no_cubiertos *
                Decimal("21")
            ) / Decimal("100")

            orden.coste_asumido_taller = (
                coste_asumido_taller
            )
            orden.trabajos_no_cubiertos = (
                trabajos_no_cubiertos
            )
            orden.iva_cliente_garantia = iva_cliente
            orden.total_cliente_garantia = (
                trabajos_no_cubiertos +
                iva_cliente
            )

        else:
            orden.coste_asumido_taller = Decimal("0.00")
            orden.trabajos_no_cubiertos = Decimal("0.00")
            orden.iva_cliente_garantia = Decimal("0.00")
            orden.total_cliente_garantia = Decimal("0.00")

        if commit:
            db.commit()
            db.refresh(orden)
        else:
            db.flush()

        return orden

    @staticmethod
    def update(
        db: Session,
        orden_id: int,
        datos: OrdenReparacionUpdate
    ):

        orden = OrdenReparacionRepository.get_by_id(
            db,
            orden_id
        )

        if orden is None:
            raise ValueError(
                "Orden de reparación no encontrada"
            )

        if orden.estado in {EstadoReparacion.FACTURADA.value, EstadoReparacion.ANULADA.value}:
            raise ValueError(
                "No se puede modificar una orden anulada o facturada"
            )

        if (
            orden.tipo == "PR"
            and orden.estado
            != EstadoReparacion.BORRADOR.value
        ):
            raise ValueError(
                "Solo se puede modificar un presupuesto en borrador"
            )

        datos_actualizados = datos.model_dump(
            exclude_unset=True
        )

        usuarios_ids = datos_actualizados.pop(
            "usuarios_ids",
            None,
        )

        if (
            not datos_actualizados
            and usuarios_ids is None
        ):
            return orden

        if (
            orden.tipo == "PR"
            and "estado" in datos_actualizados
            and datos_actualizados["estado"] != orden.estado
        ):
            raise ValueError(
                "El estado de un presupuesto solo puede cambiarse "
                "mediante Enviar, Aceptar o Rechazar"
            )

        if (
            orden.tipo == "GA"
            and "estado" in datos_actualizados
            and datos_actualizados["estado"] != orden.estado
        ):
            raise ValueError(
                "El estado de una garantía solo puede cambiarse "
                "mediante su ciclo de garantía"
            )

        if "vehiculo_id" in datos_actualizados:
            vehiculo = VehiculoRepository.get_by_id(
                db,
                datos_actualizados["vehiculo_id"]
            )

            if vehiculo is None:
                raise ValueError(
                    "El vehículo no existe"
                )

        else:
            vehiculo = orden.vehiculo

        if "kilometros_entrada" in datos_actualizados:
            OrdenReparacionService._registrar_kilometros_entrada(
                vehiculo,
                datos_actualizados["kilometros_entrada"],
                permitir_lectura_historica=True,
            )

        usuarios = None

        if usuarios_ids is not None:
            fecha_asignacion = datetime.now()

            usuarios = (
                OrdenReparacionService._obtener_usuarios_asignables(
                    db,
                    usuarios_ids,
                    fecha_asignacion,
                    fecha_asignacion + timedelta(minutes=1),
                )
            )

        try:
            orden = OrdenReparacionRepository.update(
                db,
                orden,
                datos_actualizados,
                commit=False,
            )

            if usuarios is not None:
                orden.usuarios_asignados = usuarios

            OrdenReparacionService.recalcular_totales(
                db,
                orden.id,
                commit=False,
            )

            db.commit()
            db.refresh(orden)

            return orden

        except Exception:
            db.rollback()
            raise

    @staticmethod
    def buscar(
        db: Session,
        texto: str
    ):
        return OrdenReparacionRepository.buscar(
            db,
            texto
        )

    @staticmethod
    def get_paginated(
        db: Session,
        pagination: PaginationParams,
        tipo: str | None = None,
        estado: str | None = None,
    ):
        items, total = (
            OrdenReparacionRepository.get_paginated(
                db,
                pagination,
                tipo,
                estado,
            )
        )

        return PaginatedResponse[
            OrdenReparacionResponse
        ].create(
            items=items,
            total=total,
            page=pagination.page,
            size=pagination.size
        )

    @staticmethod
    def delete(
        db: Session,
        orden_id: int
    ):

        orden = OrdenReparacionRepository.get_by_id(
            db,
            orden_id
        )

        if orden is None:
            raise ValueError(
                "La orden no existe."
            )

        if orden.estado == EstadoReparacion.FACTURADA.value:
            raise ValueError(
                "No se puede eliminar una orden facturada"
            )

        OrdenReparacionRepository.delete(
            db,
            orden
        )

    @staticmethod
    def generar_pdf(
        db: Session,
        orden_id: int
    ):
        orden = OrdenReparacionRepository.get_by_id(
            db,
            orden_id
        )

        if orden is None:
            raise ValueError(
                "Orden de reparación no encontrada"
            )

        empresa = EmpresaRepository.get_first(db)

        return OrdenReparacionService._generar_documento_pdf(
            db,
            orden,
            empresa,
        )

    @staticmethod
    def _generar_documento_pdf(
        db: Session,
        orden,
        empresa,
    ):
        """Genera OR, PR o GA usando un único contexto documental."""

        configuracion_taller = (
            ConfiguracionTallerService.obtener(db)
        )

        configuracion_documentos = (
            ConfiguracionDocumentosService.obtener(db)
        )

        contexto_documentos = (
            DocumentosContextService.obtener_contexto(db)
        )

        taller_visible = (
            DocumentosContextService.obtener_datos_taller_visibles(
                db
            )
        )

        ruta_logo = (
            DocumentosContextService.obtener_ruta_logo(db)
        )

        return PdfService.generar_orden(
            orden,
            empresa,
            configuracion_taller,
            configuracion_documentos,
            taller_visible=taller_visible,
            ruta_logo=ruta_logo,
            contexto_documentos=contexto_documentos,
        )

    @staticmethod
    def _registrar_envio_presupuesto(
        db: Session,
        orden,
        canal: str
    ) -> None:
        """Registra el primer envío únicamente tras éxito del proveedor."""

        if (
            orden.tipo == "PR"
            and orden.estado
            == EstadoReparacion.BORRADOR.value
        ):
            OrdenReparacionRepository.update(
                db,
                orden,
                {
                    "estado":
                        EstadoReparacion.ENVIADO.value,

                    "fecha_envio_presupuesto":
                        datetime.utcnow(),

                    "canal_envio_presupuesto":
                        canal,
                }
            )

    @staticmethod
    def _registrar_respuesta_presupuesto(
        db: Session,
        orden,
        estado: EstadoReparacion
    ):
        return OrdenReparacionRepository.update(
            db,
            orden,
            {
                "estado": estado.value,
                "fecha_respuesta_presupuesto":
                    datetime.utcnow(),
            }
        )

    @staticmethod
    def enviar_email(
        db: Session,
        orden_id: int
    ):
        # =====================================================
        # OBTENER ORDEN
        # =====================================================

        orden = OrdenReparacionRepository.get_by_id(
            db,
            orden_id
        )

        if orden is None:
            raise ValueError(
                "Orden de reparación no encontrada"
            )

        # =====================================================
        # OBTENER VEHÍCULO
        # =====================================================

        vehiculo = orden.vehiculo

        if vehiculo is None:
            raise ValueError(
                "La orden no tiene un vehículo asociado"
            )

        # =====================================================
        # OBTENER CLIENTE
        # =====================================================

        cliente = vehiculo.cliente

        if cliente is None:
            raise ValueError(
                "El vehículo no tiene un cliente asociado"
            )

        if not cliente.email:
            raise ValueError(
                "El cliente no tiene un correo electrónico registrado"
            )

        # =====================================================
        # OBTENER EMPRESA
        # =====================================================

        empresa = EmpresaRepository.get_first(
            db
        )

        # =====================================================
        # GENERAR PDF
        # =====================================================

        pdf_buffer = (
            OrdenReparacionService._generar_documento_pdf(
                db,
                orden,
                empresa,
            )
        )

        # =====================================================
        # PREPARAR DATOS
        # =====================================================

        nombre_cliente = ", ".join(
            filter(
                None,
                [
                    cliente.apellidos,
                    cliente.nombre
                ]
            )
        )

        nombre_vehiculo = " ".join(
            filter(
                None,
                [
                    vehiculo.marca,
                    vehiculo.modelo
                ]
            )
        )

        # =====================================================
        # ENVIAR EMAIL
        # =====================================================

        tipo_documento = (
            "Presupuesto" if orden.tipo == "PR"
            else "Garantía" if orden.tipo == "GA"
            else "Orden de reparación"
        )
        EmailService.enviar_documento_configurado(
            db=db,
            empresa_id=empresa.id,
            destinatario=cliente.email,
            asunto=f"{tipo_documento} {orden.numero}",
            texto=(
                f"Hola {nombre_cliente},\n\nAdjuntamos {tipo_documento.lower()} "
                f"{orden.numero} del vehículo {nombre_vehiculo} ({vehiculo.matricula}) "
                "en formato PDF.\n\nUn saludo."
            ),
            pdf_buffer=pdf_buffer,
            nombre_archivo=f"{orden.numero}.pdf",
        )

        # Solo se actualiza después de que SMTP
        # haya aceptado el envío.
        OrdenReparacionService._registrar_envio_presupuesto(
            db,
            orden,
            "EMAIL"
        )

        return {
            "message": (
                "Presupuesto enviado por email correctamente"
                if orden.tipo == "PR"
                else (
                    "Garantía enviada por email correctamente"
                    if orden.tipo == "GA"
                    else "Orden enviada por email correctamente"
                )
            ),
            "email": cliente.email,
            "estado": orden.estado
        }

    @staticmethod
    def enviar_whatsapp(
        db: Session,
        orden_id: int,
        empresa_id: int,
    ):
        # =====================================================
        # ORDEN
        # =====================================================

        orden = OrdenReparacionRepository.get_by_id(
            db,
            orden_id
        )

        if orden is None:
            raise ValueError(
                "Orden de reparación no encontrada"
            )

        # =====================================================
        # VEHÍCULO
        # =====================================================

        vehiculo = orden.vehiculo

        if vehiculo is None:
            raise ValueError(
                "La orden no tiene un vehículo asociado"
            )

        # =====================================================
        # CLIENTE
        # =====================================================

        cliente = vehiculo.cliente

        if cliente is None:
            raise ValueError(
                "El vehículo no tiene un cliente asociado"
            )

        if not cliente.telefono:
            raise ValueError(
                "El cliente no tiene un teléfono registrado"
            )

        # =====================================================
        # EMPRESA
        # =====================================================

        empresa = EmpresaRepository.get_by_id(
            db,
            empresa_id
        )

        if empresa is None:
            raise ValueError(
                "No hay datos del taller configurados"
            )

        # =====================================================
        # VALIDAR WHATSAPP DE LA EMPRESA
        # =====================================================

        # Las credenciales se leen de la configuración cifrada
        # de la empresa autenticada.
        whatsapp_config = WhatsAppConfigService.obtener(
            db,
            empresa_id
        )

        if whatsapp_config is None:
            raise ValueError(
                "WhatsApp no está configurado para esta empresa"
            )

        if not whatsapp_config.activo:
            raise ValueError(
                "WhatsApp no está conectado para esta empresa"
            )

        access_token = WhatsAppConfigService.obtener_token(
            db,
            empresa_id
        )

        if not access_token:
            raise ValueError(
                "La empresa no tiene un access token "
                "de WhatsApp configurado"
            )

        if not whatsapp_config.phone_number_id:
            raise ValueError(
                "La empresa no tiene un Phone Number ID "
                "de WhatsApp configurado"
            )

        # =====================================================
        # NOMBRE CLIENTE
        # =====================================================

        nombre_cliente = ", ".join(
            filter(
                None,
                [
                    getattr(
                        cliente,
                        "apellidos",
                        None
                    ),
                    getattr(
                        cliente,
                        "nombre",
                        None
                    )
                ]
            )
        )

        if not nombre_cliente:
            nombre_cliente = "Cliente"

        # =====================================================
        # VEHÍCULO
        # =====================================================

        marca = (
            getattr(
                vehiculo,
                "marca",
                None
            )
            or ""
        )

        modelo = (
            getattr(
                vehiculo,
                "modelo",
                None
            )
            or ""
        )

        nombre_vehiculo = (
            f"{marca} {modelo}"
        ).strip()

        if not nombre_vehiculo:
            nombre_vehiculo = "Vehículo"

        matricula = (
            getattr(
                vehiculo,
                "matricula",
                None
            )
            or "Sin matrícula"
        )

        # =====================================================
        # TALLER
        # =====================================================

        taller_visible = (
            DocumentosContextService.obtener_datos_taller_visibles(
                db
            )
        )

        nombre_taller = (
            taller_visible.get("razon_social")
            or taller_visible.get("nombre_comercial")
            or getattr(
                empresa,
                "nombre",
                None
            )
            or getattr(
                empresa,
                "nombre_comercial",
                None
            )
            or "Taller"
        )

        # =====================================================
        # GENERAR PDF
        # =====================================================

        pdf_buffer = (
            OrdenReparacionService._generar_documento_pdf(
                db,
                orden,
                empresa,
            )
        )

        # =====================================================
        # ENVIAR WHATSAPP
        # =====================================================

        if orden.tipo == "PR":

            # La plantilla aprobada de presupuesto tiene
            # 6 variables:
            #
            # {{1}} Cliente
            # {{2}} Nº presupuesto
            # {{3}} Vehículo
            # {{4}} Matrícula
            # {{5}} Importe total
            # {{6}} Taller
            #
            # La plantilla ya contiene el símbolo €, por lo que
            # únicamente enviamos el número.

            importe_total_whatsapp = (
                f"{orden.importe_total:.2f}"
                .replace(".", ",")
            )

            resultado = WhatsAppService.enviar_presupuesto(
                telefono=cliente.telefono,
                nombre_cliente=nombre_cliente,
                numero_presupuesto=orden.numero,
                vehiculo=nombre_vehiculo,
                matricula=matricula,
                nombre_taller=nombre_taller,
                importe_total=importe_total_whatsapp,
                pdf_buffer=pdf_buffer,
                access_token=access_token,
                phone_number_id=(
                    whatsapp_config.phone_number_id
                ),
            )

        elif orden.tipo == "GA":

            resultado = WhatsAppService.enviar_garantia(
                telefono=cliente.telefono,
                nombre_cliente=nombre_cliente,
                numero_garantia=orden.numero,
                vehiculo=nombre_vehiculo,
                matricula=matricula,
                nombre_taller=nombre_taller,
                pdf_buffer=pdf_buffer,
                access_token=access_token,
                phone_number_id=(
                    whatsapp_config.phone_number_id
                ),
            )

        else:

            resultado = WhatsAppService.enviar_orden(
                telefono=cliente.telefono,
                nombre_cliente=nombre_cliente,
                numero_orden=orden.numero,
                vehiculo=nombre_vehiculo,
                matricula=matricula,
                nombre_taller=nombre_taller,
                pdf_buffer=pdf_buffer,
                access_token=access_token,
                phone_number_id=(
                    whatsapp_config.phone_number_id
                )
            )

        # Meta ha aceptado el envío;
        # ahora queda trazado como enviado.
        OrdenReparacionService._registrar_envio_presupuesto(
            db,
            orden,
            "WHATSAPP"
        )

        # =====================================================
        # RESPUESTA
        # =====================================================

        return {
            "message": (
                "Presupuesto enviado por WhatsApp correctamente"
                if orden.tipo == "PR"
                else (
                    "Garantía enviada por WhatsApp correctamente"
                    if orden.tipo == "GA"
                    else "Orden enviada por WhatsApp correctamente"
                )
            ),
            "telefono": cliente.telefono,
            "estado": orden.estado,
            "whatsapp": resultado
        }

    @staticmethod
    def enviar_presupuesto(
        db: Session,
        orden_id: int
    ):
        orden = OrdenReparacionRepository.get_by_id(
            db,
            orden_id
        )

        if orden is None:
            raise ValueError(
                "Presupuesto no encontrado"
            )

        if orden.tipo != "PR":
            raise ValueError(
                "La orden indicada no es un presupuesto"
            )

        if orden.estado != EstadoReparacion.BORRADOR.value:
            raise ValueError(
                "Solo se puede enviar un presupuesto en borrador"
            )

        return OrdenReparacionRepository.update(
            db,
            orden,
            {
                "estado":
                    EstadoReparacion.ENVIADO.value
            }
        )

    @staticmethod
    def aceptar_presupuesto(
        db: Session,
        orden_id: int
    ):
        orden = OrdenReparacionRepository.get_by_id(
            db,
            orden_id
        )

        if orden is None:
            raise ValueError(
                "Presupuesto no encontrado"
            )

        if orden.tipo != "PR":
            raise ValueError(
                "La orden indicada no es un presupuesto"
            )

        if orden.estado != EstadoReparacion.ENVIADO.value:
            raise ValueError(
                "Solo se puede aceptar un presupuesto enviado"
            )

        return (
            OrdenReparacionService._registrar_respuesta_presupuesto(
                db,
                orden,
                EstadoReparacion.ACEPTADO
            )
        )

    @staticmethod
    def rechazar_presupuesto(
        db: Session,
        orden_id: int
    ):
        orden = OrdenReparacionRepository.get_by_id(
            db,
            orden_id
        )

        if orden is None:
            raise ValueError(
                "Presupuesto no encontrado"
            )

        if orden.tipo != "PR":
            raise ValueError(
                "La orden indicada no es un presupuesto"
            )

        if orden.estado != EstadoReparacion.ENVIADO.value:
            raise ValueError(
                "Solo se puede rechazar un presupuesto enviado"
            )

        return (
            OrdenReparacionService._registrar_respuesta_presupuesto(
                db,
                orden,
                EstadoReparacion.RECHAZADO
            )
        )

    @staticmethod
    def convertir_presupuesto_en_orden(
        db: Session,
        presupuesto_id: int
    ):

        # -------------------------------------------------
        # OBTENER PRESUPUESTO
        # -------------------------------------------------

        presupuesto = (
            OrdenReparacionRepository.get_by_id(
                db,
                presupuesto_id
            )
        )

        if presupuesto is None:
            raise ValueError(
                "Presupuesto no encontrado"
            )

        # -------------------------------------------------
        # VALIDAR TIPO
        # -------------------------------------------------

        if presupuesto.tipo != "PR":
            raise ValueError(
                "El documento indicado no es un presupuesto"
            )

        # -------------------------------------------------
        # SOLO PRESUPUESTOS ACEPTADOS
        # -------------------------------------------------

        if (
            presupuesto.estado
            != EstadoReparacion.ACEPTADO.value
        ):
            raise ValueError(
                "Solo se pueden convertir en orden "
                "los presupuestos aceptados"
            )

        # -------------------------------------------------
        # EVITAR CONVERSIONES DUPLICADAS
        # -------------------------------------------------

        if presupuesto.ordenes_generadas:
            orden_existente = (
                presupuesto.ordenes_generadas[0]
            )

            raise ValueError(
                "Este presupuesto ya fue convertido "
                f"en la orden {orden_existente.numero}"
            )

        # -------------------------------------------------
        # CREAR ORDEN REAL
        # -------------------------------------------------

        datos_orden = OrdenReparacionCreate(
            tipo="OR",
            vehiculo_id=presupuesto.vehiculo_id,
            descripcion_averia=(
                presupuesto.descripcion_averia
            ),
            garantia=False,
            garantia_meses=None,
            vehicle_damage=presupuesto.vehicle_damage,
            presupuesto_origen_id=presupuesto.id
        )

        nueva_orden = OrdenReparacionService.create(
            db,
            datos_orden
        )

        OrdenReparacionRepository.update(
            db,
            nueva_orden,
            {
                "diagnostico":
                    presupuesto.diagnostico,

                "observaciones":
                    presupuesto.observaciones,

                "observaciones_internas":
                    presupuesto.observaciones_internas,
            },
        )

        # -------------------------------------------------
        # COPIAR MANO DE OBRA
        # -------------------------------------------------

        for linea in presupuesto.mano_obra:

            ManoObraRepository.create(
                db,
                nueva_orden.id,
                {
                    "concepto":
                        linea.concepto,

                    "horas":
                        linea.horas,

                    "precio_hora":
                        linea.precio_hora,

                    "descuento_porcentaje":
                        linea.descuento_porcentaje,

                    "total":
                        linea.total
                }
            )

        # -------------------------------------------------
        # COPIAR PIEZAS
        # -------------------------------------------------

        for pieza in presupuesto.piezas:

            datos_pieza = {
                "descripcion":
                    pieza.descripcion,

                "cantidad":
                    pieza.cantidad,

                "precio_unitario":
                    pieza.precio_unitario,

                "descuento_porcentaje":
                    pieza.descuento_porcentaje,

                "total":
                    pieza.total
            }

            if hasattr(
                pieza,
                "proveedor_id"
            ):
                datos_pieza["proveedor_id"] = (
                    pieza.proveedor_id
                )

            if hasattr(
                pieza,
                "referencia"
            ):
                datos_pieza["referencia"] = (
                    pieza.referencia
                )

            PiezaRepository.create(
                db,
                nueva_orden.id,
                datos_pieza
            )

        # -------------------------------------------------
        # RECALCULAR NUEVA ORDEN
        # -------------------------------------------------

        OrdenReparacionService.recalcular_totales(
            db,
            nueva_orden.id
        )

        # -------------------------------------------------
        # DEVOLVER ORDEN COMPLETA
        # -------------------------------------------------

        return OrdenReparacionRepository.get_by_id(
            db,
            nueva_orden.id
        )

    @staticmethod
    def get_orden_generada_desde_presupuesto(
        db: Session,
        presupuesto_id: int
    ):
        presupuesto = (
            OrdenReparacionRepository.get_by_id(
                db,
                presupuesto_id
            )
        )

        if presupuesto is None:
            raise ValueError(
                "Presupuesto no encontrado"
            )

        if presupuesto.tipo != "PR":
            raise ValueError(
                "El documento indicado no es un presupuesto"
            )

        if not presupuesto.ordenes_generadas:
            raise ValueError(
                "Este presupuesto todavía no tiene "
                "una orden generada"
            )

        return presupuesto.ordenes_generadas[0]
