from datetime import datetime

from sqlalchemy.orm import Session

from app.ai.actions.cliente_action import (
    validar_datos_cliente,
    verificar_permiso_crear_cliente,
)
from app.ai.actions.orden_action import verificar_permiso_crear_orden
from app.ai.actions.vehiculo_action import (
    validar_datos_vehiculo,
    verificar_permiso_crear_vehiculo,
)
from app.ai.workflows.alta_cliente_vehiculo_cita import _validar_borrador_vehiculo
from app.ai.workflows.workflow_models import (
    EstadoPasoWorkflow,
    EstadoWorkflow,
    PasoWorkflow,
    TipoPasoWorkflow,
    TipoWorkflow,
    WorkflowPendiente,
)
from app.ai.workflows.workflow_service import crear_workflow
from app.ai.workflows.workflow_store import workflow_store
from app.models.cliente import Cliente
from app.models.orden_reparacion import EstadoReparacion, OrdenReparacion
from app.models.vehiculo import Vehiculo
from app.services.orden_reparacion_service import OrdenReparacionService
from app.ai.audit.audit_service import TipoEventoAI, registrar_evento_ai


def _validar_borrador_orden(datos: dict) -> dict:
    descripcion_averia = str(datos.get("descripcion_averia") or "").strip()
    observaciones = (
        str(datos.get("observaciones_orden") or "").strip() or None
    )
    if not descripcion_averia:
        raise ValueError("La orden necesita una descripción de la avería.")
    if len(descripcion_averia) > 5000:
        raise ValueError("La descripción de la avería es demasiado larga.")
    return {
        "descripcion_averia": descripcion_averia,
        "observaciones": observaciones,
    }


def proponer_alta_cliente_vehiculo_orden(
    db: Session,
    usuario_id: int,
    datos: dict,
) -> WorkflowPendiente:
    """Prepara cliente, vehículo y orden; no modifica la base de datos."""
    verificar_permiso_crear_cliente(db, usuario_id)
    verificar_permiso_crear_vehiculo(db, usuario_id)
    verificar_permiso_crear_orden(db, usuario_id)

    datos_cliente = validar_datos_cliente(db, {
        "nombre": datos.get("nombre"),
        "apellidos": datos.get("apellidos"),
        "dni": datos.get("dni") or datos.get("nif"),
        "telefono": datos.get("telefono"),
        "email": datos.get("email"),
        "direccion": datos.get("direccion"),
    })
    datos_vehiculo = _validar_borrador_vehiculo(db, datos)
    datos_orden = _validar_borrador_orden(datos)

    nombre_completo = " ".join(filter(None, [
        datos_cliente["nombre"], datos_cliente["apellidos"],
    ]))
    matricula = datos_vehiculo["matricula"]

    workflow = crear_workflow(
        tipo=TipoWorkflow.ALTA_CLIENTE_VEHICULO_ORDEN,
        usuario_id=usuario_id,
        resumen=(
            f"Dar de alta a {nombre_completo}, registrar el vehículo "
            f"{matricula} y abrir una orden de reparación."
        ),
        pasos=[
            PasoWorkflow(
                orden=1,
                tipo=TipoPasoWorkflow.CREAR_CLIENTE,
                resumen=f"Crear cliente {nombre_completo}",
                datos=datos_cliente,
            ),
            PasoWorkflow(
                orden=2,
                tipo=TipoPasoWorkflow.CREAR_VEHICULO,
                resumen=(
                    f"Registrar vehículo {matricula} "
                    f"({datos_vehiculo['marca']} {datos_vehiculo['modelo']})"
                ),
                datos={"cliente_id": None, **datos_vehiculo},
            ),
            PasoWorkflow(
                orden=3,
                tipo=TipoPasoWorkflow.CREAR_ORDEN,
                resumen=(
                    f"Abrir orden para {matricula}. "
                    f"Avería/trabajo: {datos_orden['descripcion_averia']}"
                ),
                datos={"vehiculo_id": None, **datos_orden},
            ),
        ],
    )
    registrar_evento_ai(
        db=db,
        usuario_id=usuario_id,
        tipo_evento=TipoEventoAI.WORKFLOW_PROPUESTO,
        recurso=workflow.tipo.value,
        referencia_id=workflow.id,
        descripcion=workflow.resumen,
        datos={
            "pasos": [
                {
                    "orden": paso.orden,
                    "tipo": paso.tipo.value,
                    "resumen": paso.resumen,
                }
                for paso in workflow.pasos
            ]
        },
    )
    return workflow


