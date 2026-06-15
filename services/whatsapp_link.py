import os
from urllib.parse import quote

from models.nlu import Intent, NluResult
from services.catalog import AGENCIA, combo_price_display, get_combo

WHATSAPP_MODE_LINK = "link"
WHATSAPP_MODE_API = "api"


def get_whatsapp_mode() -> str:
    mode = os.getenv("WHATSAPP_MODE", WHATSAPP_MODE_LINK).strip().lower()
    if mode in (WHATSAPP_MODE_LINK, WHATSAPP_MODE_API):
        return mode
    return WHATSAPP_MODE_LINK


def is_api_mode() -> bool:
    return get_whatsapp_mode() == WHATSAPP_MODE_API


def normalize_wa_phone(phone: str | None = None) -> str:
    raw = phone or AGENCIA.whatsapp_phone
    return "".join(char for char in raw if char.isdigit())


def build_whatsapp_url(message: str, phone: str | None = None) -> str:
    target = normalize_wa_phone(phone)
    return f"https://wa.me/{target}?text={quote(message, safe='')}"


INTENT_MESSAGES: dict[str, str] = {
    "consulta_precio": (
        "Hola, consulto desde la web de Point Once (Agencia TA, San Juan). "
        "Quisiera recibir información actualizada sobre precios, combos y opciones de financiación."
    ),
    "consulta_licencia": (
        "Hola, ya tengo mi equipo y quisiera consultar el precio de la licencia de Point Once. "
        "Mi PC cumple Windows 10/11, 8 GB RAM, SSD 256 GB e i3 10.ª gen. "
        "¿Podemos instalar el mismo día?"
    ),
    "consulta_stock": (
        "Hola, consulto plazos de entrega de equipos Point Once. "
        "Entiendo que los combos se piden a proveedor y con seña la entrega suele ser en menos de una semana. "
        "¿Qué combo tienen disponible?"
    ),
    "modulo_locales": (
        "Hola, me interesa el módulo de Locales de Point Once para administrar varias sucursales "
        "desde un solo sistema. ¿Podemos conversar sobre la implementación?"
    ),
    "modulo_caucion": (
        "Hola, consulto sobre el módulo de Caución en Point Once. "
        "Necesito gestionar depósitos y garantías en mi comercio."
    ),
    "modulo_excel_central": (
        "Hola, me interesa la funcionalidad de datos generados para Excel Central en Point Once. "
        "Quisiera saber cómo exportar reportes y consolidar información."
    ),
    "modulo_demanda_estado": (
        "Hola, consulto sobre la Demanda de Estado en Point Once. "
        "Necesito consultar y solicitar el estado de operaciones entre sucursales."
    ),
    "implementar": (
        "Hola, quiero implementar Point Once en mi comercio. "
        "¿Podemos coordinar para tenerlo funcionando lo antes posible?"
    ),
}


def message_for_intent(intent_type: str) -> str | None:
    return INTENT_MESSAGES.get(intent_type)


def build_combo_message(intent: Intent) -> str:
    combo_id = str(intent.args.get("combo_id", ""))
    cantidad = int(intent.args.get("cantidad", 1))
    combo = get_combo(combo_id)
    if combo is None:
        return (
            "Hola, consulto desde la web de Point Once. "
            "Me interesa un combo de caja. ¿Podemos confirmar opciones y precios?"
        )

    efectivo, _ = combo_price_display(combo, cantidad)
    if combo.has_cantidad and cantidad > 1:
        return (
            f"Hola, me interesan {cantidad} Puesto(s) Cymax Completo — total estimado: {efectivo}. "
            "Quisiera confirmar disponibilidad y coordinar la entrega."
        )
    return (
        f"Hola, me interesa el combo «{combo.nombre}» ({efectivo}). "
        "Quisiera confirmar disponibilidad y los próximos pasos para implementarlo."
    )


def build_consumer_message(user_text: str, nlu: NluResult, needs_human: bool) -> str:
    if needs_human:
        trimmed = user_text.strip()
        if trimmed:
            return (
                "Hola, consulto desde la web de Point Once. "
                f"Mi consulta: {trimmed}. Quisiera hablar con el equipo."
            )
        return (
            "Hola, consulto desde la web de Point Once. "
            "Quisiera recibir asesoramiento sobre el sistema de caja para mi comercio."
        )

    for intent in nlu.intents:
        if intent.type == "combo_compra":
            return build_combo_message(intent)
        preset = message_for_intent(intent.type)
        if preset:
            return preset

    trimmed = user_text.strip()
    if trimmed:
        return f"Hola, consulto desde la web de Point Once. {trimmed}"
    return (
        "Hola, consulto desde la web de Point Once. "
        "Quisiera recibir asesoramiento sobre el sistema de caja para mi comercio."
    )
