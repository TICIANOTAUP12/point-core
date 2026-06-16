import re
import unicodedata

from models.conversation import ConversationState
from models.nlu import Intent, IntentType, NluResult, SlotsGlobales

CONFIDENCE_THRESHOLD = 0.6

COMBO_ALIASES: dict[str, list[str]] = {
    "basico": ["basico", "básico", "inicial", "puesto inicial", "puesto basico"],
    "cymax": ["cymax", "completo", "puesto cymax", "cymax completo"],
    "mini": ["mini", "mini pc", "minipc", "ryzen", "puesto mini"],
}

INTENT_PATTERNS: list[tuple[IntentType, list[str], float]] = [
    ("hablar_humano", ["hablar con", "hablar con alguien", "persona", "humano", "asesor", "operador", "representante"], 0.92),
    ("consulta_licencia", ["licencia", "solo software", "solo el software", "precio de la licencia", "licencia point", "requisitos", "windows", "ram", "ssd", "i3"], 0.9),
    ("consulta_stock", ["stock", "disponibilidad", "tienen stock", "hay stock", "listos para entrega", "tienen disponible"], 0.88),
    ("modulo_locales", ["multi locales", "modulo locales", "módulo locales", "sucursales", "varios locales", "locales"], 0.85),
    ("modulo_caucion", ["modulo caucion", "módulo caución", "caucion", "caución", "deposito", "depósito", "garantia", "garantía"], 0.85),
    ("modulo_excel_central", ["excel central", "excel", "reportes consolidados", "datos para excel"], 0.85),
    ("modulo_demanda_estado", ["demanda de estado", "demanda estado", "estado de pedidos", "movimientos entre sucursales", "demanda"], 0.85),
    ("implementar", ["implementar", "instalar", "empezar hoy", "arrancar", "funcionando", "tenerlo funcionando"], 0.82),
    ("consulta_precio", ["precio", "precios", "promo", "promocion", "promoción", "oferta", "ofertas", "cuanto sale", "cuánto sale", "cuanto cuesta", "cuánto cuesta", "cuanto vale", "cuánto vale", "como es", "cómo es", "sale", "cuesta", "valor", "financiacion", "financiación", "cuotas"], 0.8),
    ("saludo", ["hola", "buenas", "buen dia", "buenos dias", "buenas tardes", "buenas noches", "que tal", "qué tal"], 0.9),
    ("despedida", ["chau", "adios", "adiós", "hasta luego", "nos vemos", "gracias chau", "bye"], 0.88),
]

PURCHASE_KEYWORDS = ["quiero", "me interesa", "comprar", "pedir", "solicitar", "necesito", "dame", "elijo", "elegi", "eligí"]


def normalize_text(text: str) -> str:
    lowered = text.lower().strip()
    normalized = unicodedata.normalize("NFD", lowered)
    without_accents = "".join(ch for ch in normalized if unicodedata.category(ch) != "Mn")
    collapsed = re.sub(r"\s+", " ", without_accents)
    collapsed = re.sub(r"(\d)\s*cyma+x+\w*", r"\1 cymax", collapsed)
    collapsed = re.sub(r"\bcyma+x+\w*\b", "cymax", collapsed)
    return collapsed


def extract_quantity(text: str) -> int | None:
    patterns = [
        r"\b(\d{1,2})\s*(?:puestos?|cymax|combos?)\b",
        r"\b(\d{1,2})cymax\b",
        r"\b(?:quiero|necesito|me interesan?)\s+(\d{1,2})\b",
        r"\b(\d{1,2})\s+x\b",
    ]
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            qty = int(match.group(1))
            if 1 <= qty <= 99:
                return qty
    return None


def detect_combo(text: str) -> tuple[str | None, float]:
    best_id: str | None = None
    best_score = 0.0
    for combo_id, aliases in COMBO_ALIASES.items():
        for alias in aliases:
            if alias in text:
                score = 0.95 if len(alias) > 5 else 0.88
                if score > best_score:
                    best_id = combo_id
                    best_score = score
    return best_id, best_score


