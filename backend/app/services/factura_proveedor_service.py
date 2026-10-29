"""Facturas recibidas de proveedor, enlaces a albaranes y adjuntos PDF."""

from datetime import date
from decimal import Decimal
from pathlib import Path
from uuid import uuid4

from fastapi import UploadFile
from sqlalchemy.orm import Session

from app.models.albaran_proveedor import AlbaranProveedor
from app.models.factura_proveedor import FacturaProveedor
from app.models.factura_proveedor_albaran import FacturaProveedorAlbaran
from app.models.proveedor import Proveedor
from app.schemas.factura_proveedor import FacturaProveedorCreate


class FacturaProveedorService:
    STORAGE_ROOT = Path(__file__).resolve().parents[2] / "storage" / "proveedores" / "facturas"
    TIPOS_GASTO = {"COMPRA", "SUMINISTRO", "REPARACION", "OTRO"}

    @staticmethod
    def listar(db: Session) -> list[FacturaProveedor]:
        return (
            db.query(FacturaProveedor)
            .order_by(FacturaProveedor.fecha_factura.desc(), FacturaProveedor.id.desc())
            .all()
        )

    @staticmethod
    def obtener(db: Session, factura_id: int) -> FacturaProveedor:
        factura = db.query(FacturaProveedor).filter(FacturaProveedor.id == factura_id).first()
        if factura is None:
            raise ValueError("Factura de proveedor no encontrada")
        return factura

    @staticmethod
    def crear(db: Session, datos: FacturaProveedorCreate) -> FacturaProveedor:
        numero = datos.numero_factura.strip()
        tipo_gasto = datos.tipo_gasto.strip().upper()
        if not numero:
            raise ValueError("El número de factura es obligatorio")
        if tipo_gasto not in FacturaProveedorService.TIPOS_GASTO:
            raise ValueError("El tipo de gasto no es valido")
        if datos.fecha_vencimiento and datos.fecha_vencimiento < datos.fecha_factura:
            raise ValueError("La fecha de vencimiento no puede ser anterior a la fecha de factura")
        if False:  # Los importes se calculan en el servidor a partir de porcentajes.
            raise ValueError("El total debe coincidir con la base imponible más el IVA")
        if db.query(Proveedor).filter(Proveedor.id == datos.proveedor_id).first() is None:
            raise ValueError("Proveedor no encontrado")
        if (
            db.query(FacturaProveedor)
            .filter(FacturaProveedor.proveedor_id == datos.proveedor_id, FacturaProveedor.numero_factura == numero)
            .first()
        ):
            raise ValueError("Ya existe una factura con ese número para este proveedor")

        try:
            albaranes = FacturaProveedorService._validar_albaranes(
                db,
                datos.proveedor_id,
                datos.albaranes_ids,
            )
            base = Decimal(datos.base_imponible)
            cuota_iva = (base * Decimal(datos.porcentaje_iva) / Decimal("100")).quantize(Decimal("0.01"))
            cuota_retencion = (base * Decimal(datos.porcentaje_retencion) / Decimal("100")).quantize(Decimal("0.01"))
            factura = FacturaProveedor(
                proveedor_id=datos.proveedor_id,
                numero_factura=numero,
                tipo_gasto=tipo_gasto,
                fecha_factura=datos.fecha_factura,
                fecha_vencimiento=datos.fecha_vencimiento,
                base_imponible=datos.base_imponible,
                porcentaje_iva=datos.porcentaje_iva,
                iva=cuota_iva,
                porcentaje_retencion=datos.porcentaje_retencion,
                retencion_irpf=cuota_retencion,
                total=base + cuota_iva - cuota_retencion,
                estado_pago="PENDIENTE",
                observaciones=datos.observaciones,
            )
            factura.albaranes = albaranes
            db.add(factura)
            db.commit()
            db.refresh(factura)
            return factura
        except Exception:
            db.rollback()
            raise

    @staticmethod
    def marcar_pagada(db: Session, factura_id: int, fecha_pago: date | None = None) -> FacturaProveedor:
        factura = FacturaProveedorService.obtener(db, factura_id)
        if factura.estado_pago == "PAGADA":
            raise ValueError("La factura ya está marcada como pagada")
        try:
            factura.estado_pago = "PAGADA"
            factura.fecha_pago = fecha_pago or date.today()
            db.commit()
            db.refresh(factura)
            return factura
        except Exception:
            db.rollback()
            raise

    @staticmethod
    def guardar_pdf(db: Session, factura_id: int, archivo: UploadFile) -> FacturaProveedor:
        factura = FacturaProveedorService.obtener(db, factura_id)
        if not (archivo.filename or "").lower().endswith(".pdf"):
            raise ValueError("El documento debe ser un PDF")

        contenido = archivo.file.read()
        if not contenido.startswith(b"%PDF"):
            raise ValueError("El archivo no contiene un PDF válido")
        if len(contenido) > 10 * 1024 * 1024:
            raise ValueError("El PDF no puede superar los 10 MB")

        carpeta = FacturaProveedorService.STORAGE_ROOT / str(factura.id)
        carpeta.mkdir(parents=True, exist_ok=True)
        destino = carpeta / "factura.pdf"
        temporal = carpeta / f".{uuid4().hex}.tmp"
        try:
            temporal.write_bytes(contenido)
            temporal.replace(destino)
            factura.archivo_pdf = str(destino.relative_to(FacturaProveedorService.STORAGE_ROOT.parents[2])).replace("\\", "/")
            db.commit()
            db.refresh(factura)
            return factura
        except Exception:
            db.rollback()
            if temporal.exists():
                temporal.unlink()
            raise

    @staticmethod
    def obtener_ruta_pdf(db: Session, factura_id: int) -> Path:
        factura = FacturaProveedorService.obtener(db, factura_id)
        if not factura.archivo_pdf:
            raise ValueError("Esta factura no tiene un PDF adjunto")
        ruta = (FacturaProveedorService.STORAGE_ROOT.parents[2] / factura.archivo_pdf).resolve()
        raiz = FacturaProveedorService.STORAGE_ROOT.parents[2].resolve()
        if raiz not in ruta.parents or not ruta.is_file():
            raise ValueError("El PDF asociado no está disponible")
        return ruta

    @staticmethod
    def _validar_albaranes(db: Session, proveedor_id: int, albaranes_ids: list[int]) -> list[AlbaranProveedor]:
        albaranes = []
        for albaran_id in set(albaranes_ids):
            albaran = db.query(AlbaranProveedor).filter(AlbaranProveedor.id == albaran_id).first()
            if albaran is None:
                raise ValueError(f"El albarán {albaran_id} no existe")
            if albaran.proveedor_id != proveedor_id:
                raise ValueError("Todos los albaranes deben pertenecer al proveedor de la factura")
            if albaran.estado != "CONFIRMADO":
                raise ValueError("Solo se pueden asociar albaranes confirmados")
            if db.query(FacturaProveedorAlbaran).filter(FacturaProveedorAlbaran.albaran_proveedor_id == albaran_id).first():
                raise ValueError("Uno de los albaranes ya está asociado a otra factura")
            albaranes.append(albaran)
        return albaranes
