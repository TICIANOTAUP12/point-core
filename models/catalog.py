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


STOCK_DELIVERY_REPLY = (
    "Los combos con equipos (Cymax, Básico y Mini PC) los pedimos a proveedor, "
    "así que hay una pequeña demora de gestión. "
    "Con la seña confirmada arrancamos de inmediato y la entrega del hardware "
    "suele ser en menos de una semana."
)

LICENSE_INSTALL_REPLY = (
    "Si solo necesitás la licencia (software), instalamos Point Once el mismo día "
    "en tu computadora, si cumple los requisitos mínimos."
)

SYSTEM_REQUIREMENTS_REPLY = (
    "Requisitos mínimos recomendados: Windows 10 u 11, 8 GB de RAM, "
    "SSD de 256 GB e Intel i3 de 10.ª generación (o equivalente)."
)