def _match_intents(text: str) -> list[Intent]:
    found: list[Intent] = []
    for intent_type, keywords, confidence in INTENT_PATTERNS:
        for keyword in keywords:
            if keyword in text:
                found.append(Intent(type=intent_type, confidence=confidence, args={}))
                break

    combo_id, combo_conf = detect_combo(text)
    qty = extract_quantity(text)
    has_purchase = any(kw in text for kw in PURCHASE_KEYWORDS)
    intent_types = {i.type for i in found}

    if combo_id and (has_purchase or qty is not None):
        args: dict[str, object] = {"combo_id": combo_id, "cantidad": qty or 1}
        found.append(Intent(type="combo_compra", confidence=max(combo_conf, 0.9), args=args))
    elif combo_id and ("consulta_precio" in intent_types or qty is not None):
        args = {"combo_id": combo_id, "cantidad": qty or 1}
        found.append(Intent(type="combo_compra", confidence=combo_conf, args=args))
    elif combo_id:
        found.append(
            Intent(
                type="combo_compra",
                confidence=combo_conf,
                args={"combo_id": combo_id, "cantidad": qty or 1},
            )
        )

    if not found:
        if len(text) < 3 or re.fullmatch(r"[\W\d_]+", text):
            found.append(Intent(type="desconocido", confidence=0.2, args={}))
        else:
            found.append(Intent(type="desconocido", confidence=0.35, args={}))

    return _refine_intents(_dedupe_intents(found))


def _refine_intents(intents: list[Intent]) -> list[Intent]:
    types = {i.type for i in intents}
    refined = list(intents)

    if "consulta_licencia" in types:
        refined = [i for i in refined if i.type != "consulta_precio"]

    if "combo_compra" in types:
        refined = [i for i in refined if i.type not in {"consulta_precio", "saludo"}]

    if "hablar_humano" in types:
        refined = [i for i in refined if i.type not in {"saludo", "despedida"}]

    return refined


def _dedupe_intents(intents: list[Intent]) -> list[Intent]:
    by_type: dict[IntentType, Intent] = {}
    for intent in intents:
        existing = by_type.get(intent.type)
        if existing is None or intent.confidence > existing.confidence:
            by_type[intent.type] = intent
    return list(by_type.values())


def _build_slots(intents: list[Intent]) -> SlotsGlobales:
    slots = SlotsGlobales()
    for intent in intents:
        if intent.type == "combo_compra":
            slots.combo_id = str(intent.args.get("combo_id", slots.combo_id or "")) or slots.combo_id
            cantidad = intent.args.get("cantidad")
            if isinstance(cantidad, int):
                slots.cantidad = cantidad
        if intent.type.startswith("modulo_"):
            slots.modulo = intent.type.replace("modulo_", "")
    return slots


def _needs_human(intents: list[Intent], text: str) -> bool:
    intent_types = {i.type for i in intents}
    if "hablar_humano" in intent_types:
        return True
    ambiguous_modulos = sum(1 for i in intents if i.type.startswith("modulo_"))
    if ambiguous_modulos >= 3:
        return True
    if len(text) > 400:
        return True
    return False


def parse_message(text: str, state: ConversationState = "idle") -> NluResult:
    normalized = normalize_text(text)
    intents = _match_intents(normalized)

    if state == "clarifying_combo":
        combo_id, combo_conf = detect_combo(normalized)
        if combo_id:
            qty = extract_quantity(normalized) or 1
            intents = [
                Intent(
                    type="combo_compra",
                    confidence=max(combo_conf, 0.92),
                    args={"combo_id": combo_id, "cantidad": qty},
                )
            ]

    slots = _build_slots(intents)
    needs_human = _needs_human(intents, normalized)

    return NluResult(intents=intents, slots_globales=slots, needs_human=needs_human)
