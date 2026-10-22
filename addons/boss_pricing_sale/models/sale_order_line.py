from odoo import api, fields, models
from odoo.exceptions import UserError
from odoo.tools.misc import formatLang

from odoo.addons.boss_pricing.models.boss_container_type import CONTAINER_SIZES
from odoo.addons.boss_pricing.models.boss_pricing import COST_STATUSES

from . import vat_rules
from .product_pricelist_item import BOSS_LINE_COST

SALE_STATUSES = [
    ("missing", "Sale price missing"),
    ("agreed", "Agreed price (pricelist)"),
    ("cost_based", "From the expected cost (pricelist rule)"),
    ("manual", "Entered by a person"),
    ("free", "Free of charge (confirmed)"),
]
VAT_STATUSES = [("ok", "Determined"), ("pending", "Pending")]
# Changing these on an accepted line is a re-pricing: only through the Re-price wizard (ADR-003).
FROZEN_FIELDS = {"product_id", "product_uom_id", "product_uom_qty", "price_unit", "discount", "purchase_price",
                 "boss_manual_cost", "boss_sale_free", "tax_ids", "boss_container_size", "boss_container_type_id"}
COST_FIELDS = ("boss_cost_status", "boss_cost_amount", "boss_cost_currency_id", "boss_tariff_line_id",
               "boss_cost_candidate_ids", "boss_cost_missing", "boss_cost_steps", "boss_cost_is_estimate")
