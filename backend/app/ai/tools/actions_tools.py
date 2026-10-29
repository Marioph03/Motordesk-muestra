from datetime import datetime
from uuid import uuid4

from sqlalchemy.orm import Session

from app.ai.actions.action_models import AccionPendiente, EstadoAccion, TipoAccion
from app.ai.actions.action_store import action_store
from app.ai.actions.cita_action import (
    _obtener_y_validar_datos,
    verificar_permiso_crear_cita,
)
from app.ai.actions.orden_action import (
    validar_datos_orden,
    verificar_permiso_crear_orden,
)
from app.ai.actions.cliente_action import (
    validar_datos_cliente,
    verificar_permiso_crear_cliente,
)
from app.ai.actions.vehiculo_action import (
    validar_datos_vehiculo,
    verificar_permiso_crear_vehiculo,
)
from app.ai.workflows.alta_cliente_vehiculo_cita import (
    proponer_alta_cliente_vehiculo_cita,
)
from app.ai.workflows.alta_cliente_vehiculo_orden import (
    proponer_alta_cliente_vehiculo_orden,
)
from app.ai.audit.audit_service import (
    TipoEventoAI,
    registrar_evento_ai,
)


def _registrar_accion_propuesta(
    db: Session,
    accion: AccionPendiente,
) -> None:
    registrar_evento_ai(
        db=db,
        usuario_id=accion.usuario_id,
        tipo_evento=TipoEventoAI.ACTION_PROPUESTA,
        recurso=accion.tipo.value,
        referencia_id=accion.id,
        descripcion=accion.resumen,
        datos=accion.datos,
    )


ACTIONS_TOOLS = [{
    "type": "function",
    "function": {
        "name": "proponer_alta_cliente_vehiculo_orden",
        "description": (
            "Prepara un workflow para crear un cliente nuevo, registrar su "
            "vehículo y abrir una orden de reparación. No crea ningún "
            "registro hasta que el usuario confirme el workflow completo."
        ),
        "parameters": {"type": "object", "properties": {
            "nombre": {"type": "string"},
            "apellidos": {"type": "string"},
            "dni": {"type": "string", "description": "DNI o NIF del cliente."},
            "telefono": {"type": "string"},
            "email": {"type": "string"},
            "direccion": {"type": "string"},
            "matricula": {"type": "string"},
            "marca": {"type": "string"},
            "modelo": {"type": "string"},
            "version": {"type": "string"},
            "bastidor": {"type": "string"},
            "color": {"type": "string"},
            "combustible": {"type": "string"},
            "descripcion_averia": {"type": "string"},
            "observaciones_orden": {"type": "string"}},
            "required": ["nombre", "matricula", "marca", "modelo", "descripcion_averia"],
            "additionalProperties": False},
    },
}, {
    "type": "function",
    "function": {
        "name": "proponer_alta_cliente_vehiculo_cita",
        "description": (
            "Prepara un único workflow para crear un cliente nuevo, "
            "registrar su vehículo y crear una cita. No crea ningún "
            "registro hasta que el usuario confirme el workflow completo."
        ),
        "parameters": {"type": "object", "properties": {
            "nombre": {"type": "string"},
            "apellidos": {"type": "string"},
            "dni": {"type": "string", "description": "DNI o NIF del cliente."},
            "telefono": {"type": "string"},
            "email": {"type": "string"},
            "direccion": {"type": "string"},
            "matricula": {"type": "string"},
            "marca": {"type": "string"},
            "modelo": {"type": "string"},
            "version": {"type": "string"},
            "bastidor": {"type": "string"},
            "color": {"type": "string"},
            "combustible": {"type": "string"},
            "fecha_inicio": {"type": "string", "description": "Fecha ISO 8601."},
            "fecha_fin": {"type": "string", "description": "Fecha ISO 8601 opcional."},
            "motivo": {"type": "string"},
            "observaciones_cita": {"type": "string"}},
            "required": ["nombre", "matricula", "marca", "modelo", "fecha_inicio", "motivo"],
            "additionalProperties": False},
    },
}, {
    "type": "function",
    "function": {
        "name": "proponer_crear_cita",
        "description": "Prepara una cita SIN guardarla. Requiere confirmación explícita del usuario antes de modificar MotorDesk.",
        "parameters": {"type": "object", "properties": {
            "cliente_id": {"type": "integer"}, "vehiculo_id": {"type": "integer"},
            "fecha_inicio": {"type": "string", "description": "Fecha ISO 8601."},
            "fecha_fin": {"type": "string", "description": "Fecha ISO 8601 opcional."},
            "motivo": {"type": "string"}, "observaciones": {"type": "string"}},
            "required": ["cliente_id", "vehiculo_id", "fecha_inicio", "motivo"],
            "additionalProperties": False},
    },
}, {
    "type": "function",
    "function": {
        "name": "proponer_crear_orden",
        "description": "Prepara una orden de reparación SIN crearla. Úsala solo tras identificar un vehículo existente; requiere confirmación explícita.",
        "parameters": {"type": "object", "properties": {
            "vehiculo_id": {"type": "integer"},
            "descripcion_averia": {"type": "string"},
            "observaciones": {"type": "string"}},
            "required": ["vehiculo_id", "descripcion_averia"],
            "additionalProperties": False},
    },
}, {
    "type": "function",
    "function": {
        "name": "proponer_crear_cliente",
        "description": "Prepara el alta de un cliente SIN crearlo. Requiere confirmación explícita antes de modificar MotorDesk.",
        "parameters": {"type": "object", "properties": {
            "nombre": {"type": "string"},
            "apellidos": {"type": "string"},
            "dni": {"type": "string", "description": "DNI o NIF del cliente."},
            "telefono": {"type": "string"},
            "email": {"type": "string"},
            "direccion": {"type": "string"}},
            "required": ["nombre"],
            "additionalProperties": False},
    },
}, {
    "type": "function",
    "function": {
        "name": "proponer_crear_vehiculo",
        "description": "Prepara el alta de un vehículo SIN crearlo. El cliente debe existir; matrícula, marca y modelo son obligatorios y requieren confirmación explícita.",
        "parameters": {"type": "object", "properties": {
            "cliente_id": {"type": "integer"},
            "matricula": {"type": "string"},
            "marca": {"type": "string"},
            "modelo": {"type": "string"},
            "version": {"type": "string"},
            "bastidor": {"type": "string"},
            "color": {"type": "string"},
            "combustible": {"type": "string"}},
            "required": ["cliente_id", "matricula", "marca", "modelo"],
            "additionalProperties": False},
    },
}]


