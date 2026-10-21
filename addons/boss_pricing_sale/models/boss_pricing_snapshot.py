from odoo import api, fields, models


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

    @api.model
    def _take(self, order, kind, reason=False, before=None):
        lines = order.order_line.filtered(lambda l: not l.display_type)
        data = {
            "currency": order.currency_id.name,
            "fx_policy": order.company_id.boss_fx_policy,
            "date_order": fields.Datetime.to_string(order.date_order),
            "planned_date": fields.Date.to_string(order.boss_planned_date) if order.boss_planned_date else None,
            "shipment": {key: value for key, value in order._boss_shipment_inputs().items()},
            "containers": [{"size": c.size, "quantity": c.quantity} for c in order.boss_container_ids],
            "lines": [line._boss_snapshot_values() for line in lines],
        }
        if before:
            data["before"] = before
        summary = "\n".join(
            f"[{v['service']}] {v['quantity']} x {v['uom']}: {self.env._('sale')} {v['price_unit']} "
            f"{data['currency']} · {self.env._('cost')} {v['cost_amount']} {v['cost_currency'] or ''} "
            f"({v['cost_status']}) {v['tariff']}"
            for v in data["lines"])
        return self.create({"order_id": order.id, "kind": kind, "reason": reason, "data": data,
                            "summary": summary})
