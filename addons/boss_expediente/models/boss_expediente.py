from collections import defaultdict

from psycopg2 import errors as pg_errors

from odoo import Command, api, fields, models
from odoo.exceptions import UserError
from odoo.tools import float_compare
from odoo.tools.misc import formatLang

from odoo.addons.boss_pricing.models.boss_container_type import CONTAINER_SIZES
from odoo.addons.boss_pricing.models.boss_tariff import DIRECTIONS, LOAD_TYPES, TRANSPORT_MODES

STATES = [
    ("open", "Open"),
    ("in_transit", "In transit"),
    ("delivered", "Delivered"),
    ("closed", "Operations closed"),
    ("cancel", "Cancelled"),
]
SCOPES = ("pickup", "origin_customs", "main", "destination_customs", "delivery")
# Shipment data copied ONCE from the accepted quotation (file field: quotation field). From then on the file holds
# the actual data and the quotation keeps what was agreed; differences are shown, never synchronised.
FROM_ORDER = {
    "direction": "boss_direction", "transport_mode": "boss_transport_mode", "load_type": "boss_load_type",
    "carrier_id": "boss_carrier_id", "port_id": "boss_port_id", "country_id": "boss_country_id",
    "inland_state_id": "boss_inland_state_id", "incoterm_id": "incoterm", "origin_place": "boss_origin_place",
    "destination_place": "boss_destination_place", "shipper_id": "boss_shipper_id",
    "consignee_id": "boss_consignee_id", "goods_description": "boss_goods_description", "packages": "boss_packages",
    "gross_kg": "boss_gross_kg", "volume_m3": "boss_volume_m3", "awb_kg": "boss_awb_kg", "pallets": "boss_pallets",
    **{f"scope_{scope}": f"boss_scope_{scope}" for scope in SCOPES},
}
# Compared with the quotation in "Differences with the quotation" (data that changes the cost).
COMPARED = ("transport_mode", "load_type", "carrier_id", "port_id", "country_id", "inland_state_id", "gross_kg",
            "volume_m3", "awb_kg", "pallets")


def with_account(distribution, account):
    """Analytic distribution with the file's account added (100 % when empty, combined with other plans if set)."""
    key = str(account.id)
    if not distribution:
        return {key: 100.0}
    if any(key in combination.split(",") for combination in distribution):
        return distribution
    return {f"{combination},{key}": share for combination, share in distribution.items()}


def account_share(line, account):
    """Share (0-1) of a journal item that belongs to the analytic account."""
    key = str(account.id)
    return sum(share for combination, share in (line.analytic_distribution or {}).items()
               if key in combination.split(",")) / 100.0


