from models.catalog import (
    AgenciaInfo,
    Combo,
    LICENSE_INSTALL_REPLY,
    STOCK_DELIVERY_REPLY,
    SYSTEM_REQUIREMENTS_REPLY,
)

# Source of truth: Agencia_TA/src/app/App.tsx (puestos + CYMAX_UNIT_*)
COMBOS: dict[str, Combo] = {
    "basico": Combo(
        id="basico",
        nombre="Puesto Inicial Básico",
        precio_efectivo=855_000,
        cuotas="6 cuotas de $205.200",
        has_cantidad=False,
    ),
    "cymax": Combo(
        id="cymax",
        nombre="Puesto Cymax Completo",
        precio_efectivo=1_050_000,
        cuotas="6 cuotas de $252.000",
        has_cantidad=True,
    ),
    "mini": Combo(
        id="mini",
        nombre="Puesto Mini PC",
        precio_efectivo=1_300_000,
        cuotas="6 cuotas de $312.000",
        has_cantidad=False,
    ),
}

AGENCIA = AgenciaInfo()

__all__ = [
    "AGENCIA",
    "COMBOS",
    "LICENSE_INSTALL_REPLY",
    "STOCK_DELIVERY_REPLY",
    "SYSTEM_REQUIREMENTS_REPLY",
    "combo_price_display",
    "format_price",
    "get_combo",
    "list_combos",
]


def get_combo(combo_id: str) -> Combo | None:
    return COMBOS.get(combo_id)


def list_combos() -> list[Combo]:
    return list(COMBOS.values())


def format_price(amount: int) -> str:
    return f"${amount:,}".replace(",", ".")


def combo_price_display(combo: Combo, cantidad: int = 1) -> tuple[str, str]:
    qty = max(1, cantidad)
    if combo.has_cantidad:
        total = combo.precio_efectivo * qty
        cuota_unit = 252_000
        cuotas = f"6 cuotas de {format_price(cuota_unit * qty)}"
        return format_price(total), cuotas
    return format_price(combo.precio_efectivo), combo.cuotas
