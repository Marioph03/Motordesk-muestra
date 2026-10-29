"""Servicio del registro horario diario y mensual."""

from calendar import monthrange
from datetime import date

from sqlalchemy.orm import Session

from app.models.registro_jornada import RegistroJornada
from app.models.usuario import Usuario


class RegistroJornadaService:
    @staticmethod
    def listado(db: Session, mes: str) -> list[dict]:
        try:
            ano, numero_mes = map(int, mes.split("-"))
            inicio, fin = date(ano, numero_mes, 1), date(ano, numero_mes, monthrange(ano, numero_mes)[1])
        except (TypeError, ValueError):
            raise ValueError("El mes debe tener el formato AAAA-MM")
        usuarios = db.query(Usuario).filter(Usuario.activo.is_(True)).order_by(Usuario.nombre, Usuario.apellidos).all()
        registros = db.query(RegistroJornada).filter(RegistroJornada.fecha.between(inicio, fin)).all()
        por_clave = {(registro.usuario_id, registro.fecha): registro for registro in registros}
        resultado = []
        for usuario in usuarios:
            for dia in range(1, fin.day + 1):
                fecha = date(ano, numero_mes, dia)
                registro = por_clave.get((usuario.id, fecha))
                resultado.append(RegistroJornadaService._respuesta(usuario, fecha, registro))
        return resultado

    @staticmethod
    def marcar(db: Session, usuario_id: int, fecha: date, presente: bool) -> dict:
        usuario = db.get(Usuario, usuario_id)
        if usuario is None or not usuario.activo:
            raise ValueError("Trabajador no encontrado o inactivo")
        registro = db.query(RegistroJornada).filter_by(usuario_id=usuario_id, fecha=fecha).first()
        if registro is None:
            registro = RegistroJornada(usuario_id=usuario_id, fecha=fecha)
            db.add(registro)
        registro.presente = presente
        registro.hora_entrada = usuario.hora_entrada_predeterminada if presente else None
        registro.hora_salida = usuario.hora_salida_predeterminada if presente else None
        db.commit()
        db.refresh(registro)
        return RegistroJornadaService._respuesta(usuario, fecha, registro)

    @staticmethod
    def actualizar_horario(db: Session, usuario_id: int, entrada, salida) -> dict:
        if entrada >= salida:
            raise ValueError("La salida debe ser posterior a la entrada")
        usuario = db.get(Usuario, usuario_id)
        if usuario is None:
            raise ValueError("Trabajador no encontrado")
        usuario.hora_entrada_predeterminada = entrada
        usuario.hora_salida_predeterminada = salida
        db.commit()
        return {"usuario_id": usuario.id, "hora_entrada": entrada, "hora_salida": salida}

    @staticmethod
    def _respuesta(usuario, fecha, registro) -> dict:
        return {"id": registro.id if registro else None, "usuario_id": usuario.id, "nombre": usuario.nombre, "apellidos": usuario.apellidos, "fecha": fecha, "presente": registro.presente if registro else False, "hora_entrada": registro.hora_entrada if registro else None, "hora_salida": registro.hora_salida if registro else None, "hora_entrada_predeterminada": usuario.hora_entrada_predeterminada, "hora_salida_predeterminada": usuario.hora_salida_predeterminada}
