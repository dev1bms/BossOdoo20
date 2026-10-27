from odoo import fields, models


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

    def action_ws_test(self):
        """Test pricing with the first price of this tariff (simulated while it is not approved)."""
        self.ensure_one()
        return self.line_ids[:1].action_ws_test() if self.line_ids else self.env["boss.pricing.test"]._open({})


class BossTariffLine(models.Model):
    _inherit = "boss.tariff.line"

    def action_ws_test(self):
        """Test pricing pre-filled with this price and a shipment inside its scope."""
        self.ensure_one()
        tariff = self.tariff_id
        today = fields.Date.context_today(self)
        day = max(today, tariff.valid_from) if not tariff.valid_to or tariff.valid_to >= today else tariff.valid_to
        values = {
            "product_id": self.product_id.id, "uom_id": self.uom_id.id, "supplier_id": tariff.partner_id.id,
            # the price's own scope when it narrows its tariff (a section of the document)
            "date": day, "direction": self.line_direction or tariff.direction,
            "transport_mode": self.line_transport_mode or tariff.transport_mode,
            "load_type": self.line_load_type or tariff.load_type, "carrier_id": tariff.carrier_id.id,
            "port_id": (self.line_port_ids or tariff.port_ids)[:1].id,
            "country_id": (self.line_country_ids or tariff.country_ids)[:1].id,
            "state_id": (self.line_state_ids or tariff.state_ids)[:1].id,
            # a demo price is tried with a demo customer (it never prices a real one)
            "customer_id": (tariff.customer_id or (self.env["res.partner"].search([("boss_demo", "=", True)], limit=1)
                                                   if tariff.is_demo else self.env["res.partner"])).id,
            "container_size": self.container_size or False,
            "container_type_id": self.container_type_ids[:1].id,
        }
        if tariff.state != "approved":
            values["simulate_tariff_ids"] = [tariff.id]
        return self.env["boss.pricing.test"]._open(values)
