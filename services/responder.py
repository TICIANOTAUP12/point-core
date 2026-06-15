from models.conversation import ConversationRecord, ConversationState
from models.nlu import Intent, NluResult
from services.catalog import AGENCIA, combo_price_display, format_price, get_combo, list_combos


def build_reply(record: ConversationRecord, nlu: NluResult) -> str:
    if record.state == "handoff" or nlu.needs_human:
        return _handoff_reply()

    intent_types = {i.type for i in nlu.intents}

    if "despedida" in intent_types:
        return "¡Gracias por escribirnos! Cualquier consulta, estamos por acá. 👋"

    parts: list[str] = []

    if "saludo" in intent_types:
        parts.append(
            f"¡Hola! Soy el asistente de Point Once ({AGENCIA.nombre}, {AGENCIA.ubicacion}). "
            "¿En qué te puedo ayudar?"
        )

    for intent in nlu.intents:
        if intent.type == "saludo":
            continue
        segment = _reply_for_intent(intent, record.state)
        if segment and segment not in parts:
            parts.append(segment)

    if not parts:
        if record.state == "clarifying_combo":
            return _clarify_combo_reply()
        return _handoff_reply()

    return "\n\n".join(parts)


def _reply_for_intent(intent: Intent, state: ConversationState) -> str:
    handlers = {
        "consulta_precio": _price_overview_reply,
        "consulta_licencia": _license_reply,
        "consulta_stock": _stock_reply,
        "modulo_locales": _modulo_reply,
        "modulo_caucion": _modulo_reply,
        "modulo_excel_central": _modulo_reply,
        "modulo_demanda_estado": _modulo_reply,
        "implementar": _implement_reply,
        "combo_compra": _combo_purchase_reply,
        "desconocido": lambda _: _clarify_combo_reply() if state == "clarifying_combo" else "",
    }
    handler = handlers.get(intent.type)
    if handler is None:
        return ""
    return handler(intent)


def _price_overview_reply(_: Intent) -> str:
    lines = ["Estos son nuestros combos con precios actualizados:"]
    for combo in list_combos():
        efectivo, cuotas = combo_price_display(combo)
        suffix = " (precio por puesto, podés pedir varios)" if combo.has_cantidad else ""
        lines.append(f"• {combo.nombre}: {efectivo} efectivo / {cuotas}{suffix}")
    lines.append("¿Cuál te interesa? (básico, cymax o mini)")
    return "\n".join(lines)


def _license_reply(_: Intent) -> str:
    return (
        "La licencia Point Once (solo software) tiene precio según tu equipo y necesidades. "
        "Te puedo derivar con el equipo para una cotización personalizada. "
        f"WhatsApp directo: +54 264 628-1854."
    )


def _stock_reply(_: Intent) -> str:
    return (
        "Tenemos stock disponible para entrega de los combos Cymax, Básico y Mini PC. "
        "¿Querés que te confirme disponibilidad de alguno en particular?"
    )


def _modulo_reply(intent: Intent) -> str:
    labels = {
        "modulo_locales": "Multi Locales (varias sucursales desde un solo sistema)",
        "modulo_caucion": "Gestión de Caución (depósitos y garantías integrados a la caja)",
        "modulo_excel_central": "Datos para Excel Central (reportes consolidados)",
        "modulo_demanda_estado": "Demanda de Estado (seguimiento de pedidos y movimientos)",
    }
    label = labels.get(intent.type, "este módulo")
    return (
        f"Sobre {label}: es un módulo adicional de Point Once. "
        "Te puedo dar más detalle o coordinar una demo con el equipo técnico."
    )


def _implement_reply(_: Intent) -> str:
    return (
        "¡Perfecto! Para implementar Point Once coordinamos instalación y capacitación. "
        "¿Ya elegiste un combo (básico, cymax o mini) o solo necesitás la licencia?"
    )


def _combo_purchase_reply(intent: Intent) -> str:
    combo_id = str(intent.args.get("combo_id", ""))
    cantidad = int(intent.args.get("cantidad", 1))
    combo = get_combo(combo_id)
    if combo is None:
        return _clarify_combo_reply()

    efectivo, cuotas = combo_price_display(combo, cantidad)
    qty_line = f" ({cantidad} puesto{'s' if cantidad > 1 else ''})" if combo.has_cantidad and cantidad > 1 else ""
    return (
        f"¡Genial! El {combo.nombre}{qty_line}:\n"
        f"• Efectivo/transferencia: {efectivo}\n"
        f"• Financiado: {cuotas}\n\n"
        "¿Confirmamos y te derivo con el equipo para los próximos pasos?"
    )


def _clarify_combo_reply() -> str:
    basico = get_combo("basico")
    cymax = get_combo("cymax")
    mini = get_combo("mini")
    if not all([basico, cymax, mini]):
        return _handoff_reply()
    b_efe, _ = combo_price_display(basico)
    c_efe, _ = combo_price_display(cymax)
    m_efe, _ = combo_price_display(mini)
    return (
        "¿Cuál combo te interesa?\n"
        f"• Básico — {b_efe}\n"
        f"• Cymax Completo — {c_efe} (podés pedir varios)\n"
        f"• Mini PC — {m_efe}"
    )


def _handoff_reply() -> str:
    return (
        f"Te derivo con el equipo de {AGENCIA.nombre}. "
        f"Podés escribirnos al WhatsApp {AGENCIA.whatsapp_phone} "
        f"({AGENCIA.ubicacion}) y te atiende una persona."
    )
