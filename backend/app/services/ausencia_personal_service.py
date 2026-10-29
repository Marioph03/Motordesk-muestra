"""Ausencias de personal y cálculo reutilizable de disponibilidad por rango."""

from datetime import datetime

from sqlalchemy.orm import Session

from app.models.ausencia_personal import TipoAusenciaPersonal
from app.repositories.ausencia_personal_repository import (
    AusenciaPersonalRepository,
)
from app.repositories.usuario_repository import UsuarioRepository
from app.repositories.cita_repository import CitaRepository
from app.schemas.ausencia_personal import (
    AusenciaPersonalCreate,
    AusenciaPersonalUpdate,
)


class AusenciaPersonalService:
    @staticmethod
    def get_all(
        db: Session,
        usuario_id: int | None = None,
    ):
        return AusenciaPersonalRepository.get_all(db, usuario_id)

    @staticmethod
    def get_by_id(
        db: Session,
        ausencia_id: int,
    ):
        ausencia = AusenciaPersonalRepository.get_by_id(
            db,
            ausencia_id,
        )

        if ausencia is None:
            raise ValueError("Ausencia no encontrada")

        return ausencia

    @staticmethod
    def get_by_rango(
        db: Session,
        fecha_inicio: datetime,
        fecha_fin: datetime,
        usuario_id: int | None = None,
    ):
        AusenciaPersonalService.validar_intervalo(
            fecha_inicio,
            fecha_fin,
        )

        return AusenciaPersonalRepository.get_by_rango(
            db,
            fecha_inicio,
            fecha_fin,
            usuario_id,
        )

    @staticmethod
    def usuario_disponible(
        db: Session,
        usuario_id: int,
        fecha_inicio: datetime,
        fecha_fin: datetime,
    ) -> bool:
        """Indica si el usuario no tiene vacaciones ni ausencias en el intervalo."""

        usuario = UsuarioRepository.get_by_id(db, usuario_id)
        if usuario is None:
            raise ValueError("Usuario no encontrado")

        AusenciaPersonalService.validar_intervalo(
            fecha_inicio,
            fecha_fin,
        )

        return not AusenciaPersonalRepository.get_solapadas(
            db,
            usuario_id,
            fecha_inicio,
            fecha_fin,
        )

    @staticmethod
    def obtener_disponibilidad_personal(
        db: Session,
        fecha_inicio: datetime,
        fecha_fin: datetime,
        excluir_cita_id: int | None = None,
        excluir_orden_id: int | None = None,
    ) -> list[dict]:
        """Resume la disponibilidad de todo el personal en un intervalo."""

        AusenciaPersonalService.validar_intervalo(
            fecha_inicio,
            fecha_fin,
        )

        resultado = []
        for usuario in UsuarioRepository.get_all(db):
            if not usuario.activo:
                resultado.append({
                    "usuario_id": usuario.id,
                    "nombre": usuario.nombre,
                    "apellidos": usuario.apellidos,
                    "rol": usuario.rol,
                    "disponible": False,
                    "motivo": "INACTIVO",
                    "conflicto_tipo": None,
                    "conflicto_id": None,
                    "conflicto_referencia": None,
                })
                continue

            ausencias = AusenciaPersonalRepository.get_solapadas(
                db,
                usuario.id,
                fecha_inicio,
                fecha_fin,
            )

            ausencia = ausencias[0] if ausencias else None

            if ausencia is not None:
                resultado.append({
                    "usuario_id": usuario.id,
                    "nombre": usuario.nombre,
                    "apellidos": usuario.apellidos,
                    "rol": usuario.rol,
                    "disponible": False,
                    "motivo": ausencia.tipo,
                    "conflicto_tipo": "AUSENCIA",
                    "conflicto_id": ausencia.id,
                    "conflicto_referencia": ausencia.tipo,
                })
                continue

            citas = CitaRepository.get_solapadas_usuario(
                db,
                usuario.id,
                fecha_inicio,
                fecha_fin,
                excluir_cita_id=excluir_cita_id,
            )
            cita = citas[0] if citas else None

            if cita is not None:
                resultado.append({
                    "usuario_id": usuario.id,
                    "nombre": usuario.nombre,
                    "apellidos": usuario.apellidos,
                    "rol": usuario.rol,
                    "disponible": False,
                    "motivo": "CITA_ASIGNADA",
                    "conflicto_tipo": "CITA",
                    "conflicto_id": cita.id,
                    "conflicto_referencia": cita.motivo,
                })
                continue

            resultado.append({
                "usuario_id": usuario.id,
                "nombre": usuario.nombre,
                "apellidos": usuario.apellidos,
                "rol": usuario.rol,
                "disponible": True,
                "motivo": None,
                "conflicto_tipo": None,
                "conflicto_id": None,
                "conflicto_referencia": None,
            })

        return resultado

    @staticmethod
    def validar_intervalo(
        fecha_inicio: datetime,
        fecha_fin: datetime,
    ) -> None:
        if fecha_fin <= fecha_inicio:
            raise ValueError(
                "La fecha final debe ser posterior a la fecha inicial"
            )

    @staticmethod
    def _validar_tipo(tipo: str) -> None:
        tipos_validos = {
            tipo_ausencia.value
            for tipo_ausencia in TipoAusenciaPersonal
        }

        if tipo not in tipos_validos:
            raise ValueError("Tipo de ausencia no válido")
        
    @staticmethod
    def _validar_fechas(
        fecha_inicio: datetime,
        fecha_fin: datetime
    ):

        if fecha_fin <= fecha_inicio:

            raise ValueError(
                "La fecha final debe ser "
                "posterior a la inicial"
            )

    @staticmethod
    def _validar_sin_solapes(
        db: Session,
        usuario_id: int,
        fecha_inicio: datetime,
        fecha_fin: datetime,
        excluir_ausencia_id: int | None = None,
    ) -> None:
        solapadas = AusenciaPersonalRepository.get_solapadas(
            db,
            usuario_id,
            fecha_inicio,
            fecha_fin,
            excluir_ausencia_id,
        )

        if solapadas:
            raise ValueError(
                "El usuario ya tiene una ausencia que se solapa "
                "con ese intervalo"
            )

    @staticmethod
    def create(
        db: Session,
        datos: AusenciaPersonalCreate,
    ):
        usuario = UsuarioRepository.get_by_id(db, datos.usuario_id)
        if usuario is None:
            raise ValueError("Usuario no encontrado")

        AusenciaPersonalService.validar_intervalo(
            datos.fecha_inicio,
            datos.fecha_fin,
        )
        AusenciaPersonalService._validar_tipo(datos.tipo)
        AusenciaPersonalService._validar_sin_solapes(
            db,
            datos.usuario_id,
            datos.fecha_inicio,
            datos.fecha_fin,
        )

        return AusenciaPersonalRepository.create(
            db,
            datos.model_dump(),
        )

    @staticmethod
    def update(
        db: Session,
        ausencia_id: int,
        datos: AusenciaPersonalUpdate,
    ):
        ausencia = AusenciaPersonalRepository.get_by_id(
            db,
            ausencia_id,
        )
        if ausencia is None:
            raise ValueError("Ausencia no encontrada")

        cambios = datos.model_dump(exclude_unset=True)
        fecha_inicio = cambios.get("fecha_inicio", ausencia.fecha_inicio)
        fecha_fin = cambios.get("fecha_fin", ausencia.fecha_fin)
        tipo = cambios.get("tipo", ausencia.tipo)

        AusenciaPersonalService.validar_intervalo(
            fecha_inicio,
            fecha_fin,
        )
        AusenciaPersonalService._validar_tipo(tipo)
        AusenciaPersonalService._validar_sin_solapes(
            db,
            ausencia.usuario_id,
            fecha_inicio,
            fecha_fin,
            excluir_ausencia_id=ausencia.id,
        )

        return AusenciaPersonalRepository.update(
            db,
            ausencia,
            cambios,
        )

    @staticmethod
    def delete(
        db: Session,
        ausencia_id: int,
    ) -> None:
        ausencia = AusenciaPersonalRepository.get_by_id(
            db,
            ausencia_id,
        )
        if ausencia is None:
            raise ValueError("Ausencia no encontrada")

        AusenciaPersonalRepository.delete(db, ausencia)

    @staticmethod
    def eliminar(
        db: Session,
        ausencia_id: int
    ):

        ausencia = (
            AusenciaPersonalRepository.get_by_id(
                db,
                ausencia_id
            )
        )

        if ausencia is None:
            raise ValueError(
                "Ausencia no encontrada"
            )

        try:

            AusenciaPersonalRepository.delete(
                db,
                ausencia
            )

            db.commit()

        except Exception:

            db.rollback()
            raise
