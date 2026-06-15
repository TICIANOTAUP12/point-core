from pydantic import BaseModel, Field


class Combo(BaseModel):
    id: str
    nombre: str
    precio_efectivo: int
    cuotas: str
    has_cantidad: bool = False


class AgenciaInfo(BaseModel):
    whatsapp_phone: str = "542646281854"
    nombre: str = "Agencia TA"
    ubicacion: str = "San Juan, Argentina"
