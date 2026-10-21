"""Small helpers shared by measures and methods."""
from decimal import Decimal


class MissingInput(Exception):
    """A shipment input (or a tariff parameter) needed to compute is empty: never guessed."""

    def __init__(self, *names):
        super().__init__(", ".join(names))
        self.names = list(names)


class OutOfRange(Exception):
    """The quantity is outside what the supplier document prices (e.g. above the last bracket)."""


def dec(value):
    return value if isinstance(value, Decimal) else Decimal(str(value))


def bounded(amount, params, steps):
    """Minimum and maximum always apply to the line total."""
    minimum, maximum = params.get("min_amount"), params.get("max_amount")
    if minimum and amount < dec(minimum):
        amount = dec(minimum)
        steps.append(("minimum", {"amount": amount}))
    if maximum and amount > dec(maximum):
        amount = dec(maximum)
        steps.append(("maximum", {"amount": amount}))
    return amount
