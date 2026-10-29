from datetime import datetime

from sqlalchemy.orm import Session

from app.ai.actions.action_models import (
    AccionPendiente,
    EstadoAccion,
    TipoAccion,
)
from app.ai.actions.action_store import action_store
from app.models.usuario import Usuario
from app.models.vehiculo import Vehiculo
from app.schemas.orden_reparacion import OrdenReparacionCreate
from app.services.orden_reparacion_service import OrdenReparacionService
from app.services.permisos_service import PermisosService


def verificar_permiso_crear_orden(
    db: Session,
    usuario_id: int,
) -> None:
    usuario = (
        db.query(Usuario)
        .filter(Usuario.id == usuario_id)
        .first()
    )

    if usuario is None or not usuario.activo:
        raise PermissionError(
            "El usuario no puede crear órdenes."
        )

    if not PermisosService.usuario_tiene_permiso(
        db,
        usuario,
        "ordenes.crear",
    ):
        raise PermissionError(
            "No tienes permiso para crear órdenes."
        )


def validar_datos_orden(
    db: Session,
    datos: dict,
) -> dict:
    vehiculo_id = datos.get("vehiculo_id")
    descripcion_averia = str(
        datos.get("descripcion_averia") or ""
    ).strip()
    observaciones = str(
        datos.get("observaciones") or ""
    ).strip() or None

    if not vehiculo_id:
        raise ValueError("La orden necesita un vehículo.")
    if not descripcion_averia:
        raise ValueError(
            "La orden necesita una descripción de la avería."
        )
    if len(descripcion_averia) > 5000:
        raise ValueError(
            "La descripción de la avería es demasiado larga."
        )

    vehiculo = (
        db.query(Vehiculo)
        .filter(Vehiculo.id == vehiculo_id)
        .first()
    )

    if vehiculo is None:
        raise ValueError("El vehículo seleccionado ya no existe.")
    if not vehiculo.cliente_id:
        raise ValueError(
            "El vehículo no tiene un cliente asociado."
        )

    return {
        "vehiculo": vehiculo,
        "vehiculo_id": vehiculo.id,
        "cliente_id": vehiculo.cliente_id,
        "descripcion_averia": descripcion_averia,
        "observaciones": observaciones,
    }


def ejecutar_crear_orden(
    db: Session,
    accion: AccionPendiente,
    usuario_id: int,
) -> dict:
    if accion.tipo != TipoAccion.CREAR_ORDEN:
        raise ValueError("La acción no corresponde a una orden.")
    if accion.usuario_id != usuario_id:
        raise PermissionError("La acción pertenece a otro usuario.")
    if accion.estado != EstadoAccion.PENDIENTE:
        raise ValueError("La acción ya no está pendiente.")

    # Repetimos autorización y validación: entre propuesta y confirmación
    # pueden haber cambiado los permisos o los datos del vehículo.
    verificar_permiso_crear_orden(db, usuario_id)
    datos = validar_datos_orden(db, accion.datos)

    nueva_orden = OrdenReparacionService.create(
        db,
        OrdenReparacionCreate(
            tipo="OR",
            vehiculo_id=datos["vehiculo_id"],
            descripcion_averia=datos["descripcion_averia"],
            observaciones=datos["observaciones"],
            usuarios_ids=[],
        ),
    )

    ahora = datetime.utcnow().isoformat()
    accion.estado = EstadoAccion.EJECUTADA
    accion.confirmada_en = ahora
    accion.ejecutada_en = ahora
    accion.resultado = {
        "orden_id": nueva_orden.id,
        "numero": nueva_orden.numero,
        "vehiculo_id": nueva_orden.vehiculo_id,
        "estado": nueva_orden.estado,
        "descripcion_averia": nueva_orden.descripcion_averia,
    }
    action_store.guardar(accion)

    return {
        "ok": True,
        "mensaje": (
            f"Orden {nueva_orden.numero} creada correctamente."
        ),
        "orden": accion.resultado,
    }
"""Propuesta y ejecución confirmada de una orden de reparación mediante IA."""