SHIPMENT_DEPENDS = (
    "order_id.partner_id", "order_id.boss_direction", "order_id.boss_transport_mode", "order_id.boss_load_type",
    "order_id.boss_carrier_id", "order_id.boss_port_id", "order_id.boss_country_id", "order_id.boss_planned_date",
    "order_id.boss_inland_state_id", "order_id.boss_awb_kg",
    "order_id.boss_container_ids.size", "order_id.boss_container_ids.container_type_id",
    "order_id.boss_container_ids.quantity", "order_id.boss_gross_kg", "order_id.boss_volume_m3",
    "order_id.boss_pallets", "order_id.boss_goods_value", "order_id.boss_duties_amount",
    "order_id.boss_storage_days", "order_id.boss_storage_days_known",
    # percentage of other services of the same supplier (fuel surcharge on transport)
    "order_id.order_line.product_id", "order_id.order_line.product_uom_qty",
)


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    boss_pricing_mode = fields.Selection(related="product_id.boss_pricing_mode")
    boss_container_size = fields.Selection(CONTAINER_SIZES, "Container size",
                                           help="Containers of this size only. Empty: all sizes.")
    boss_container_type_id = fields.Many2one("boss.container.type", "Container type",
                                             help="Containers of this type only. Empty: all types.")
    boss_supplier_id = fields.Many2one(
        "res.partner", "Supplier",
        help="Supplier of this service. Only its tariffs price the line (handling, storage or road transport often "
        "come from another supplier than the carrier). Empty: any supplier whose tariff fits the shipment.")
    boss_cost_method = fields.Selection(related="product_id.boss_cost_method")
    boss_days_source = fields.Selection(
        [("shipment", "Days of the shipment"), ("estimate", "Estimate of this line"), ("actual", "Actual period (ended)")],
        "Days for this service", default="shipment", required=True,
        help="Time-based services: the days of the Shipment tab, an estimate for this line (e.g. port occupancy shorter "
        "than demurrage; 0 is a deliberate zero) or the actual period once it has ended.")
    boss_days = fields.Integer(
        "Days (line)", compute="_compute_boss_days", store=True, readonly=False, precompute=True,
        help="Days priced on this line: the days of the shipment unless an estimate of the line or the actual period "
        "is typed (typing a number makes it the estimate of this line).")
    boss_cost_status = fields.Selection(
        COST_STATUSES + [("currency", "Other currency, no conversion policy")], "Cost status",
        compute="_compute_boss_cost", store=True, copy=False, precompute=True)
    boss_cost_amount = fields.Monetary(
        "Expected cost", currency_field="boss_cost_currency_id", compute="_compute_boss_cost",
        store=True, copy=False, precompute=True,
        help="Expected supplier cost of the whole line, in the tariff currency.")
    boss_cost_currency_id = fields.Many2one("res.currency", compute="_compute_boss_cost", store=True, copy=False,
                                            precompute=True)
    boss_tariff_line_id = fields.Many2one("boss.tariff.line", "Supplier price", compute="_compute_boss_cost",
                                          store=True, copy=False, precompute=True, index="btree_not_null")
    boss_cost_candidate_ids = fields.Many2many(
        "boss.tariff.line", "boss_sale_line_cost_candidate_rel", "line_id", "tariff_line_id",
        "Prices involved", compute="_compute_boss_cost", store=True, copy=False, precompute=True)
    boss_cost_missing = fields.Char("Missing data", compute="_compute_boss_cost", store=True, copy=False,
                                    precompute=True)
    boss_cost_steps = fields.Json("Calculation steps", compute="_compute_boss_cost", store=True, copy=False,
                                  precompute=True)
    boss_cost_is_estimate = fields.Boolean(
        "Estimate", compute="_compute_boss_cost", store=True, copy=False, precompute=True,
        help="Time-based cost computed with the days assumed on the quotation; the actual cost is known "
        "when the period ends.")
    boss_cost_explanation = fields.Text("How the cost is computed", compute="_compute_boss_cost_explanation")
    boss_manual_cost = fields.Monetary(
        "Manual unit cost", currency_field="currency_id", copy=False,
        help="Expected cost per unit entered by a person when the service is not priced from a tariff "
        "(freight offer, amount paid on behalf of the customer...).")
    boss_manual_cost_note = fields.Char("Cost reference", copy=False, help="E.g. supplier offer number.")
    boss_price_frozen = fields.Boolean("Accepted price", readonly=True, copy=False)
    boss_sale_free = fields.Boolean(
        "Free of charge", copy=False,
        help="Confirms that a zero sale price is intended. Without it a zero price means 'missing'.")
    boss_sale_status = fields.Selection(SALE_STATUSES, "Sale price", compute="_compute_boss_sale_status")
    boss_sale_explanation = fields.Text("How the sale price is set", compute="_compute_boss_sale_status")
    boss_markup = fields.Float(
        "Markup on cost", compute="_compute_boss_markup",
        help="(Sale - cost) / cost. The margin shown by Odoo is (sale - cost) / sale.")
    boss_vat_class = fields.Selection([("NS", "NS"), ("EX", "EX"), ("NR", "NR")], "VAT class",
                                      compute="_compute_boss_vat", store=True, copy=False, precompute=True)
    boss_vat_status = fields.Selection(VAT_STATUSES, "VAT", compute="_compute_boss_vat", store=True, copy=False,
                                       precompute=True)
    boss_vat_trace = fields.Char("Why this VAT", compute="_compute_boss_vat", store=True, copy=False,
                                 precompute=True)
    boss_vat_tax_id = fields.Many2one("account.tax", "Odoo tax of the VAT case", compute="_compute_boss_vat",
                                      store=True, copy=False, precompute=True)

    @api.depends("boss_days_source", "order_id.boss_storage_days")
    def _compute_boss_days(self):
        for line in self:
            if line.boss_days_source == "shipment":
                line.boss_days = line.order_id.boss_storage_days

    @api.onchange("boss_days")
    def _onchange_boss_days(self):
        if self.boss_days_source == "shipment" and self.boss_days != self.order_id.boss_storage_days:
            self.boss_days_source = "estimate"

    def _boss_skip(self):
        """Lines whose price is frozen (accepted) and not being re-priced on purpose."""
        if self.env.context.get("boss_reprice"):
            return self.browse()
        return self.filtered("boss_price_frozen")

    def _boss_keep(self, *fnames):
        """Frozen lines keep their stored values when a dependency changes: a stored compute that
        assigns nothing makes the ORM write an empty value (odoo/orm/fields.py, "fallback to null")."""
        for line in self:
            for fname in fnames:
                line[fname] = line[fname]

    def _boss_lines(self):
        return self.filtered(lambda l: l.product_id.boss_pricing_mode and not l.display_type)

    @api.model_create_multi
    def create(self, vals_list):
        # The field default (1.0) wins over the compute on create: count the shipment explicitly.
        counted = [i for i, vals in enumerate(vals_list) if "product_uom_qty" not in vals]
        lines = super().create(vals_list)
        auto = self.browse([lines[i].id for i in counted])
        self.env.add_to_compute(self._fields["product_uom_qty"], auto)
        auto._recompute_recordset(["product_uom_qty"])
        # An explicit recompute does not notify the fields that depend on the quantity (cost, sale price, line
        # total, taxes): notify them like a write would, so nothing keeps the default quantity of 1.
        auto.modified(["product_uom_qty"])
        auto._boss_recompute_cost()
        return lines

    # --- quantity: charge bases counted from the shipment -------------------------------------------

    @api.depends("product_uom_id", "boss_container_size", "boss_container_type_id",
                 "order_id.boss_container_ids.size", "order_id.boss_container_ids.container_type_id",
                 "order_id.boss_container_ids.quantity", "order_id.boss_gross_kg", "order_id.boss_volume_m3",
                 "order_id.boss_pallets", "order_id.boss_awb_kg")
    def _compute_product_uom_qty(self):
        frozen = self._boss_skip()
        super(SaleOrderLine, self - frozen)._compute_product_uom_qty()
        frozen._boss_keep("product_uom_qty")
        for line in (self - frozen)._boss_lines():
            source = line.product_uom_id.boss_quantity_source
            if source in (False, "input"):
                continue
            quantity = line.order_id._boss_quantity(source, line.boss_container_size, line.boss_container_type_id)
            if quantity is not None:
                line.product_uom_qty = quantity

    # --- cost: one call to boss.pricing --------------------------------------------------------------

    def _boss_inputs(self):
        self.ensure_one()
        inputs = self.order_id._boss_shipment_inputs()
        inputs.update({"line_qty": self.product_uom_qty, "container_size": self.boss_container_size or None,
                       "container_type_id": self.boss_container_type_id.id or None,
                       "supplier_id": self.boss_supplier_id.id or None})
        if self.boss_days_source != "shipment":
            inputs["storage_days"] = self.boss_days
        return inputs

    def _boss_price(self, related_costs=None):
        self.ensure_one()
        inputs = self._boss_inputs()
        if related_costs is not None:
            inputs["related_costs"] = related_costs
        return self.env["boss.pricing"].price_cost(self.product_id, self.product_uom_id, inputs,
                                                   self.order_id.boss_planned_date, self.order_id.company_id)

    def _boss_related_costs(self):
        """Costs of the other lines of the order, for percentages on services of the same supplier."""
        self.ensure_one()
        related = []
        for sibling in (self.order_id.order_line - self)._boss_lines():
            if sibling.product_id.boss_cost_method == "percent":
                continue
            res = sibling._boss_price()
            if res.status == "ok" and res.line:
                related.append({"product_id": sibling.product_id.id, "supplier_id": res.line.partner_id.id,
                                "amount": res.amount, "currency": res.line.currency_id.name})
        return related

    @api.depends("product_id", "product_uom_id", "product_uom_qty", "currency_id", "boss_container_size",
                 "boss_container_type_id", "boss_supplier_id", "boss_days", "boss_days_source", *SHIPMENT_DEPENDS)
    def _compute_boss_cost(self):
        frozen = self._boss_skip()
        frozen._boss_keep(*COST_FIELDS)
        for line in self - frozen:
            if line.display_type or not line.product_id.boss_pricing_mode or not line.order_id:
                line.update({"boss_cost_status": False, "boss_cost_amount": 0.0, "boss_cost_currency_id": False,
                             "boss_tariff_line_id": False, "boss_cost_candidate_ids": False,
                             "boss_cost_missing": False, "boss_cost_steps": False, "boss_cost_is_estimate": False})
                continue
            percent = line.product_id.boss_cost_method == "percent"
            res = line._boss_price(line._boss_related_costs() if percent else None)
            status = res.status
            if (status == "ok" and res.currency and res.currency != line.currency_id
                    and line.order_id.company_id.boss_fx_policy == "none"):
                status = "currency"
            line.update({
                "boss_cost_status": status,
                "boss_cost_amount": res.amount,
                "boss_cost_currency_id": (res.currency or line.currency_id).id,
                "boss_tariff_line_id": res.line.id,
                "boss_cost_candidate_ids": res.candidates,
                "boss_cost_missing": ",".join(res.missing) or False,
                "boss_cost_steps": res.steps or False,
                "boss_cost_is_estimate": bool(res.line) and res.line.method == "time" and line.boss_days_source != "actual",
            })

    @api.depends("boss_cost_status", "boss_cost_amount", "boss_manual_cost", "boss_cost_steps",
                 "boss_cost_is_estimate", "boss_days", "boss_days_source")
    def _compute_boss_cost_explanation(self):
        pricing = self.env["boss.pricing"]
        for line in self:
            if not line.boss_cost_status:
                line.boss_cost_explanation = False
                continue
            text = pricing.explain(
                line.product_id, line.product_uom_id, line.boss_cost_status, line.boss_cost_amount,
                line.boss_tariff_line_id, line.boss_cost_candidate_ids,
                line.boss_cost_missing.split(",") if line.boss_cost_missing else [], line.boss_cost_steps)
            if line.boss_cost_status == "currency":
                text = self.env._(
                    "Cost in %(cur)s and quotation in %(order)s: no conversion policy yet (company "
                    "setting).", cur=line.boss_cost_currency_id.name, order=line.currency_id.name)
            elif line.boss_cost_status in ("manual", "not_ready") and line.boss_manual_cost:
                text = self.env._("Manual cost per unit: %(cost)s %(cur)s %(ref)s", cost=line.boss_manual_cost,
                                  cur=line.currency_id.name, ref=line.boss_manual_cost_note or "")
            if line.boss_cost_is_estimate and line.boss_cost_status == "ok":
                days = line.boss_days if line.boss_days_source == "estimate" else line.order_id.boss_storage_days
                where = (self.env._("estimate of this line") if line.boss_days_source == "estimate"
                         else self.env._("days of the shipment"))
                text = self.env._("ESTIMATE with %(days)s days (%(where)s); the actual cost is known when the period "
                                  "ends.", days=days, where=where) + "\n" + text
            elif (line.boss_days_source == "actual" and line.boss_cost_status == "ok"
                  and line.boss_tariff_line_id.method == "time"):
                text = self.env._("ACTUAL period of %s days.", line.boss_days) + "\n" + text
            line.boss_cost_explanation = text

    def _boss_unit_cost(self):
        """Expected cost per unit in the quotation currency, or 0 when not known."""
        self.ensure_one()
        if self.boss_cost_status in ("manual", "not_ready"):
            return self.boss_manual_cost
        if self.boss_cost_status != "ok" or not self.product_uom_qty:
            return 0.0
        amount, currency = self.boss_cost_amount, self.boss_cost_currency_id
        if currency and currency != self.currency_id:
            amount = currency._convert(amount, self.currency_id, self.order_id.company_id, self._boss_fx_date())
        return amount / self.product_uom_qty

    def _boss_fx_date(self):
        return fields.Date.to_date(self.order_id.date_order) or fields.Date.today()

    @api.depends("boss_cost_status", "boss_cost_amount", "boss_cost_currency_id", "boss_manual_cost",
                 "product_uom_qty")
    def _compute_purchase_price(self):
        boss = self._boss_lines()
        super(SaleOrderLine, self - boss)._compute_purchase_price()
        frozen = boss._boss_skip()
        frozen._boss_keep("purchase_price")
        for line in boss - frozen:
            line.purchase_price = line._boss_unit_cost()

    def _boss_recompute_cost(self):
        """Cost, then the sale price built on it (cost-based pricelist rules). An explicit recompute does not
        propagate to dependent fields like a write does, so the chain is recomputed here in order; typed and
        accepted prices are kept by _compute_price_unit."""
        lines = self._boss_lines()
        for fname in ("boss_cost_status", "purchase_price", "price_unit"):
            self.env.add_to_compute(self._fields[fname], lines)
            lines._recompute_recordset([fname])
            # notify the dependent fields (sale price, line total, taxes, margin) like a write would
            lines.modified([fname])
        lines.invalidate_recordset(["boss_sale_status", "boss_sale_explanation", "boss_markup"])

    # --- VAT: Ángel's rules give the class; the BOSS VAT table gives the Odoo tax (ADR-004) ------------------

    def _boss_zones(self):
        order = self.order_id
        eu = set(self.env.ref("base.europe").country_ids.mapped("code"))
        port = order.boss_port_id
        spain = vat_rules.zone(port.country_id.code, canary=port.canary_islands) if port else None
        abroad = vat_rules.zone(order.boss_country_id.code, eu_codes=eu) if order.boss_country_id else None
        customer = order.partner_id.commercial_partner_id
        cust_zone = vat_rules.zone(customer.country_id.code, customer.state_id.code, eu_codes=eu)
        if order.boss_direction == "import":
            return abroad, spain, cust_zone
        if order.boss_direction == "export":
            return spain, abroad, cust_zone
        return None, None, cust_zone

    @api.depends("product_id", "product_id.boss_paid_on_behalf", "boss_manual_cost_note", "order_id.partner_id",
                 "order_id.partner_id.vat", "order_id.boss_direction", "order_id.boss_port_id", "order_id.boss_country_id")
    def _compute_boss_vat(self):
        frozen = self._boss_skip()
        frozen._boss_keep("boss_vat_class", "boss_vat_status", "boss_vat_trace", "boss_vat_tax_id")
        VatTax = self.env["boss.vat.tax"]
        for line in self - frozen:
            if line.display_type or not line.product_id.boss_pricing_mode:
                line.update({"boss_vat_class": False, "boss_vat_status": False, "boss_vat_trace": False,
                             "boss_vat_tax_id": False})
                continue
            origin, destination, customer = line._boss_zones()
            vat_class, trace = vat_rules.vat_class(line.product_id.boss_vat_class, origin, destination, customer)
            # Paid on behalf only with its document in the customer's name (customs declaration, invoice): the
            # product flag alone does not prove it.
            on_behalf = line.product_id.boss_paid_on_behalf and bool(line.boss_manual_cost_note)
            blocked = False
            if line.product_id.boss_paid_on_behalf and not on_behalf:
                trace.append(self.env._("paid on behalf without its document (type the declaration or invoice in "
                                        "'Cost reference')"))
                blocked = vat_class == "NS"
            if vat_class == "EX" and customer == "COM" and not line.order_id.partner_id.commercial_partner_id.vat:
                trace.append(self.env._("EU customer without VAT number: the business-to-business rule cannot be applied"))
                blocked = True
            row = vat_class and not blocked and VatTax._boss_find(
                line.order_id.company_id or self.env.company, vat_class, customer, on_behalf)
            if row:
                trace.append(f"{row.tax_id.name} ({row.source})" if row.source else row.tax_id.name)
            elif vat_class and not blocked:
                trace.append(self.env._(
                    "no Odoo tax for class %(cls)s and customer zone %(zone)s in the BOSS VAT table (decision pending)",
                    cls=vat_class, zone=customer or "?"))
            line.update({"boss_vat_class": vat_class, "boss_vat_status": "ok" if row else "pending",
                         "boss_vat_trace": " · ".join(trace), "boss_vat_tax_id": row.tax_id.id if row else False})

    def _boss_recompute_vat(self):
        lines = self._boss_lines()
        for fname in ("boss_vat_status", "tax_ids"):
            self.env.add_to_compute(self._fields[fname], lines)
            lines._recompute_recordset([fname])

    @api.depends("boss_vat_tax_id", "boss_vat_status")
    def _compute_tax_ids(self):
        boss = self._boss_lines()
        super(SaleOrderLine, self - boss)._compute_tax_ids()
        frozen = boss._boss_skip()
        frozen._boss_keep("tax_ids")
        for line in boss - frozen:
            line.tax_ids = line.boss_vat_tax_id if line.boss_vat_status == "ok" else False

    # --- sale price: standard prices, frozen once accepted -------------------------------------------

    @api.depends("purchase_price", "pricelist_item_id")
    def _compute_price_unit(self):
        frozen = self._boss_skip()
        frozen._boss_keep("price_unit")
        super(SaleOrderLine, self - frozen)._compute_price_unit()

    def _compute_discount(self):
        frozen = self._boss_skip()
        frozen._boss_keep("discount")
        super(SaleOrderLine, self - frozen)._compute_discount()

    def _boss_cost_known(self):
        """A cost a sale price can be built on: a supplier price (a justified 0 included) or a manual cost."""
        self.ensure_one()
        if self.boss_cost_status == "ok":
            return bool(self.boss_tariff_line_id)
        return self.boss_cost_status in ("manual", "not_ready") and bool(self.boss_manual_cost)

    def _get_pricelist_price(self):
        item = self.pricelist_item_id
        if item.base != BOSS_LINE_COST:
            return super()._get_pricelist_price()
        if not self.product_id.boss_pricing_mode or not self._boss_cost_known():
            return 0.0  # no cost yet: the sale price stays missing, never built on a zero cost
        return item._compute_price(
            product=self.product_id.with_context(**self._get_product_price_context()),
            boss_unit_cost=self.purchase_price, **self._get_pricelist_kwargs())

    @api.onchange("boss_sale_free")
    def _onchange_boss_sale_free(self):
        if self.boss_sale_free:
            self.price_unit = 0.0

    @api.depends("price_unit", "technical_price_unit", "boss_sale_free", "product_id", "product_uom_id",
                 "product_uom_qty", "pricelist_item_id", "purchase_price", "boss_cost_status", "boss_manual_cost")
    def _compute_boss_sale_status(self):
        _ = self.env._
        for line in self:
            currency = line.currency_id or line.company_id.currency_id
            item = line.pricelist_item_id
            from_rule = item and not currency.compare_amounts(line.technical_price_unit, line.price_unit)
            cost_rule = from_rule and item.base == BOSS_LINE_COST
            if line.display_type or not line.product_id.boss_pricing_mode:
                status, text = False, False
            elif currency.is_zero(line.price_unit):
                if line.boss_sale_free:
                    status, text = "free", _("Free of charge, confirmed by a person.")
                elif cost_rule and not line._boss_cost_known():
                    status, text = "missing", _(
                        "Rule '%(rule)s' of pricelist %(pricelist)s builds the sale price on the expected cost, "
                        "which is not known yet (see the cost).", rule=item.price, pricelist=item.pricelist_id.name)
                else:
                    status, text = "missing", _(
                        "No sale price: type it, agree it in the customer pricelist or tick 'Free of charge'.")
            elif cost_rule:
                status = "cost_based"
                text = _("Pricelist %(pricelist)s, rule '%(rule)s': expected cost %(cost)s per %(uom)s gives "
                         "%(price)s.", pricelist=item.pricelist_id.name, rule=item.price,
                         cost=line._boss_money(line.purchase_price), uom=line.product_uom_id.name,
                         price=line._boss_money(line.price_unit))
                if item.price_min_margin and not currency.compare_amounts(
                        line.price_unit, line.purchase_price + item.price_min_margin):
                    text += " " + _("The minimum margin of %s per unit applies.", line._boss_money(item.price_min_margin))
            elif from_rule:
                status = "agreed"
                text = _("Agreed price in pricelist %(pricelist)s (%(rule)s) per %(uom)s.",
                         pricelist=item.pricelist_id.name, rule=item.price, uom=item.uom_id.name or line.product_uom_id.name)
            else:
                status, text = "manual", _("Price typed by a person (not from a pricelist rule).")
            line.boss_sale_status = status
            line.boss_sale_explanation = text

    def _boss_money(self, amount):
        return formatLang(self.env, amount, currency_obj=self.currency_id or self.company_id.currency_id)

    @api.depends("price_subtotal", "product_uom_qty", "purchase_price")
    def _compute_boss_markup(self):
        for line in self:
            cost = line.purchase_price * line.product_uom_qty
            line.boss_markup = (line.price_subtotal - cost) / cost if cost else 0.0

    def write(self, vals):
        if "boss_days" in vals and "boss_days_source" not in vals:
            shipment_lines = self.filtered(lambda l: l.boss_days_source == "shipment")
            if shipment_lines:  # typing days on the line makes them the estimate of this line
                super(SaleOrderLine, shipment_lines).write({"boss_days_source": "estimate"})
        if FROZEN_FIELDS & set(vals) and self.filtered("boss_price_frozen"):
            # The context flag comes from the Re-price wizard; RPC callers cannot use it to bypass the rule.
            if not (self.env.context.get("boss_reprice") and self.env.user.has_group("sales_team.group_sale_manager")):
                raise UserError(self.env._(
                    "This line belongs to an accepted quotation. Use 'Re-price' and give the reason."))
        return super().write(vals)

    # --- actions from the quotation line -------------------------------------------------------------

    def _boss_dialog(self, name, res_model, **kw):
        return {"type": "ir.actions.act_window", "name": name, "res_model": res_model, "target": "new",
                "view_mode": kw.pop("view_mode", "form"), **kw}

    def action_boss_pricing_details(self):
        self.ensure_one()
        view = self.env.ref("boss_pricing_sale.sale_order_line_view_form_boss_pricing")
        return self._boss_dialog(self.env._("Pricing of %s", self.product_id.display_name), "sale.order.line",
                                 res_id=self.id, views=[(view.id, "form")])

    def action_boss_add_supplier_price(self):
        """No supplier price: record it in a supplier tariff, pre-filled from this quotation. Simple prices
        use a short form; brackets, percentages and time prices open the full tariff form."""
        self.ensure_one()
        if self.product_id.boss_cost_method == "per_unit":
            return self._boss_dialog(self.env._("Add supplier price"), "boss.supplier.price.wizard",
                                     views=[(False, "form")], context={"default_sale_line_id": self.id})
        order = self.order_id
        context = {
            "default_name": f"{order.boss_carrier_id.name or ''} {self.product_id.default_code}".strip(),
            "default_partner_id": order.boss_carrier_id.id, "default_carrier_id": order.boss_carrier_id.id,
            "default_valid_from": order.boss_planned_date or fields.Date.today(),
            "default_currency_id": order.currency_id.id, "default_direction": order.boss_direction,
            "default_transport_mode": order.boss_transport_mode, "default_load_type": order.boss_load_type,
            "default_port_ids": order.boss_port_id.ids, "default_country_ids": order.boss_country_id.ids,
            "default_line_ids": [(0, 0, {"product_id": self.product_id.id, "uom_id": self.product_uom_id.id,
                                         "method": self.product_id.boss_cost_method,
                                         "container_size": self.boss_container_size})],
        }
        return self._boss_dialog(self.env._("Add supplier price"), "boss.tariff", views=[(False, "form")],
                                 context=context)

    def action_boss_open_tariffs(self):
        """Pending approval or conflict: open the tariffs involved."""
        self.ensure_one()
        tariffs = self.boss_cost_candidate_ids.tariff_id
        if len(tariffs) == 1:
            return self._boss_dialog(tariffs.name, "boss.tariff", res_id=tariffs.id, views=[(False, "form")])
        return self._boss_dialog(self.env._("Tariffs involved"), "boss.tariff", view_mode="list,form",
                                 views=[(False, "list"), (False, "form")], domain=[("id", "in", tariffs.ids)])

    def action_boss_open_service(self):
        self.ensure_one()
        return self._boss_dialog(self.product_id.display_name, "product.template",
                                 res_id=self.product_id.product_tmpl_id.id, views=[(False, "form")])

    def _boss_snapshot_values(self):
        self.ensure_one()
        tariff_line = self.boss_tariff_line_id
        fx_rate = False
        if self.boss_cost_currency_id and self.boss_cost_currency_id != self.currency_id and self.boss_cost_status == "ok":
            fx_rate = self.boss_cost_currency_id._get_conversion_rate(
                self.boss_cost_currency_id, self.currency_id, self.order_id.company_id, self._boss_fx_date())
        return {
            "line_id": self.id, "service": self.product_id.default_code, "name": self.product_id.name,
            "uom": self.product_uom_id.name, "quantity": self.product_uom_qty,
            "container_size": self.boss_container_size or "", "container_type": self.boss_container_type_id.code or "",
            "price_unit": self.price_unit, "discount": self.discount, "subtotal": self.price_subtotal,
            "currency": self.currency_id.name, "sale_status": self.boss_sale_status,
            "sale_explanation": self.boss_sale_explanation or "",
            "pricelist_item_id": self.pricelist_item_id.id, "pricelist_rule": self.pricelist_item_id.display_name or "",
            "cost_status": self.boss_cost_status, "cost_amount": self.boss_cost_amount,
            "cost_currency": self.boss_cost_currency_id.name, "unit_cost": self.purchase_price,
            "fx_rate": fx_rate, "cost_is_estimate": self.boss_cost_is_estimate,
            "manual_cost_note": self.boss_manual_cost_note or "", "steps": self.boss_cost_steps or [],
            "tariff_line_id": tariff_line.id, "tariff_id": tariff_line.tariff_id.id,
            "tariff": tariff_line.tariff_id.name or "", "tariff_version": tariff_line.tariff_id.version,
            "document": tariff_line.tariff_id.document_reference or "", "page": tariff_line.document_page or "",
            "vat_class": self.boss_vat_class or "", "vat_trace": self.boss_vat_trace or "",
            "taxes": self.tax_ids.mapped("name"),
            "explanation": self.boss_cost_explanation or "",
        }
