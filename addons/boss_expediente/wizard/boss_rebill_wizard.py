from odoo import api, fields, models
from odoo.exceptions import UserError


class BossRebillWizard(models.TransientModel):
    """Extra cost re-invoiced to the customer: one new sale line on an accepted order of the file, with its price,
    the reason and a snapshot. The only way to add a service to an accepted order (sales manager)."""

    _name = "boss.rebill.wizard"
    _description = "Re-invoice an extra cost"

    cost_id = fields.Many2one("boss.expediente.cost", required=True)
    expediente_id = fields.Many2one(related="cost_id.expediente_id")
    order_id = fields.Many2one(
        "sale.order", "Order", required=True,
        domain="[('boss_expediente_id', '=', expediente_id), ('state', '=', 'sale')]")
    currency_id = fields.Many2one(related="order_id.currency_id")
    quantity = fields.Float(related="cost_id.quantity", string="Quantity")
    uom_id = fields.Many2one(related="cost_id.uom_id", string="Unit")
    price_unit = fields.Monetary("Sale price per unit", currency_field="currency_id", required=True)
    reason = fields.Text(required=True)

    @api.model
    def default_get(self, fields_list):
        values = super().default_get(fields_list)
        need = self.env["boss.expediente.cost"].browse(values.get("cost_id"))
        orders = need.expediente_id.sale_order_ids.filtered(lambda o: o.state == "sale")
        if orders and "order_id" in fields_list:
            values["order_id"] = orders.sorted("date_order")[:1].id
        return values

    def action_apply(self):
        self.ensure_one()
        need, order = self.cost_id, self.order_id
        if need.rebill_line_id:
            raise UserError(self.env._("%s is already re-invoiced.", need.display_name))
        if not self.env.user.has_group("sales_team.group_sale_manager"):
            raise UserError(self.env._("Only a sales manager can add a service to an accepted order."))
        line = self.env["sale.order.line"].with_context(boss_addition=True).create({
            "order_id": order.id, "product_id": need.product_id.id, "product_uom_id": need.uom_id.id,
            "product_uom_qty": need.quantity, "price_unit": self.price_unit, "boss_execution": "supplier",
            "boss_supplier_id": need.partner_id.id, "name": need.name or need.product_id.display_name,
        })
        line.boss_price_frozen = True
        need.write({"rebill_line_id": line.id, "extra_class": "rebill"})
        need.expediente_id._boss_link_orders(order)
        self.env["boss.pricing.snapshot"].sudo()._take(order, "addition", self.reason)
        order.message_post(body=self.env._("Service %(service)s added after acceptance. Reason: %(reason)s",
                                           service=line.product_id.display_name, reason=self.reason))
        return {"type": "ir.actions.act_window_close"}
