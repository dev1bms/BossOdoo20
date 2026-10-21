from odoo import models


class BossTariff(models.Model):
    _inherit = "boss.tariff"

    def action_approve(self):
        res = super().action_approve()
        # Open quotations waiting for these prices are refreshed at once (frozen lines never are).
        lines = self.env["sale.order.line"].search([
            ("product_id", "in", self.line_ids.product_id.ids),
            ("boss_price_frozen", "=", False),
            ("order_id.state", "in", ("draft", "sent")),
        ])
        lines._boss_recompute_cost()
        return res
