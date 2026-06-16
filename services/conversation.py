from datetime import UTC, datetime

from core.database import get_conversation, save_conversation
from models.conversation import ConversationRecord, ConversationState
from models.nlu import Intent, NluResult, SlotsGlobales
from services.nlu_rules import parse_message


def process_message(phone: str, text: str) -> tuple[ConversationRecord, NluResult]:
    record = get_conversation(phone)
    nlu = parse_message(text, state=record.state)

    record.message_count += 1
    record.last_message_at = datetime.now(UTC)
    record.needs_human = nlu.needs_human
    record.slots = _merge_slots(record.slots, nlu.slots_globales)
    record.state = _next_state(record.state, nlu)

    save_conversation(record)
    return record, nlu


def _merge_slots(existing: SlotsGlobales, incoming: SlotsGlobales) -> SlotsGlobales:
    return SlotsGlobales(
        combo_id=incoming.combo_id or existing.combo_id,
        cantidad=incoming.cantidad or existing.cantidad,
        modulo=incoming.modulo or existing.modulo,
    )


def _next_state(current: ConversationState, nlu: NluResult) -> ConversationState:
    intent_types = {i.type for i in nlu.intents}

    if "saludo" in intent_types and current in {"handoff", "closed"}:
        return "idle"

    if nlu.needs_human or "hablar_humano" in intent_types:
        return "handoff"

    if "despedida" in intent_types and current in {"idle", "confirming", "clarifying_combo"}:
        return "closed"

    if "combo_compra" in intent_types:
        combo_intent = next(i for i in nlu.intents if i.type == "combo_compra")
        combo_id = combo_intent.args.get("combo_id")
        if combo_id:
            return "confirming"

    if current == "clarifying_combo" and "desconocido" in intent_types:
        return "clarifying_combo"

    if "consulta_precio" in intent_types and "combo_compra" not in intent_types:
        return "clarifying_combo"

    if current == "handoff":
        return "handoff"

    if current == "closed":
        return "idle"

    return current if current != "idle" else "idle"


def get_record(phone: str) -> ConversationRecord:
    return get_conversation(phone)