class BossExpediente(models.Model):
    """Shipment file: who, route, cargo, references, dates and every linked document. Amounts are never typed here:
    they are read from the quotations, purchase orders, invoices and bills of the file (ADR-005)."""

    _name = "boss.expediente"
    _description = "Shipment file (expediente)"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "id desc"
    _check_company_auto = True

    name = fields.Char("Reference", required=True, readonly=True, copy=False, default="/", tracking=True)
    company_id = fields.Many2one("res.company", required=True, default=lambda self: self.env.company, index=True)
    currency_id = fields.Many2one(related="company_id.currency_id")
    partner_id = fields.Many2one(
        "res.partner", "Customer", required=True, tracking=True, index=True, check_company=True,
        help="Contracting customer: who orders the shipment and is invoiced.")
    user_id = fields.Many2one("res.users", "Responsible", default=lambda self: self.env.user, tracking=True)
    state = fields.Selection(STATES, default="open", required=True, tracking=True, copy=False)
    preliminary = fields.Boolean(
        compute="_compute_preliminary",
        help="Opened before an accepted quotation (pre-alert, documents received). Link the quotation when it is "
        "accepted.")
    # parties
    shipper_id = fields.Many2one("res.partner", "Shipper", tracking=True)
    consignee_id = fields.Many2one("res.partner", "Consignee", tracking=True)
    notify_id = fields.Many2one("res.partner", "Notify party")
    agent_id = fields.Many2one("res.partner", "Agent abroad", tracking=True)
    carrier_id = fields.Many2one("res.partner", "Carrier", tracking=True, help="Shipping line, airline or haulier.")
    haulier_id = fields.Many2one("res.partner", "Haulier")
    customs_broker_id = fields.Many2one("res.partner", "Customs broker")
    # route and scope
    direction = fields.Selection(DIRECTIONS, tracking=True)
    transport_mode = fields.Selection(TRANSPORT_MODES, "Transport mode", tracking=True)
    load_type = fields.Selection(LOAD_TYPES, "Load type", tracking=True)
    incoterm_id = fields.Many2one("account.incoterms", "Incoterm", tracking=True)
    port_id = fields.Many2one("boss.port", "Spanish port / airport", tracking=True)
    country_id = fields.Many2one("res.country", "Country abroad", tracking=True)
    inland_state_id = fields.Many2one("res.country.state", "Inland province",
                                      domain="[('country_id.code', '=', 'ES')]")
    origin_place = fields.Char("Origin (place)")
    destination_place = fields.Char("Destination (place)")
    scope_pickup = fields.Boolean("Pickup")
    scope_origin_customs = fields.Boolean("Customs at origin")
    scope_main = fields.Boolean("Main carriage")
    scope_destination_customs = fields.Boolean("Customs at destination")
    scope_delivery = fields.Boolean("Delivery")
    # cargo
    goods_description = fields.Char("Goods")
    packages = fields.Integer()
    gross_kg = fields.Float("Gross weight (kg)", digits=(12, 2), tracking=True)
    volume_m3 = fields.Float("Volume (m³)", digits=(12, 3), tracking=True)
    awb_kg = fields.Float("Chargeable weight (AWB, kg)", digits=(12, 2))
    pallets = fields.Integer()
    container_ids = fields.One2many("boss.expediente.container", "expediente_id", "Containers", copy=False)
    # references
    booking_ref = fields.Char("Booking", tracking=True)
    mbl_ref = fields.Char("Master BL", tracking=True)
    hbl_ref = fields.Char("House BL", tracking=True)
    mawb_ref = fields.Char("Master AWB", tracking=True)
    hawb_ref = fields.Char("House AWB", tracking=True)
    vessel = fields.Char("Vessel / flight")
    voyage = fields.Char("Voyage")
    customs_ref = fields.Char("Customs declaration (DUA)")
    # dates: estimated and actual are separate fields, the actual one never overwrites the estimate
    etd = fields.Date("ETD", tracking=True)
    eta = fields.Date("ETA", tracking=True)
    atd = fields.Date("ATD (actual departure)", tracking=True)
    ata = fields.Date("ATA (actual arrival)", tracking=True)
    pickup_date = fields.Date("Pickup (actual)")
    delivery_date = fields.Date("Delivery (actual)")
    event_ids = fields.One2many("boss.expediente.event", "expediente_id", "Events", copy=False)
    # links: every document points to the file, the file never duplicates their amounts
    sale_order_ids = fields.One2many("sale.order", "boss_expediente_id", "Quotations and orders")
    purchase_order_ids = fields.One2many("purchase.order", "boss_expediente_id", "Purchase orders")
    cost_ids = fields.One2many("boss.expediente.cost", "expediente_id", "Services to buy and extra costs")
    analytic_account_id = fields.Many2one("account.analytic.account", "Analytic account", readonly=True, copy=False,
                                          check_company=True)
    invoice_ids = fields.Many2many("account.move", compute="_compute_documents", compute_sudo=True, string="Customer invoices")
    bill_ids = fields.Many2many("account.move", compute="_compute_documents", compute_sudo=True, string="Vendor bills")
    sale_count = fields.Integer(compute="_compute_documents", compute_sudo=True)
    purchase_count = fields.Integer(compute="_compute_documents", compute_sudo=True)
    invoice_count = fields.Integer(compute="_compute_documents", compute_sudo=True)
    bill_count = fields.Integer(compute="_compute_documents", compute_sudo=True)
    quote_difference = fields.Text("Differences with the quotation", compute="_compute_quote_difference",
                                   compute_sudo=True)
    # profitability, company currency, untaxed, from posted documents and open purchase needs
    amount_sale = fields.Monetary("Agreed sale", compute="_compute_amounts", compute_sudo=True,
                                  help="Untaxed total of the confirmed sales of the file.")
    amount_sale_own = fields.Monetary("of which BOSS services", compute="_compute_amounts", compute_sudo=True)
    amount_on_behalf = fields.Monetary("of which paid on behalf", compute="_compute_amounts", compute_sudo=True,
                                       help="Amounts paid in the customer's name and re-invoiced at cost.")
    amount_cost_accepted = fields.Monetary("Expected cost at acceptance", compute="_compute_amounts", compute_sudo=True)
    amount_committed = fields.Monetary("Committed purchases", compute="_compute_amounts", compute_sudo=True,
                                       help="Untaxed total of the confirmed purchase orders of the file.")
    amount_cost_actual = fields.Monetary("Actual cost", compute="_compute_amounts", compute_sudo=True,
                                         help="Posted vendor bills minus vendor credit notes on the file.")
    amount_cost_pending = fields.Monetary("Cost still expected", compute="_compute_amounts", compute_sudo=True,
                                          help="Ordered or expected costs not billed yet.")
    amount_cost_forecast = fields.Monetary("Forecast final cost", compute="_compute_amounts", compute_sudo=True)
    amount_margin_accepted = fields.Monetary("Margin at acceptance", compute="_compute_amounts", compute_sudo=True)
    amount_margin_forecast = fields.Monetary(
        "Margin after external costs", compute="_compute_amounts", compute_sudo=True,
        help="Agreed sale minus the forecast external cost. BOSS's own work (staff, office) is not a cost here: "
        "this is not the net profit.")
    amount_invoiced = fields.Monetary("Invoiced", compute="_compute_amounts", compute_sudo=True,
                                      help="Posted customer invoices minus credit notes, untaxed.")
    amount_to_invoice = fields.Monetary("To invoice", compute="_compute_amounts", compute_sudo=True)
    amount_collected = fields.Monetary("Collected (with taxes)", compute="_compute_amounts", compute_sudo=True)
    amount_paid = fields.Monetary("Paid to suppliers (with taxes)", compute="_compute_amounts", compute_sudo=True)
    cost_complete = fields.Boolean("Costs complete", compute="_compute_amounts", compute_sudo=True,
                                   help="Every external cost is billed or closed: the margin is final.")
    completeness = fields.Text("To do", compute="_compute_amounts", compute_sudo=True)
    financial_closed = fields.Boolean("Financially closed", readonly=True, copy=False, tracking=True)
    financial_closed_date = fields.Date(readonly=True, copy=False)
    financial_closed_by = fields.Many2one("res.users", readonly=True, copy=False)

    # --- creation ------------------------------------------------------------------------------------------------

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("name", "/") == "/":
                vals["name"] = self.env["ir.sequence"].next_by_code("boss.expediente") or "/"
        files = super().create(vals_list)
        files._boss_create_analytic_account()
        return files

    def _boss_create_analytic_account(self):
        plan = self.env.ref("boss_expediente.analytic_plan_files")
        for file in self.filtered(lambda f: not f.analytic_account_id):
            file.analytic_account_id = self.env["account.analytic.account"].sudo().create({
                "name": file.name, "plan_id": plan.id, "partner_id": file.partner_id.commercial_partner_id.id,
                "company_id": file.company_id.id,
            })

    def _boss_link_orders(self, orders):
        """Accepted orders of the file: analytic account on their lines and one purchase need per service bought
        from a supplier. Idempotent: a line already linked is skipped."""
        self.ensure_one()
        lines = orders.order_line.filtered(lambda l: not l.display_type and not l.is_downpayment)
        for line in lines:
            distribution = with_account(line.analytic_distribution, self.analytic_account_id)
            if distribution != line.analytic_distribution:
                line.analytic_distribution = distribution
        known = self.cost_ids.sale_line_id | self.cost_ids.rebill_line_id
        bought = lines.filtered(lambda l: l.boss_execution == "supplier") - known
        if bought:
            Cost = self.env["boss.expediente.cost"]
            Cost.create([Cost._values_from_sale_line(line, self) for line in bought])

    @api.depends("sale_order_ids.state")
    def _compute_preliminary(self):
        for file in self:
            file.preliminary = not file.sale_order_ids.filtered(lambda o: o.state == "sale")

    # --- documents and summary -----------------------------------------------------------------------------------

    def _boss_journal_items(self, move_types):
        self.ensure_one()
        if not self.analytic_account_id:
            return self.env["account.move.line"]
        return self.env["account.move.line"].sudo().search([
            ("distribution_analytic_account_ids", "in", self.analytic_account_id.ids),
            ("parent_state", "=", "posted"), ("display_type", "=", "product"),
            ("move_id.move_type", "in", move_types),
        ])

    @api.depends("sale_order_ids", "purchase_order_ids")
    def _compute_documents(self):
        Move = self.env["account.move"]
        for file in self:
            invoices, bills = file.sale_order_ids.invoice_ids, file.purchase_order_ids.invoice_ids
            if file.analytic_account_id:
                items = self.env["account.move.line"].sudo().search([
                    ("distribution_analytic_account_ids", "in", file.analytic_account_id.ids),
                    ("display_type", "=", "product"), ("parent_state", "!=", "cancel")])
                invoices |= items.move_id.filtered(lambda m: m.move_type in ("out_invoice", "out_refund"))
                bills |= items.move_id.filtered(lambda m: m.move_type in ("in_invoice", "in_refund", "in_receipt"))
            file.invoice_ids = Move.browse(invoices.ids)
            file.bill_ids = Move.browse(bills.ids)
            file.sale_count = len(file.sale_order_ids)
            file.purchase_count = len(file.purchase_order_ids)
            file.invoice_count = len(invoices)
            file.bill_count = len(bills)

    def _compute_quote_difference(self):
        _ = self.env._
        for file in self:
            order = file.sale_order_ids.filtered(lambda o: o.state == "sale").sorted("date_order")[:1]
            if not order:
                file.quote_difference = False
                continue
            rows = []
            for fname in COMPARED:
                actual, agreed = file[fname], order[FROM_ORDER[fname]]
                if actual != agreed and (actual or agreed):
                    label = file._fields[fname].get_description(self.env)["string"]
                    rows.append(f"{label}: {self._boss_display(agreed)} → {self._boss_display(actual)}")
            agreed_containers = defaultdict(int)
            for row in order.boss_container_ids:
                agreed_containers[(row.size, row.container_type_id.code)] += row.quantity
            actual_containers = defaultdict(int)
            for row in file.container_ids:
                actual_containers[(row.size, row.container_type_id.code)] += 1
            if dict(agreed_containers) != dict(actual_containers):
                rows.append(_("Containers: %(agreed)s → %(actual)s",
                              agreed=self._boss_containers_text(agreed_containers) or "-",
                              actual=self._boss_containers_text(actual_containers) or "-"))
            planned = order.boss_planned_date
            actual_date = file.ata if file.direction == "import" else file.atd
            if planned and actual_date and planned != actual_date:
                rows.append(_("Date: planned %(planned)s, actual %(actual)s", planned=planned, actual=actual_date))
            file.quote_difference = "\n".join(rows) or False

    @api.model
    def _boss_display(self, value):
        if isinstance(value, models.BaseModel):
            return value.display_name or "-"
        return str(value) if value not in (False, None) else "-"

    @api.model
    def _boss_containers_text(self, counts):
        return ", ".join(f"{qty} x {size}' {code or ''}".strip() for (size, code), qty in sorted(counts.items()))

    def _compute_amounts(self):
        _ = self.env._
        for file in self:
            company = file.company_id
            currency = company.currency_id
            today = fields.Date.context_today(file)

            def company_amount(amount, from_currency, date):
                return from_currency._convert(amount, currency, company, fields.Date.to_date(date) or today)

            sale_lines = file.sale_order_ids.filtered(lambda o: o.state == "sale").order_line.filtered(
                lambda l: not l.display_type and not l.is_downpayment)
            line_amount = {line: company_amount(line.price_subtotal, line.currency_id, line.order_id.date_order)
                           for line in sale_lines}
            amount_sale = sum(line_amount.values())
            own = sum(amount for line, amount in line_amount.items() if line.boss_execution == "boss")
            on_behalf = sum(amount for line, amount in line_amount.items() if line.product_id.boss_paid_on_behalf)

            purchase_lines = file.purchase_order_ids.filtered(lambda p: p.state == "purchase").order_line.filtered(
                lambda l: not l.display_type)
            committed = sum(company_amount(l.price_subtotal, l.currency_id, l.order_id.date_order)
                            for l in purchase_lines)
            account = file.analytic_account_id
            cost_items = file._boss_journal_items(("in_invoice", "in_refund", "in_receipt"))
            revenue_items = file._boss_journal_items(("out_invoice", "out_refund"))
            actual = sum(item.balance * account_share(item, account) for item in cost_items)
            invoiced = -sum(item.balance * account_share(item, account) for item in revenue_items)
            # cost still expected: open needs, and confirmed purchase lines entered without a need
            needs = file.cost_ids
            pending = sum(needs.mapped("pending_amount_company"))
            billed_by_line = needs._boss_billed_by_purchase_line(purchase_lines)
            for line in purchase_lines.filtered(lambda l: not l.boss_cost_id):
                ordered = company_amount(line.price_subtotal, line.currency_id, line.order_id.date_order)
                pending += max(ordered - billed_by_line.get(line.id, 0.0), 0.0)
            unknown = needs.filtered("cost_unknown")

            invoices = (file.sale_order_ids.invoice_ids | revenue_items.move_id).filtered(
                lambda m: m.state == "posted" and m.move_type in ("out_invoice", "out_refund"))
            bills = (file.purchase_order_ids.invoice_ids | cost_items.move_id).filtered(
                lambda m: m.state == "posted" and m.move_type in ("in_invoice", "in_refund", "in_receipt"))
            file.update({
                "amount_sale": amount_sale, "amount_sale_own": own, "amount_on_behalf": on_behalf,
                "amount_cost_accepted": sum(needs.filtered(lambda n: n.kind == "sale").mapped("accepted_amount_company")),
                "amount_committed": committed, "amount_cost_actual": actual, "amount_cost_pending": pending,
                "amount_cost_forecast": actual + pending,
                # services re-invoiced after acceptance were not part of it (their cost is an extra cost)
                "amount_margin_accepted": amount_sale - sum(
                    amount for line, amount in line_amount.items() if line in needs.rebill_line_id) - sum(
                    needs.filtered(lambda n: n.kind == "sale").mapped("accepted_amount_company")),
                "amount_margin_forecast": amount_sale - actual - pending,
                "amount_invoiced": invoiced, "amount_to_invoice": amount_sale - invoiced,
                "amount_collected": sum(m.amount_total_signed - m.amount_residual_signed for m in invoices),
                "amount_paid": -sum(m.amount_total_signed - m.amount_residual_signed for m in bills),
                "cost_complete": not unknown and currency.is_zero(pending),
            })
            todo = []
            for label, records in (
                    (_("services with unknown cost"), unknown),
                    (_("services without supplier"), needs.filtered(lambda n: n.state == "no_supplier")),
                    (_("services to order (RFQ)"), needs.filtered(lambda n: n.state == "to_order")),
                    (_("RFQs to confirm"), file.purchase_order_ids.filtered(lambda p: p.state in ("draft", "sent"))),
                    (_("extra costs to decide"), needs.filtered(lambda n: n.extra_class in ("approval", "disputed")
                                                                 and not n.closed)),
                    (_("cost variances to review"), needs.filtered("variance_to_review")),
                    (_("draft invoices or bills"), (file.invoice_ids | file.bill_ids).filtered(
                        lambda m: m.state == "draft"))):
                if records:
                    todo.append(f"{len(records)} {label}")
            if float_compare(file.amount_to_invoice, 0.0, precision_rounding=currency.rounding) > 0:
                todo.append(_("%s to invoice", formatLang(self.env, file.amount_to_invoice, currency_obj=currency)))
            if not currency.is_zero(pending):
                todo.append(_("%s of cost not billed yet", formatLang(self.env, pending, currency_obj=currency)))
            file.completeness = "\n".join(todo) or False

    # --- actions ---------------------------------------------------------------------------------------------------

    def _boss_lock(self):
        """One user at a time creates purchase orders of a file: the row lock makes a second click (or a second
        user) stop instead of ordering twice, and the row update makes a concurrent transaction retry."""
        try:
            with self.env.cr.savepoint(flush=False):
                self.env.cr.execute("SELECT id FROM boss_expediente WHERE id IN %s FOR UPDATE NOWAIT",
                                    [tuple(self.ids)])
        except pg_errors.LockNotAvailable:
            raise UserError(self.env._("Another user is ordering the services of this file. Try again in a moment.")) \
                from None
        self.env.cr.execute("UPDATE boss_expediente SET write_date = now() AT TIME ZONE 'UTC' WHERE id IN %s",
                            [tuple(self.ids)])

    def action_create_rfqs(self):
        """Draft RFQs for what is still to order, one per supplier and currency (an open draft RFQ of the file is
        completed instead of opening another one). Nothing is confirmed or sent: a person reviews them."""
        self.ensure_one()
        self._boss_lock()
        self.cost_ids.invalidate_recordset()
        groups = defaultdict(list)
        skipped = []
        digits = self.env["decimal.precision"].precision_get("Product Unit")
        for need in self.cost_ids.filtered(lambda n: not n.closed):
            quantity = need._boss_remaining_qty()
            if float_compare(quantity, 0.0, precision_digits=digits) <= 0:
                continue
            if not need.partner_id:
                skipped.append(need.display_name)
                continue
            groups[(need.partner_id, need.currency_id)].append((need, quantity))
        if not groups:
            raise UserError(self.env._("Nothing to order.") + (
                "\n" + self.env._("Choose the supplier of: %s", ", ".join(skipped)) if skipped else ""))
        PurchaseOrder = self.env["purchase.order"]
        orders = PurchaseOrder
        for (partner, currency), items in groups.items():
            order = self.purchase_order_ids.filtered(
                lambda p, partner=partner, currency=currency: p.state in ("draft", "sent")
                and p.partner_id == partner and p.currency_id == currency)[:1]
            if not order:
                order = PurchaseOrder.with_company(self.company_id).create({
                    "partner_id": partner.id, "currency_id": currency.id, "company_id": self.company_id.id,
                    "origin": self.name, "boss_expediente_id": self.id,
                })
            order.order_line = [Command.create(need._boss_purchase_line_values(quantity)) for need, quantity in items]
            orders |= order
        if skipped:
            self.message_post(body=self.env._("Not ordered, supplier missing: %s", ", ".join(skipped)))
        return self._boss_action("purchase.order", orders, self.env._("Requests for quotation"))

    def action_invoice_services(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window", "res_model": "boss.invoice.services", "view_mode": "form",
            "views": [(False, "form")], "target": "new", "name": self.env._("Invoice services"),
            "context": {"default_expediente_id": self.id},
        }

    def action_new_quotation(self):
        """A service sold later: a new quotation of the same customer, linked to this file, with its shipment data."""
        self.ensure_one()
        context = {"default_partner_id": self.partner_id.id, "default_boss_expediente_id": self.id,
                   "default_origin": self.name}
        for fname, order_field in FROM_ORDER.items():
            value = self[fname]
            context[f"default_{order_field}"] = value.id if isinstance(value, models.BaseModel) else value
        context["default_boss_planned_date"] = (self.eta if self.direction == "import" else self.etd) or False
        return {"type": "ir.actions.act_window", "res_model": "sale.order", "view_mode": "form",
                "views": [(False, "form")], "name": self.env._("New quotation"), "context": context}

    def _boss_action(self, model, records, name):
        action = {"type": "ir.actions.act_window", "res_model": model, "name": name,
                  "domain": [("id", "in", records.ids)]}
        if len(records) == 1:
            return dict(action, view_mode="form", views=[(False, "form")], res_id=records.id)
        return dict(action, view_mode="list,form", views=[(False, "list"), (False, "form")])

    def action_open_sale_orders(self):
        return self._boss_action("sale.order", self.sale_order_ids, self.env._("Quotations and orders"))

    def action_open_purchase_orders(self):
        return self._boss_action("purchase.order", self.purchase_order_ids, self.env._("Purchase orders"))

    def action_open_invoices(self):
        action = self._boss_action("account.move", self.invoice_ids, self.env._("Customer invoices"))
        return dict(action, context={"default_move_type": "out_invoice"})

    def action_open_bills(self):
        action = self._boss_action("account.move", self.bill_ids, self.env._("Vendor bills"))
        return dict(action, context={"default_move_type": "in_invoice"})

    def action_new_bill(self):
        """A cost without purchase order (expense, receipt): a vendor bill on the file's analytic account."""
        self.ensure_one()
        return {
            "type": "ir.actions.act_window", "res_model": "account.move", "view_mode": "form",
            "views": [(False, "form")], "name": self.env._("Vendor bill"),
            "context": {"default_move_type": "in_invoice", "default_ref": self.name,
                        "boss_default_analytic": {str(self.analytic_account_id.id): 100.0}},
        }

    def action_in_transit(self):
        self.write({"state": "in_transit"})

    def action_delivered(self):
        self.write({"state": "delivered"})

    def action_close_operations(self):
        self.write({"state": "closed"})

    def action_reopen(self):
        self.write({"state": "open"})

    def action_cancel(self):
        for file in self:
            if file.purchase_order_ids.filtered(lambda p: p.state == "purchase") or file.invoice_ids.filtered(
                    lambda m: m.state == "posted") or file.bill_ids.filtered(lambda m: m.state == "posted"):
                raise UserError(self.env._(
                    "%s has confirmed purchases or posted invoices: cancel or credit them first.", file.name))
        self.write({"state": "cancel"})

    def action_close_financial(self):
        """Financial close is separate from the operational close: everything invoiced, every cost billed or
        closed, variances reviewed, nothing in draft."""
        for file in self:
            problems = []
            if file.state not in ("closed", "cancel"):
                problems.append(self.env._("operations are not closed"))
            if file.completeness:
                problems.append(file.completeness)
            if problems:
                raise UserError(self.env._("%(file)s cannot be closed financially:\n%(problems)s", file=file.name,
                                           problems="\n".join(problems)))
        self.write({"financial_closed": True, "financial_closed_date": fields.Date.context_today(self),
                    "financial_closed_by": self.env.uid})

    def action_reopen_financial(self):
        self.write({"financial_closed": False, "financial_closed_date": False, "financial_closed_by": False})


