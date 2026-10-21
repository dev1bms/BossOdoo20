"""Calculation methods. One function per method; the differences between services are data.

Every method returns (amount, steps) with `amount` before rounding, or raises MissingInput.
Minimum and maximum always apply to the line total (ADR-002 §Methods).
"""
from decimal import Decimal


class MissingInput(Exception):
    def __init__(self, *names):
        super().__init__(", ".join(names))
        self.names = list(names)


def dec(value):
    return value if isinstance(value, Decimal) else Decimal(str(value))


def _bounded(amount, params, steps):
    minimum, maximum = params.get("min_amount"), params.get("max_amount")
    if minimum and amount < dec(minimum):
        amount = dec(minimum)
        steps.append(("minimum", {"amount": amount}))
    if maximum and amount > dec(maximum):
        amount = dec(maximum)
        steps.append(("maximum", {"amount": amount}))
    return amount


def per_unit(params, quantity):
    """Unit price x quantity in the line's charge basis (container 40', BL, shipment...)."""
    unit_price = dec(params["unit_price"])
    amount = unit_price * quantity
    steps = [("per_unit", {"quantity": quantity, "unit_price": unit_price, "amount": amount})]
    return _bounded(amount, params, steps), steps


METHODS = {
    "per_unit": per_unit,
}
