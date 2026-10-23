"""Calculation methods (ADR-002 §4). One function per method; the differences between suppliers
and services are parameters read from the supplier document.

Signature: method(params, inputs) -> (amount before rounding, steps). `steps` explain the result.
Raise MissingInput when an input is empty and OutOfRange when the document does not price it.
"""
import itertools
import math
from datetime import UTC

from .measures import measure
from .methods_base import MissingInput, OutOfRange, Undecided, bounded, dec


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


FRIDAY, SATURDAY, MONDAY = 4, 5, 0


def _actual_period(params, inputs):
    """Actual stay from its start and end events (timezone-aware datetimes of the warehouse), or None.

    Hours are exact (UTC difference, daylight-saving safe); weekdays and calendar days are the warehouse's.
    period_unit '24h': started periods of 24 hours from the start («por 24 horas»); 'calendar': calendar
    days, the entry day and the exit day both counted («se contabiliza el día de entrada y el día de salida»).
    """
    start, end = inputs.get("storage_start"), inputs.get("storage_end")
    if not start or not end:
        return None
    if end < start:
        raise MissingInput("storage_end")  # an exit before the start is a typing error: never priced
    hours = dec((end.astimezone(UTC) - start.astimezone(UTC)).total_seconds()) / 3600
    gap = (end.date() - start.date()).days  # calendar days between the two dates
    periods = math.ceil(hours / 24) if params.get("period_unit") == "24h" else gap + 1
    return {"start": start, "end": end, "hours": hours, "gap": gap, "periods": periods}


def _franchise(params, actual, start_weekday):
    """Free limit as (hours or None, periods or None) and the supplier exception that set it.

    Free hours are compared with the exact hours of an actual stay; an estimate (days only) is free only when
    its whole days fit in the free hours. Supplier exceptions that depend on the exit day (Friday with a
    Monday exit, Saturday until Monday included) need the actual dates: an estimate never assumes them.
    """
    free_hours, free_days = int(params.get("free_hours") or 0), int(params.get("free_days") or 0)
    rule = None
    if params.get("friday_extra_day") and start_weekday == FRIDAY:  # any Friday start, whatever the exit day
        if free_hours:
            free_hours += 24
        else:
            free_days += 1
        rule = "friday_extra_day"
    if actual:
        start, end = actual["start"], actual["end"]
        if (params.get("friday_monday_free") and start.weekday() == FRIDAY and end.weekday() == MONDAY
                and actual["gap"] == 3):
            limit = int(params["friday_monday_free"])  # same unit as the franchise: hours, or days
            free_hours, free_days, rule = (limit, 0, "friday_monday") if free_hours else (0, limit, "friday_monday")
        if params.get("saturday_until_monday") and start.weekday() == SATURDAY and actual["gap"] <= 2:
            return None, None, "saturday_until_monday"  # free whatever the hours: exit on Monday at the latest
    return free_hours or None, free_days if not free_hours else None, rule


def _charged_positions(params, inputs, days, actual):
    """Positions (1 = first period) of the charged periods, the free limit and the rule applied."""
    free_hours, free_days, rule = _franchise(params, actual, inputs.get("start_weekday"))
    if rule == "saturday_until_monday":
        return range(0), {"rule": rule}
    if free_hours is not None:
        within = actual["hours"] <= free_hours if actual else days * 24 <= free_hours
        free_periods = free_hours // 24  # deduct: whole free periods (an estimate never rounds a free part up)
    else:
        within = days <= (free_days or 0)
        free_periods = free_days or 0
    free = {"rule": rule, "free_hours": free_hours, "free_days": free_days}
    if params.get("free_mode") == "threshold":
        return (range(0) if within else range(1, days + 1)), free
    if actual and free_hours is not None:  # deduct exact hours: periods started after the free hours
        count = math.ceil(max(actual["hours"] - free_hours, 0) / 24)
        return range(days - count + 1, days + 1), free
    return range(free_periods + 1, days + 1), free


def _day_prices(tiers, mode, days, charged):
    if mode == "whole_stay":
        return [dec(_bracket(tiers, dec(days))["unit_price"])] * len(charged)
    first = charged[0] if charged else 1
    position = (lambda day: day) if mode == "positional" else (lambda day: day - first + 1)
    return [dec(_bracket(tiers, dec(position(day)))["unit_price"]) for day in charged]


