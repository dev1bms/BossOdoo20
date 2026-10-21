"""BOSS pricing engine: pure Python, no Odoo import (ADR-002).

`price()` is the only entry point used by Odoo: select the rule, then compute it.
"""
from decimal import ROUND_HALF_UP, Decimal

from .methods import METHODS, MissingInput, dec
from .model import Match, Result, Rule, Status
from .selection import select

__all__ = ["Match", "Result", "Rule", "Status", "price", "select"]


def price(rules, shipment, day, quantity, decimals=2):
    """Price one service on one charge basis for one shipment.

    rules: engine Rules of this service and charge basis (any state/validity).
    shipment: dict of shipment inputs used by rule conditions.
    day: date that picks the tariff version (None = not known yet).
    quantity: quantity in the charge basis (None or <= 0 = not known yet).
    decimals: rounding of the result (currency precision), ROUND_HALF_UP.
    """
    result = select(rules, shipment, day)
    if result.status is not Status.OK:
        return result
    rule = result.rule
    result.currency = rule.currency
    if rule.on_request:
        result.status = Status.ON_REQUEST
        return result
    if quantity is None or dec(quantity) <= 0:
        result.status, result.missing = Status.MISSING_INPUT, ["quantity"]
        return result
    result.quantity = dec(quantity)
    try:
        amount, steps = METHODS[rule.method](rule.params, result.quantity)
    except MissingInput as exc:
        result.status, result.missing = Status.MISSING_INPUT, exc.names
        return result
    result.amount = amount.quantize(Decimal(1).scaleb(-decimals), rounding=ROUND_HALF_UP)
    result.steps = steps
    return result