def proponer_crear_cita(db: Session, argumentos: dict, usuario_id: int) -> dict:
    verificar_permiso_crear_cita(db, usuario_id)
    validado = _obtener_y_validar_datos(db, argumentos)
    anterior = action_store.obtener_pendiente_usuario(usuario_id)
    if anterior:
        anterior.estado = EstadoAccion.CANCELADA
        action_store.guardar(anterior)

    datos = {"cliente_id": validado["cliente"].id, "vehiculo_id": validado["vehiculo"].id,
             "fecha_inicio": validado["fecha_inicio"].isoformat(), "fecha_fin": validado["fecha_fin"].isoformat(),
             "motivo": validado["motivo"], "observaciones": validado["observaciones"]}
    cliente, vehiculo = validado["cliente"], validado["vehiculo"]
    nombre = " ".join(filter(None, [cliente.nombre, cliente.apellidos]))
    resumen = (f"Crear cita para {nombre} ({vehiculo.matricula}) el "
               f"{validado['fecha_inicio'].strftime('%d/%m/%Y %H:%M')} - "
               f"{validado['fecha_fin'].strftime('%H:%M')}. Motivo: {validado['motivo']}.")
    accion = AccionPendiente(id=str(uuid4()), tipo=TipoAccion.CREAR_CITA,
        estado=EstadoAccion.PENDIENTE, datos=datos, resumen=resumen,
        usuario_id=usuario_id, creada_en=datetime.utcnow().isoformat())
    action_store.guardar(accion)
    _registrar_accion_propuesta(db, accion)
    return {"accion_pendiente": True, "accion_id": accion.id, "tipo": accion.tipo.value,
            "resumen": accion.resumen, "datos": accion.datos,
            "instruccion": "La cita todavía NO se ha creado. Pide al usuario que confirme la acción."}


