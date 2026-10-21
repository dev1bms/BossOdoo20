"""Ángel's VAT rules for sale lines (final, 31/08/2026; Odoo 19 docs/iva_rules.md). Pure functions.

1. Base class NS (not subject) or EX (exempt) is final.
2. NR, layer 1 (origin -> destination zones): stays NR only for PRO->PRO, CAN->PRO, COM->PRO,
   COM->COM, TER->PRO, TER->COM; any other pair -> EX.
3. NR, layer 2 (customer zone): PRO keeps NR; CAN, COM, TER -> EX.
4. A missing zone is pending, never guessed.
Zones: PRO = mainland Spain + Balearics, CAN = Canary Islands, COM = rest of the EU, TER = third countries.
"""

NR_PAIRS = {("PRO", "PRO"), ("CAN", "PRO"), ("COM", "PRO"), ("COM", "COM"), ("TER", "PRO"), ("TER", "COM")}
CANARY_STATE_CODES = {"GC", "TF"}
SPAIN_OUTSIDE_ZONES = {"CE", "ME"}  # Ceuta, Melilla (Odoo codes): zone not settled (P17) -> pending


def zone(country_code, state_code=None, eu_codes=frozenset(), canary=False):
    """Zone of a place, or None when it cannot be told."""
    if not country_code:
        return None
    if country_code == "ES":
        if canary or state_code in CANARY_STATE_CODES:
            return "CAN"
        if state_code in SPAIN_OUTSIDE_ZONES:
            return None
        return "PRO"
    return "COM" if country_code in eu_codes else "TER"


def vat_class(base_class, origin, destination, customer):
    """Return (class or None, trace list). None = pending (a zone is missing)."""
    if base_class in ("NS", "EX"):
        return base_class, [f"base {base_class}"]
    if not base_class:
        return None, ["service without VAT class"]
    if not origin or not destination:
        return None, ["origin or destination zone missing"]
    if (origin, destination) not in NR_PAIRS:
        return "EX", [f"base NR", f"{origin}->{destination}: EX"]
    if not customer:
        return None, ["base NR", f"{origin}->{destination}: NR", "customer zone missing"]
    if customer != "PRO":
        return "EX", ["base NR", f"{origin}->{destination}: NR", f"customer {customer}: EX"]
    return "NR", ["base NR", f"{origin}->{destination}: NR", "customer PRO: NR"]