class BossExpedienteContainer(models.Model):
    _name = "boss.expediente.container"
    _description = "Container of a shipment file"
    _order = "expediente_id, id"

    expediente_id = fields.Many2one("boss.expediente", required=True, ondelete="cascade", index=True)
    size = fields.Selection(CONTAINER_SIZES, required=True, default="40")
    container_type_id = fields.Many2one("boss.container.type", "Type", required=True,
                                        default=lambda self: self.env.ref("boss_pricing.container_type_dv",
                                                                          raise_if_not_found=False))
    number = fields.Char("Container number")
    seal = fields.Char()
    gross_kg = fields.Float("Gross weight (kg)", digits=(12, 2))
    pickup_date = fields.Date("Full pickup")
    return_date = fields.Date("Empty return")


class BossExpedienteEvent(models.Model):
    _name = "boss.expediente.event"
    _description = "Event of a shipment file"
    _order = "date desc, id desc"

    expediente_id = fields.Many2one("boss.expediente", required=True, ondelete="cascade", index=True)
    date = fields.Datetime(required=True, default=fields.Datetime.now)
    kind = fields.Selection([("milestone", "Milestone"), ("incident", "Incident"), ("note", "Note")],
                            required=True, default="milestone")
    name = fields.Char("Event", required=True)
    note = fields.Text()
    user_id = fields.Many2one("res.users", default=lambda self: self.env.user, readonly=True)
