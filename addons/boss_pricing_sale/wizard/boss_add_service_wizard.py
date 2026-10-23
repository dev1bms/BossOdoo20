from odoo import api, fields, models
from odoo.exceptions import UserError

from ..models.sale_order_line import EXECUTIONS


class BossAddServiceWizard(models.TransientModel):
    """A service sold after acceptance, as an explicit commercial change: one new line with its sale price, who
    executes it (BOSS or a supplier), the reason and a snapshot. The accepted lines and their snapshot do not change
    (ADR-005)."""

    _name = "boss.add.service.wizard"
    _description = "Add a service to an accepted order"

    order_id = fields.Many2one("sale.order", required=True)
    currency_id = fields.Many2one(related="order_id.currency_id")
    product_id = fields.Many2one("product.product", "Service", required=True,
                                 domain="[('boss_pricing_mode', '!=', False), ('sale_ok', '=', True)]")
    allowed_uom_ids = fields.Many2many("uom.uom", compute="_compute_allowed_uom_ids")
    uom_id = fields.Many2one("uom.uom", "Charge basis", required=True, domain="[('id', 'in', allowed_uom_ids)]",
                             compute="_compute_uom_id", store=True, readonly=False,
                             precompute=True)
    quantity = fields.Float(digits="Product Unit", required=True, compute="_compute_quantity", store=True,
                            readonly=False, precompute=True)
    execution = fields.Selection(EXECUTIONS, "Executed by", required=True, compute="_compute_execution", store=True,
                                 readonly=False, precompute=True)
    supplier_id = fields.Many2one("res.partner", "Supplier")
    manual_cost = fields.Monetary(
        "Expected unit cost", currency_field="currency_id",
        help="Only for a service without supplier tariff (typed cost, e.g. supplier offer).")
    price_unit = fields.Monetary("Sale price per unit", currency_field="currency_id")
    reason = fields.Text(required=True)

    @api.depends("product_id")
    def _compute_allowed_uom_ids(self):
        for wiz in self:
            wiz.allowed_uom_ids = wiz.product_id.product_tmpl_id._boss_charge_bases() if wiz.product_id else False

    @api.depends("product_id")
    def _compute_uom_id(self):
        for wiz in self:
            wiz.uom_id = wiz.product_id.uom_id

    @api.depends("uom_id", "order_id")
    def _compute_quantity(self):
        for wiz in self:
            counted = wiz.order_id and wiz.uom_id and wiz.order_id._boss_quantity(wiz.uom_id.boss_quantity_source)
            wiz.quantity = counted or 1.0

    @api.depends("product_id")
    def _compute_execution(self):
        for wiz in self:
            wiz.execution = "boss" if wiz.product_id.boss_pricing_mode == "own" else "supplier"

    def action_apply(self):
        self.ensure_one()
        order = self.order_id
        if not self.env.user.has_group("sales_team.group_sale_manager"):
            raise UserError(self.env._("Only a sales manager can add a service to an accepted order."))
        if order.state != "sale" or not order.boss_pricing_frozen:
            raise UserError(self.env._("%s is not an accepted order: add the service to the quotation.", order.name))
        values = {
            "order_id": order.id, "product_id": self.product_id.id, "product_uom_id": self.uom_id.id,
            "product_uom_qty": self.quantity, "price_unit": self.price_unit, "boss_execution": self.execution,
            "boss_supplier_id": self.supplier_id.id if self.execution == "supplier" else False,
            "boss_added_after_acceptance": True,
            "boss_sale_free": self.currency_id.is_zero(self.price_unit),  # zero only on purpose, with the reason
        }
        if self.execution == "supplier" and self.manual_cost:
            values["boss_manual_cost"] = self.manual_cost
        line = self.env["sale.order.line"].with_context(boss_addition=True).create(values)
        if line.boss_cost_kind == "unknown":
            line.boss_unknown_cost_reason = self.reason[:250]
        line.boss_price_frozen = True
        self.env["boss.pricing.snapshot"].sudo()._take(order, "addition", self.reason)
        order.message_post(body=self.env._("Service %(service)s added after acceptance. Reason: %(reason)s",
                                           service=line.product_id.display_name, reason=self.reason))
        return {"type": "ir.actions.act_window_close"}
