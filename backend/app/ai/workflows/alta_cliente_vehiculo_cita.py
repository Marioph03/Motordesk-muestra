from datetime import datetime, timedelta

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.ai.actions.cita_action import (
    _obtener_y_validar_datos,
    _parsear_fecha,
    verificar_permiso_crear_cita,
)
from app.ai.actions.cliente_action import (
    validar_datos_cliente,
    verificar_permiso_crear_cliente,
)
from app.ai.actions.vehiculo_action import (
    _normalizar_matricula,
    _texto,
    validar_datos_vehiculo,
    verificar_permiso_crear_vehiculo,
)
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
from app.models.cita import Cita, EstadoCita
from app.models.cliente import Cliente
from app.models.vehiculo import Vehiculo
from app.repositories.cita_repository import CitaRepository
from app.services.cita_service import CitaService
from app.services.configuracion_agenda_service import ConfiguracionAgendaService
from app.ai.audit.audit_service import TipoEventoAI, registrar_evento_ai


def _validar_borrador_vehiculo(db: Session, datos: dict) -> dict:
    """Valida la información que no depende todavía del nuevo cliente."""
    matricula = _normalizar_matricula(_texto(datos, "matricula"))
    marca = _texto(datos, "marca")
    modelo = _texto(datos, "modelo")
    version = _texto(datos, "version")
    bastidor = _texto(datos, "bastidor")
    color = _texto(datos, "color")
    combustible = _texto(datos, "combustible")

    if not matricula:
        raise ValueError("El vehículo necesita una matrícula.")
    if not marca:
        raise ValueError("El vehículo necesita una marca.")
    if not modelo:
        raise ValueError("El vehículo necesita un modelo.")
    if len(matricula) > 10:
        raise ValueError("La matrícula es demasiado larga.")
    if len(marca) > 50 or len(modelo) > 50:
        raise ValueError("La marca o el modelo son demasiado largos.")

    existente = db.query(Vehiculo).filter(
        func.upper(
            func.replace(
                func.replace(Vehiculo.matricula, " ", ""),
                "-",
                "",
            )
        ) == matricula
    ).first()
    if existente:
        raise ValueError(f"Ya existe un vehículo con la matrícula {matricula}.")

    if bastidor:
        bastidor = bastidor.upper()
        existente_bastidor = db.query(Vehiculo).filter(
            Vehiculo.bastidor.ilike(bastidor)
        ).first()
        if existente_bastidor:
            raise ValueError("Ya existe un vehículo con ese número de bastidor.")

    return {
        "matricula": matricula,
        "marca": marca,
        "modelo": modelo,
        "version": version,
        "bastidor": bastidor,
        "color": color,
        "combustible": combustible,
    }


def _validar_borrador_cita(db: Session, datos: dict) -> dict:
    motivo = str(datos.get("motivo") or "").strip()
    if not motivo:
        raise ValueError("La cita necesita un motivo.")
    if len(motivo) > 500:
        raise ValueError("El motivo de la cita es demasiado largo.")

    fecha_inicio = _parsear_fecha(datos.get("fecha_inicio"))
    fecha_fin = (
        _parsear_fecha(datos.get("fecha_fin"))
        if datos.get("fecha_fin")
        else fecha_inicio + timedelta(hours=1)
    )
    if fecha_inicio < datetime.now():
        raise ValueError("No se puede crear una cita en el pasado.")

    CitaService._validar_fechas(fecha_inicio, fecha_fin)
    ConfiguracionAgendaService.validar_fecha_cita(db, fecha_inicio, fecha_fin)
    if CitaRepository.get_solapadas(db, fecha_inicio, fecha_fin):
        raise ValueError("Ya existe una cita en ese intervalo horario.")

    return {
        "fecha_inicio": fecha_inicio.isoformat(),
        "fecha_fin": fecha_fin.isoformat(),
        "motivo": motivo,
        "observaciones": str(datos.get("observaciones_cita") or "").strip() or None,
    }