def ejecutar_alta_cliente_vehiculo_orden(
    db: Session,
    workflow: WorkflowPendiente,
    usuario_id: int,
) -> dict:
    if workflow.usuario_id != usuario_id:
        raise PermissionError("El workflow pertenece a otro usuario.")
    if workflow.estado != EstadoWorkflow.PENDIENTE:
        raise ValueError("El workflow ya no está pendiente.")

    verificar_permiso_crear_cliente(db, usuario_id)
    verificar_permiso_crear_vehiculo(db, usuario_id)
    verificar_permiso_crear_orden(db, usuario_id)
    workflow.estado = EstadoWorkflow.EJECUTANDO
    workflow_store.guardar(workflow)

    try:
        paso_cliente, paso_vehiculo, paso_orden = workflow.pasos

        paso_cliente.estado = EstadoPasoWorkflow.EJECUTANDO
        cliente = Cliente(**validar_datos_cliente(db, paso_cliente.datos))
        db.add(cliente)
        db.flush()
        paso_cliente.resultado = {"cliente_id": cliente.id}
        paso_cliente.estado = EstadoPasoWorkflow.COMPLETADO

        paso_vehiculo.estado = EstadoPasoWorkflow.EJECUTANDO
        paso_vehiculo.datos["cliente_id"] = cliente.id
        datos_vehiculo = validar_datos_vehiculo(db, paso_vehiculo.datos)
        vehiculo = Vehiculo(
            cliente_id=datos_vehiculo["cliente_id"],
            matricula=datos_vehiculo["matricula"],
            marca=datos_vehiculo["marca"],
            modelo=datos_vehiculo["modelo"],
            version=datos_vehiculo["version"],
            bastidor=datos_vehiculo["bastidor"],
            color=datos_vehiculo["color"],
            combustible=datos_vehiculo["combustible"],
        )
        db.add(vehiculo)
        db.flush()
        paso_vehiculo.resultado = {"vehiculo_id": vehiculo.id}
        paso_vehiculo.estado = EstadoPasoWorkflow.COMPLETADO

        paso_orden.estado = EstadoPasoWorkflow.EJECUTANDO
        paso_orden.datos["vehiculo_id"] = vehiculo.id
        datos_orden = _validar_borrador_orden(paso_orden.datos)
        numero = OrdenReparacionService.generar_numero(db, "OR")
        orden = OrdenReparacion(
            numero=numero,
            tipo="OR",
            vehiculo_id=vehiculo.id,
            descripcion_averia=datos_orden["descripcion_averia"],
            observaciones=datos_orden["observaciones"],
            estado=EstadoReparacion.ABIERTA.value,
            garantia=False,
        )
        db.add(orden)
        db.flush()
        paso_orden.resultado = {
            "orden_id": orden.id,
            "numero": orden.numero,
        }
        paso_orden.estado = EstadoPasoWorkflow.COMPLETADO

        # Único commit para todo el workflow. Un error en la orden revierte
        # igualmente cliente y vehículo.
        db.commit()

        workflow.estado = EstadoWorkflow.COMPLETADO
        workflow.ejecutada_en = datetime.utcnow().isoformat()
        workflow.resultado = {
            "cliente_id": cliente.id,
            "vehiculo_id": vehiculo.id,
            "orden_id": orden.id,
            "numero_orden": orden.numero,
            "matricula": vehiculo.matricula,
        }
        workflow_store.guardar(workflow)
        return {
            "ok": True,
            "mensaje": (
                f"Cliente, vehículo y orden {orden.numero} creados correctamente."
            ),
            "resultado": workflow.resultado,
        }
    except Exception as error:
        db.rollback()
        workflow.estado = EstadoWorkflow.ERROR
        workflow.error = str(error)
        for paso in workflow.pasos:
            if paso.estado == EstadoPasoWorkflow.EJECUTANDO:
                paso.estado = EstadoPasoWorkflow.ERROR
                paso.error = str(error)
            elif paso.estado == EstadoPasoWorkflow.PENDIENTE:
                paso.estado = EstadoPasoWorkflow.OMITIDO
        workflow_store.guardar(workflow)
        raise
