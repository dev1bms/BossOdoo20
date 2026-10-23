from odoo import api, fields, models

from odoo.addons.boss_pricing.models.boss_container_type import CONTAINER_SIZES
from odoo.addons.boss_pricing.models.boss_pricing import COST_STATUSES
from odoo.addons.boss_pricing.models.boss_tariff import DIRECTIONS, LOAD_TYPES, TRANSPORT_MODES

# Shipment fields of the panel = fields of the quotation (sale.order) with the same meaning.
ORDER_FIELDS = {
    "direction": "boss_direction", "transport_mode": "boss_transport_mode", "load_type": "boss_load_type",
    "carrier_id": "boss_carrier_id", "port_id": "boss_port_id", "country_id": "boss_country_id",
    "state_id": "boss_inland_state_id", "date": "boss_planned_date", "gross_kg": "boss_gross_kg",
    "awb_kg": "boss_awb_kg", "volume_m3": "boss_volume_m3", "pallets": "boss_pallets",
    "goods_value": "boss_goods_value", "duties_amount": "boss_duties_amount", "storage_days": "boss_storage_days",
    "storage_days_known": "boss_storage_days_known", "customer_id": "partner_id",
}
INPUT_FIELDS = (*ORDER_FIELDS, "product_id", "uom_id", "supplier_id", "simulate_tariff_ids", "container_size",
                "container_type_id", "container_qty", "line_qty", "base_amount", "pricelist_id", "storage_start",
                "storage_end")


