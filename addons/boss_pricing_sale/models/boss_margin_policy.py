from odoo import api, fields, models

from odoo.addons.boss_pricing.models.boss_tariff import DIRECTIONS, LOAD_TYPES, TRANSPORT_MODES

from .boss_shipment_route import BUSINESSES

# Minimum margin control of Odoo 17 (summary_utils + x_profit_group_rules, x_profit_types, x_concept_profits,
# x_profit_exceptions), roadmap item 15. A warning, never a block (P01/P02-a). Margin = sale - expected cost.
# Odoo 17 BASE_MARGIN_PERC (10 %) and VALUE_ROUND (10): company settings since 04/11/2026 (res.company).
from .account_incoterms import FREIGHT_PAYMENTS  # noqa: E402  (prepaid / collect is said on each incoterm)


class BossMarginFamily(models.Model):
    """A group of services checked together (Odoo 17 «profit types»: Transporte, Flete, Gastos Locales…), or a policy
    for single services outside those groups (Odoo 17 «concept profits»: taxes exact, no margin, may lose…)."""
    _name = "boss.margin.family"
    _description = "Minimum margin: service group or policy"
    _order = "kind, sequence, id"

    name = fields.Char(required=True, translate=True)
    sequence = fields.Integer(default=10)
    active = fields.Boolean(default=True)
    kind = fields.Selection(
        [("group", "Group of services (its margin is checked together, by the rules)"),
         ("policy", "Policy of single services (each checked on its own)")], required=True, default="group")
    product_ids = fields.Many2many("product.product", string="Services", domain=[("type", "=", "service")])
    rule_ids = fields.One2many("boss.margin.rule", "family_id", "Rules")
    percent = fields.Float("Minimum margin (% of cost)", digits=(5, 2),
                           help="Policy: minimum margin of each of its services. Group: used when no rule applies "
                                "(empty: the default 10 %).")
    allow_negative = fields.Boolean("May lose money", help="Policy: no warning even with a negative margin.")
    exact = fields.Boolean("Re-invoiced exactly", help="Policy: sale must equal cost (taxes and duties paid on behalf).")


class BossMarginRule(models.Model):
    """Minimum margin of a group of services in a kind of shipment (Odoo 17 x_profit_group_rules and the condition
    formulas of x_profit_conditions_co, as fields). Minimum = the higher of a % of the cost (optionally capped per
    container) and an amount (fixed, per container of each size or per chargeable kg)."""
    _name = "boss.margin.rule"
    _description = "Minimum margin rule"
    _order = "family_id, sequence, id"

    name = fields.Char(required=True, translate=True)
    sequence = fields.Integer(default=10)
    active = fields.Boolean(default=True)
    family_id = fields.Many2one("boss.margin.family", "Group of services", required=True, ondelete="cascade",
                                domain=[("kind", "=", "group")])
    # conditions (empty = any)
    transport_mode = fields.Selection(TRANSPORT_MODES, "Transport mode")
    load_type = fields.Selection(LOAD_TYPES, "Load type")
    business = fields.Selection(BUSINESSES, "Business of")
    direction = fields.Selection(DIRECTIONS, "Direction")
    freight_payment = fields.Selection(FREIGHT_PAYMENTS, "Freight", help="From the incoterm: C and D terms prepaid, "
                                       "E and F terms collect.")
    # minimum
    percent = fields.Float("% of the cost", digits=(5, 2))
    cap_per_container = fields.Float("The % at most, per container")
    min_amount = fields.Float("At least (amount)")
    min_per_container = fields.Float("At least, per container")
    min_per_container_20 = fields.Float("At least, per 20' container")
    min_per_container_40 = fields.Float("At least, per 40'/45' container")
    min_per_kg = fields.Float("At least, per chargeable kg", digits=(12, 4))

    def _boss_matches(self, ctx):
        self.ensure_one()
        return all(not self[name] or self[name] == ctx.get(name)
                   for name in ("transport_mode", "load_type", "business", "direction", "freight_payment"))

    def _boss_target(self, cost, ctx):
        """Minimum margin of the group for a cost (0 when nothing is bought, as in Odoo 17)."""
        self.ensure_one()
        if cost <= 0:
            return 0.0
        containers = ctx.get("containers_20", 0) + ctx.get("containers_40", 0)
        part = self.percent / 100 * cost
        if self.cap_per_container:
            part = min(part, self.cap_per_container * containers)
        amount = max(self.min_amount, self.min_per_container * containers,
                     self.min_per_container_20 * ctx.get("containers_20", 0)
                     + self.min_per_container_40 * ctx.get("containers_40", 0),
                     self.min_per_kg * (ctx.get("chargeable_kg") or 0.0))
        return max(part, amount)


class BossMarginException(models.Model):
    """A minimum margin agreed apart (Odoo 17 x_profit_exceptions): for a customer, a carrier, prepaid freight or
    always; on a group of services or on given services."""
    _name = "boss.margin.exception"
    _description = "Minimum margin exception"
    _order = "sequence, id"

    name = fields.Char(required=True)
    sequence = fields.Integer(default=10)
    active = fields.Boolean(default=True)
    customer_id = fields.Many2one("res.partner", "Customer", domain=[("is_company", "=", True)])
    carrier_id = fields.Many2one("res.partner", "Main carrier", domain=[("is_company", "=", True)])
    freight_payment = fields.Selection(FREIGHT_PAYMENTS, "Freight")
    family_id = fields.Many2one("boss.margin.family", "Group of services", domain=[("kind", "=", "group")])
    product_ids = fields.Many2many("product.product", string="Services")
    force_amount = fields.Boolean("Minimum amount")
    amount = fields.Float("Amount")
    force_percent = fields.Boolean("Minimum %")
    percent = fields.Float("% of the cost", digits=(5, 2))
    allow_negative = fields.Boolean("May lose money", help="With no minimum set, a negative margin is accepted too.")

    def _boss_matches(self, ctx):
        self.ensure_one()
        if self.customer_id and self.customer_id != ctx.get("customer"):
            return False
        if self.carrier_id and self.carrier_id.id not in ctx.get("carrier_ids", ()):
            return False
        return not self.freight_payment or self.freight_payment == ctx.get("freight_payment")

    def _boss_target(self, cost):
        """None when it sets nothing; -inf when it accepts a loss."""
        self.ensure_one()
        if not self.force_amount and not self.force_percent:
            return None
        value = 0.0
        if self.force_amount:
            value = max(value, self.amount)
        if self.force_percent:
            value = max(value, self.percent / 100 * cost)
        return float("-inf") if value == 0 and self.allow_negative else value


