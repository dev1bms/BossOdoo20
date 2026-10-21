from odoo import api, fields, models
from odoo.tools.misc import formatLang


class BossPricingSnapshot(models.Model):
    """What was accepted (or re-priced), as evidence for operations and invoicing (ADR-003)."""

    _name = "boss.pricing.snapshot"
    _description = "Pricing snapshot of a quotation"
    _order = "date desc, id desc"

    order_id = fields.Many2one("sale.order", required=True, ondelete="cascade", index=True, readonly=True)
    kind = fields.Selection([("acceptance", "Acceptance"), ("repricing", "Re-pricing")], required=True,
                            readonly=True)
    reason = fields.Text(readonly=True)
    user_id = fields.Many2one("res.users", default=lambda self: self.env.user, readonly=True)
    date = fields.Datetime(default=fields.Datetime.now, readonly=True)
    data = fields.Json(readonly=True, help="Shipment inputs, policy and every line with its price source.")
    summary = fields.Text(readonly=True)

    def _summary_line(self, line, values):
        """One readable line: quantity, sale total and cost total of the line (same basis), source."""
        _ = self.env._
        sale = formatLang(self.env, line.price_subtotal, currency_obj=line.currency_id)
        cost = formatLang(self.env, line.boss_cost_amount, currency_obj=line.boss_cost_currency_id or line.currency_id)
        size = f" {values['container_size']}' {values['container_type']}" if values["container_size"] else ""
        estimate = f" ({_('estimate')})" if values["cost_is_estimate"] else ""
        quantity = formatLang(self.env, values["quantity"], digits=2)
        return (f"[{values['service']}]{size} {quantity} x {values['uom']}: {_('sale')} {sale} · "
                f"{_('cost')} {cost}{estimate} · {values['tariff'] or values['cost_status']}")

    @api.model
    def _take(self, order, kind, reason=False, before=None):
        lines = order.order_line.filtered(lambda l: not l.display_type)
        data = {
            "currency": order.currency_id.name,
            "fx_policy": order.company_id.boss_fx_policy,
            "date_order": fields.Datetime.to_string(order.date_order),
            "planned_date": fields.Date.to_string(order.boss_planned_date) if order.boss_planned_date else None,
            "shipment": dict(order._boss_shipment_inputs()),
            "containers": [{"size": c.size, "type": c.container_type_id.code, "quantity": c.quantity}
                           for c in order.boss_container_ids],
            "lines": [line._boss_snapshot_values() for line in lines],
        }
        if before:
            data["before"] = before
        summary = "\n".join(self._summary_line(line, values) for line, values in zip(lines, data["lines"]))
        return self.create({"order_id": order.id, "kind": kind, "reason": reason, "data": data,
                            "summary": summary})
