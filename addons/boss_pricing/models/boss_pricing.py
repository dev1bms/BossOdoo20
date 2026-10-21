"""The single matching + compute service (ADR-002). Every screen asks here; nothing else selects prices."""
from dataclasses import dataclass, field

from odoo import api, models
from odoo.tools.misc import formatLang

from .. import engine

COST_STATUSES = [
    ("ok", "Priced"),
    ("missing_input", "Missing shipment data"),
    ("no_tariff", "No supplier price"),
    ("pending_approval", "Price waiting for approval"),
    ("on_request", "On request"),
    ("conflict", "Several prices apply"),
    ("not_ready", "Not priced automatically"),
    ("manual", "Manual amount"),
]


@dataclass
class CostResult:
    status: str
    quantity: float = 0.0
    amount: float = 0.0  # line total in `currency`
    currency: object = None  # res.currency record or None
    line: object = None  # boss.tariff.line record (empty when no price)
    candidates: object = None  # boss.tariff.line records involved (conflict, approval)
    missing: list = field(default_factory=list)  # shipment input names


class BossPricing(models.AbstractModel):
    _name = "boss.pricing"
    _description = "BOSS pricing service"

    @api.model
    def _input_labels(self):
        return {
            "direction": self.env._("Direction"),
            "transport_mode": self.env._("Transport mode"),
            "load_type": self.env._("Load type"),
            "carrier_id": self.env._("Carrier"),
            "port_id": self.env._("Port"),
            "customer_id": self.env._("Customer"),
            "tariff_date": self.env._("Planned date (ETA import / ETD export)"),
            "quantity": self.env._("Quantity"),
        }

    @api.model
    def price_cost(self, product, uom, quantity, shipment, day):
        """Expected supplier cost of `quantity` x `uom` of `product` for one shipment.

        shipment: dict of inputs named like the tariff scope (direction, transport_mode, load_type,
        carrier_id, port_id, customer_id); `day` picks the tariff version (None: unknown).
        """
        Line = self.env["boss.tariff.line"]
        mode = product.boss_pricing_mode
        if mode == "own":
            return CostResult("ok", quantity=quantity, line=Line, candidates=Line)
        if mode == "manual":
            return CostResult("manual", quantity=quantity, line=Line, candidates=Line)
        if mode != "tariff" or product.boss_cost_method not in engine.METHODS:
            return CostResult("not_ready", quantity=quantity, line=Line, candidates=Line)

        lines = Line.search([("product_id", "=", product.id), ("uom_id", "=", uom.id),
                             ("tariff_id.active", "=", True)])
        currency = lines.tariff_id.currency_id[:1]
        decimals = currency.decimal_places if currency else 2
        res = engine.price([ln._to_engine_rule() for ln in lines], shipment, day, quantity, decimals)
        line = Line.browse(res.rule.id) if res.rule else Line
        return CostResult(
            status=res.status.value,
            quantity=float(res.quantity) if res.quantity is not None else quantity,
            amount=float(res.amount) if res.amount is not None else 0.0,
            currency=line.currency_id if line else None,
            line=line,
            candidates=Line.browse([r.id for r in res.candidates]),
            missing=res.missing,
        )

    @api.model
    def explain(self, product, uom, status, quantity, amount, line, candidates, missing):
        """Plain-language explanation of a cost result, in the reader's language."""
        _ = self.env._
        if status == "ok" and product.boss_pricing_mode == "own":
            return _("BOSS own fee: no supplier cost.")
        if status == "ok":
            tariff = line.tariff_id
            text = _("%(qty)s x %(price)s per %(uom)s = %(amount)s",
                     qty=formatLang(self.env, quantity, digits=2), uom=uom.name,
                     price=formatLang(self.env, line.unit_price, currency_obj=tariff.currency_id),
                     amount=formatLang(self.env, amount, currency_obj=tariff.currency_id))
            if line.min_amount and quantity * line.unit_price < line.min_amount:
                text += " " + _("(minimum applied)")
            if line.max_amount and quantity * line.unit_price > line.max_amount:
                text += " " + _("(maximum applied)")
            source = _("Source: %(tariff)s v%(version)s (%(supplier)s), valid from %(start)s",
                       tariff=tariff.name, version=tariff.version, supplier=tariff.partner_id.name,
                       start=tariff.valid_from)
            if tariff.document_reference or line.document_page:
                source += _(", document %(doc)s page %(page)s",
                            doc=tariff.document_reference or "-", page=line.document_page or "-")
            return f"{text}\n{source}"
        if status == "missing_input":
            labels = self._input_labels()
            return _("Fill in on the quotation: %s", ", ".join(labels.get(m, m) for m in missing))
        if status == "no_tariff":
            return _("No approved supplier price of %(service)s per %(uom)s applies to this shipment.",
                     service=product.display_name, uom=uom.name)
        if status == "pending_approval":
            return _("Supplier price entered but not approved yet: %s",
                     ", ".join(candidates.mapped("display_name")))
        if status == "on_request":
            return _("The supplier document says 'on request' (%s): ask the supplier.", line.display_name)
        if status == "conflict":
            return _("Several supplier prices apply: %s. Choose the carrier, narrow a tariff scope or "
                     "set a priority.", ", ".join(candidates.mapped("display_name")))
        if status == "manual":
            return _("Manual amount: enter the expected cost of this shipment (e.g. the freight offer).")
        if product.boss_pricing_mode == "pending":
            return _("Pending business decision (%s): not priced automatically; enter the cost "
                     "manually if this quotation needs it.", product.boss_open_question or "-")
        method = dict(product._fields["boss_cost_method"]._description_selection(self.env))
        return _("Calculation '%s' is not available yet: enter the cost manually.",
                 method.get(product.boss_cost_method, product.boss_cost_method or "-"))
