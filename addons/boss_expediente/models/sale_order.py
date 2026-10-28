from odoo import Command, api, fields, models
from odoo.exceptions import ValidationError

from .boss_airline_handler import HANDLER_SERVICE_CODES
from odoo.addons.boss_pricing_sale.models.boss_shipment_route import key_date

from .boss_expediente import FROM_ORDER, PACKAGE_TYPES, SCOPES, with_accounts


class SaleOrder(models.Model):
    _inherit = "sale.order"

    # Scope agreed with the customer (the quotation basis; route: boss.shipment.route); the file keeps the actual data.
    boss_scope_pickup = fields.Boolean("Pickup")
    boss_scope_origin_customs = fields.Boolean("Customs at origin")
    boss_scope_main = fields.Boolean("Main carriage")
    boss_scope_destination_customs = fields.Boolean("Customs at destination")
    boss_scope_delivery = fields.Boolean("Delivery")
    boss_goods_description = fields.Char("Goods")
    boss_packages = fields.Integer("Packages")
    boss_package_type = fields.Selection(PACKAGE_TYPES, "Type of unit",
                                         help="What the packages are: cartons, pallets, crates... (Odoo 17 partida).")
    boss_hs_code = fields.Char("Goods code (HS)", help="Customs tariff code of the goods: it decides the duties "
                               "(Ángel, 27/10/2026). Information for the customs declaration; the duties estimate is typed.")
    boss_requested_service_ids = fields.Many2many(
        "product.product", string="Requested services",
        domain="[('boss_pricing_mode', '!=', False), ('sale_ok', '=', True)]",
        help="Services the customer asked for (from the opportunity); proposed by 'Add services'.")
    boss_expediente_id = fields.Many2one(
        "boss.expediente", "File", copy=False, index="btree_not_null", tracking=True,
        domain="[('state', '!=', 'cancel'), ('financial_closed', '=', False)]",
        help="Shipment file of this order. Empty: opened when the quotation is accepted. Choose a file to add a "
        "service sold later or to link a file opened before the quotation (pre-alert).")

    def _boss_apply_template_case(self):
        """The template also says what BOSS handles in this case (pickup, customs, main carriage, delivery)."""
        super()._boss_apply_template_case()
        template = self.sale_order_template_id
        if any(template[f"boss_scope_{scope}"] for scope in SCOPES):
            for scope in SCOPES:
                self[f"boss_scope_{scope}"] = template[f"boss_scope_{scope}"]

    def _boss_handler_candidates(self):
        """Handlers known for the airline at the airport of an air quotation (empty otherwise)."""
        self.ensure_one()
        if self.boss_transport_mode != "air":
            return self.env["res.partner"]
        return self.env["boss.airline.handler"]._handlers_for(self.boss_carrier_id, self.boss_port_id)

    @api.onchange("boss_carrier_id", "boss_port_id", "boss_transport_mode")
    def _onchange_boss_handler_supplier(self):
        """Airline or airport changed on the quotation: the handling lines without supplier, or with a handler no
        longer known for that pair, follow the new handler when exactly one is known."""
        for order in self:
            handlers = order._boss_handler_candidates()
            if len(handlers) != 1:
                continue
            for line in order.order_line.filtered(
                    lambda l: l.product_id.default_code in HANDLER_SERVICE_CODES and l.boss_supplier_id != handlers):
                line.boss_supplier_id = handlers
    boss_expediente_ids = fields.Many2many("boss.expediente", string="Files", compute="_compute_boss_expediente_ids",
                                           help="Every file with part of the accepted services of this order.")
    boss_expediente_count = fields.Integer(compute="_compute_boss_expediente_ids")

    @api.constrains("boss_expediente_id", "partner_id")
    def _check_boss_expediente_customer(self):
        for order in self.filtered("boss_expediente_id"):
            if order.partner_id.commercial_partner_id != order.boss_expediente_id.partner_id.commercial_partner_id:
                raise ValidationError(self.env._(
                    "%(order)s and file %(file)s have different customers.", order=order.name,
                    file=order.boss_expediente_id.name))

    def _boss_file_values(self):
        """A new file starts from the accepted quotation; afterwards each keeps its own data."""
        self.ensure_one()
        values = {}
        for file_field, order_field in FROM_ORDER.items():
            value = self[order_field]
            values[file_field] = value.id if isinstance(value, models.BaseModel) else value
        if not (self.boss_etd or self.boss_eta) and self.boss_planned_date:
            values[key_date(self.boss_direction)] = self.boss_planned_date
        company_currency = self.company_id.currency_id
        for file_field, order_field in (("goods_value", "boss_goods_value"), ("duties_amount", "boss_duties_amount")):
            values[file_field] = self.currency_id._convert(self[order_field], company_currency, self.company_id,
                                                           fields.Date.to_date(self.date_order) or fields.Date.today())
        values.update({
            "partner_id": self.partner_id.commercial_partner_id.id, "user_id": self.user_id.id,
            "company_id": self.company_id.id, "haulier_id": self.boss_haulier_id.id,
            "container_ids": [Command.create({"size": c.size, "container_type_id": c.container_type_id.id})
                              for c in self.boss_container_ids for _ in range(c.quantity)],
        })
        return values

    def _boss_open_files(self):
        """Accepted BOSS orders get a file once: the linked one (preliminary file or service sold later) or a new
        one. Confirming again or twice never opens a second file."""
        File = self.env["boss.expediente"]
        for order in self.filtered(lambda o: o.state == "sale" and o.order_line._boss_lines()):
            file = order.boss_expediente_id or File.create(order._boss_file_values())
            if order.boss_expediente_id != file:
                order.boss_expediente_id = file
            file._boss_link_orders(order)

    def action_confirm(self):
        res = super().action_confirm()
        self._boss_open_files()
        return res

    @api.depends("order_line.boss_allocation_ids.expediente_id", "boss_expediente_id")
    def _compute_boss_expediente_ids(self):
        for order in self:
            order.boss_expediente_ids = order.boss_expediente_id | order.order_line.boss_allocation_ids.expediente_id
            order.boss_expediente_count = len(order.boss_expediente_ids)

    def action_boss_open_file(self):
        self.ensure_one()
        files = self.boss_expediente_ids
        if len(files) == 1:
            return {"type": "ir.actions.act_window", "res_model": "boss.expediente", "view_mode": "form",
                    "views": [(False, "form")], "res_id": files.id}
        return {"type": "ir.actions.act_window", "res_model": "boss.expediente", "view_mode": "list,form",
                "views": [(False, "list"), (False, "form")], "domain": [("id", "in", files.ids)],
                "name": self.env._("Files of %s", self.name)}

    def _get_invoiceable_lines(self, final=False):
        """Invoice selected services only (milestones, partial invoicing): the selection comes from the 'Invoice
        services' wizard; without it the standard rule applies."""
        lines = super()._get_invoiceable_lines(final)
        selected = self.env.context.get("boss_invoice_line_ids")
        if selected is None:
            return lines
        return lines.filtered(lambda l: l.id in selected)


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    boss_allocation_ids = fields.One2many("boss.expediente.allocation", "sale_line_id", "Files", copy=False)

    @api.model_create_multi
    def create(self, vals_list):
        """Air handling services (HAN, ALM, AWB, ETX, X-R) are bought from the handler of the airline at the airport:
        when the quotation knows exactly one, it becomes the supplier of the line (only its tariffs price it)."""
        Order = self.env["sale.order"]
        for vals in vals_list:
            if vals.get("boss_supplier_id") or not vals.get("order_id") or not vals.get("product_id"):
                continue
            product = self.env["product.product"].browse(vals["product_id"])
            if product.default_code in HANDLER_SERVICE_CODES:
                handlers = Order.browse(vals["order_id"])._boss_handler_candidates()
                if len(handlers) == 1:
                    vals["boss_supplier_id"] = handlers.id
        return super().create(vals_list)

    def _boss_posted_invoiced_qty(self):
        """Quantity invoiced to the customer on posted invoices, minus posted credit notes (drafts do not count)."""
        self.ensure_one()
        return sum(-l.quantity if l.move_id.move_type == "out_refund" else l.quantity
                   for l in self.invoice_lines.filtered(lambda l: l.parent_state == "posted"))

    def _boss_sync_file_analytic(self):
        """Analytic distribution of each line = its shares in the files (accepted quantity of each file), the
        accounts of other plans kept."""
        Account = self.env["account.analytic.account"]
        plan = self.env.ref("boss_expediente.analytic_plan_files")
        for line in self.filtered("boss_allocation_ids"):
            allocated = sum(line.boss_allocation_ids.mapped("quantity"))
            if not allocated:
                continue
            shares = {}
            for allocation in line.boss_allocation_ids:
                account = allocation.expediente_id.analytic_account_id
                shares[account.id] = shares.get(account.id, 0.0) + allocation.quantity * 100.0 / allocated
            present = Account.browse({int(key) for combination in (line.analytic_distribution or {})
                                      for key in combination.split(",") if key.strip()}).exists()
            plan_accounts = present.filtered(lambda a: a.plan_id == plan) | Account.browse(list(shares))
            distribution = with_accounts(line.analytic_distribution, shares, plan_accounts)
            if distribution != line.analytic_distribution:
                # done right after the confirmation, when Odoo may already have locked the order
                line.with_context(boss_file_analytic=True).analytic_distribution = distribution

    def _get_protected_fields(self):
        """A locked order (setting «Lock confirmed sales») still gets the analytic account of its files: BOSS writes
        it on acceptance and when services move between files. Only that write, nothing else, passes the lock."""
        fields = super()._get_protected_fields()
        if self.env.context.get("boss_file_analytic"):
            fields = [f for f in fields if f != "analytic_distribution"]
        return fields


class BossAddServiceWizard(models.TransientModel):
    _inherit = "boss.add.service.wizard"

    def action_apply(self):
        res = super().action_apply()
        file = self.order_id.boss_expediente_id
        if file:
            file._boss_link_orders(self.order_id)  # analytic account and, for a supplier, the service to buy
        return res


class BossAddServices(models.TransientModel):
    _inherit = "boss.add.services"

    @api.model
    def default_get(self, fields_list):
        values = super().default_get(fields_list)
        order = self.env["sale.order"].browse(values.get("order_id") or self.env.context.get("default_order_id"))
        if "product_ids" in fields_list and not values.get("product_ids") and order.boss_requested_service_ids:
            missing = order.boss_requested_service_ids - order.order_line.product_id
            values["product_ids"] = [Command.set(missing.ids)]
        return values