class BossMarginPolicy(models.AbstractModel):
    """One check for the quotation and the file: [(label, sale, cost, minimum, problem or False, exception or False)]."""
    _name = "boss.margin.policy"
    _description = "Minimum margin check"

    @api.model
    def _boss_check(self, by_product, ctx, money, exact_problems=None):
        """by_product: {product: (sale, cost)} in one currency; ctx: shipment data; money: formatter. exact_problems:
        a list that receives the problems of the amounts paid on behalf not re-invoiced exactly (a VAT rule, kept apart
        from the margin)."""
        _ = self.env._
        company = ctx.get("company") or self.env.company
        DEFAULT_RATE, TOLERANCE = company.boss_margin_default_rate / 100, company.boss_margin_tolerance
        families = self.env["boss.margin.family"].search([])
        groups = families.filtered(lambda f: f.kind == "group")
        policies = families - groups
        exceptions = self.env["boss.margin.exception"].search([]).filtered(lambda e: e._boss_matches(ctx))
        results = []

        def verdict(label, sale, cost, target, exact=False, allow_negative=False, exception=None, strict_loss=False):
            margin = sale - cost
            problem = False
            if exact and abs(margin) >= 0.01:
                problem = _("%(group)s: paid on behalf, re-invoiced %(sale)s for %(cost)s paid (must be equal)",
                            group=label, sale=money(sale), cost=money(cost))
                if exact_problems is not None:
                    exact_problems.append(problem)
            elif strict_loss and not allow_negative and margin <= -0.01:
                problem = _("%(group)s: loss of %(loss)s", group=label, loss=money(-margin))
            elif not allow_negative and target != float("-inf") and margin + TOLERANCE < target:
                problem = _("%(group)s: margin %(margin)s, minimum %(minimum)s", group=label, margin=money(margin),
                            minimum=money(target))
            results.append((label, sale, cost, target, problem, exception and exception.name))

        grouped = set()
        for family in groups:
            mine = {p: v for p, v in by_product.items() if p in family.product_ids}
            if not mine:
                continue
            grouped |= set(mine)
            sale, cost = sum(v[0] for v in mine.values()), sum(v[1] for v in mine.values())
            if not sale and not cost:
                continue
            rules = family.rule_ids.filtered(lambda r: r._boss_matches(ctx))
            target = (max(r._boss_target(cost, ctx) for r in rules) if rules
                      else (family.percent / 100 if family.percent else DEFAULT_RATE) * cost)
            exception = exceptions.filtered(lambda e, f=family: e.family_id == f)[:1]
            forced = exception._boss_target(cost) if exception else None
            if forced is not None:
                target = forced
            verdict(family.name, sale, cost, target, exception=exception if forced is not None else None)
        for product, (sale, cost) in by_product.items():
            if product in grouped or (not sale and not cost):
                continue
            policy = policies.filtered(lambda f, p=product: p in f.product_ids)[:1]
            exact = policy.exact or product.boss_paid_on_behalf
            target = (policy.percent / 100 if policy else DEFAULT_RATE) * cost
            label = product.default_code or product.display_name
            margin = sale - cost
            allow_negative = policy.allow_negative
            failing = (exact and abs(margin) >= 0.01) or (not allow_negative and (
                margin <= -0.01 or margin + TOLERANCE < target))
            exception = exceptions.filtered(lambda e, p=product: p in e.product_ids)[:1] if failing else None
            forced = exception._boss_target(cost) if exception else None
            if forced is not None:
                verdict(label, sale, cost, forced, exception=exception)
            else:  # Odoo 17: a single service at a loss is flagged even within the tolerance
                verdict(label, sale, cost, target, exact=exact, allow_negative=allow_negative, strict_loss=True)
        return results

    @api.model
    def _boss_context(self, record, containers, chargeable_kg, freight_payment=None):
        """Shipment data of a quotation or a file (same field names, with or without the «boss_» prefix)."""
        def get(name):
            return record[f"boss_{name}"] if f"boss_{name}" in record._fields else record[name]
        incoterm = record.incoterm if "incoterm" in record._fields else record.incoterm_id
        carrier = get("carrier_id")
        return {
            "company": record.company_id,
            "transport_mode": get("transport_mode"), "load_type": get("load_type"), "business": get("business"),
            "direction": get("direction"),
            "freight_payment": freight_payment or incoterm.boss_freight_payment or False,
            "customer": record.partner_id.commercial_partner_id,
            "carrier_ids": set(carrier._boss_carrier_family_ids()) if carrier else set(),
            "containers_20": sum(q for size, q in containers if size == "20"),
            "containers_40": sum(q for size, q in containers if size in ("40", "45")),
            "chargeable_kg": chargeable_kg,
        }
