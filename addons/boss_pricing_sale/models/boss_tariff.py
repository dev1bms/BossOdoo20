from odoo import models


class BossTariff(models.Model):
    _inherit = "boss.tariff"

    def _boss_refresh_quotations(self):
        """Open quotations of these services see the new tariff state at once.

        sudo is limited to finding and recomputing the cost of open lines: the approver may have no
        access to quotations, nothing is returned or shown to them, only quotations of the tariff's company
        are touched (the pricing service filters tariffs by the order company) and accepted (frozen) lines
        or quotations are never re-priced."""
        for tariff in self:
            lines = self.env["sale.order.line"].sudo().search([
                ("company_id", "=", tariff.company_id.id),
                ("product_id", "in", tariff.line_ids.product_id.ids),
                ("boss_price_frozen", "=", False),
                ("order_id.boss_pricing_frozen", "=", False),
                ("order_id.state", "in", ("draft", "sent")),
            ])
            lines.with_company(tariff.company_id)._boss_recompute_cost()

    def action_submit(self):
        res = super().action_submit()
        self._boss_refresh_quotations()
        return res

    def action_approve(self):
        res = super().action_approve()
        self._boss_refresh_quotations()
        return res