class BossPricingTest(models.TransientModel):
    """'Test pricing': the same pricing service as quotations (boss.pricing.price_cost) on a shipment typed
    here, with its explanation. Nothing is saved on quotations or tariffs."""

    _name = "boss.pricing.test"
    _description = "Test pricing"

    sale_line_id = fields.Many2one("sale.order.line", "From quotation line", readonly=True)
    product_id = fields.Many2one("product.product", "Service", domain="[('boss_pricing_mode', '!=', False)]")
    allowed_uom_ids = fields.Many2many("uom.uom", compute="_compute_allowed_uom_ids")
    uom_id = fields.Many2one("uom.uom", "Charge basis", domain="[('id', 'in', allowed_uom_ids)]")
    supplier_id = fields.Many2one("res.partner", "Supplier", help="Empty: any supplier (like a quotation line "
                                  "without supplier).")
    simulate_tariff_ids = fields.Many2many(
        "boss.tariff", string="Simulate drafts", domain="[('state', '!=', 'approved')]",
        help="Tariffs not approved yet that count as approved in this test only. Quotations never use them.")
    date = fields.Date("Planned date", default=fields.Date.context_today,
                       help="Picks the tariff version (ETA for imports, ETD for exports).")
    direction = fields.Selection(DIRECTIONS)
    transport_mode = fields.Selection(TRANSPORT_MODES)
    load_type = fields.Selection(LOAD_TYPES)
    carrier_id = fields.Many2one("res.partner", "Carrier")
    port_id = fields.Many2one("boss.port", "Spanish port / airport")
    country_id = fields.Many2one("res.country", "Country abroad")
    state_id = fields.Many2one("res.country.state", "Province (inland)", domain="[('country_id.code', '=', 'ES')]")
    customer_id = fields.Many2one("res.partner", "Customer", help="Optional: for prices agreed with a customer "
                                  "and for the sale price.")
    pricelist_id = fields.Many2one("product.pricelist", "Pricelist", compute="_compute_pricelist_id", store=True,
                                   readonly=False, help="Optional: shows the sale price and the profit.")
    container_size = fields.Selection(CONTAINER_SIZES, "Container size")
    container_type_id = fields.Many2one("boss.container.type", "Container type",
                                        help="Empty: dry standard (DV).")
    container_qty = fields.Integer("Containers", default=1)
    gross_kg = fields.Float("Gross weight (kg)")
    awb_kg = fields.Float("Chargeable weight (AWB, kg)")
    volume_m3 = fields.Float("Volume (m³)", digits=(12, 3))
    pallets = fields.Integer()
    goods_value = fields.Float()
    duties_amount = fields.Float("Customs duties")
    storage_days = fields.Integer("Days")
    storage_days_known = fields.Boolean("Days known", help="Unticked: the days are not known yet (not zero).")
    storage_start = fields.Datetime(
        "Period start", help="Actual start of a time-based service (storage: arrival notice NOA or freight on hand "
        "FOH; demurrage: the carrier's event). With the end, it replaces the days: exact hours and weekdays.")
    storage_end = fields.Datetime("Period end", help="Actual end (pickup / exit of the goods, return of the "
                                  "container).")
    line_qty = fields.Float("Quantity typed on the line", default=1.0,
                            help="Used when the charge basis is not taken from the shipment (e.g. km, hours).")
    base_amount = fields.Float("Cost of the base services",
                               help="For a percentage of other services of the same supplier (e.g. fuel surcharge).")
    # Result (computed live, never stored on a quotation)
    quantity_source = fields.Selection(related="uom_id.boss_quantity_source")
    quantity = fields.Float(compute="_compute_result")
    status = fields.Selection(COST_STATUSES, compute="_compute_result")
    cost_amount = fields.Monetary("Expected cost", currency_field="cost_currency_id", compute="_compute_result")
    cost_currency_id = fields.Many2one("res.currency", compute="_compute_result")
    tariff_line_id = fields.Many2one("boss.tariff.line", "Supplier price used", compute="_compute_result")
    explanation = fields.Text(compute="_compute_result")
    choice = fields.Text("Why this price", compute="_compute_result")
    simulated = fields.Boolean(compute="_compute_result",
                               help="The price used is not approved: the result is a simulation, not usable in "
                               "quotations until the tariff is approved.")
    sale_currency_id = fields.Many2one("res.currency", compute="_compute_result")
    sale_unit = fields.Monetary("Sale price per unit", currency_field="sale_currency_id", compute="_compute_result")
    sale_total = fields.Monetary("Sale", currency_field="sale_currency_id", compute="_compute_result")
    profit = fields.Monetary(currency_field="sale_currency_id", compute="_compute_result")
    sale_note = fields.Char("Sale rule", compute="_compute_result")

    @api.model
    def default_get(self, fields_list):
        values = super().default_get(fields_list)
        line = self.env["sale.order.line"].browse(self.env.context.get("default_sale_line_id"))
        if line:
            order = line.order_id
            values.update({name: order[ofield].id if hasattr(order[ofield], "ids") else order[ofield]
                           for name, ofield in ORDER_FIELDS.items()})
            # the containers of this line (its size and type), like the quotation groups them
            rows = order.boss_container_ids.filtered(
                lambda c: (not line.boss_container_size or c.size == line.boss_container_size)
                and (not line.boss_container_type_id or c.container_type_id == line.boss_container_type_id))
            values.update({"product_id": line.product_id.id, "uom_id": line.product_uom_id.id,
                           "supplier_id": line.boss_supplier_id.id, "pricelist_id": order.pricelist_id.id,
                           "container_size": line.boss_container_size or rows[:1].size,
                           "container_type_id": (line.boss_container_type_id or rows[:1].container_type_id).id,
                           "container_qty": sum(rows.mapped("quantity")) or 1,
                           "line_qty": line.product_uom_qty})
            if line.boss_days_source != "shipment":
                values.update(storage_days=line.boss_days, storage_days_known=True)
        return values

    @api.depends("product_id")
    def _compute_allowed_uom_ids(self):
        for test in self:
            test.allowed_uom_ids = test.product_id.product_tmpl_id._boss_charge_bases() if test.product_id else False

    @api.onchange("product_id")
    def _onchange_product_id(self):
        allowed = self.product_id.product_tmpl_id._boss_charge_bases() if self.product_id else False
        if allowed and self.uom_id not in allowed:
            self.uom_id = self.product_id.uom_id

    @api.onchange("storage_days")
    def _onchange_storage_days(self):
        if self.storage_days:  # 0 is a valid estimate too: then tick «Days known» by hand
            self.storage_days_known = True

    @api.depends("customer_id")
    def _compute_pricelist_id(self):
        for test in self:
            if test.customer_id:
                test.pricelist_id = test.customer_id.property_product_pricelist

    def _shipment(self):
        """In-memory quotation with the panel's shipment: its inputs and quantities are the quotation's own."""
        values = {ofield: self[name].id if hasattr(self[name], "ids") else self[name]
                  for name, ofield in ORDER_FIELDS.items()}
        values["company_id"] = self.env.company.id
        if self.container_size and self.container_qty:
            # no type given: the containers count as dry standard (a price for any type still applies)
            ctype = self.container_type_id or self.env.ref("boss_pricing.container_type_dv")
            values["boss_container_ids"] = [(0, 0, {"size": self.container_size, "quantity": self.container_qty,
                                                    "container_type_id": ctype.id})]
        return self.env["sale.order"].new(values)

    def _inputs(self, order):
        inputs = order._boss_shipment_inputs()
        quantity = order._boss_quantity(self.uom_id.boss_quantity_source, self.container_size,
                                        self.container_type_id)
        inputs.update({"line_qty": self.line_qty if quantity is None else quantity,
                       "container_size": self.container_size or None,
                       "container_type_id": self.container_type_id.id or None,
                       "supplier_id": self.supplier_id.id or None})
        inputs.update(self.env["boss.pricing"]._warehouse_period(self.storage_start, self.storage_end, self.port_id))
        if self.base_amount:
            lines = self.env["boss.tariff.line"].search([("product_id", "=", self.product_id.id),
                                                         ("uom_id", "=", self.uom_id.id), ("method", "=", "percent")])
            inputs["related_costs"] = list({
                (ln.partner_id.id, product.id): {"product_id": product.id, "supplier_id": ln.partner_id.id,
                                                 "amount": self.base_amount, "currency": ln.currency_id.name}
                for ln in lines for product in ln.base_product_ids[:1]}.values())
        return inputs

    @api.depends(*INPUT_FIELDS)
    @api.depends_context("lang")
    def _compute_result(self):
        _ = self.env._
        pricing = self.env["boss.pricing"]
        for test in self:
            test.update({"quantity": 0.0, "status": False, "cost_amount": 0.0, "cost_currency_id": False,
                         "tariff_line_id": False, "explanation": False, "choice": False, "sale_unit": 0.0,
                         "sale_total": 0.0, "profit": 0.0, "sale_note": False, "sale_currency_id": False,
                         "simulated": False})
            if not test.product_id or not test.uom_id:
                test.explanation = _("Choose a service and its charge basis.")
                continue
            order = test._shipment()
            inputs = test._inputs(order)
            res = pricing.price_cost(test.product_id, test.uom_id, inputs, test.date, self.env.company,
                                     simulate=test.simulate_tariff_ids._origin)  # real tariffs, also live
            test.quantity = inputs["line_qty"] or 0.0
            test.status = res.status
            test.cost_amount = res.amount
            test.cost_currency_id = res.currency or res.line.currency_id
            test.tariff_line_id = res.line
            test.simulated = bool(res.line) and res.line.tariff_id.state != "approved"
            test.explanation = pricing.explain(test.product_id, test.uom_id, res.status, res.amount, res.line,
                                               res.candidates, res.missing, res.steps)
            test.choice = test._choice_text(res)
            if res.status == "ok":
                test._sale_price(res)

    def _choice_text(self, res):
        _ = self.env._
        others = self.env["boss.tariff.line"].search_count([
            ("product_id", "=", self.product_id.id), ("uom_id", "=", self.uom_id.id),
            ("tariff_id.company_id", "=", self.env.company.id), ("id", "!=", res.line.id)])
        lines = []
        if res.line:
            tariff = res.line.tariff_id
            state = (_("simulated (not approved)") if tariff.state != "approved"
                     else _("approved by %s", tariff.approved_by_id.name or "-"))
            lines.append(_("%(price)s · %(tariff)s v%(version)s · %(state)s",
                           price=res.line.price_display, tariff=tariff.name, version=tariff.version, state=state))
            lines.append(_("Applies to: %s", res.line.scope_display))
            lines.append(_("Chosen because it is valid on the date, applies to this shipment and is the most "
                           "specific (customer, then carrier, port...), then the newest version."))
        if res.candidates and res.status != "ok":
            lines.append(_("Prices involved: %s", ", ".join(res.candidates.mapped("display_name"))))
        lines.append(_("Other prices of this service and charge basis: %s (other supplier, scope, date or "
                       "approval).", others))
        if self.simulate_tariff_ids:
            lines.append(_("Simulation: %s counted as approved in this test only.",
                           ", ".join(self.simulate_tariff_ids.mapped("name"))))
        return "\n".join(lines)

    def _sale_price(self, res):
        """Sale price with the pricelist's own rule functions, as on a quotation line (cost per unit)."""
        _ = self.env._
        pricelist = self.pricelist_id
        if not pricelist or not self.quantity:
            self.sale_note = _("Choose a customer or a pricelist to see the sale price.")
            return
        currency = pricelist.currency_id
        cost = (res.currency or currency)._convert(res.amount, currency, self.env.company,
                                                   self.date or fields.Date.today())
        price, rule_id = pricelist._compute_price_rule(
            self.product_id, self.quantity, currency=currency, uom=self.uom_id, date=self.date,
            boss_unit_cost=cost / self.quantity)[self.product_id.id]
        rule = self.env["product.pricelist.item"].browse(rule_id)
        self.sale_currency_id = currency
        self.sale_unit = price
        self.sale_total = currency.round(price * self.quantity)
        self.profit = self.sale_total - cost
        self.sale_note = rule.price if rule else _("No rule: sales price of the product")

    @api.model
    def _open(self, values):
        """The panel in a dialog, pre-filled with `values` (field name -> value)."""
        return {"type": "ir.actions.act_window", "res_model": self._name, "view_mode": "form",
                "views": [(False, "form")], "target": "new", "name": self.env._("Test pricing"),
                "context": {f"default_{name}": value for name, value in values.items() if value}}