def proponer_crear_orden(
    db: Session,
    argumentos: dict,
    usuario_id: int,
) -> dict:
    verificar_permiso_crear_orden(db, usuario_id)
    validado = validar_datos_orden(db, argumentos)

    anterior = action_store.obtener_pendiente_usuario(usuario_id)
    if anterior:
        anterior.estado = EstadoAccion.CANCELADA
        action_store.guardar(anterior)

    vehiculo = validado["vehiculo"]
    vehiculo_texto = " ".join(filter(None, [
        vehiculo.marca,
        vehiculo.modelo,
    ]))
    datos = {
        "vehiculo_id": validado["vehiculo_id"],
        "cliente_id": validado["cliente_id"],
        "descripcion_averia": validado["descripcion_averia"],
        "observaciones": validado["observaciones"],
    }
    resumen = (
        "Crear una orden de reparación para "
        f"{vehiculo.matricula}"
        f" ({vehiculo_texto})"
        f". Avería/trabajo: {validado['descripcion_averia']}."
    )
    if validado["observaciones"]:
        resumen += (
            f" Observaciones: {validado['observaciones']}."
        )

    accion = AccionPendiente(
        id=str(uuid4()),
        tipo=TipoAccion.CREAR_ORDEN,
        estado=EstadoAccion.PENDIENTE,
        datos=datos,
        resumen=resumen,
        usuario_id=usuario_id,
        creada_en=datetime.utcnow().isoformat(),
    )
    action_store.guardar(accion)
    _registrar_accion_propuesta(db, accion)

    return {
        "accion_pendiente": True,
        "accion_id": accion.id,
        "tipo": accion.tipo.value,
        "resumen": accion.resumen,
        "datos": accion.datos,
        "instruccion": (
            "La orden todavía NO se ha creado. El usuario debe "
            "confirmar la acción desde MotorDesk."
        ),
    }


def proponer_crear_cliente(
    db: Session,
    argumentos: dict,
    usuario_id: int,
) -> dict:
    verificar_permiso_crear_cliente(db, usuario_id)
    datos = validar_datos_cliente(db, argumentos)

    anterior = action_store.obtener_pendiente_usuario(usuario_id)
    if anterior:
        anterior.estado = EstadoAccion.CANCELADA
        action_store.guardar(anterior)

    nombre_completo = " ".join(filter(None, [
        datos["nombre"],
        datos["apellidos"],
    ]))
    partes = [f"Crear cliente {nombre_completo}"]
    if datos["dni"]:
        partes.append(f"DNI/NIF: {datos['dni']}")
    if datos["telefono"]:
        partes.append(f"Teléfono: {datos['telefono']}")
    if datos["email"]:
        partes.append(f"Email: {datos['email']}")

    accion = AccionPendiente(
        id=str(uuid4()),
        tipo=TipoAccion.CREAR_CLIENTE,
        estado=EstadoAccion.PENDIENTE,
        datos=datos,
        resumen=". ".join(partes) + ".",
        usuario_id=usuario_id,
        creada_en=datetime.utcnow().isoformat(),
    )
    action_store.guardar(accion)
    _registrar_accion_propuesta(db, accion)

    return {
        "accion_pendiente": True,
        "accion_id": accion.id,
        "tipo": accion.tipo.value,
        "resumen": accion.resumen,
        "datos": accion.datos,
        "instruccion": (
            "El cliente todavía NO se ha creado. El usuario debe "
            "confirmar la acción desde MotorDesk."
        ),
    }


def proponer_crear_vehiculo(
    db: Session,
    argumentos: dict,
    usuario_id: int,
) -> dict:
    verificar_permiso_crear_vehiculo(db, usuario_id)
    validado = validar_datos_vehiculo(db, argumentos)

    anterior = action_store.obtener_pendiente_usuario(usuario_id)
    if anterior:
        anterior.estado = EstadoAccion.CANCELADA
        action_store.guardar(anterior)

    datos = {
        "cliente_id": validado["cliente_id"],
        "matricula": validado["matricula"],
        "marca": validado["marca"],
        "modelo": validado["modelo"],
        "version": validado["version"],
        "bastidor": validado["bastidor"],
        "color": validado["color"],
        "combustible": validado["combustible"],
    }
    cliente = validado["cliente"]
    nombre_cliente = " ".join(filter(None, [
        cliente.nombre,
        cliente.apellidos,
    ]))
    descripcion = " ".join(filter(None, [
        validado["marca"],
        validado["modelo"],
        validado["version"],
    ]))
    resumen = (
        f"Crear vehículo {validado['matricula']}"
        f" ({descripcion}) para {nombre_cliente}."
    )

    accion = AccionPendiente(
        id=str(uuid4()),
        tipo=TipoAccion.CREAR_VEHICULO,
        estado=EstadoAccion.PENDIENTE,
        datos=datos,
        resumen=resumen,
        usuario_id=usuario_id,
        creada_en=datetime.utcnow().isoformat(),
    )
    action_store.guardar(accion)
    _registrar_accion_propuesta(db, accion)

    return {
        "accion_pendiente": True,
        "accion_id": accion.id,
        "tipo": accion.tipo.value,
        "resumen": accion.resumen,
        "datos": accion.datos,
        "instruccion": (
            "El vehículo todavía NO se ha creado. El usuario debe "
            "confirmar la acción desde MotorDesk."
        ),
    }
"""Definiciones de herramientas IA que solo proponen acciones confirmables."""
