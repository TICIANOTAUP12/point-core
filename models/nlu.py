from typing import Any, Literal

from pydantic import BaseModel, Field

IntentType = Literal[
    "consulta_precio",
    "consulta_licencia",
    "consulta_stock",
    "modulo_locales",
    "modulo_caucion",
    "modulo_excel_central",
    "modulo_demanda_estado",
    "implementar",
    "hablar_humano",
    "saludo",
    "despedida",
    "desconocido",
    "combo_compra",
]


class Intent(BaseModel):
    type: IntentType
    confidence: float = Field(ge=0.0, le=1.0)
    args: dict[str, Any] = Field(default_factory=dict)


class SlotsGlobales(BaseModel):
    combo_id: str | None = None
    cantidad: int | None = None
    modulo: str | None = None


class NluResult(BaseModel):
    intents: list[Intent]
    slots_globales: SlotsGlobales = Field(default_factory=SlotsGlobales)
    needs_human: bool = False
