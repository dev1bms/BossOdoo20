from odoo import Command, api, fields, models
from odoo.exceptions import UserError

from .boss_shipment_container import shipment_quantity

# Case data a quotation template gives to the quotation (ADR-006): what the template is for.
TEMPLATE_CASE_FIELDS = {"boss_business": "boss_business", "boss_direction": "boss_direction",
                        "boss_transport_mode": "boss_transport_mode", "boss_load_type": "boss_load_type",
                        "boss_incoterm_id": "incoterm"}


class SaleOrder(models.Model):
    _name = "sale.order"
    _inherit = ["sale.order", "boss.shipment.route"]

    # Shipment data needed to price the quotation (ADR-003); route, dates and weights: boss.shipment.route (ADR-006).
    boss_container_ids = fields.One2many("boss.shipment.container", "order_id", "Containers", copy=True)
    boss_pallets = fields.Integer("Pallets")
    boss_goods_value = fields.Monetary("Goods value", currency_field="currency_id",
                                       help="Commercial value of the goods (insurance, value brackets).")
    boss_duties_amount = fields.Monetary("Customs duties (estimate)", currency_field="currency_id",
                                         help="Duties and taxes of the customs declaration, for the guarantee fee.")
    boss_storage_days = fields.Integer(
        "Days in storage (estimate)",
        help="Days assumed for storage, demurrage and port occupancy in the quotation; normally 0 (BOSS does not "
        "plan storage unless the customer says the cargo will wait). The actual cost is known when the period ends.")
    # An integer cannot be empty in Odoo: this flag told 'not indicated yet' from a deliberate 0 days. Since the
    # meeting of 27/10/2026 the estimate is 0 days unless another figure is entered (ADR-006): set by default.
    boss_storage_days_known = fields.Boolean(
        "Days indicated", default=True,
        help="Cleared only by code that has no estimate yet: time-based services then show 'missing shipment "
        "data'.")
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
            "awb_kg": self._boss_awb_weight(),
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

    def _boss_container_groups(self):
        return sorted({(c.size, c.container_type_id) for c in self.boss_container_ids},
                      key=lambda g: (g[0], g[1].sequence))

    @staticmethod
    def _boss_per_container(product, uom):
        return bool(product.boss_pricing_mode) and uom.boss_quantity_source in ("container", "teu")

    @api.onchange("sale_order_template_id")
    def _onchange_sale_order_template_id(self):
        """The template lists the services of a case; container services become one line per container size and
        type of the shipment, like «Add services» does (they may be priced and sold differently).
        Odoo replaces every line when a template is chosen: on a quotation that already has services that would
        silently delete the work done (prices, suppliers, added services). Then nothing is removed: only the services
        of the template that are missing are added, and the user is told which."""
        if not self.sale_order_template_id:
            return None
        self._boss_apply_template_case()
        existing = self.order_line.filtered(lambda l: l.product_id and not l.display_type)
        if existing:
            return self._boss_merge_template(existing)
        super()._onchange_sale_order_template_id()
        groups = self._boss_container_groups()
        if not groups:
            return None
        added = []
        for line in self.order_line:
            if not line.boss_container_size and self._boss_per_container(line.product_id, line.product_uom_id):
                (line.boss_container_size, line.boss_container_type_id), *rest = groups
                added += [Command.create({"product_id": line.product_id.id, "product_uom_id": line.product_uom_id.id,
                                          "boss_container_size": size, "boss_container_type_id": ctype.id,
                                          "sequence": line.sequence}) for size, ctype in rest]
        if added:
            self.update({"order_line": added})
        return None

    def _boss_apply_template_case(self):
        """The template says which case it is (air import FOB, sea import FCL...): its direction, mode, load type,
        incoterm and whose client fill the quotation; what it leaves empty stays as it is."""
        template = self.sale_order_template_id
        for template_field, order_field in TEMPLATE_CASE_FIELDS.items():
            if template[template_field]:
                self[order_field] = template[template_field]
        self._onchange_boss_direction_spain()

    def _boss_merge_template(self, existing):
        _ = self.env._
        template = self.sale_order_template_id.with_context(lang=self.partner_id.lang).with_company(self.company_id)
        groups = self._boss_container_groups()
        have = {(l.product_id, l.boss_container_size or False, l.boss_container_type_id) for l in existing}
        sequence = max(self.order_line.mapped("sequence") or [10])
        commands, added, present = [], [], []
        for t_line in template.sale_order_template_line_ids.filtered(lambda t: t.product_id and not t.display_type):
            product = t_line.product_id
            if groups and self._boss_per_container(product, t_line.product_uom_id):
                keys = [(size, ctype) for size, ctype in groups if (product, size, ctype) not in have]
            else:
                keys = [] if product in existing.product_id else [(False, False)]
            if not keys:
                present.append(product.default_code or product.name)
                continue
            for size, ctype in keys:
                sequence += 1
                vals = t_line._prepare_order_line_values(self.fiscal_position_id, self.currency_id)
                vals["sequence"] = sequence
                if size:
                    vals.update(boss_container_size=size, boss_container_type_id=ctype.id)
                commands.append(Command.create(vals))
            added.append(product.default_code or product.name)
        if commands:
            self.update({"order_line": commands})
        return {"warning": {
            "title": _("Template applied without removing anything"),
            "message": _("Added: %(added)s. Already on the quotation (kept as they are): %(present)s. Delete by hand "
                         "the services that do not apply.", added=", ".join(added) or "-",
                         present=", ".join(present) or "-"),
            "type": "notification"}}

    def _boss_quantity(self, source, size=False, ctype=False):
        """Quantity of a charge basis taken from the shipment, or None when entered on the line."""
        self.ensure_one()
        return shipment_quantity(
            source, [(c.size, c.container_type_id, c.quantity) for c in self.boss_container_ids], self.boss_gross_kg,
            self.boss_volume_m3, self.boss_pallets, self._boss_awb_weight(), size, ctype)

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

    def action_boss_add_service(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window", "res_model": "boss.add.service.wizard", "view_mode": "form",
            "views": [(False, "form")], "target": "new", "name": self.env._("Add a service after acceptance"),
            "context": {"default_order_id": self.id},
        }

    def action_boss_reprice(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window", "res_model": "boss.reprice.wizard", "view_mode": "form",
            "views": [(False, "form")], "target": "new", "name": self.env._("Re-price accepted quotation"),
            "context": {"default_order_id": self.id},
        }

    def _boss_check_costs(self):
        """Acceptance needs the cost of every service bought from a supplier (Odoo 19 decision B22), unless a sales
        manager recorded why it is accepted without it."""
        for order in self:
            unknown = order.order_line.filtered(
                lambda l: l.boss_cost_kind == "unknown" and not l.boss_unknown_cost_reason)
            if unknown:
                raise UserError(self.env._(
                    "%(order)s cannot be accepted: the supplier cost of these services is unknown:\n%(lines)s\n"
                    "Complete the cost (supplier price or manual cost), mark the service as executed by BOSS, or "
                    "ask a sales manager to record why it is accepted without it.", order=order.name,
                    lines="\n".join(f"- {line.product_id.display_name}" for line in unknown)))

    def action_confirm(self):
        self._boss_check_ready()
        self._boss_check_costs()
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
