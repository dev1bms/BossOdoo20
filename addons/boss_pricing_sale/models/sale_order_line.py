from odoo import api, fields, models
from odoo.exceptions import UserError

from odoo.addons.boss_pricing.models.boss_pricing import COST_STATUSES

SALE_STATUSES = [
    ("missing", "Sale price missing"),
    ("agreed", "Agreed price (pricelist)"),
    ("manual", "Entered by a person"),
    ("free", "Free of charge (confirmed)"),
]
# Changing these on an accepted line is a re-pricing: only through the Re-price wizard (ADR-003).
FROZEN_FIELDS = {"product_id", "product_uom_id", "product_uom_qty", "price_unit", "discount",
                 "purchase_price", "boss_manual_cost", "boss_sale_free"}
CONTAINER_SOURCES = ("container_20", "container_40", "container_45")
COST_FIELDS = ("boss_cost_status", "boss_cost_amount", "boss_cost_currency_id", "boss_tariff_line_id",
               "boss_cost_candidate_ids", "boss_cost_missing")


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    boss_pricing_mode = fields.Selection(related="product_id.boss_pricing_mode")
    boss_cost_status = fields.Selection(
        COST_STATUSES + [("currency", "Other currency, no conversion policy")], "Cost status",
        compute="_compute_boss_cost", store=True, copy=False, precompute=True)
    boss_cost_amount = fields.Monetary(
        "Expected cost", currency_field="boss_cost_currency_id", compute="_compute_boss_cost",
        store=True, copy=False, precompute=True,
        help="Expected supplier cost of the whole line, in the tariff currency.")
    boss_cost_currency_id = fields.Many2one("res.currency", compute="_compute_boss_cost", store=True, copy=False, precompute=True)
    boss_tariff_line_id = fields.Many2one("boss.tariff.line", "Supplier price", compute="_compute_boss_cost",
                                          store=True, copy=False, precompute=True, index="btree_not_null")
    boss_cost_candidate_ids = fields.Many2many(
        "boss.tariff.line", "boss_sale_line_cost_candidate_rel", "line_id", "tariff_line_id",
        "Prices involved", compute="_compute_boss_cost", store=True, copy=False, precompute=True)
    boss_cost_missing = fields.Char("Missing data", compute="_compute_boss_cost", store=True, copy=False, precompute=True)
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

    # --- quantity: charge bases counted from the shipment -------------------------------------------

    @api.depends("product_uom_id", "order_id.boss_container_ids.size", "order_id.boss_container_ids.quantity")
    def _compute_product_uom_qty(self):
        frozen = self._boss_skip()
        super(SaleOrderLine, self - frozen)._compute_product_uom_qty()
        frozen._boss_keep("product_uom_qty")
        for line in self - frozen:
            source = line.product_uom_id.boss_quantity_source
            if line.display_type or not line.product_id.boss_pricing_mode or source in (False, "input"):
                continue
            line.product_uom_qty = line.order_id._boss_quantity(source)

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

    # --- cost: one call to boss.pricing --------------------------------------------------------------

    @api.depends("product_id", "product_uom_id", "product_uom_qty", "currency_id", "order_id.partner_id",
                 "order_id.boss_direction", "order_id.boss_transport_mode", "order_id.boss_load_type",
                 "order_id.boss_carrier_id", "order_id.boss_port_id", "order_id.boss_planned_date")
    def _compute_boss_cost(self):
        pricing = self.env["boss.pricing"]
        frozen = self._boss_skip()
        frozen._boss_keep(*COST_FIELDS)
        for line in self - frozen:
            if line.display_type or not line.product_id.boss_pricing_mode:
                line.update({"boss_cost_status": False, "boss_cost_amount": 0.0, "boss_cost_currency_id": False,
                             "boss_tariff_line_id": False, "boss_cost_candidate_ids": False,
                             "boss_cost_missing": False})
                continue
            order = line.order_id
            res = pricing.price_cost(line.product_id, line.product_uom_id, line.product_uom_qty,
                                     order._boss_shipment_inputs(), order.boss_planned_date)
            status = res.status
            if (status == "ok" and res.currency and res.currency != line.currency_id
                    and order.company_id.boss_fx_policy == "none"):
                status = "currency"
            line.update({
                "boss_cost_status": status,
                "boss_cost_amount": res.amount,
                "boss_cost_currency_id": (res.currency or line.currency_id).id,
                "boss_tariff_line_id": res.line.id,
                "boss_cost_candidate_ids": res.candidates,
                "boss_cost_missing": ",".join(res.missing) or False,
            })

    @api.depends("boss_cost_status", "boss_cost_amount", "boss_manual_cost", "product_uom_qty")
    def _compute_boss_cost_explanation(self):
        pricing = self.env["boss.pricing"]
        for line in self:
            if not line.boss_cost_status:
                line.boss_cost_explanation = False
                continue
            text = pricing.explain(
                line.product_id, line.product_uom_id, line.boss_cost_status, line.product_uom_qty,
                line.boss_cost_amount, line.boss_tariff_line_id, line.boss_cost_candidate_ids,
                (line.boss_cost_missing or "").split(",") if line.boss_cost_missing else [])
            if line.boss_cost_status == "currency":
                text = self.env._(
                    "Cost in %(cur)s and quotation in %(order)s: no conversion policy yet (company "
                    "setting).", cur=line.boss_cost_currency_id.name, order=line.currency_id.name)
            elif line.boss_cost_status in ("manual", "not_ready") and line.boss_manual_cost:
                text = self.env._("Manual cost per unit: %(cost)s %(cur)s %(ref)s", cost=line.boss_manual_cost,
                                  cur=line.currency_id.name, ref=line.boss_manual_cost_note or "")
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
            order = self.order_id
            amount = currency._convert(amount, self.currency_id, order.company_id,
                                       fields.Date.to_date(order.date_order) or fields.Date.today())
        return amount / self.product_uom_qty

    @api.depends("boss_cost_status", "boss_cost_amount", "boss_cost_currency_id", "boss_manual_cost",
                 "product_uom_qty")
    def _compute_purchase_price(self):
        boss = self.filtered(lambda l: l.product_id.boss_pricing_mode and not l.display_type)
        super(SaleOrderLine, self - boss)._compute_purchase_price()
        frozen = boss._boss_skip()
        frozen._boss_keep("purchase_price")
        for line in boss - frozen:
            line.purchase_price = line._boss_unit_cost()

    def _boss_recompute_cost(self):
        lines = self.filtered(lambda l: l.product_id.boss_pricing_mode and not l.display_type)
        for fname in ("boss_cost_status", "purchase_price"):
            self.env.add_to_compute(self._fields[fname], lines)
            lines._recompute_recordset([fname])

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
        if (FROZEN_FIELDS & set(vals) and not self.env.context.get("boss_reprice")
                and self.filtered("boss_price_frozen")):
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
        self.ensure_one()
        return self._boss_dialog(self.env._("Add supplier price"), "boss.supplier.price.wizard",
                                 views=[(False, "form")], context={"default_sale_line_id": self.id})

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
        return {
            "line_id": self.id, "service": self.product_id.default_code, "name": self.product_id.name,
            "uom": self.product_uom_id.name, "quantity": self.product_uom_qty,
            "price_unit": self.price_unit, "discount": self.discount, "subtotal": self.price_subtotal,
            "sale_status": self.boss_sale_status, "pricelist_item_id": self.pricelist_item_id.id,
            "cost_status": self.boss_cost_status, "cost_amount": self.boss_cost_amount,
            "cost_currency": self.boss_cost_currency_id.name, "unit_cost": self.purchase_price,
            "manual_cost_note": self.boss_manual_cost_note or "",
            "tariff_line_id": tariff_line.id, "tariff_id": tariff_line.tariff_id.id,
            "tariff": tariff_line.tariff_id.name or "", "tariff_version": tariff_line.tariff_id.version,
            "document": tariff_line.tariff_id.document_reference or "", "page": tariff_line.document_page or "",
            "explanation": self.boss_cost_explanation or "",
        }