def _time_amount(prices, quantity, params, steps):
    """Total of the charged periods. The minimum applies to the stay (line total) or, when the document says so
    («mínimo … AWB/día», «/expedición/día»), to each charged period."""
    if params.get("min_per_day") and params.get("min_amount"):
        minimum = dec(params["min_amount"])
        days = [max(price * quantity, minimum) for price in prices]
        amount = sum(days, dec(0))
        if any(price * quantity < minimum for price in prices):
            steps.append(("minimum_per_day", {"amount": minimum}))
        return bounded(amount, {"max_amount": params.get("max_amount")}, steps)
    return bounded(sum(prices, dec(0)) * quantity, params, steps)


# Readings of a time-based price that a document may leave open: each one is set on the price, or 'undecided'.
READINGS = {"period_unit": ("24h", "calendar"), "tier_mode": ("positional", "whole_stay"), "round_up": (False, True)}


def time_based(params, inputs):
    """Storage / demurrage / port occupancy: quantity per period x price of each charged period.

    The stay is the actual one (storage_start/storage_end) when both events are known, else the estimate
    in days (storage_days; 0 is a deliberate estimate, empty is missing). free_mode 'deduct': only the
    periods after the free period are paid; 'threshold': once the free period is exceeded every period from
    the first is paid. Day tiers apply by the period's position since the start ('positional', «día 5 hasta
    el 7»), by the position after the free period ('relative', «5 días a 40, a partir de ahí 95») or with
    'whole_stay' the tier reached by the whole stay.

    A reading the document leaves open (day count, tiers, «por 100 kg» with or without «o fracción») is
    'undecided' on the price: every reading is computed; when they give the same amount it is priced, when
    they differ nothing is priced (Undecided) and the steps show each reading's amount.
    """
    open_ = {name: values for name, values in READINGS.items()
             if (params.get("round_undecided") if name == "round_up" else params.get(name) == "undecided")}
    if not open_:
        return _time_once(params, inputs)
    results = []
    for combination in itertools.product(*open_.values()):
        reading = dict(zip(open_, combination))
        amount, steps = _time_once({**params, **reading}, inputs)
        results.append((reading, amount, steps))
    amounts = {amount for _reading, amount, _steps in results}
    if len(amounts) == 1:
        reading, amount, steps = results[0]
        return amount, steps + [("readings_agree", {"open": sorted(open_)})]
    code, values = results[0][2][0]
    raise Undecided([(code, dict(values, open=sorted(open_))), ("readings_undecided", {
        "readings": [dict(reading, amount=amount) for reading, amount, _steps in results],
        "low": min(amounts), "high": max(amounts)})])


def _time_once(params, inputs):
    """time_based with every reading decided."""
    actual = _actual_period(params, inputs)
    if actual:
        days = actual["periods"]
    else:
        days = inputs.get("storage_days")
        if days is None or days == "":  # not indicated; 0 days indicated is a valid estimate
            raise MissingInput("storage_days")
        days = int(days)
    charged, free = _charged_positions(params, inputs, days, actual)
    quantity, raw = measure(params.get("basis") or "containers", inputs, params)
    tiers = params.get("brackets") or []
    mode = params.get("tier_mode") or "positional"
    values = {"days": days, "estimate": not actual, "charged_days": len(charged), "quantity": quantity, "raw": raw,
              "period_unit": params.get("period_unit") or "calendar", "free_mode": params.get("free_mode") or "deduct",
              **free}
    if actual:
        values.update(start=actual["start"].isoformat(timespec="minutes"),
                      end=actual["end"].isoformat(timespec="minutes"), hours=actual["hours"])
    else:
        weekday = inputs.get("start_weekday")
        values["start_weekday"] = weekday
        # exceptions that depend on the exit day: named so that the estimate says it did not assume them
        values["not_assumed"] = [name for name, day in (("friday_monday", FRIDAY), ("saturday_until_monday", SATURDAY))
                                 if weekday == day and params.get("friday_monday_free" if day == FRIDAY else name)]
    prices = _day_prices(tiers, mode, days, charged)
    steps = [("time", dict(values, day_prices=prices, amount=sum(prices, dec(0)) * quantity))]
    if not charged:
        return dec(0), steps  # inside the free period: a justified zero, minimum not applied
    return _time_amount(prices, quantity, params, steps), steps


METHODS = {
    "per_unit": per_unit,
    "max_of_bases": max_of_bases,
    "brackets": brackets,
    "percent": percent,
    "time": time_based,
}
