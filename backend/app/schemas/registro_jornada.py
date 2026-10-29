from datetime import date, time
from pydantic import BaseModel


class HorarioJornadaUpdate(BaseModel):
    hora_entrada: time
    hora_salida: time


class MarcajeJornadaCreate(BaseModel):
    usuario_id: int
    fecha: date
    presente: bool


class RegistroJornadaResponse(BaseModel):
    id: int | None = None
    usuario_id: int
    nombre: str
    apellidos: str
    fecha: date
    presente: bool
    hora_entrada: time | None = None
    hora_salida: time | None = None
    hora_entrada_predeterminada: time
    hora_salida_predeterminada: time
