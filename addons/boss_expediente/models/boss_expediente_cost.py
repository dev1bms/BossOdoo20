from odoo import api, fields, models
from odoo.exceptions import UserError
from odoo.tools import float_compare

from odoo.addons.boss_pricing_sale.models.sale_order_line import COST_KINDS

NEED_STATES = [
    ("no_supplier", "Supplier missing"),
    ("to_order", "To order"),
    ("rfq", "RFQ"),
    ("ordered", "Ordered"),
    ("performed", "Performed"),
    ("billed", "Billed"),
    ("closed", "Closed"),
]
EXTRA_CLASSES = [
    ("covered", "Covered by the agreed price"),
    ("rebill", "Re-invoice to the customer"),
    ("approval", "Needs customer approval"),
    ("absorb", "BOSS bears it"),
    ("disputed", "Disputed with the supplier"),
]


class BossExpedienteCost(models.Model):
    """One external cost of a file: a service sold and bought from a supplier, or an extra cost found later. The
    purchase basis (unit, quantity, currency) is its own: never copied blindly from the sale, never converted."""

    _name = "boss.expediente.cost"
    _description = "Service to buy or extra cost of a shipment file"
    _order = "expediente_id, kind desc, id"

    expediente_id = fields.Many2one("boss.expediente", "File", required=True, ondelete="cascade", index=True)
    company_id = fields.Many2one(related="expediente_id.company_id", store=True)
    company_currency_id = fields.Many2one(related="company_id.currency_id")
    kind = fields.Selection([("sale", "Sold service"), ("extra", "Extra cost")], required=True, default="extra",
                            readonly=True)
    sale_line_id = fields.Many2one("sale.order.line", "Sale line", readonly=True, index="btree_not_null")
    product_id = fields.Many2one("product.product", "Service", required=True,
                                 domain="[('purchase_ok', '=', True), ('type', '=', 'service')]")
    name = fields.Char("Description")
    partner_id = fields.Many2one("res.partner", "Supplier", help="Can be changed while nothing is ordered "
                                 "(cancel the purchase order first to replace the supplier).")
    currency_id = fields.Many2one("res.currency", required=True,
                                  default=lambda self: self.env.company.currency_id)
    uom_id = fields.Many2one("uom.uom", "Purchase unit", required=True)
    quantity = fields.Float("Purchase quantity", digits="Product Unit", default=1.0, required=True)
    expected_unit_cost = fields.Monetary("Expected unit cost", currency_field="currency_id")
    expected_amount = fields.Monetary("Expected cost", currency_field="currency_id",
                                      compute="_compute_expected_amount", store=True)
    accepted_unit_cost = fields.Monetary("Unit cost at acceptance", currency_field="currency_id", readonly=True)
    accepted_amount_company = fields.Monetary("Cost at acceptance (company currency)",
                                              currency_field="company_currency_id", readonly=True)
    accepted_cost_kind = fields.Selection(COST_KINDS, "Cost kind at acceptance", readonly=True)
    tariff_line_id = fields.Many2one("boss.tariff.line", "Supplier price", readonly=True)
    extra_class = fields.Selection(EXTRA_CLASSES, "Extra cost is",
                                   help="Who bears an extra cost found after acceptance.")
    reason = fields.Text("Reason")
    rebill_line_id = fields.Many2one("sale.order.line", "Re-invoiced in", readonly=True, copy=False)
    closed = fields.Boolean("No more cost expected", help="Nothing more will be ordered or billed (service cancelled, "
                            "supplier replaced, cost not incurred).")
    purchase_line_ids = fields.One2many("purchase.order.line", "boss_cost_id", "Purchase lines", readonly=True)
    state = fields.Selection(NEED_STATES, compute="_compute_state", store=True)
    qty_ordered = fields.Float("Ordered", compute="_compute_quantities", compute_sudo=True, digits="Product Unit")
    qty_received = fields.Float("Performed", compute="_compute_quantities", compute_sudo=True, digits="Product Unit")
    qty_billed = fields.Float("Billed", compute="_compute_quantities", compute_sudo=True, digits="Product Unit")
    ordered_amount_company = fields.Monetary("Ordered amount", currency_field="company_currency_id",
                                             compute="_compute_amounts", compute_sudo=True)
    billed_amount_company = fields.Monetary("Billed amount", currency_field="company_currency_id",
                                            compute="_compute_amounts", compute_sudo=True, help="Posted bills minus credit notes.")
    pending_amount_company = fields.Monetary("Still expected", currency_field="company_currency_id",
                                             compute="_compute_amounts", compute_sudo=True)
    variance_company = fields.Monetary("Variance", currency_field="company_currency_id", compute="_compute_amounts", compute_sudo=True,
                                       help="Billed minus ordered (or expected when nothing was ordered).")
    cost_unknown = fields.Boolean("Cost unknown", compute="_compute_amounts", compute_sudo=True)
    variance_to_review = fields.Boolean(compute="_compute_amounts", compute_sudo=True)
    variance_reviewed = fields.Boolean("Variance reviewed", copy=False)
    variance_note = fields.Char("Variance note")

    @api.depends("quantity", "expected_unit_cost")
    def _compute_expected_amount(self):
        for need in self:
            need.expected_amount = need.quantity * need.expected_unit_cost

    @api.model
    def _values_from_sale_line(self, line, expediente):
        """Purchase need of an accepted line, in the basis and currency of its supplier price."""
        order = line.order_id
        tariff_line = line.boss_tariff_line_id if line.boss_cost_status == "ok" else self.env["boss.tariff.line"]
        if tariff_line:
            currency = line.boss_cost_currency_id
            unit = line.boss_cost_amount / line.product_uom_qty if line.product_uom_qty else 0.0
            uom = tariff_line.uom_id or line.product_uom_id
        else:
            currency = line.currency_id
            unit = line.boss_manual_cost if line.boss_cost_status in ("manual", "not_ready") else 0.0
            uom = line.product_uom_id
        company = expediente.company_id
        accepted = currency._convert(unit * line.product_uom_qty, company.currency_id, company,
                                     fields.Date.to_date(order.date_order) or fields.Date.today())
        return {
            "expediente_id": expediente.id, "kind": "sale", "sale_line_id": line.id, "product_id": line.product_id.id,
            "name": line.product_id.display_name, "partner_id": line._boss_purchase_partner().id,
            "currency_id": currency.id, "uom_id": uom.id, "quantity": line.product_uom_qty,
            "expected_unit_cost": unit, "accepted_unit_cost": unit, "accepted_amount_company": accepted,
            "accepted_cost_kind": line.boss_cost_kind, "tariff_line_id": tariff_line.id,
        }

    @api.onchange("product_id")
    def _onchange_product_id(self):
        if self.product_id and not self.uom_id:
            self.uom_id = self.product_id.uom_id
        if self.product_id and not self.name:
            self.name = self.product_id.display_name

    def _boss_active_lines(self):
        return self.purchase_line_ids.filtered(lambda l: l.state != "cancel")

    def _boss_remaining_qty(self):
        self.ensure_one()
        return self.quantity - sum(self._boss_active_lines().mapped("product_qty"))

    @api.depends("closed", "partner_id", "quantity", "purchase_line_ids.state", "purchase_line_ids.product_qty",
                 "purchase_line_ids.qty_received", "purchase_line_ids.qty_invoiced")
    def _compute_state(self):
        digits = self.env["decimal.precision"].precision_get("Product Unit")
        for need in self:
            lines = need._boss_active_lines()
            confirmed = lines.filtered(lambda l: l.state == "purchase")
            ordered = sum(confirmed.mapped("product_qty"))
            billed = sum(lines.mapped("qty_invoiced"))
            if need.closed:
                state = "closed"
            elif billed > 0 and float_compare(billed, need.quantity, precision_digits=digits) >= 0:
                state = "billed"
            elif confirmed and float_compare(sum(confirmed.mapped("qty_received")), ordered,
                                             precision_digits=digits) >= 0:
                state = "performed"
            elif confirmed:
                state = "ordered"
            elif lines:
                state = "rfq"
            elif not need.partner_id:
                state = "no_supplier"
            else:
                state = "to_order"
            need.state = state

    def _compute_quantities(self):
        for need in self:
            confirmed = need._boss_active_lines().filtered(lambda l: l.state == "purchase")
            need.qty_ordered = sum(confirmed.mapped("product_qty"))
            need.qty_received = sum(confirmed.mapped("qty_received"))
            need.qty_billed = sum(need._boss_active_lines().mapped("qty_invoiced"))

    @api.model
    def _boss_billed_by_purchase_line(self, purchase_lines):
        """Posted bill amounts (minus vendor credit notes) per purchase line, company currency."""
        if not purchase_lines:
            return {}
        groups = self.env["account.move.line"].sudo()._read_group(
            [("purchase_line_id", "in", purchase_lines.ids), ("parent_state", "=", "posted"),
             ("display_type", "=", "product")], ["purchase_line_id"], ["balance:sum"])
        return {line.id: balance for line, balance in groups}

    def _compute_amounts(self):
        billed_by_line = self._boss_billed_by_purchase_line(self.purchase_line_ids)
        today = fields.Date.today()
        for need in self:
            company = need.company_id or self.env.company
            currency = company.currency_id
            confirmed = need._boss_active_lines().filtered(lambda l: l.state == "purchase")
            ordered = sum(l.currency_id._convert(l.price_subtotal, currency, company,
                                                 fields.Date.to_date(l.order_id.date_order) or today)
                          for l in confirmed)
            billed = sum(billed_by_line.get(line.id, 0.0) for line in need.purchase_line_ids)
            expected = need.currency_id._convert(need.expected_amount, currency, company, today)
            reference = ordered if confirmed else expected
            unknown = (not need.closed and not confirmed and not billed
                       and need.currency_id.is_zero(need.expected_unit_cost) and need.accepted_cost_kind != "zero")
            variance = billed - reference if need.state in ("billed", "closed") and billed else 0.0
            need.update({
                "ordered_amount_company": ordered, "billed_amount_company": billed,
                "pending_amount_company": 0.0 if need.closed or need.state == "billed" else max(reference - billed, 0.0),
                "variance_company": variance, "cost_unknown": unknown,
                "variance_to_review": not currency.is_zero(variance) and not need.variance_reviewed,
            })

    def write(self, vals):
        if "partner_id" in vals or "currency_id" in vals or "uom_id" in vals:
            for need in self.filtered(lambda n: n._boss_active_lines()):
                if vals.get("partner_id", need.partner_id.id) != need.partner_id.id or vals.get(
                        "currency_id", need.currency_id.id) != need.currency_id.id or vals.get(
                        "uom_id", need.uom_id.id) != need.uom_id.id:
                    raise UserError(self.env._(
                        "%s is already in a purchase order: cancel that order before changing supplier, currency or "
                        "unit.", need.display_name))
        return super().write(vals)

    @api.ondelete(at_uninstall=False)
    def _unlink_except_sold_or_ordered(self):
        for need in self:
            if need.kind == "sale" or need.purchase_line_ids:
                raise UserError(self.env._("%s comes from the accepted sale or is ordered: close it instead of "
                                           "deleting it.", need.display_name))

    @api.depends("product_id", "name", "expediente_id")
    def _compute_display_name(self):
        for need in self:
            need.display_name = f"{need.expediente_id.name or ''} · {need.name or need.product_id.display_name}"

    def _boss_purchase_line_values(self, quantity):
        self.ensure_one()
        file = self.expediente_id
        planned = (file.eta if file.direction == "import" else file.etd) or fields.Date.context_today(self)
        return {
            "product_id": self.product_id.id, "name": f"{file.name} · {self.name or self.product_id.display_name}",
            "product_qty": quantity, "uom_id": self.uom_id.id, "price_unit": self.expected_unit_cost,
            "boss_cost_id": self.id, "sale_line_id": (self.sale_line_id or self.rebill_line_id).id,
            "analytic_distribution": {str(file.analytic_account_id.id): 100.0},
            "date_planned": fields.Datetime.to_datetime(planned),
        }

    def action_mark_performed(self):
        """The supplier performed the service: received quantity = ordered quantity (services have no stock move).
        With the bill control 'on received quantities' only performed services can be billed."""
        for line in self._boss_active_lines().filtered(lambda l: l.state == "purchase"):
            line.qty_received = line.product_qty

    def action_rebill(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window", "res_model": "boss.rebill.wizard", "view_mode": "form",
            "views": [(False, "form")], "target": "new", "name": self.env._("Re-invoice to the customer"),
            "context": {"default_cost_id": self.id},
        }

    def action_open_purchase_lines(self):
        self.ensure_one()
        orders = self.purchase_line_ids.order_id
        return self.expediente_id._boss_action("purchase.order", orders, self.env._("Purchase orders"))
