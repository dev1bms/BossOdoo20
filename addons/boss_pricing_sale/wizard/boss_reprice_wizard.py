from odoo import api, fields, models


class BossRepriceWizard(models.TransientModel):
    """The only way to change prices of an accepted quotation: explicit, with a reason, recorded."""

    _name = "boss.reprice.wizard"
    _description = "Re-price an accepted quotation"

    order_id = fields.Many2one("sale.order", required=True)
    reason = fields.Text(required=True)
    line_ids = fields.One2many("boss.reprice.wizard.line", "wizard_id", compute="_compute_line_ids",
                               store=True, readonly=False)

    @api.depends("order_id")
    def _compute_line_ids(self):
        for wiz in self:
            lines = wiz.order_id.order_line.filtered(lambda l: l.boss_price_frozen)
            wiz.line_ids = [(5,)] + [(0, 0, {"sale_line_id": line.id, "new_price": line.price_unit})
                                     for line in lines]

    def action_apply(self):
        self.ensure_one()
        order = self.order_id
        before = [line._boss_snapshot_values() for line in order.order_line.filtered("boss_price_frozen")]
        ctx_self = self.with_context(boss_reprice=True)
        # Odoo refuses price changes on a locked order: unlock for the re-pricing only (D-9, found in Chrome on boss20)
        locked = order.locked
        if locked:
            order.action_unlock()
        for wl in ctx_self.line_ids:
            line = wl.sale_line_id
            if wl.recompute_cost:
                line._boss_recompute_cost()
            if line.currency_id.compare_amounts(wl.new_price, line.price_unit):
                line.price_unit = wl.new_price
        if locked:
            order.action_lock()
        self.env["boss.pricing.snapshot"].sudo()._take(order, "repricing", self.reason, before)
        order.message_post(body=self.env._("Prices re-priced. Reason: %s", self.reason))
        return {"type": "ir.actions.act_window_close"}


class BossRepriceWizardLine(models.TransientModel):
    _name = "boss.reprice.wizard.line"
    _description = "Line to re-price"

    wizard_id = fields.Many2one("boss.reprice.wizard", required=True, ondelete="cascade")
    sale_line_id = fields.Many2one("sale.order.line", required=True, readonly=True)
    product_id = fields.Many2one(related="sale_line_id.product_id")
    uom_id = fields.Many2one(related="sale_line_id.product_uom_id")
    quantity = fields.Float(related="sale_line_id.product_uom_qty")
    currency_id = fields.Many2one(related="sale_line_id.currency_id")
    current_price = fields.Float(related="sale_line_id.price_unit", string="Accepted price")
    current_cost = fields.Float(related="sale_line_id.purchase_price", string="Accepted unit cost")
    new_price = fields.Float("New price", min_display_digits="Product Price")
    recompute_cost = fields.Boolean("Recompute cost from tariffs", default=True)
