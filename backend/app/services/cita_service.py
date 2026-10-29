"""Reglas de agenda: horarios, solapes y disponibilidad del personal."""

from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from app.models.cita import (
    EstadoCita
)

from app.repositories.cita_repository import (
    CitaRepository
)

from app.repositories.cliente_repository import (
    ClienteRepository
)

from app.repositories.vehiculo_repository import (
    VehiculoRepository
)
from app.repositories.usuario_repository import UsuarioRepository
from app.services.ausencia_personal_service import AusenciaPersonalService
from app.services.configuracion_agenda_service import ConfiguracionAgendaService

from app.schemas.cita import (
    CitaCreate,
    CitaUpdate
)
from app.models.orden_reparacion import EstadoReparacion
from app.services.orden_reparacion_service import OrdenReparacionService
from app.schemas.orden_reparacion import OrdenReparacionCreate
from app.services.email_service import EmailService
from app.models.cita import Cita


class CitaService:

    @staticmethod
    def _obtener_usuarios_asignados(
        db: Session,
        usuarios_ids: list[int],
        fecha_inicio: datetime,
        fecha_fin: datetime,
    ):
        """Resuelve usuarios activos y disponibles para el intervalo solicitado."""

        usuarios = []

        for usuario_id in dict.fromkeys(usuarios_ids):
            usuario = UsuarioRepository.get_by_id(db, usuario_id)

            if usuario is None:
                raise ValueError(
                    f"Usuario {usuario_id} no encontrado"
                )

            if not usuario.activo:
                raise ValueError(
                    f"{usuario.nombre} {usuario.apellidos} "
                    "no está activo"
                )

            if not AusenciaPersonalService.usuario_disponible(
                db,
                usuario.id,
                fecha_inicio,
                fecha_fin,
            ):
                raise ValueError(
                    f"{usuario.nombre} {usuario.apellidos} "
                    "no está disponible en ese horario"
                )

            usuarios.append(usuario)

        return usuarios

    @staticmethod
    def _cambiar_estado(db: Session, cita_id: int, permitidos: tuple[str, ...], destino: EstadoCita, error: str):
        """Aplica una transición de agenda únicamente desde estados permitidos."""

        cita = CitaService.get_by_id(db, cita_id)
        if cita.estado not in permitidos:
            raise ValueError(error)
        return CitaRepository.update(db, cita, {"estado": destino.value})

    @staticmethod
    def confirmar(db: Session, cita_id: int):
        return CitaService._cambiar_estado(db, cita_id, (EstadoCita.PENDIENTE.value,), EstadoCita.CONFIRMADA, "Solo se puede confirmar una cita pendiente")

    @staticmethod
    def marcar_en_taller(db: Session, cita_id: int):
        return CitaService._cambiar_estado(db, cita_id, (EstadoCita.PENDIENTE.value, EstadoCita.CONFIRMADA.value), EstadoCita.EN_TALLER, "La cita no se puede marcar como llegada en su estado actual")

    @staticmethod
    def completar(db: Session, cita_id: int):
        return CitaService._cambiar_estado(db, cita_id, (EstadoCita.EN_TALLER.value,), EstadoCita.COMPLETADA, "Solo se puede completar una cita cuando el vehículo está en el taller")

    @staticmethod
    def cancelar(db: Session, cita_id: int):
        return CitaService._cambiar_estado(db, cita_id, (EstadoCita.PENDIENTE.value, EstadoCita.CONFIRMADA.value), EstadoCita.CANCELADA, "La cita no se puede cancelar en su estado actual")

    @staticmethod
    def marcar_no_presentado(db: Session, cita_id: int):
        return CitaService._cambiar_estado(db, cita_id, (EstadoCita.PENDIENTE.value, EstadoCita.CONFIRMADA.value), EstadoCita.NO_PRESENTADO, "La cita no se puede marcar como no presentada")

    @staticmethod
    def procesar_recordatorios_automaticos(db: Session) -> int:
        """Envía una sola vez los recordatorios de las próximas 24 horas."""
        ahora = datetime.utcnow()
        limite = ahora + timedelta(hours=24)
        citas = (
            db.query(Cita)
            .filter(
                Cita.fecha_inicio > ahora,
                Cita.fecha_inicio <= limite,
                Cita.fecha_recordatorio.is_(None),
                Cita.estado.in_([
                    EstadoCita.PENDIENTE.value,
                    EstadoCita.CONFIRMADA.value,
                ]),
            )
            .all()
        )

        enviados = 0
        for cita in citas:
            try:
                CitaService.enviar_recordatorio_email(db, cita.id)
                enviados += 1
            except (ValueError, RuntimeError):
                db.rollback()
        return enviados

    @staticmethod
    def enviar_recordatorio_email(db: Session, cita_id: int):
        cita = CitaRepository.get_by_id(db, cita_id)
        if cita is None: raise ValueError("Cita no encontrada")
        if cita.estado not in (EstadoCita.PENDIENTE.value, EstadoCita.CONFIRMADA.value):
            raise ValueError("Solo se pueden enviar recordatorios de citas pendientes o confirmadas")
        cliente, vehiculo = cita.cliente, cita.vehiculo
        EmailService.enviar_recordatorio_cita(cliente.email, cliente.nombre, cita.fecha_inicio.strftime("%d/%m/%Y"), cita.fecha_inicio.strftime("%H:%M"), f"{vehiculo.marca or ''} {vehiculo.modelo or ''}".strip(), vehiculo.matricula, cita.motivo)
        CitaRepository.update(db, cita, {"fecha_recordatorio": datetime.utcnow(), "canal_recordatorio": "EMAIL"})
        return {"email": cliente.email}

    @staticmethod
    def enviar_confirmacion_email(db: Session, cita_id: int):
        cita = CitaRepository.get_by_id(db, cita_id)
        if cita is None:
            raise ValueError("Cita no encontrada")
        if cita.estado in (EstadoCita.CANCELADA.value, EstadoCita.NO_PRESENTADO.value):
            raise ValueError("No se puede confirmar una cita cancelada o no presentada")

        cliente = cita.cliente
        vehiculo = cita.vehiculo
        EmailService.enviar_confirmacion_cita(
            cliente.email,
            ", ".join(parte for parte in [cliente.apellidos or "", cliente.nombre or ""] if parte),
            cita.fecha_inicio,
            f"{vehiculo.marca} {vehiculo.modelo} · {vehiculo.matricula}",
            cita.motivo,
        )
        return CitaRepository.update(db, cita, {
            "estado": EstadoCita.CONFIRMADA.value,
            "fecha_confirmacion": datetime.utcnow(),
            "canal_confirmacion": "EMAIL",
        })

    @staticmethod
    def crear_orden_desde_cita(db: Session, cita_id: int):
        cita = CitaRepository.get_by_id(db, cita_id)

        if cita is None:
            raise ValueError("Cita no encontrada")

        if cita.estado in (
            EstadoCita.CANCELADA.value,
            EstadoCita.NO_PRESENTADO.value,
        ):
            raise ValueError(
                "No se puede crear una orden desde una cita cancelada "
                "o con cliente no presentado"
            )

        if cita.orden_generada_id is not None:
            raise ValueError("Esta cita ya tiene una orden asociada")

        nueva_orden = OrdenReparacionService.create(
            db,
            OrdenReparacionCreate(
                tipo="OR",
                vehiculo_id=cita.vehiculo_id,
                descripcion_averia=cita.motivo,
                garantia=False,
                garantia_meses=None,
                cita_origen_id=cita.id,
            ),
        )

        CitaRepository.update(
            db,
            cita,
            {
                "orden_generada_id": nueva_orden.id,
                "estado": EstadoCita.EN_TALLER.value,
            },
        )

        return nueva_orden

    @staticmethod
    def crear_presupuesto_desde_cita(db: Session, cita_id: int):
        cita = CitaRepository.get_by_id(db, cita_id)

        if cita is None:
            raise ValueError("Cita no encontrada")

        if cita.estado in (
            EstadoCita.CANCELADA.value,
            EstadoCita.NO_PRESENTADO.value,
        ):
            raise ValueError("No se puede crear un presupuesto desde esta cita")

        if cita.orden_generada_id is not None:
            raise ValueError("Esta cita ya tiene un documento asociado")

        presupuesto = OrdenReparacionService.create(
            db,
            OrdenReparacionCreate(
                tipo="PR",
                vehiculo_id=cita.vehiculo_id,
                descripcion_averia=cita.motivo,
                garantia=False,
                garantia_meses=None,
                cita_origen_id=cita.id,
            ),
        )

        CitaRepository.update(
            db,
            cita,
            {"orden_generada_id": presupuesto.id},
        )

        return presupuesto

    @staticmethod
    def get_all(
        db: Session
    ):
        return CitaRepository.get_all(
            db
        )


    @staticmethod
    def get_by_id(
        db: Session,
        cita_id: int
    ):

        cita = CitaRepository.get_by_id(
            db,
            cita_id
        )

        if cita is None:
            raise ValueError(
                "Cita no encontrada"
            )

        return cita


    @staticmethod
    def get_by_rango(
        db: Session,
        fecha_inicio: datetime,
        fecha_fin: datetime
    ):

        if fecha_fin <= fecha_inicio:
            raise ValueError(
                "La fecha final debe ser posterior "
                "a la fecha inicial"
            )

        return CitaRepository.get_by_rango(
            db,
            fecha_inicio,
            fecha_fin
        )


    @staticmethod
    def create(
        db: Session,
        datos: CitaCreate
    ):

        # ---------------------------------------------
        # CLIENTE
        # ---------------------------------------------

        cliente = ClienteRepository.get_by_id(
            db,
            datos.cliente_id
        )

        if cliente is None:
            raise ValueError(
                "Cliente no encontrado"
            )

        # ---------------------------------------------
        # VEHÍCULO
        # ---------------------------------------------

        vehiculo = VehiculoRepository.get_by_id(
            db,
            datos.vehiculo_id
        )

        if vehiculo is None:
            raise ValueError(
                "Vehículo no encontrado"
            )

        # El vehículo debe pertenecer al cliente
        if vehiculo.cliente_id != cliente.id:
            raise ValueError(
                "El vehículo no pertenece "
                "al cliente seleccionado"
            )

        # ---------------------------------------------
        # FECHAS
        # ---------------------------------------------

        CitaService._validar_fechas(
            datos.fecha_inicio,
            datos.fecha_fin
        )

        ConfiguracionAgendaService.validar_fecha_cita(
            db,
            datos.fecha_inicio,
            datos.fecha_fin
        )

        # ---------------------------------------------
        # MOTIVO
        # ---------------------------------------------

        motivo = datos.motivo.strip()

        if not motivo:
            raise ValueError(
                "Debes indicar el motivo de la cita"
            )

        # ---------------------------------------------
        # SOLAPES
        # ---------------------------------------------

        solapadas = (
            CitaRepository.get_solapadas(
                db,
                datos.fecha_inicio,
                datos.fecha_fin
            )
        )

        if solapadas:
            raise ValueError(
                "Ya existe una cita en ese horario"
            )

        usuarios_asignados = CitaService._obtener_usuarios_asignados(
            db,
            datos.usuarios_ids,
            datos.fecha_inicio,
            datos.fecha_fin,
        )

        datos_db = datos.model_dump(exclude={"usuarios_ids"})

        datos_db["motivo"] = motivo

        datos_db["estado"] = (
            EstadoCita.PENDIENTE.value
        )

        try:
            cita = CitaRepository.create(
                db,
                datos_db,
                commit=False,
            )

            cita.usuarios_asignados = usuarios_asignados

            db.commit()
            db.refresh(cita)

            return cita
        except Exception:
            db.rollback()
            raise


    @staticmethod
    def update(
        db: Session,
        cita_id: int,
        datos: CitaUpdate
    ):

        cita = CitaRepository.get_by_id(
            db,
            cita_id
        )

        if cita is None:
            raise ValueError(
                "Cita no encontrada"
            )

        cambios = datos.model_dump(
            exclude_unset=True
        )

        usuarios_ids = cambios.pop("usuarios_ids", None)

        if not cambios and usuarios_ids is None:
            return cita

        # ---------------------------------------------
        # CLIENTE / VEHÍCULO RESULTANTE
        # ---------------------------------------------

        cliente_id = cambios.get(
            "cliente_id",
            cita.cliente_id
        )

        vehiculo_id = cambios.get(
            "vehiculo_id",
            cita.vehiculo_id
        )

        cliente = ClienteRepository.get_by_id(
            db,
            cliente_id
        )

        if cliente is None:
            raise ValueError(
                "Cliente no encontrado"
            )

        vehiculo = VehiculoRepository.get_by_id(
            db,
            vehiculo_id
        )

        if vehiculo is None:
            raise ValueError(
                "Vehículo no encontrado"
            )

        if vehiculo.cliente_id != cliente.id:
            raise ValueError(
                "El vehículo no pertenece "
                "al cliente seleccionado"
            )

        # ---------------------------------------------
        # FECHAS RESULTANTES
        # ---------------------------------------------

        fecha_inicio = cambios.get(
            "fecha_inicio",
            cita.fecha_inicio
        )

        fecha_fin = cambios.get(
            "fecha_fin",
            cita.fecha_fin
        )

        CitaService._validar_fechas(
            fecha_inicio,
            fecha_fin
        )

        ConfiguracionAgendaService.validar_fecha_cita(
            db,
            fecha_inicio,
            fecha_fin
        )

        cambia_horario = (
            fecha_inicio != cita.fecha_inicio
            or fecha_fin != cita.fecha_fin
        )

        if cambia_horario:
            cambios["fecha_inicio_anterior"] = cita.fecha_inicio
            cambios["fecha_fin_anterior"] = cita.fecha_fin
            cambios["fecha_reprogramacion"] = datetime.utcnow()
            cambios["fecha_recordatorio"] = None
            cambios["canal_recordatorio"] = None

        # ---------------------------------------------
        # COMPROBAR SOLAPES
        # ---------------------------------------------

        solapadas = (
            CitaRepository.get_solapadas(
                db,
                fecha_inicio,
                fecha_fin,
                excluir_cita_id=cita.id
            )
        )

        if solapadas:
            raise ValueError(
                "Ya existe una cita en ese horario"
            )

        # Si se cambia el personal, se valida la nueva selección. Si solo se
        # reprograma la cita, se vuelve a comprobar el personal ya asignado:
        # una ausencia puede afectar al nuevo horario.
        usuarios_asignados = None
        if usuarios_ids is not None:
            usuarios_asignados = CitaService._obtener_usuarios_asignados(
                db,
                usuarios_ids,
                fecha_inicio,
                fecha_fin,
            )
        elif cambia_horario:
            CitaService._obtener_usuarios_asignados(
                db,
                [usuario.id for usuario in cita.usuarios_asignados],
                fecha_inicio,
                fecha_fin,
            )

        # ---------------------------------------------
        # MOTIVO
        # ---------------------------------------------

        if "motivo" in cambios:

            motivo = (
                cambios["motivo"]
                or ""
            ).strip()

            if not motivo:
                raise ValueError(
                    "Debes indicar el motivo de la cita"
                )

            cambios["motivo"] = motivo

        # ---------------------------------------------
        # ESTADO
        # ---------------------------------------------

        if "estado" in cambios:

            estados_validos = {
                estado.value
                for estado in EstadoCita
            }

            if (
                cambios["estado"]
                not in estados_validos
            ):
                raise ValueError(
                    "Estado de cita no válido"
                )

        try:
            cita = CitaRepository.update(
                db,
                cita,
                cambios,
                usuarios_asignados,
                commit=False,
            )
            db.commit()
            db.refresh(cita)
            return cita
        except Exception:
            db.rollback()
            raise

    @staticmethod
    def enviar_aviso_reprogramacion_email(db: Session, cita_id: int):
        cita = CitaService.get_by_id(db, cita_id)

        if cita.fecha_reprogramacion is None:
            raise ValueError("La cita no ha sido reprogramada")

        cliente = cita.cliente
        vehiculo = cita.vehiculo

        EmailService.enviar_aviso_reprogramacion_cita(
            destinatario=cliente.email,
            nombre_cliente=cliente.nombre,
            fecha_inicio=cita.fecha_inicio,
            vehiculo=f"{vehiculo.marca or ''} {vehiculo.modelo or ''}".strip(),
            matricula=vehiculo.matricula or "",
        )

        return cita


    @staticmethod
    def delete(
        db: Session,
        cita_id: int
    ):

        cita = CitaRepository.get_by_id(
            db,
            cita_id
        )

        if cita is None:
            raise ValueError(
                "Cita no encontrada"
            )

        if cita.orden_generada_id is not None:
            raise ValueError(
                "No se puede eliminar una cita "
                "que ya tiene una orden asociada"
            )

        CitaRepository.delete(
            db,
            cita
        )


    @staticmethod
    def _validar_fechas(
        fecha_inicio: datetime,
        fecha_fin: datetime
    ):

        if fecha_fin <= fecha_inicio:
            raise ValueError(
                "La hora de fin debe ser posterior "
                "a la hora de inicio"
            )

        duracion = (
            fecha_fin -
            fecha_inicio
        )

        if duracion.total_seconds() < 15 * 60:
            raise ValueError(
                "La cita debe durar al menos "
                "15 minutos"
            )

        if duracion.total_seconds() > 12 * 60 * 60:
            raise ValueError(
                "La duración de la cita "
                "no puede superar 12 horas"
            )
