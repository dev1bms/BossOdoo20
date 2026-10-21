"""The single matching + compute service (ADR-002). Every screen asks here; nothing else selects prices."""
from dataclasses import dataclass, field
from decimal import Decimal

from odoo import api, models
from odoo.tools.misc import formatLang

from .. import engine
from .boss_tariff_line import BASES, PERCENT_BASES

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


def _plain(value):
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, list):
        return [_plain(v) for v in value]
    return value


@dataclass
class CostResult:
    status: str
    amount: float = 0.0  # line total in `currency`
    currency: object = None  # res.currency record or None
    line: object = None  # boss.tariff.line record (empty when no price)
    candidates: object = None  # boss.tariff.line records involved (conflict, approval)
    missing: list = field(default_factory=list)  # input names
    steps: list = field(default_factory=list)  # [[code, {values}]] JSON-ready


class BossPricing(models.AbstractModel):
    _name = "boss.pricing"
    _description = "BOSS pricing service"

    @api.model
    def _input_labels(self):
        _ = self.env._
        return {
            "direction": _("Direction"), "transport_mode": _("Transport mode"), "load_type": _("Load type"),
            "carrier_id": _("Carrier"), "port_id": _("Spanish port / airport"), "customer_id": _("Customer"),
            "country_id": _("Country abroad"), "tariff_date": _("Planned date (ETA import / ETD export)"),
            "quantity": _("Quantity"), "containers": _("Containers"), "container_size": _("Container size"),
            "container_type_id": _("Container type"), "gross_kg": _("Gross weight"), "volume_m3": _("Volume"),
            "pallets": _("Pallets"), "goods_value": _("Goods value"), "duties_amount": _("Customs duties"),
            "storage_days": _("Days (estimate)"), "km": _("Kilometres"),
            "volumetric_factor": _("Volumetric factor of the tariff"),
            "base_services": _("Base services of the same supplier"),
            "base_services_currency": _("Base services in the tariff currency"),
        }

    @api.model
    def price_cost(self, product, uom, inputs, day):
        """Expected supplier cost of one quotation line.

        inputs: shipment inputs named like the tariff scope (direction, carrier_id, port_id, country_id...)
        plus line inputs (line_qty, container_size, container_type_id) and measures (containers,
        gross_kg, volume_m3, storage_days, related_costs...). `day` picks the tariff version.
        """
        Line = self.env["boss.tariff.line"]
        mode = product.boss_pricing_mode
        if mode == "own":
            return CostResult("ok", line=Line, candidates=Line)
        if mode == "manual":
            return CostResult("manual", line=Line, candidates=Line)
        if mode != "tariff" or product.boss_cost_method not in engine.METHODS:
            return CostResult("not_ready", line=Line, candidates=Line)

        lines = Line.search([("product_id", "=", product.id), ("uom_id", "=", uom.id),
                             ("tariff_id.active", "=", True)])
        currencies = lines.tariff_id.currency_id
        decimals = currencies[:1].decimal_places if len(currencies) == 1 else 2
        res = engine.price([ln._to_engine_rule() for ln in lines], inputs, day, decimals)
        line = Line.browse(res.rule.id) if res.rule else Line
        return CostResult(
            status=res.status.value,
            amount=float(res.amount) if res.amount is not None else 0.0,
            currency=line.currency_id if line else None,
            line=line,
            candidates=Line.browse([r.id for r in res.candidates]),
            missing=res.missing,
            steps=[[code, {k: _plain(v) for k, v in values.items()}] for code, values in res.steps],
        )

    # --- explanation ---------------------------------------------------------------------------

    def _num(self, value, currency=None):
        if currency:
            return formatLang(self.env, value, currency_obj=currency)
        return formatLang(self.env, value, digits=2).rstrip("0").rstrip(",.") or "0"

    def _explain_step(self, code, v, currency, uom):
        _ = self.env._
        bases = dict(BASES)
        money = lambda x: self._num(x, currency)  # noqa: E731
        if code == "per_unit":
            text = _("%(qty)s x %(price)s per %(uom)s = %(amount)s", qty=self._num(v["quantity"]),
                     price=money(v["unit_price"]), uom=uom.name, amount=money(v["amount"]))
            if v.get("basis") not in (None, "line") and v["raw"] != v["quantity"]:
                text = _("%(basis)s %(raw)s -> %(qty)s units. ", basis=bases.get(v["basis"], v["basis"]),
                         raw=self._num(v["raw"]), qty=self._num(v["quantity"])) + text
            return text
        if code == "max_of_bases":
            return _("Larger of %(q1)s x %(p1)s = %(a1)s and %(q2)s x %(p2)s = %(a2)s",
                     q1=self._num(v["quantity"]), p1=money(v["unit_price"]), a1=money(v["amount_1"]),
                     q2=self._num(v["quantity_2"]), p2=money(v["unit_price_2"]), a2=money(v["amount_2"]))
        if code == "bracket":
            limit = self._num(v["up_to"]) if v["up_to"] else _("no limit")
            return _("Bracket up to %(limit)s for %(qty)s: %(amount)s", limit=limit, qty=self._num(v["quantity"]),
                     amount=money(v["amount"]))
        if code == "floor_previous":
            return _("not below the previous bracket: %s", money(v["amount"]))
        if code == "per_container":
            return _("x %(count)s containers = %(amount)s", count=self._num(v["count"]), amount=money(v["amount"]))
        if code == "percent":
            return _("%(rate)s%% of %(base_kind)s %(base)s = %(amount)s", rate=self._num(v["rate"]),
                     base_kind=dict(PERCENT_BASES).get(v["base_kind"], v["base_kind"]), base=money(v["base"]),
                     amount=money(v["amount"]))
        if code == "time":
            return _("%(days)s days, %(free)s free, %(charged)s charged x %(qty)s = %(amount)s",
                     days=v["days"], free=v["free"], charged=v["charged_days"], qty=self._num(v["quantity"]),
                     amount=money(v["amount"]))
        if code == "minimum":
            return _("(minimum applied: %s)", money(v["amount"]))
        if code == "maximum":
            return _("(maximum applied: %s)", money(v["amount"]))
        if code == "out_of_range":
            return _("The quantity is outside the brackets of the supplier document.")
        return ""

    @api.model
    def explain(self, product, uom, status, amount, line, candidates, missing, steps):
        """Plain-language explanation of a cost result, in the reader's language."""
        _ = self.env._
        if status == "ok" and product.boss_pricing_mode == "own":
            return _("BOSS own fee: no supplier cost.")
        if status == "ok":
            tariff = line.tariff_id
            text = " ".join(filter(None, (self._explain_step(code, values, tariff.currency_id, uom)
                                          for code, values in steps or [])))
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
            if steps and steps[0][0] == "out_of_range":
                return _("The quantity is outside the brackets of the supplier document: ask the supplier.")
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
