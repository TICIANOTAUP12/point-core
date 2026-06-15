import pytest

from services.catalog import COMBOS, combo_price_display, format_price, get_combo
from services.nlu_rules import parse_message


class TestCatalog:
    def test_combo_prices_match_landing(self) -> None:
        assert COMBOS["basico"].precio_efectivo == 855_000
        assert COMBOS["cymax"].precio_efectivo == 1_050_000
        assert COMBOS["mini"].precio_efectivo == 1_300_000

    def test_cymax_quantity_pricing(self) -> None:
        combo = get_combo("cymax")
        assert combo is not None
        efectivo, cuotas = combo_price_display(combo, 2)
        assert efectivo == "$2.100.000"
        assert cuotas == "6 cuotas de $504.000"

    def test_format_price(self) -> None:
        assert format_price(855000) == "$855.000"


class TestMandatoryPhrases:
    def test_hola_quiero_2_cymax(self) -> None:
        result = parse_message("hola quiero 2 cymax")
        types = {i.type for i in result.intents}
        assert "combo_compra" in types
        combo = next(i for i in result.intents if i.type == "combo_compra")
        assert combo.args["combo_id"] == "cymax"
        assert combo.args["cantidad"] == 2

    def test_cuanto_sale_licencia(self) -> None:
        result = parse_message("cuánto sale la licencia")
        types = {i.type for i in result.intents}
        assert "consulta_licencia" in types

    def test_tienen_stock(self) -> None:
        result = parse_message("tienen stock?")
        assert any(i.type == "consulta_stock" for i in result.intents)

    def test_precio_caucion_y_locales(self) -> None:
        result = parse_message("precio caución y locales")
        types = {i.type for i in result.intents}
        assert "modulo_caucion" in types
        assert "modulo_locales" in types

    def test_el_basico_clarifying(self) -> None:
        result = parse_message("el básico", state="clarifying_combo")
        combo = next(i for i in result.intents if i.type == "combo_compra")
        assert combo.args["combo_id"] == "basico"
        assert combo.args["cantidad"] == 1

    def test_hablar_humano(self) -> None:
        result = parse_message("quiero hablar con alguien")
        assert any(i.type == "hablar_humano" for i in result.intents)
        assert result.needs_human is True

    def test_gibberish(self) -> None:
        result = parse_message("asdkjhasd")
        assert any(i.type == "desconocido" for i in result.intents)
        assert result.needs_human is True


@pytest.mark.parametrize(
    "text,expected_type",
    [
        ("hola", "saludo"),
        ("buenas tardes", "saludo"),
        ("chau gracias", "despedida"),
        ("quiero implementar point once", "implementar"),
        ("necesito el modulo de excel central", "modulo_excel_central"),
        ("demanda de estado entre sucursales", "modulo_demanda_estado"),
        ("cuanto cuesta el mini pc", "combo_compra"),
        ("precio del puesto basico", "combo_compra"),
        ("me interesa 3 puestos cymax", "combo_compra"),
        ("hay disponibilidad de equipos", "consulta_stock"),
        ("consultar precios y financiacion", "consulta_precio"),
        ("solo software licencia point", "consulta_licencia"),
        ("modulo caucion depositos", "modulo_caucion"),
        ("administrar varias sucursales", "modulo_locales"),
        ("hablar con un asesor", "hablar_humano"),
        ("xyz qwerty", "desconocido"),
    ],
)
def test_phrase_intents(text: str, expected_type: str) -> None:
    result = parse_message(text)
    assert any(i.type == expected_type for i in result.intents), (
        f"'{text}' -> {[i.type for i in result.intents]}"
    )


class TestConversationFlow:
    def test_combo_purchase_state(self, temp_db: str) -> None:
        from services.conversation import process_message

        record, nlu = process_message("5491111111111", "quiero 2 cymax")
        assert record.state == "confirming"
        assert record.slots.combo_id == "cymax"
        assert record.slots.cantidad == 2
        assert any(i.type == "combo_compra" for i in nlu.intents)

    def test_handoff_state(self, temp_db: str) -> None:
        from services.conversation import process_message

        record, _ = process_message("5492222222222", "quiero hablar con alguien")
        assert record.state == "handoff"
        assert record.needs_human is True

    def test_clarifying_combo_transition(self, temp_db: str) -> None:
        from services.conversation import process_message

        record, _ = process_message("5493333333333", "cuanto sale")
        assert record.state == "clarifying_combo"

        record2, nlu2 = process_message("5493333333333", "el basico")
        assert record2.state == "confirming"
        assert any(i.type == "combo_compra" for i in nlu2.intents)


class TestResponder:
    def test_reply_uses_catalog_prices(self, temp_db: str) -> None:
        from services.conversation import process_message
        from services.responder import build_reply

        record, nlu = process_message("5494444444444", "precio del basico")
        reply = build_reply(record, nlu)
        assert "$855.000" in reply

    def test_multi_module_reply(self, temp_db: str) -> None:
        from services.conversation import process_message
        from services.responder import build_reply

        record, nlu = process_message("5495555555555", "precio caución y locales")
        reply = build_reply(record, nlu)
        assert "Multi Locales" in reply
        assert "Caución" in reply
