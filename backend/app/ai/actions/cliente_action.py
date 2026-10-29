from datetime import datetime

from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.ai.actions.action_models import (
    AccionPendiente,
    EstadoAccion,
    TipoAccion,
)
from app.ai.actions.action_store import action_store
from app.models.cliente import Cliente
from app.models.usuario import Usuario
from app.schemas.cliente import ClienteCreate
from app.services.cliente_service import ClienteService
from app.services.permisos_service import PermisosService


def verificar_permiso_crear_cliente(
    db: Session,
    usuario_id: int,
) -> Usuario:
    usuario = (
        db.query(Usuario)
        .filter(Usuario.id == usuario_id)
        .first()
    )

    if usuario is None or not usuario.activo:
        raise PermissionError(
            "El usuario no puede crear clientes."
        )

    if not PermisosService.usuario_tiene_permiso(
        db,
        usuario,
        "clientes.crear",
    ):
        raise PermissionError(
            "No tienes permiso para crear clientes."
        )

    return usuario


def validar_datos_cliente(
    db: Session,
    datos: dict,
) -> dict:
    nombre = str(datos.get("nombre") or "").strip()
    apellidos = str(datos.get("apellidos") or "").strip() or None
    dni = str(datos.get("dni") or "").strip().upper() or None
    telefono = str(datos.get("telefono") or "").strip() or None
    email = str(datos.get("email") or "").strip().lower() or None
    direccion = str(datos.get("direccion") or "").strip() or None

    if not nombre:
        raise ValueError("El cliente necesita un nombre.")
    if len(nombre) > 100:
        raise ValueError("El nombre del cliente es demasiado largo.")
    if apellidos and len(apellidos) > 150:
        raise ValueError("Los apellidos del cliente son demasiado largos.")

    if dni:
        existente = (
            db.query(Cliente)
            .filter(Cliente.dni == dni)
            .first()
        )
        if existente:
            raise ValueError(
                f"Ya existe un cliente con el DNI/NIF {dni}."
            )

    if email:
        existente_email = (
            db.query(Cliente)
            .filter(Cliente.email.ilike(email))
            .first()
        )
        if existente_email:
            raise ValueError(
                "Ya existe un cliente con ese correo electrónico."
            )

    return {
        "nombre": nombre,
        "apellidos": apellidos,
        "dni": dni,
        "telefono": telefono,
        "email": email,
        "direccion": direccion,
    }


def ejecutar_crear_cliente(
    db: Session,
    accion: AccionPendiente,
    usuario_id: int,
) -> dict:
    if accion.tipo != TipoAccion.CREAR_CLIENTE:
        raise ValueError("La acción no corresponde a un cliente.")
    if accion.usuario_id != usuario_id:
        raise PermissionError("La acción pertenece a otro usuario.")
    if accion.estado != EstadoAccion.PENDIENTE:
        raise ValueError("La acción ya no está pendiente.")

    usuario = verificar_permiso_crear_cliente(db, usuario_id)
    datos = validar_datos_cliente(db, accion.datos)
    try:
        nuevo_cliente = ClienteService.create(
            db,
            ClienteCreate(**datos),
            usuario,
        )
    except IntegrityError as error:
        db.rollback()
        raise ValueError(
            "No se ha podido crear el cliente porque ya existe un "
            "registro con el mismo DNI/NIF."
        ) from error

    ahora = datetime.utcnow().isoformat()
    accion.estado = EstadoAccion.EJECUTADA
    accion.confirmada_en = ahora
    accion.ejecutada_en = ahora
    accion.resultado = {
        "cliente_id": nuevo_cliente.id,
        "nombre": nuevo_cliente.nombre,
        "apellidos": nuevo_cliente.apellidos,
        "dni": nuevo_cliente.dni,
        "telefono": nuevo_cliente.telefono,
        "email": nuevo_cliente.email,
    }
    action_store.guardar(accion)

    return {
        "ok": True,
        "mensaje": "Cliente creado correctamente.",
        "cliente": accion.resultado,
    }
"""Propuesta y ejecución confirmada del alta de un cliente mediante IA."""
