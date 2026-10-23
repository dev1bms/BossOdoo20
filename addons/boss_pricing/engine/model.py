"""Plain data structures of the pricing engine (no Odoo import: testable with python -m unittest).

See docs/adr/002-pricing-model.md.
"""
from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal
from enum import Enum


class Status(str, Enum):
    """Explicit outcome of pricing one service on one charge basis (ADR-002 §Results)."""

    OK = "ok"
    MISSING_INPUT = "missing_input"  # a shipment input needed to decide or compute is empty
    NO_TARIFF = "no_tariff"  # no approved supplier price applies
    PENDING_APPROVAL = "pending_approval"  # a matching price exists but is not approved yet
    ON_REQUEST = "on_request"  # the supplier document says "on request": no amount
    CONFLICT = "conflict"  # several prices apply and nothing decides between them
    NOT_READY = "not_ready"  # the price reads two ways with different amounts: pending a business decision


class Match(Enum):
    YES = 1
    NO = 2
    UNKNOWN = 3  # the shipment does not have the input this condition needs


@dataclass(frozen=True)
class Rule:
    """One supplier price line, flattened for the engine."""

    id: int
    product_id: int
    uom_id: int
    method: str
    currency: str
    lineage_id: int  # all versions of one supplier tariff share it
    version: int = 1
    valid_from: date | None = None
    valid_to: date | None = None
    approved: bool = False
    on_request: bool = False
    priority: int = 10  # lower wins; set on purpose by the approver
    # condition name -> accepted values; a missing key means "any"
    conditions: dict = field(default_factory=dict)
    params: dict = field(default_factory=dict)  # method parameters read from the supplier document

    def valid_on(self, day):
        return (not self.valid_from or self.valid_from <= day) and (
            not self.valid_to or day <= self.valid_to
        )


@dataclass
class Result:
    status: Status
    rule: Rule | None = None
    quantity: Decimal | None = None
    amount: Decimal | None = None  # line total in `currency`
    currency: str | None = None
    missing: list = field(default_factory=list)  # names of the missing inputs
    candidates: list = field(default_factory=list)  # rules involved (conflict, approval)
    steps: list = field(default_factory=list)  # (code, values) to explain the computation

    @property
    def unit_amount(self):
        if self.amount is None or not self.quantity:
            return None
        return self.amount / self.quantity
