from odoo import api, fields, models
from odoo.exceptions import UserError

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
    boss_country_id = fields.Many2one(
        "res.country", "Country abroad", tracking=True,
        help="Origin country of an import or destination country of an export. Used by tariffs and VAT.")
    boss_planned_date = fields.Date(
        "Planned date", tracking=True,
        help="ETA for imports, ETD for exports. It chooses the version of each supplier tariff.")
    boss_container_ids = fields.One2many("boss.shipment.container", "order_id", "Containers", copy=True)
    boss_inland_state_id = fields.Many2one(
        "res.country.state", "Inland province", domain="[('country_id.code', '=', 'ES')]", tracking=True,
        help="Province of the pickup (export) or delivery (import) place in Spain; hauliers price by zone.")
    boss_gross_kg = fields.Float("Gross weight (kg)", digits=(12, 2))
    boss_awb_kg = fields.Float("Chargeable weight (AWB, kg)", digits=(12, 2),
                               help="Chargeable weight written on the air waybill; air handlers price on it.")
    boss_volume_m3 = fields.Float("Volume (m³)", digits=(12, 3))
    boss_pallets = fields.Integer("Pallets")
    boss_goods_value = fields.Monetary("Goods value", currency_field="currency_id",
                                       help="Commercial value of the goods (insurance, value brackets).")
    boss_duties_amount = fields.Monetary("Customs duties (estimate)", currency_field="currency_id",
                                         help="Duties and taxes of the customs declaration, for the guarantee fee.")
    boss_storage_days = fields.Integer(
        "Days in storage (estimate)",
        help="Days assumed for storage, demurrage and port occupancy in the quotation. The actual cost is "
        "only known when the period ends.")
    # An integer cannot be empty in Odoo: this flag tells 'not indicated yet' from a deliberate 0 days.
    boss_storage_days_known = fields.Boolean(
        "Days indicated",
        help="Set when the days are entered (tick it to confirm 0 days). Until then time-based services "
        "(storage, demurrage, port occupancy) show 'missing shipment data' instead of a zero cost.")
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
            "country_id": self.boss_country_id.id,
            "state_id": self.boss_inland_state_id.id,
            "customer_id": self.partner_id.commercial_partner_id.id,
            # always given: demo tariffs never price a real customer, not even "for lack of input"
            "tariff_use": "demo" if self.partner_id.commercial_partner_id.boss_demo else "real",
            "containers": [{"size": c.size, "type_id": c.container_type_id.id, "quantity": c.quantity}
                           for c in self.boss_container_ids],
            "gross_kg": self.boss_gross_kg or None,
            "awb_kg": self.boss_awb_kg or None,
            "volume_m3": self.boss_volume_m3 or None,
            "pallets": self.boss_pallets or None,
            "goods_value": self.boss_goods_value or None,
            "duties_amount": self.boss_duties_amount or None,
            "storage_days": self.boss_storage_days if self.boss_storage_days_known else None,
            "start_weekday": self.boss_planned_date.weekday() if self.boss_planned_date else None,
        }

    @api.onchange("boss_storage_days")
    def _onchange_boss_storage_days(self):
        self.boss_storage_days_known = True

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if "boss_storage_days" in vals and "boss_storage_days_known" not in vals:
                vals["boss_storage_days_known"] = True
        return super().create(vals_list)

    def write(self, vals):
        if "boss_storage_days" in vals and "boss_storage_days_known" not in vals:
            vals = dict(vals, boss_storage_days_known=True)
        return super().write(vals)

    def _boss_quantity(self, source, size=False, ctype=False):
        """Quantity of a charge basis taken from the shipment, or None when entered on the line."""
        self.ensure_one()
        rows = self.boss_container_ids.filtered(
            lambda c: (not size or c.size == size) and (not ctype or c.container_type_id == ctype))
        values = {
            "shipment": 1.0,
            "container": float(sum(rows.mapped("quantity"))),
            "teu": float(sum(c.quantity * TEU[c.size] for c in rows)),
            "gross_kg": self.boss_gross_kg,
            "gross_ton": self.boss_gross_kg / 1000,
            "volume_m3": self.boss_volume_m3,
            "wm": max(self.boss_gross_kg / 1000, self.boss_volume_m3),
            "pallets": float(self.boss_pallets),
            "awb_kg": self.boss_awb_kg or None,  # empty: the quantity stays the one typed on the line
        }
        return values.get(source)

    @api.depends("order_line.boss_cost_status", "order_line.boss_sale_status", "order_line.boss_vat_status",
                 "order_line.boss_manual_cost")
    def _compute_boss_pricing_alert(self):
        line_model = self.env["sale.order.line"]
        cost_labels = dict(line_model._fields["boss_cost_status"]._description_selection(self.env))
        for order in self:
            lines = order.order_line.filtered(lambda l: l.product_id.boss_pricing_mode and not l.display_type)
            issues = []
            for status in ("missing_input", "no_tariff", "pending_approval", "on_request", "conflict",
                           "currency", "not_ready", "manual"):
                count = len(lines.filtered(lambda l, s=status: l.boss_cost_status == s and not (
                    s in ("manual", "not_ready") and l.boss_manual_cost)))
                if count:
                    issues.append(f"{cost_labels[status]}: {count}")
            for field_name, value, label in (
                    ("boss_sale_status", "missing", self.env._("Sale price missing")),
                    ("boss_vat_status", "pending", self.env._("VAT pending"))):
                count = len(lines.filtered(lambda l, f=field_name, v=value: l[f] == v))
                if count:
                    issues.append(f"{label}: {count}")
            order.boss_pricing_alert = " · ".join(issues) if issues else False

    def _boss_check_ready(self):
        """A quotation is not sent or accepted with an undecided VAT treatment or a missing sale price."""
        for order in self:
            lines = order.order_line.filtered(lambda l: l.product_id.boss_pricing_mode and not l.display_type)
            blocking = lines.filtered(lambda l: l.boss_vat_status == "pending" or l.boss_sale_status == "missing")
            if blocking:
                details = "\n".join(
                    f"- {line.product_id.display_name}: "
                    + ", ".join(filter(None, (
                        line.boss_sale_status == "missing" and self.env._("sale price missing"),
                        line.boss_vat_status == "pending" and (line.boss_vat_trace or self.env._("VAT pending")))))
                    for line in blocking)
                raise UserError(self.env._("%(order)s is not ready to send or accept:\n%(details)s",
                                           order=order.name, details=details))

    def action_quotation_send(self):
        self._boss_check_ready()
        return super().action_quotation_send()

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
        self._boss_check_ready()
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