def proponer_alta_cliente_vehiculo_cita(
    db: Session,
    usuario_id: int,
    datos: dict,
) -> WorkflowPendiente:
    """Prepara el alta completa sin escribir ningún registro en la base de datos."""
    verificar_permiso_crear_cliente(db, usuario_id)
    verificar_permiso_crear_vehiculo(db, usuario_id)
    verificar_permiso_crear_cita(db, usuario_id)

    # ``nif`` se mantiene como compatibilidad con propuestas antiguas.
    datos_cliente = validar_datos_cliente(db, {
        "nombre": datos.get("nombre"),
        "apellidos": datos.get("apellidos"),
        "dni": datos.get("dni") or datos.get("nif"),
        "telefono": datos.get("telefono"),
        "email": datos.get("email"),
        "direccion": datos.get("direccion"),
    })
    datos_vehiculo = _validar_borrador_vehiculo(db, datos)
    datos_cita = _validar_borrador_cita(db, datos)

    nombre_completo = " ".join(filter(None, [
        datos_cliente["nombre"], datos_cliente["apellidos"],
    ]))
    matricula = datos_vehiculo["matricula"]
    pasos = [
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
            tipo=TipoPasoWorkflow.CREAR_CITA,
            resumen=(
                f"Crear cita para {matricula} el "
                f"{_parsear_fecha(datos_cita['fecha_inicio']).strftime('%d/%m/%Y %H:%M')}. "
                f"Motivo: {datos_cita['motivo']}"
            ),
            datos={"cliente_id": None, "vehiculo_id": None, **datos_cita},
        ),
    ]
    workflow = crear_workflow(
        tipo=TipoWorkflow.ALTA_CLIENTE_VEHICULO_CITA,
        usuario_id=usuario_id,
        resumen=(
            f"Dar de alta a {nombre_completo}, registrar el vehículo "
            f"{matricula} y crear su cita."
        ),
        pasos=pasos,
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


def ejecutar_alta_cliente_vehiculo_cita(
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
    verificar_permiso_crear_cita(db, usuario_id)
    workflow.estado = EstadoWorkflow.EJECUTANDO
    workflow_store.guardar(workflow)

    try:
        paso_cliente, paso_vehiculo, paso_cita = workflow.pasos

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

        paso_cita.estado = EstadoPasoWorkflow.EJECUTANDO
        paso_cita.datos["cliente_id"] = cliente.id
        paso_cita.datos["vehiculo_id"] = vehiculo.id
        datos_cita = _obtener_y_validar_datos(db, paso_cita.datos)
        if CitaRepository.get_solapadas(
            db, datos_cita["fecha_inicio"], datos_cita["fecha_fin"]
        ):
            raise ValueError("Ya existe una cita en ese intervalo horario.")
        cita = Cita(
            cliente_id=cliente.id,
            vehiculo_id=vehiculo.id,
            fecha_inicio=datos_cita["fecha_inicio"],
            fecha_fin=datos_cita["fecha_fin"],
            motivo=datos_cita["motivo"],
            observaciones=datos_cita["observaciones"],
            estado=EstadoCita.PENDIENTE.value,
        )
        db.add(cita)
        db.flush()
        paso_cita.resultado = {"cita_id": cita.id}
        paso_cita.estado = EstadoPasoWorkflow.COMPLETADO

        # Un solo commit: no quedan altas parciales si falla cualquier paso.
        db.commit()
        workflow.estado = EstadoWorkflow.COMPLETADO
        workflow.ejecutada_en = datetime.utcnow().isoformat()
        workflow.resultado = {
            "cliente_id": cliente.id,
            "vehiculo_id": vehiculo.id,
            "cita_id": cita.id,
            "matricula": vehiculo.matricula,
            "fecha_cita": cita.fecha_inicio.isoformat(),
        }
        workflow_store.guardar(workflow)
        return {
            "ok": True,
            "mensaje": "Cliente, vehículo y cita creados correctamente.",
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
