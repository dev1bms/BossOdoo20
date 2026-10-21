from odoo import api, fields, models

from odoo.addons.boss_pricing.models.boss_tariff import DIRECTIONS, LOAD_TYPES, TRANSPORT_MODES

from .boss_shipment_container import TEU



class SaleOrder(models.Model):
    _inherit = "sale.order"

    # Shipment data needed to price the quotation (ADR-003). One place: the quotation.
    boss_direction = fields.Selection(DIRECTIONS, "Direction", tracking=True)
    boss_transport_mode = fields.Selection(TRANSPORT_MODES, "Transport mode", tracking=True)
    boss_load_type = fields.Selection(LOAD_TYPES, "Load type", tracking=True)
    boss_carrier_id = fields.Many2one("res.partner", "Carrier", tracking=True,
                                      help="Shipping line, airline or haulier.")
    boss_port_id = fields.Many2one("boss.port", "Spanish port / airport", tracking=True,
                                   help="Port or airport in Spain where BOSS handles the cargo.")
    boss_planned_date = fields.Date(
        "Planned date", tracking=True,
        help="ETA for imports, ETD for exports. It chooses the version of each supplier tariff.")
    boss_container_ids = fields.One2many("boss.shipment.container", "order_id", "Containers", copy=True)
    boss_pricing_frozen = fields.Boolean(
        "Prices frozen", readonly=True, copy=False,
        help="Set when the quotation is accepted: prices only change through Re-price, with a reason.")
    boss_snapshot_ids = fields.One2many("boss.pricing.snapshot", "order_id", "Pricing history", readonly=True)
    boss_pricing_alert = fields.Text(compute="_compute_boss_pricing_alert")

    def _boss_shipment_inputs(self):
        """Shipment inputs for boss.pricing, named like the tariff scope (one meaning per name)."""
        self.ensure_one()
        return {
            "direction": self.boss_direction,
            "transport_mode": self.boss_transport_mode,
            "load_type": self.boss_load_type,
            "carrier_id": self.boss_carrier_id.id,
            "port_id": self.boss_port_id.id,
            "customer_id": self.partner_id.commercial_partner_id.id,
        }

    def _boss_quantity(self, source):
        """Quantity of a charge basis taken from the shipment, or None if entered on the line."""
        self.ensure_one()
        if source == "shipment":
            return 1.0
        sizes = {"container_20": "20", "container_40": "40", "container_45": "45"}
        if source in sizes:
            return float(sum(c.quantity for c in self.boss_container_ids if c.size == sizes[source]))
        if source == "teu":
            return float(sum(c.quantity * TEU[c.size] for c in self.boss_container_ids))
        return None

    @api.depends("order_line.boss_cost_status", "order_line.boss_sale_status")
    def _compute_boss_pricing_alert(self):
        cost_labels = dict(self.env["sale.order.line"]._fields["boss_cost_status"]._description_selection(self.env))
        for order in self:
            lines = order.order_line.filtered(lambda l: l.product_id.boss_pricing_mode and not l.display_type)
            issues = []
            for status in ("missing_input", "no_tariff", "pending_approval", "on_request", "conflict",
                           "currency", "not_ready", "manual"):
                count = len(lines.filtered(lambda l, s=status: l.boss_cost_status == s))
                if count:
                    issues.append(f"{cost_labels[status]}: {count}")
            missing_sale = len(lines.filtered(lambda l: l.boss_sale_status == "missing"))
            if missing_sale:
                issues.append(self.env._("Sale price missing: %s", missing_sale))
            order.boss_pricing_alert = " · ".join(issues) if issues else False

    def action_boss_add_services(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window", "res_model": "boss.add.services", "view_mode": "form",
            "views": [(False, "form")], "target": "new", "name": self.env._("Add services"),
            "context": {"default_order_id": self.id},
        }

    def action_boss_update_costs(self):
        self.order_line.filtered(lambda l: not l.boss_price_frozen)._boss_recompute_cost()

    def action_boss_reprice(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window", "res_model": "boss.reprice.wizard", "view_mode": "form",
            "views": [(False, "form")], "target": "new", "name": self.env._("Re-price accepted quotation"),
            "context": {"default_order_id": self.id},
        }

    def action_confirm(self):
        res = super().action_confirm()
        # Acceptance = evidence: finish pending computations, then freeze every line and keep a
        # snapshot (ADR-003). Nothing is recomputed from tariffs here: what was quoted is accepted.
        self.env.flush_all()
        for order in self:
            lines = order.order_line.filtered(lambda l: not l.display_type)
            lines.write({"boss_price_frozen": True})
            order.boss_pricing_frozen = True
            self.env["boss.pricing.snapshot"].sudo()._take(order, "acceptance")
        return res
