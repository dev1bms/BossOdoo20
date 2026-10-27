"""The single matching + compute service (ADR-002). Every screen asks here; nothing else selects prices."""
from dataclasses import dataclass, field
from datetime import UTC, datetime
from decimal import Decimal
from zoneinfo import ZoneInfo

from odoo import api, models
from odoo.tools.misc import format_date, formatLang

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


def _plain(value):
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, list):
        return [_plain(v) for v in value]
    if isinstance(value, dict):
        return {k: _plain(v) for k, v in value.items()}
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
            "foreign_port_id": _("Port / airport abroad"),
            "country_id": _("Country abroad"), "tariff_date": _("Planned date (ETA import / ETD export)"),
            "quantity": _("Quantity"), "containers": _("Containers"), "container_size": _("Container size"),
            "container_type_id": _("Container type"), "gross_kg": _("Gross weight"), "volume_m3": _("Volume"),
            "pallets": _("Pallets"), "goods_value": _("Goods value"), "duties_amount": _("Customs duties"),
            "storage_days": _("Days (estimate)"), "km": _("Kilometres"),
            "storage_end": _("End of the period after its start (exit date and time)"),
            "awb_kg": _("Chargeable weight of the air waybill"), "state_id": _("Province (inland)"),
            "volumetric_factor": _("Volumetric factor of the tariff"),
            "chargeable_kg": _("Chargeable weight (gross weight and volume)"),
            "base_services": _("Base services of the same supplier"),
            "base_services_currency": _("Base services in the tariff currency"),
            "tariff_use": _("Demo or real customer"),
        }

    @api.model
    def _warehouse_period(self, start, end, port=None):
        """Inputs of an actual period for time-based prices: Odoo datetimes (UTC) as aware datetimes of the
        warehouse (peninsula, or the Canary Islands), so that weekdays and calendar days are the warehouse's
        and the hours stay exact. Empty when the period has not ended."""
        if not start or not end:
            return {}
        tz = ZoneInfo("Atlantic/Canary" if port and port.canary_islands else "Europe/Madrid")
        return {"storage_start": start.replace(tzinfo=UTC).astimezone(tz),
                "storage_end": end.replace(tzinfo=UTC).astimezone(tz)}

    @api.model
    def price_cost(self, product, uom, inputs, day, company=None, simulate=None):
        """Expected supplier cost of one quotation line.

        inputs: shipment inputs named like the tariff scope (direction, carrier_id, port_id, country_id...)
        plus line inputs (line_qty, container_size, container_type_id) and measures (containers,
        gross_kg, volume_m3, storage_days, related_costs...). `day` picks the tariff version.
        Only tariffs of `company` (default: current company) apply, whoever asks (also under sudo).
        simulate: tariffs not approved yet that count as approved in this call only ("Test pricing").
        """
        Line = self.env["boss.tariff.line"]
        mode = product.boss_pricing_mode
        if mode == "own":
            return CostResult("ok", line=Line, candidates=Line)
        if mode not in ("tariff", "manual"):
            return CostResult("not_ready", line=Line, candidates=Line)
        # The method belongs to each supplier price line (one service, different suppliers, different methods).

        lines = Line.search([("product_id", "=", product.id), ("uom_id", "=", uom.id),
                             ("tariff_id.active", "=", True),
                             ("tariff_id.company_id", "=", (company or self.env.company).id)]
                            + ([("tariff_id.partner_id", "=", inputs["supplier_id"])] if inputs.get("supplier_id") else []))
        currencies = lines.tariff_id.currency_id
        decimals = currencies[:1].decimal_places if len(currencies) == 1 else 2
        res = engine.price([ln._to_engine_rule(simulate) for ln in lines], inputs, day, decimals)
        if mode == "manual" and res.status.value != "ok":
            # Manual amount (freight offer...): a person types the cost of each shipment, unless an approved
            # supplier price applies to this route (weekly freight rate entered from a quotation, ADR-007).
            return CostResult("manual", line=Line, candidates=Line)
        line = Line.browse(res.rule.id) if res.rule else Line
        if (res.status.value == "no_tariff" and inputs.get("tariff_use") != "demo"
                and lines.filtered("tariff_id.is_demo")):
            res.steps = [("demo_only", {})]  # say why: the prices that exist are demo prices
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
        line_fields = self.env["boss.tariff.line"]._fields  # labels in the user's language
        bases = dict(line_fields["basis"]._description_selection(self.env))
        percent_bases = dict(line_fields["percent_base"]._description_selection(self.env))
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
                     base_kind=percent_bases.get(v["base_kind"], v["base_kind"]), base=money(v["base"]),
                     amount=money(v["amount"]))
        if code == "time":
            return self._explain_time(v, money)
        if code == "minimum":
            return _("(minimum applied: %s)", money(v["amount"]))
        if code == "minimum_per_day":
            return _("(minimum of %s applied to each charged day)", money(v["amount"]))
        if code == "readings_undecided":
            return self._explain_readings(v, money)
        if code == "readings_agree":
            return _("(the readings not decided yet give the same amount for this shipment)")
        if code == "maximum":
            return _("(maximum applied: %s)", money(v["amount"]))
        if code == "out_of_range":
            return _("The quantity is outside the brackets of the supplier document.")
        return ""

    def _explain_readings(self, v, money):
        """Amount of each reading the document leaves open, when they differ for this shipment."""
        _ = self.env._
        labels = {("period_unit", "24h"): _("periods of 24 h"), ("period_unit", "calendar"): _("calendar days"),
                  ("tier_mode", "positional"): _("tiers day by day"),
                  ("tier_mode", "whole_stay"): _("whole stay at the tier reached"),
                  ("round_up", False): _("pro rata per 100 kg"), ("round_up", True): _("per 100 kg or fraction")}
        # one row per amount, naming only the readings that set it (the others give the same amount either way)
        groups = {}
        for reading in v["readings"]:
            groups.setdefault(reading["amount"], []).append(reading)
        names = [k for k in v["readings"][0] if k != "amount"]
        rows = []
        for amount, readings in sorted(groups.items()):
            fixed = [k for k in names if len({r[k] for r in readings}) == 1
                     and len({r[k] for r in v["readings"]}) > 1]
            label = ", ".join(labels.get((k, readings[0][k]), f"{k} {readings[0][k]}") for k in fixed)
            rows.append(f"· {label or _('other readings')}: {money(amount)}")
        return "\n".join([_("Not priced automatically: the supplier document can be read in ways the business has not "
                            "decided yet, and they give different amounts for this shipment (from %(low)s to "
                            "%(high)s). Enter the cost by hand (supplier bill or written quote) until it is decided "
                            "(questions P29, P40, P41).", low=money(v["low"]), high=money(v["high"]))] + rows)

    def _explain_time(self, v, money):
        """Period, free rule and charged days of a time-based price, saying what is estimated or actual."""
        _ = self.env._
        if v.get("free_hours"):
            free = _("%s h free", v["free_hours"])
        else:
            free = _("%s days free", v.get("free_days") or 0)
        unit = _("periods of 24 h") if v.get("period_unit") == "24h" else _("calendar days")
        if "period_unit" in (v.get("open") or v.get("agreed") or []):
            unit = _("24-hour periods or calendar days, not decided")
        if v.get("estimate", True):
            head = _("Estimate: %(days)s days", days=v["days"])
        else:
            start, end = (datetime.fromisoformat(v[k]) for k in ("start", "end"))  # warehouse local time
            head = _("Actual period %(start)s → %(end)s (%(hours)s h): %(days)s %(unit)s", start=start.strftime(
                "%d/%m/%Y %H:%M"), end=end.strftime("%d/%m/%Y %H:%M"), hours=self._num(v["hours"]), days=v["days"],
                unit=unit)
        rule = {"saturday_until_monday": _("arrival on a Saturday and exit on Monday at the latest: free"),
                "friday_monday": _("arrival on a Friday and exit on Monday: %s", free),
                "friday_extra_day": _("arrival on a Friday: %s", free)}.get(v.get("rule"))
        if v.get("open"):  # the amount depends on the readings listed next
            return head + "."
        if v.get("rule") == "saturday_until_monday" or not v["charged_days"]:
            text = _("%(head)s; %(rule)s → nothing charged (inside the free period, no minimum).", head=head,
                     rule=rule or free)
        elif v.get("free_mode") == "threshold":
            text = _("%(head)s; %(rule)s exceeded → charged from the start: %(charged)s days x %(qty)s units = "
                     "%(amount)s", head=head, rule=rule or free, charged=v["charged_days"],
                     qty=self._num(v["quantity"]), amount=money(v["amount"]))
        else:
            text = _("%(head)s; %(rule)s deducted → %(charged)s days charged x %(qty)s units = %(amount)s",
                     head=head, rule=rule or free, charged=v["charged_days"], qty=self._num(v["quantity"]),
                     amount=money(v["amount"]))
        for name in v.get("not_assumed") or []:
            text = text.rstrip(".") + ". " + {
                "friday_monday": _("Arrival on a Friday: the supplier's longer free period for a Monday exit is not "
                                   "assumed in an estimate; it is applied with the actual exit."),
                "saturday_until_monday": _("Arrival on a Saturday: free until Monday if collected by then; not "
                                           "assumed in an estimate, applied with the actual exit."),
            }[name]
        return text

    @api.model
    def explain(self, product, uom, status, amount, line, candidates, missing, steps):
        """Plain-language explanation of a cost result, in the reader's language."""
        _ = self.env._
        if status == "ok" and product.boss_pricing_mode == "own":
            return _("BOSS own fee: no supplier cost.")
        if status == "ok" or (status == "not_ready" and line and dict(steps or []).get("readings_undecided")):
            tariff = line.tariff_id
            text = " ".join(filter(None, (self._explain_step(code, values, tariff.currency_id, uom)
                                          for code, values in steps or [])))
            source = _("Source: %(tariff)s v%(version)s (%(supplier)s), valid from %(start)s",
                       tariff=tariff.name, version=tariff.version, supplier=tariff.partner_id.name,
                       start=format_date(self.env, tariff.valid_from))
            if tariff.valid_to:
                source += _(" to %s", format_date(self.env, tariff.valid_to))
            if line.scope_display:
                source += _(", applies to %s", line.scope_display)
            if tariff.document_reference or line.document_page:
                source += _(", document %(doc)s page %(page)s",
                            doc=tariff.document_reference or "-", page=line.document_page or "-")
            return f"{text}\n{source}"
        if status == "missing_input":
            labels = self._input_labels()
            return _("Shipment data missing: %s. Fill it in (quotation 'Shipment' tab or test panel) to price this "
                     "service.", ", ".join(labels.get(m, m) for m in missing))
        if status == "no_tariff":
            if steps and steps[0][0] == "out_of_range":
                return _("The quantity is outside the brackets of the supplier document: ask the supplier.")
            if steps and steps[0][0] == "demo_only":
                return _("Only demo prices exist for %(service)s per %(uom)s: they price demo customers only, "
                         "never a real customer. Enter the supplier's real price, or choose a demo customer to "
                         "try the demo price.", service=product.display_name, uom=uom.name)
            if steps and steps[0][0] == "no_rule_on_date":
                day = steps[0][1].get("date")
                return _("There are supplier prices of %(service)s per %(uom)s, but none is valid on %(date)s "
                         "(expired or not started): ask the supplier for the current document, or check the "
                         "planned date.", service=product.display_name, uom=uom.name,
                         date=format_date(self.env, day) if day else "-")
            return _("No approved supplier price of %(service)s per %(uom)s applies to this shipment.",
                     service=product.display_name, uom=uom.name)
        if status == "pending_approval":
            return _("Supplier price entered but not approved yet: %s",
                     ", ".join(candidates.mapped("display_name")))
        if status == "on_request":
            return _("The supplier document says 'on request' (%s): ask the supplier.", line.display_name)
        if status == "conflict" and len(candidates.partner_id) > 1:
            return _("Several suppliers have a price for this shipment: %s. Choose the supplier on the line (column "
                     "Supplier) to price it with that supplier's tariff.",
                     ", ".join(candidates.partner_id.mapped("name")))
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
