from odoo import models


class BossTariff(models.Model):
    _inherit = "boss.tariff"

    def _boss_refresh_quotations(self):
        """Open quotations of these services see the new state at once (frozen lines never change)."""
        # System refresh: the approver may not have access to quotations.
        lines = self.env["sale.order.line"].sudo().search([
            ("product_id", "in", self.line_ids.product_id.ids),
            ("boss_price_frozen", "=", False),
            ("order_id.state", "in", ("draft", "sent")),
        ])
        lines._boss_recompute_cost()

    def action_submit(self):
        res = super().action_submit()
        self._boss_refresh_quotations()
        return res

    def action_approve(self):
        res = super().action_approve()
        self._boss_refresh_quotations()
        return res
