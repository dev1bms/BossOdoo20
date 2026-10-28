from odoo import Command, api, fields, models
from odoo.exceptions import UserError

from .boss_shipment_container import shipment_quantity
from .boss_shipment_route import spanish_side

# Case data a quotation template gives to the quotation (ADR-006): what the template is for.
# Road transport services (inland leg): their supplier is the haulier, the inland carrier (Ángel, 27/10/2026).
ROAD_SERVICE_CODES = ("TTE-CON", "TTE-FCL")
TEMPLATE_CASE_FIELDS = {"boss_business": "boss_business", "boss_direction": "boss_direction",
                        "boss_transport_mode": "boss_transport_mode", "boss_load_type": "boss_load_type",
                        "boss_incoterm_id": "incoterm"}


class SaleOrder(models.Model):
    _name = "sale.order"
    _inherit = ["sale.order", "boss.shipment.route"]

    # Shipment data needed to price the quotation (ADR-003); route, dates and weights: boss.shipment.route (ADR-006).
    boss_container_ids = fields.One2many("boss.shipment.container", "order_id", "Containers", copy=True)
    boss_haulier_id = fields.Many2one(
        "res.partner", "Inland carrier (haulier)", compute="_compute_boss_haulier_id",
        help="Supplier of the road transport line (pickup or delivery): chosen on that line, as any supplier. The "
        "main carrier is the shipping line or airline.")
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
    boss_rate_quotation = fields.Boolean(
        "Rate quotation (no quantities)", copy=True,
        help="The customer asks for rates (per container of each size, per B/L...) without saying how many "
        "containers will ship: per-container services are priced for one unit of their size, the document shows "
        "unit rates and no total, and the containers are entered before acceptance (Ángel, 27/10/2026).")

    def _boss_shipment_inputs(self):
        """Shipment inputs for boss.pricing, named like the tariff scope (one meaning per name)."""
        self.ensure_one()
        return {
            "direction": self.boss_direction,
            "transport_mode": self.boss_transport_mode,
            "load_type": self.boss_load_type,
            "carrier_id": self.boss_carrier_id._boss_carrier_family().id if self.boss_carrier_id else False,
            "port_id": self.boss_port_id.id,
            "foreign_port_id": self._boss_foreign_port().id,
            "country_id": self.boss_country_id.id,
            "state_id": self.boss_inland_state_id.id,
            "customer_id": self.partner_id.commercial_partner_id.id,
            # always given: demo tariffs never price a real customer, not even "for lack of input"
            "tariff_use": "demo" if self.partner_id.commercial_partner_id.boss_demo else "real",
            "containers": [{"size": c.size, "type_id": c.container_type_id.id, "quantity": c.quantity}
                           for c in self.boss_container_ids],
            "gross_kg": self.boss_gross_kg or None,
            "awb_kg": self._boss_awb_weight(),
            "chargeable_kg": self.boss_chargeable_kg or None,
            "chargeable_kg_by_mode": self._boss_chargeable_by_mode(),
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
        res = super().write(vals)
        if "boss_container_ids" in vals:
            self.filtered(lambda o: not o.boss_pricing_frozen)._boss_assign_container_groups()
        return res

    @api.depends("order_line.boss_supplier_id", "order_line.product_id")
    def _compute_boss_haulier_id(self):
        for order in self:
            order.boss_haulier_id = order._boss_road_lines().boss_supplier_id[:1]

    def _boss_road_lines(self):
        """Road transport services of the quotation (inland leg), whatever the main mode of the shipment."""
        return self.order_line.filtered(lambda l: l.product_id.default_code in ROAD_SERVICE_CODES)

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
        self._boss_assign_container_groups()
        return None

    def _boss_assign_container_groups(self):
        """Per-container services without a size take the containers of the shipment: the first size and type on the
        existing line, one more line per other size and type, like the template and «Add services» do. Lines already
        sized, frozen or not priced per container are left alone. Also run when the containers are entered after the
        services (Ángel's order of steps on 27/10/2026: template first, then 1×40'): otherwise size-dependent prices
        (T3-PAD, GLO-CCC) stay «missing shipment data»."""
        for order in self:
            groups = order._boss_container_groups()
            if not groups:
                continue
            added = []
            for line in order.order_line.filtered(
                    lambda l: l.product_id and not l.display_type and not l.boss_price_frozen
                    and not l.boss_container_size and self._boss_per_container(l.product_id, l.product_uom_id)):
                (line.boss_container_size, line.boss_container_type_id), *rest = groups
                added += [Command.create({"product_id": line.product_id.id, "product_uom_id": line.product_uom_id.id,
                                          "boss_container_size": size, "boss_container_type_id": ctype.id,
                                          "sequence": line.sequence}) for size, ctype in rest]
            if added:
                order.update({"order_line": added})

    @api.onchange("boss_container_ids")
    def _onchange_boss_container_ids(self):
        self._boss_assign_container_groups()

    def _boss_apply_template_case(self):
        """The template says which case it is (air import FOB, sea import FCL...): its direction, mode, load type,
        incoterm and whose client fill the quotation; what it leaves empty stays as it is."""
        template = self.sale_order_template_id
        for template_field, order_field in TEMPLATE_CASE_FIELDS.items():
            if template[template_field]:
                self[order_field] = template[template_field]
        self._onchange_boss_direction_spain()
        self._boss_apply_orderer_party()

    @api.onchange("partner_id", "boss_direction", "boss_business")
    def _onchange_boss_orderer_party(self):
        self._boss_apply_orderer_party()

    @api.onchange("boss_delivery_address_id", "boss_pickup_address_id", "boss_direction")
    def _onchange_boss_spanish_address(self):
        """Odoo's own «Delivery Address» of the quotation (invoicing, standard) follows the BOSS address of the
        Spanish side when it belongs to the ordering party (the warehouse chosen among the customer's addresses), so
        the header and the Shipment tab never show two different addresses of the same customer."""
        side = spanish_side(self.boss_direction)
        address = self.boss_delivery_address_id if side == "destination" else self.boss_pickup_address_id
        if address and address.commercial_partner_id == self.partner_id.commercial_partner_id:
            self.partner_shipping_id = address

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
            self.boss_volume_m3, self.boss_pallets, self._boss_awb_weight(), size, ctype,
            chargeable_kg=self.boss_chargeable_kg, chargeable_by_mode=self._boss_chargeable_by_mode())

    @api.depends("order_line.boss_cost_status", "order_line.boss_sale_status", "order_line.boss_vat_status",
                 "order_line.boss_manual_cost", "partner_id.commercial_partner_id.country_id")
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
                if count and field_name == "boss_vat_status" and order._boss_customer_zone_missing():
                    label = self.env._("VAT pending (customer without country: set it on the contact)")
                if count:
                    issues.append(f"{label}: {count}")
            order.boss_pricing_alert = " · ".join(issues) if issues else False

    def _boss_customer_zone_missing(self):
        """The customer's VAT zone is unknown: no country on the contact (or a province Odoo cannot place)."""
        self.ensure_one()
        customer = self.partner_id.commercial_partner_id
        return bool(customer) and not customer.country_id

    def _boss_readiness_issues(self):
        """What stops this quotation from being sent or accepted, grouped by cause (not one line per service):
        the customer without country, the sale prices missing, the VAT treatments pending."""
        self.ensure_one()
        _ = self.env._
        lines = self.order_line.filtered(lambda l: l.product_id.boss_pricing_mode and not l.display_type)
        code = lambda l: l.product_id.default_code or l.product_id.display_name  # noqa: E731
        issues = []
        missing_sale = lines.filtered(lambda l: l.boss_sale_status == "missing")
        if missing_sale:
            issues.append(_("Sale price missing on %(count)s services: %(codes)s. Type it on the line or set it in "
                            "the customer's pricelist.", count=len(missing_sale),
                            codes=", ".join(missing_sale.mapped(code))))
        pending_vat = lines.filtered(lambda l: l.boss_vat_status == "pending")
        if pending_vat and self._boss_customer_zone_missing():
            issues.append(_("VAT pending on %(count)s services because the customer «%(customer)s» has no country: "
                            "set the country (and tax ID) on the contact, then the VAT follows.",
                            count=len(pending_vat), customer=self.partner_id.commercial_partner_id.name))
        elif pending_vat:
            issues.append(_("VAT pending on %(count)s services:\n%(details)s", count=len(pending_vat),
                            details="\n".join(f"- {code(l)}: {l.boss_vat_trace or _('VAT pending')}"
                                               for l in pending_vat)))
        return issues

    def _boss_check_ready(self):
        """A quotation is not sent or accepted with an undecided VAT treatment or a missing sale price."""
        for order in self:
            issues = order._boss_readiness_issues()
            if issues:
                raise UserError(self.env._("%(order)s is not ready to send or accept.\n\n%(details)s",
                                           order=order.name, details="\n\n".join(issues)))

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

    def _boss_check_containers(self):
        """A rate quotation gives rates per container size (20', 40', 40' HC...) without knowing how many ship: the
        file needs the actual containers, so acceptance waits until they are entered, and the alternatives that
        are not shipped are named so that the person removes them or adds the container (Ángel, 27/10/2026: the
        client tells the number of containers when booking). Other quotations keep their behaviour (ADR-003)."""
        _ = self.env._
        for order in self.filtered("boss_rate_quotation"):
            per_container = order.order_line.filtered(
                lambda l: l.product_id.boss_pricing_mode and not l.display_type
                and l.product_uom_id.boss_quantity_source in ("container", "teu"))
            if not per_container:
                continue
            if not order.boss_container_ids:
                raise UserError(_(
                    "%s cannot be accepted yet: enter the containers of the shipment (size, type, quantity) in the "
                    "Shipment tab. The quotation gives rates per container; the file needs the actual containers.",
                    order.name))
            shipped = {(c.size, c.container_type_id) for c in order.boss_container_ids}
            shipped |= {(size, self.env["boss.container.type"]) for size, _type in shipped}
            unused = per_container.filtered(
                lambda l: l.boss_container_size and (l.boss_container_size, l.boss_container_type_id) not in shipped)
            if unused:
                raise UserError(_(
                    "%(order)s: these rates are for containers that are not in the shipment: %(lines)s. Remove the "
                    "lines the client did not book, or add the container to the shipment.", order=order.name,
                    lines=", ".join(f"{l.product_id.default_code or l.product_id.name} {l.boss_container_size}' "
                                    f"{l.boss_container_type_id.code or ''}".strip() for l in unused)))

    def action_confirm(self):
        self._boss_check_ready()
        self._boss_check_containers()
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
