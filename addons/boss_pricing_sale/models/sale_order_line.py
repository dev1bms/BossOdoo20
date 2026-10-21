from odoo import api, fields, models
from odoo.exceptions import UserError

from odoo.addons.boss_pricing.models.boss_container_type import CONTAINER_SIZES
from odoo.addons.boss_pricing.models.boss_pricing import COST_STATUSES

from . import vat_rules

SALE_STATUSES = [
    ("missing", "Sale price missing"),
    ("agreed", "Agreed price (pricelist)"),
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
    "order_id.boss_container_ids.size", "order_id.boss_container_ids.container_type_id",
    "order_id.boss_container_ids.quantity", "order_id.boss_gross_kg", "order_id.boss_volume_m3",
    "order_id.boss_pallets", "order_id.boss_goods_value", "order_id.boss_duties_amount",
    "order_id.boss_storage_days",
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
    boss_markup = fields.Float(
        "Markup on cost", compute="_compute_boss_markup",
        help="(Sale - cost) / cost. The margin shown by Odoo is (sale - cost) / sale.")
    boss_vat_class = fields.Selection([("NS", "NS"), ("EX", "EX"), ("NR", "NR")], "VAT class",
                                      compute="_compute_boss_vat", store=True, copy=False, precompute=True)
    boss_vat_status = fields.Selection(VAT_STATUSES, "VAT", compute="_compute_boss_vat", store=True, copy=False,
                                       precompute=True)
    boss_vat_trace = fields.Char("Why this VAT", compute="_compute_boss_vat", store=True, copy=False,
                                 precompute=True)

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
        auto._boss_recompute_cost()  # the cost was precomputed with the default quantity
        return lines

    # --- quantity: charge bases counted from the shipment -------------------------------------------

    @api.depends("product_uom_id", "boss_container_size", "boss_container_type_id",
                 "order_id.boss_container_ids.size", "order_id.boss_container_ids.container_type_id",
                 "order_id.boss_container_ids.quantity", "order_id.boss_gross_kg", "order_id.boss_volume_m3",
                 "order_id.boss_pallets")
    def _compute_product_uom_qty(self):
        frozen = self._boss_skip()
        super(SaleOrderLine, self - frozen)._compute_product_uom_qty()
        frozen._boss_keep("product_uom_qty")
        for line in (self - frozen)._boss_lines():
            source = line.product_uom_id.boss_quantity_source
            if source in (False, "input"):
                continue
            line.product_uom_qty = line.order_id._boss_quantity(source, line.boss_container_size,
                                                                line.boss_container_type_id)

    # --- cost: one call to boss.pricing --------------------------------------------------------------

    def _boss_inputs(self):
        self.ensure_one()
        inputs = self.order_id._boss_shipment_inputs()
        inputs.update({"line_qty": self.product_uom_qty, "container_size": self.boss_container_size or None,
                       "container_type_id": self.boss_container_type_id.id or None})
        return inputs

    def _boss_price(self, related_costs=None):
        self.ensure_one()
        inputs = self._boss_inputs()
        if related_costs is not None:
            inputs["related_costs"] = related_costs
        return self.env["boss.pricing"].price_cost(self.product_id, self.product_uom_id, inputs,
                                                   self.order_id.boss_planned_date)

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
                 "boss_container_type_id", *SHIPMENT_DEPENDS)
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
                "boss_cost_is_estimate": bool(res.line) and res.line.method == "time",
            })

    @api.depends("boss_cost_status", "boss_cost_amount", "boss_manual_cost", "boss_cost_steps",
                 "boss_cost_is_estimate")
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
                text = self.env._("ESTIMATE with %s days assumed; the actual cost is known when the period "
                                  "ends.", line.order_id.boss_storage_days) + "\n" + text
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
        lines = self._boss_lines()
        for fname in ("boss_cost_status", "purchase_price"):
            self.env.add_to_compute(self._fields[fname], lines)
            lines._recompute_recordset([fname])

    # --- VAT: Ángel's rules, Odoo tax from the company mapping (ADR-004) -----------------------------

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

    @api.depends("product_id", "order_id.partner_id", "order_id.boss_direction", "order_id.boss_port_id",
                 "order_id.boss_country_id")
    def _compute_boss_vat(self):
        frozen = self._boss_skip()
        frozen._boss_keep("boss_vat_class", "boss_vat_status", "boss_vat_trace")
        for line in self - frozen:
            if line.display_type or not line.product_id.boss_pricing_mode:
                line.update({"boss_vat_class": False, "boss_vat_status": False, "boss_vat_trace": False})
                continue
            vat_class, trace = vat_rules.vat_class(line.product_id.boss_vat_class, *line._boss_zones())
            company = line.order_id.company_id or self.env.company
            tax = vat_class and company[f"boss_tax_{vat_class.lower()}_id"]
            if vat_class and not tax:
                trace.append(self.env._("no Odoo tax set for class %s (Sales settings)", vat_class))
            line.update({"boss_vat_class": vat_class, "boss_vat_status": "ok" if tax else "pending",
                         "boss_vat_trace": " · ".join(trace)})

    @api.depends("boss_vat_class", "boss_vat_status")
    def _compute_tax_ids(self):
        boss = self._boss_lines()
        super(SaleOrderLine, self - boss)._compute_tax_ids()
        frozen = boss._boss_skip()
        frozen._boss_keep("tax_ids")
        for line in boss - frozen:
            company = line.order_id.company_id or self.env.company
            line.tax_ids = (line.boss_vat_status == "ok" and line.boss_vat_class
                            and company[f"boss_tax_{line.boss_vat_class.lower()}_id"]) or False

    # --- sale price: standard prices, frozen once accepted -------------------------------------------

    def _compute_price_unit(self):
        frozen = self._boss_skip()
        frozen._boss_keep("price_unit")
        super(SaleOrderLine, self - frozen)._compute_price_unit()

    def _compute_discount(self):
        frozen = self._boss_skip()
        frozen._boss_keep("discount")
        super(SaleOrderLine, self - frozen)._compute_discount()

    @api.onchange("boss_sale_free")
    def _onchange_boss_sale_free(self):
        if self.boss_sale_free:
            self.price_unit = 0.0

    @api.depends("price_unit", "technical_price_unit", "boss_sale_free", "product_id", "product_uom_id",
                 "product_uom_qty")
    def _compute_boss_sale_status(self):
        for line in self:
            currency = line.currency_id or line.company_id.currency_id
            if line.display_type or not line.product_id.boss_pricing_mode:
                line.boss_sale_status = False
            elif currency.is_zero(line.price_unit):
                line.boss_sale_status = "free" if line.boss_sale_free else "missing"
            elif line.pricelist_item_id and not currency.compare_amounts(line.technical_price_unit, line.price_unit):
                line.boss_sale_status = "agreed"
            else:
                line.boss_sale_status = "manual"

    @api.depends("price_subtotal", "product_uom_qty", "purchase_price")
    def _compute_boss_markup(self):
        for line in self:
            cost = line.purchase_price * line.product_uom_qty
            line.boss_markup = (line.price_subtotal - cost) / cost if cost else 0.0

    def write(self, vals):
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
