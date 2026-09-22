from datetime import date, time
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field, EmailStr, field_validator, model_validator

class Input(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra='forbid')

class Login(Input):
    correo: EmailStr
    password: str = Field(min_length=8, max_length=128)

class Registro(Login):
    nombre: str = Field(min_length=2, max_length=80)

class Actividad(Input):
    asignatura: str = Field(min_length=2, max_length=80)
    descripcion: str = Field(default='', max_length=3000)
    prioridad: Literal['baja','media','alta'] = 'media'
    dificultad: int = Field(default=3, ge=1, le=5)
    tiempo_estimado: int = Field(default=60, ge=15, le=6000)

class Tarea(Actividad):
    titulo: str = Field(min_length=2, max_length=120)
    fecha_entrega: date
    estado: Literal['pendiente','completada'] = 'pendiente'

    @field_validator('fecha_entrega')
    @classmethod
    def fecha_valida(cls, value):
        if not 2000 <= value.year <= 2100: raise ValueError('Fecha fuera de rango')
        return value

class Evaluacion(Actividad):
    nombre: str = Field(min_length=2, max_length=120)
    fecha: date

    @field_validator('fecha')
    @classmethod
    def fecha_valida(cls, value):
        if not 2000 <= value.year <= 2100: raise ValueError('Fecha fuera de rango')
        return value

class Estado(Input):
    estado: Literal['pendiente','completada']

class Disponibilidad(Input):
    dias: list[int] = Field(min_length=1, max_length=7)
    llegada: time
    hasta: time
    minutos_diarios: int = Field(ge=30, le=480)
    descansos: bool = True
    asignaturas_dificiles: str = Field(default='', max_length=500)

    @model_validator(mode='after')
    def validar(self):
        if len(set(self.dias)) != len(self.dias) or any(d < 0 or d > 6 for d in self.dias):
            raise ValueError('Selecciona días válidos sin repetir')
        if self.llegada.second or self.hasta.second: raise ValueError('Usa horas y minutos')
        ventana=(self.hasta.hour*60+self.hasta.minute)-(self.llegada.hour*60+self.llegada.minute)
        if ventana < self.minutos_diarios: raise ValueError('Las horas disponibles no alcanzan para ese tiempo')
        return self

class Bloque(Input):
    fecha: date
    inicio: time
    fin: time
    tipo: Literal['tarea','evaluacion','descanso']
    actividad_id: int | None = None
    asignatura: str = Field(max_length=80)
    actividad: str = Field(min_length=1,max_length=500)

class Plan(Input):
    resumen: str = Field(min_length=1,max_length=1500)
    bloques: list[Bloque] = Field(min_length=1,max_length=100)
    advertencias: list[str] = Field(default_factory=list,max_length=30)
