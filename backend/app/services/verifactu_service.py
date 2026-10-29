"""Orquestación de registros VERI*FACTU y su trazabilidad fiscal."""

import hashlib
from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.models.factura import EstadoFactura
from app.models.registro_verifactu import (
    EstadoRegistroVerifactu,
    TipoRegistroVerifactu,
)
from app.config.verifactu_config import VerifactuConfig
from app.repositories.empresa_repository import EmpresaRepository
from app.repositories.factura_repository import FacturaRepository
from app.repositories.registro_verifactu_repository import (
    RegistroVerifactuRepository,
)
from app.services.verifactu_xml_service import VerifactuXmlService
from app.services.verifactu_validation_service import (VerifactuValidationService)
from app.services.configuracion_facturacion_service import ConfiguracionFacturacionService


class VerifactuService:
    """Genera el registro de alta VERI*FACTU y conserva su trazabilidad."""

    @staticmethod
    def _formatear_decimal(valor: Decimal | int | float | str) -> str:
        return format(Decimal(str(valor)), ".2f")

    @staticmethod
    def _generar_hash(contenido: str) -> str:
        return hashlib.sha256(contenido.encode("utf-8")).hexdigest().upper()

    @staticmethod
    def _bloquear_cadena(db: Session, nif_emisor: str) -> None:
        """Evita dos altas simultáneas con el mismo hash anterior en PostgreSQL."""
        if db.bind is not None and db.bind.dialect.name == "postgresql":
            db.execute(
                text("SELECT pg_advisory_xact_lock(hashtext(:clave))"),
                {"clave": f"verifactu:{nif_emisor}:{VerifactuConfig.NUMERO_INSTALACION}"},
            )

    @staticmethod
    def _obtener_ultimo_registro(db: Session):
        return RegistroVerifactuRepository.get_ultimo(db)

    @staticmethod
    def get_registros_factura(db: Session, factura_id: int):
        factura = FacturaRepository.get_by_id(db, factura_id)
        if factura is None:
            raise ValueError("Factura no encontrada")

        return RegistroVerifactuRepository.get_by_factura(db, factura_id)

    @staticmethod
    def generar_registro_alta(
        db: Session,
        factura_id: int,
        commit: bool = True,
    ):
        factura = FacturaRepository.get_by_id(db, factura_id)
        if factura is None:
            raise ValueError("Factura no encontrada")

        if factura.estado != EstadoFactura.EMITIDA.value:
            raise ValueError(
                "Solo se puede generar VERI*FACTU para una factura emitida"
            )
        if factura.es_prueba:
            raise ValueError("Una factura de prueba no puede generar un registro VERI*FACTU")

        empresa = EmpresaRepository.get_first(db)
        if empresa is None:
            raise ValueError("No hay datos de empresa configurados")
        if not empresa.nif or not empresa.nif.strip():
            raise ValueError("La empresa no tiene NIF configurado")

        # Mantiene la generación manual de registros fuera del modo de pruebas.
        configuracion = ConfiguracionFacturacionService.obtener(db)
        if configuracion.modo_facturacion != "VERIFACTU":
            raise ValueError("Activa el modo VERI*FACTU para generar registros fiscales")

        cliente = factura.cliente
        if cliente is None:
            raise ValueError("La factura no tiene cliente asociado")

        registros_existentes = RegistroVerifactuRepository.get_by_factura(
            db, factura.id
        )
        if any(
            registro.tipo_registro == TipoRegistroVerifactu.ALTA.value
            for registro in registros_existentes
        ):
            raise ValueError("La factura ya tiene un registro VERI*FACTU de alta")

        VerifactuService._bloquear_cadena(db, empresa.nif.strip())
        ultimo_registro = VerifactuService._obtener_ultimo_registro(db)
        hash_anterior = None
        factura_anterior_numero = None
        factura_anterior_fecha = None

        if ultimo_registro is not None:
            if ultimo_registro.factura is None:
                raise ValueError(
                    "El último registro VERI*FACTU no tiene factura asociada"
                )
            hash_anterior = ultimo_registro.hash_registro
            factura_anterior_numero = ultimo_registro.factura.numero
            factura_anterior_fecha = (
                ultimo_registro.factura.fecha_emision.strftime("%d-%m-%Y")
            )

        fecha_generacion = datetime.now(timezone.utc)
        fecha_expedicion = factura.fecha_emision.strftime("%d-%m-%Y")
        cuota_iva = VerifactuService._formatear_decimal(factura.cuota_iva)
        total = VerifactuService._formatear_decimal(factura.total)
        fecha_hora_huso = fecha_generacion.isoformat(timespec="seconds")

        contenido_hash = VerifactuService._construir_cadena_hash_alta(
            nif_emisor=empresa.nif.strip(),
            numero_factura=factura.numero,
            fecha_expedicion=fecha_expedicion,
            tipo_factura="F1",
            cuota_total=cuota_iva,
            importe_total=total,
            huella_anterior=hash_anterior,
            fecha_hora_huso=fecha_hora_huso,
        )
        hash_registro = VerifactuService._generar_hash(contenido_hash)

        xml_registro = VerifactuXmlService.generar_registro_alta(
            factura=factura,
            empresa=empresa,
            cliente=cliente,
            hash_registro=hash_registro,
            hash_anterior=hash_anterior,
            factura_anterior_numero=factura_anterior_numero,
            factura_anterior_fecha=factura_anterior_fecha,
            fecha_hora_huso=fecha_hora_huso,
            nombre_productor=VerifactuConfig.NOMBRE_PRODUCTOR,
            nif_productor=VerifactuConfig.NIF_PRODUCTOR,
        )

        VerifactuValidationService.validar_xml(
            xml_registro
        )

        return RegistroVerifactuRepository.create(
            db,
            {
                "factura_id": factura.id,
                "tipo_registro": TipoRegistroVerifactu.ALTA.value,
                "estado": EstadoRegistroVerifactu.PENDIENTE.value,
                "hash_registro": hash_registro,
                "hash_anterior": hash_anterior,
                "factura_anterior_numero": factura_anterior_numero,
                "factura_anterior_fecha": factura_anterior_fecha,
                "xml_registro": xml_registro,
                "intentos_envio": 0,
                "fecha_generacion": fecha_generacion,
            },
            commit=commit,
        )

    @staticmethod
    def generar_registro_anulacion(
        db: Session,
        factura_id: int,
        commit: bool = True,
    ):
        """Genera, pero no envía, la anulación encadenada de una factura emitida."""
        factura = FacturaRepository.get_by_id(db, factura_id)
        if factura is None:
            raise ValueError("Factura no encontrada")
        if factura.estado != EstadoFactura.EMITIDA.value:
            raise ValueError(
                "Solo se puede generar una anulación VERI*FACTU para una factura emitida"
            )
        if factura.es_prueba:
            raise ValueError("Una factura de prueba no puede generar una anulación VERI*FACTU")

        empresa = EmpresaRepository.get_first(db)
        if empresa is None:
            raise ValueError("No hay datos de empresa configurados")
        if not empresa.nif or not empresa.nif.strip():
            raise ValueError("La empresa no tiene NIF configurado")

        configuracion = ConfiguracionFacturacionService.obtener(db)
        if configuracion.modo_facturacion != "VERIFACTU":
            raise ValueError("Activa el modo VERI*FACTU para generar registros fiscales")

        registros = RegistroVerifactuRepository.get_by_factura(db, factura.id)
        alta = next(
            (
                registro for registro in registros
                if registro.tipo_registro == TipoRegistroVerifactu.ALTA.value
            ),
            None,
        )
        if alta is None:
            raise ValueError(
                "La factura no tiene un registro VERI*FACTU de alta que anular"
            )
        if alta.estado not in (
            EstadoRegistroVerifactu.ACEPTADO.value,
            EstadoRegistroVerifactu.ACEPTADO_CON_ERRORES.value,
        ):
            raise ValueError(
                "El registro VERI*FACTU de alta debe estar aceptado por AEAT antes de anular la factura"
            )
        if any(
            registro.tipo_registro == TipoRegistroVerifactu.ANULACION.value
            for registro in registros
        ):
            raise ValueError(
                "La factura ya tiene un registro VERI*FACTU de anulación"
            )

        VerifactuService._bloquear_cadena(db, empresa.nif.strip())
        ultimo_registro = VerifactuService._obtener_ultimo_registro(db)
        hash_anterior = None
        factura_anterior_numero = None
        factura_anterior_fecha = None
        if ultimo_registro is not None:
            if ultimo_registro.factura is None:
                raise ValueError(
                    "El último registro VERI*FACTU no tiene factura asociada"
                )
            hash_anterior = ultimo_registro.hash_registro
            factura_anterior_numero = ultimo_registro.factura.numero
            factura_anterior_fecha = (
                ultimo_registro.factura.fecha_emision.strftime("%d-%m-%Y")
            )

        fecha_generacion = datetime.now(timezone.utc)
        fecha_expedicion = factura.fecha_emision.strftime("%d-%m-%Y")
        fecha_hora_huso = fecha_generacion.isoformat(timespec="seconds")
        contenido_hash = VerifactuService._construir_cadena_hash_anulacion(
            nif_emisor=empresa.nif.strip(),
            numero_factura=factura.numero,
            fecha_expedicion=fecha_expedicion,
            huella_anterior=hash_anterior,
            fecha_hora_huso=fecha_hora_huso,
        )
        hash_registro = VerifactuService._generar_hash(contenido_hash)

        xml_registro = VerifactuXmlService.generar_registro_anulacion(
            factura=factura,
            empresa=empresa,
            hash_registro=hash_registro,
            hash_anterior=hash_anterior,
            factura_anterior_numero=factura_anterior_numero,
            factura_anterior_fecha=factura_anterior_fecha,
            fecha_hora_huso=fecha_hora_huso,
            nombre_productor=VerifactuConfig.NOMBRE_PRODUCTOR,
            nif_productor=VerifactuConfig.NIF_PRODUCTOR,
        )
        VerifactuValidationService.validar_xml(xml_registro)

        return RegistroVerifactuRepository.create(
            db,
            {
                "factura_id": factura.id,
                "tipo_registro": TipoRegistroVerifactu.ANULACION.value,
                "estado": EstadoRegistroVerifactu.PENDIENTE.value,
                "hash_registro": hash_registro,
                "hash_anterior": hash_anterior,
                "factura_anterior_numero": factura_anterior_numero,
                "factura_anterior_fecha": factura_anterior_fecha,
                "xml_registro": xml_registro,
                "intentos_envio": 0,
                "fecha_generacion": fecha_generacion,
            },
            commit=commit,
        )

    @staticmethod
    def _construir_cadena_hash_alta(
        nif_emisor: str,
        numero_factura: str,
        fecha_expedicion: str,
        tipo_factura: str,
        cuota_total: str,
        importe_total: str,
        huella_anterior: str | None,
        fecha_hora_huso: str,
    ) -> str:
        return (
            f"IDEmisorFactura={nif_emisor}"
            f"&NumSerieFactura={numero_factura}"
            f"&FechaExpedicionFactura={fecha_expedicion}"
            f"&TipoFactura={tipo_factura}"
            f"&CuotaTotal={cuota_total}"
            f"&ImporteTotal={importe_total}"
            f"&Huella={huella_anterior or ''}"
            f"&FechaHoraHusoGenRegistro={fecha_hora_huso}"
        )

    @staticmethod
    def _construir_cadena_hash_anulacion(
        nif_emisor: str,
        numero_factura: str,
        fecha_expedicion: str,
        huella_anterior: str | None,
        fecha_hora_huso: str,
    ) -> str:
        return (
            f"IDEmisorFacturaAnulada={nif_emisor}"
            f"&NumSerieFacturaAnulada={numero_factura}"
            f"&FechaExpedicionFacturaAnulada={fecha_expedicion}"
            f"&Huella={huella_anterior or ''}"
            f"&FechaHoraHusoGenRegistro={fecha_hora_huso}"
        )
