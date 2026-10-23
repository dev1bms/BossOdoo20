"""BOSS pricing engine: pure Python, no Odoo import (ADR-002).

`price()` is the only entry point used by Odoo: select the rule, then compute it.
"""
from decimal import ROUND_HALF_UP, Decimal

from .methods import METHODS
from .methods_base import MissingInput, OutOfRange, Undecided, dec
from .model import Match, Result, Rule, Status
from .selection import select

__all__ = ["METHODS", "Match", "Result", "Rule", "Status", "price", "select"]


def price(rules, inputs, day, decimals=2):
    """Price one service on one charge basis for one shipment.

    rules: engine Rules of this service and charge basis (any state/validity).
    inputs: shipment inputs + line inputs (line_qty, container filter...) used by conditions and
        quantities.
    day: date that picks the tariff version (None = not known yet).
    decimals: rounding of the result (currency precision), ROUND_HALF_UP.
    """
    result = select(rules, inputs, day)
    if result.status is not Status.OK:
        return result
    rule = result.rule
    result.currency = rule.currency
    if rule.on_request:
        result.status = Status.ON_REQUEST
        return result
    try:
        amount, steps = METHODS[rule.method](rule.params, inputs)
    except MissingInput as exc:
        result.status = Status.MISSING_INPUT
        result.missing = ["quantity" if name == "line_qty" else name for name in exc.names]
        return result
    except OutOfRange:
        result.status, result.steps = Status.NO_TARIFF, [("out_of_range", {})]
        return result
    except Undecided as exc:
        result.status, result.steps = Status.NOT_READY, exc.steps
        return result
    if inputs.get("line_qty") not in (None, False, "") and dec(inputs["line_qty"]) <= 0:
        result.status, result.missing = Status.MISSING_INPUT, ["quantity"]
        return result
    result.quantity = dec(inputs.get("line_qty") or 0)
    result.amount = amount.quantize(Decimal(1).scaleb(-decimals), rounding=ROUND_HALF_UP)
    result.steps = steps
    return result
