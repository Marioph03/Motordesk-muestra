from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, Field

class OrdenInternaCreate(BaseModel):
    titulo: str = Field(min_length=1, max_length=200)
    categoria: str = "OTRO"
    vehiculo_id: int | None = None
    referencia_activo: str | None = None
    descripcion: str = Field(min_length=1)
    responsable_id: int | None = None

class LineaOrdenInternaCreate(BaseModel):
    tipo: str
    articulo_stock_id: int | None = None
    descripcion: str = Field(min_length=1, max_length=500)
    cantidad: Decimal = Field(default=Decimal("1"), gt=0)
    coste_unitario: Decimal = Field(default=Decimal("0"), ge=0)

class LineaOrdenInternaResponse(BaseModel):
    id: int
    tipo: str
    articulo_stock_id: int | None
    referencia: str | None
    descripcion: str
    cantidad: Decimal
    coste_unitario: Decimal
    model_config = {"from_attributes": True}

class OrdenInternaResponse(BaseModel):
    id: int
    numero: str
    titulo: str
    categoria: str
    vehiculo_id: int | None
    referencia_activo: str | None
    descripcion: str
    estado: str
    responsable_id: int | None
    coste_total: Decimal
    fecha_apertura: datetime
    fecha_cierre: datetime | None
    lineas: list[LineaOrdenInternaResponse] = []
    model_config = {"from_attributes": True}
