"""Calculation methods (ADR-002 §4). One function per method; the differences between suppliers
and services are parameters read from the supplier document.

Signature: method(params, inputs) -> (amount before rounding, steps). `steps` explain the result.
Raise MissingInput when an input is empty and OutOfRange when the document does not price it.
"""
from .measures import measure
from .methods_base import MissingInput, OutOfRange, bounded, dec


def per_unit(params, inputs):
    """Unit price x quantity (line quantity, containers, chargeable kg, tonnes or fraction...)."""
    quantity, raw = measure(params.get("basis") or "line", inputs, params)
    unit_price = dec(params["unit_price"])
    amount = unit_price * quantity
    steps = [("per_unit", {"basis": params.get("basis") or "line", "raw": raw, "quantity": quantity,
                           "unit_price": unit_price, "amount": amount})]
    return bounded(amount, params, steps), steps


def max_of_bases(params, inputs):
    """The larger of two priced bases, e.g. tonnes x price/t vs m³ x price/m³ (THC-LCL)."""
    first, raw1 = measure(params["basis"], inputs, params)
    second, raw2 = measure(params["basis_2"], inputs, params, prefix="b2_")
    a1, a2 = first * dec(params["unit_price"]), second * dec(params["unit_price_2"])
    amount = max(a1, a2)
    steps = [("max_of_bases", {"basis": params["basis"], "quantity": first, "unit_price": dec(params["unit_price"]),
                               "amount_1": a1, "basis_2": params["basis_2"], "quantity_2": second,
                               "unit_price_2": dec(params["unit_price_2"]), "amount_2": a2, "amount": amount})]
    return bounded(amount, params, steps), steps


def _bracket(brackets, value):
    """First bracket whose inclusive upper bound holds `value`; up_to 0/None = open last bracket."""
    for bracket in sorted(brackets, key=lambda b: (not b["up_to"], dec(b["up_to"] or 0))):
        if not bracket["up_to"] or value <= dec(bracket["up_to"]):
            return bracket
    raise OutOfRange()


def _bracket_amount(bracket, quantity):
    return dec(bracket.get("fixed_amount") or 0) + dec(bracket.get("unit_price") or 0) * quantity


def brackets(params, inputs):
    """Bracket table on one measure (weight, km, value, count). The unit price multiplies the
    whole quantity (not only the part above the previous bound). Above the last closed bracket the
    document gives no price. Optional: never below the previous bracket's top amount; per container."""
    quantity, raw = measure(params.get("basis") or "line", inputs, params)
    table = params.get("brackets") or []
    bracket = _bracket(table, quantity)
    amount = _bracket_amount(bracket, quantity)
    steps = [("bracket", {"quantity": quantity, "up_to": bracket["up_to"], "fixed_amount": bracket.get("fixed_amount"),
                          "unit_price": bracket.get("unit_price"), "amount": amount})]
    if params.get("floor_previous"):
        lower = [b for b in table if b["up_to"] and (not bracket["up_to"] or dec(b["up_to"]) < dec(bracket["up_to"]))]
        if lower:
            prev = max(lower, key=lambda b: dec(b["up_to"]))
            floor = _bracket_amount(prev, dec(prev["up_to"]))
            if amount < floor:
                amount = floor
                steps.append(("floor_previous", {"amount": amount}))
    if params.get("per_container"):
        count, _raw = measure("containers", inputs, params, prefix="none_")
        amount = bounded(amount, params, steps) * count
        steps.append(("per_container", {"count": count, "amount": amount}))
        return amount, steps
    return bounded(amount, params, steps), steps


def percent(params, inputs):
    """Rate % of a base: goods value, customs duties, or the cost of other services of the same
    supplier in the same currency (e.g. fuel surcharge on road transport)."""
    base_kind = params["percent_base"]
    if base_kind == "services":
        related = [c for c in inputs.get("related_costs") or []
                   if c["product_id"] in params.get("base_product_ids", ())
                   and c["supplier_id"] == params.get("supplier_id")]
        if not related:
            raise MissingInput("base_services")
        if any(c["currency"] != params.get("currency") for c in related):
            raise MissingInput("base_services_currency")
        base = sum(dec(c["amount"]) for c in related)
    else:
        base, _raw = measure(base_kind, inputs, params)
    rate = dec(params["rate"])
    amount = base * rate / 100
    steps = [("percent", {"base_kind": base_kind, "base": base, "rate": rate, "amount": amount})]
    return bounded(amount, params, steps), steps


def _free_days(params, inputs):
    """Free period in days. Free hours become whole days when only days are known (quotation)."""
    free = int(params.get("free_days") or 0)
    if params.get("free_hours"):
        free = -(-int(params["free_hours"]) // 24)  # ceil
    weekday = inputs.get("start_weekday")  # 0 = Monday
    if weekday == 4 and params.get("friday_extra_day"):
        free += 1
    if weekday == 5 and params.get("saturday_until_monday"):
        free = max(free, 3)
    return free


def time_based(params, inputs):
    """Storage / demurrage / port occupancy: quantity per day x price of each charged day.

    free_mode 'deduct': only the days after the free period are paid; 'threshold': once the free
    period is exceeded every day from day 1 is paid. Day tiers apply by the day's position since the
    start ('positional') or, with 'whole_stay', the tier reached by the whole stay prices every day.
    """
    days = inputs.get("storage_days")
    if days in (None, False, ""):
        raise MissingInput("storage_days")
    days = int(days)
    free = _free_days(params, inputs)
    if params.get("free_mode") == "threshold":
        charged = range(1, days + 1) if days > free else range(0)
    else:
        charged = range(free + 1, days + 1)
    quantity, raw = measure(params.get("basis") or "containers", inputs, params)
    tiers = params.get("brackets") or []
    if params.get("tier_mode") == "whole_stay":
        prices = [dec(_bracket(tiers, dec(days))["unit_price"])] * len(charged)
    else:
        prices = [dec(_bracket(tiers, dec(day))["unit_price"]) for day in charged]
    amount = sum(prices, dec(0)) * quantity
    steps = [("time", {"days": days, "free": free, "charged_days": len(charged), "quantity": quantity,
                       "raw": raw, "day_prices": prices, "amount": amount})]
    if not charged:
        return amount, steps  # inside the free period: a justified zero, minimum not applied
    return bounded(amount, params, steps), steps


METHODS = {
    "per_unit": per_unit,
    "max_of_bases": max_of_bases,
    "brackets": brackets,
    "percent": percent,
    "time": time_based,
}
