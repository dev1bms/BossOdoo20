from collections import defaultdict

from markupsafe import Markup
from psycopg2 import errors as pg_errors

from odoo import Command, api, fields, models
from odoo.exceptions import UserError
from odoo.tools import float_compare
from odoo.tools.misc import formatLang

from odoo.addons.boss_pricing.models.boss_container_type import CONTAINER_SIZES
from odoo.addons.boss_pricing.models.boss_tariff import DIRECTIONS, LOAD_TYPES, TRANSPORT_MODES
from odoo.addons.boss_pricing_sale.models.boss_shipment_container import shipment_quantity

from .boss_airline_handler import HANDLER_SERVICE_CODES

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
# Who may read which figure of a file (field groups; the documents behind them are read as superuser).
SALE_GROUPS = "sales_team.group_sale_salesman,account.group_account_invoice,account.group_account_readonly"
COST_GROUPS = ("purchase.group_purchase_user,sales_team.group_sale_manager,account.group_account_invoice,"
               "account.group_account_readonly")
ACCEPTED_GROUPS = SALE_GROUPS + ",purchase.group_purchase_user"  # cost shown on the quotation and to purchasing
MARGIN_GROUPS = "sales_team.group_sale_manager,account.group_account_invoice,account.group_account_readonly"
# Compared with the quotation in "Differences with the quotation" (data that changes the cost).
COMPARED = ("transport_mode", "load_type", "carrier_id", "port_id", "country_id", "inland_state_id", "gross_kg",
            "volume_m3", "awb_kg", "pallets")


def with_account(distribution, account):
    """Analytic distribution with the file's account added (100 % when empty, combined with other plans if set)."""
    return with_accounts(distribution, {account.id: 100.0}, account)


def with_accounts(distribution, shares, plan_accounts):
    """Analytic distribution where the accounts of the files (plan «Shipment files») get their shares (percent) and
    the accounts of other plans are kept: each existing combination is split between the files."""
    plan_ids = {str(account_id) for account_id in plan_accounts.ids}
    base = {}
    for combination, share in (distribution or {}).items():
        others = ",".join(key for key in combination.split(",") if key not in plan_ids)
        if others:
            base[others] = base.get(others, 0.0) + share
    if not base:
        return {str(account_id): share for account_id, share in shares.items()}
    return {f"{combination},{account_id}": share * file_share / 100.0
            for combination, share in base.items() for account_id, file_share in shares.items()}


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
    handler_id = fields.Many2one(
        "res.partner", "Handler", tracking=True,
        help="Air handling agent of the airline at the airport (HAN, ALM, AWB, ETX, X-R are bought from it). "
             "Proposed from «Airlines and handlers» when one handler is known; with several, choose among them.")
    handler_candidate_ids = fields.Many2many(
        "res.partner", compute="_compute_handler_candidate_ids",
        string="Handlers known for this airline at this airport")
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
    # Actual dates carry the time: the time-based services (storage, demurrage, occupancy) are priced on the exact
    # period between them (Cristina, 26/10/2026: ATA and Pickup with date and time on every file; the system
    # computes the dates). NOA and FOH are optional events that refine the start when the supplier counts from them.
    atd = fields.Datetime("ATD (actual departure)", tracking=True)
    ata = fields.Datetime("ATA (actual arrival)", tracking=True)
    noa = fields.Datetime("NOA (arrival notice)", tracking=True,
                          help="Air import: the handler's arrival notice. When set, the storage period starts here "
                               "instead of the ATA (WFS counts from the NOA).")
    foh = fields.Datetime("FOH (goods in the terminal)", tracking=True,
                          help="Export: freight on hand at the handler or terminal. Start of the export storage.")
    pickup_date = fields.Datetime("Pickup (actual)", tracking=True)
    delivery_date = fields.Datetime("Delivery (actual)", tracking=True)
    event_ids = fields.One2many("boss.expediente.event", "expediente_id", "Events", copy=False)
    # links: every document points to the file, the file never duplicates their amounts
    order_link_ids = fields.One2many("sale.order", "boss_expediente_id", "Orders of this file",
                                     help="Quotations and orders whose file is this one (before and after acceptance).")
    allocation_ids = fields.One2many("boss.expediente.allocation", "expediente_id", "Sold services in this file")
    sale_order_ids = fields.Many2many(
        "sale.order", string="Quotations and orders", compute="_compute_sale_order_ids",
        search="_search_sale_order_ids",
        help="Orders of the file: linked to it, or with part of their accepted services in it.")
    purchase_order_ids = fields.One2many("purchase.order", "boss_expediente_id", "Purchase orders")
    cost_ids = fields.One2many("boss.expediente.cost", "expediente_id", "Services to buy and extra costs")
    revision_ids = fields.One2many("boss.expediente.cost.revision", "expediente_id", "Cost recalculations",
                                   readonly=True)
    analytic_account_id = fields.Many2one("account.analytic.account", "Analytic account", readonly=True, copy=False,
                                          check_company=True)
    # Documents and figures are computed as superuser (a file mixes sales, purchases and accounting), so each field is
    # readable only by the roles that can read its source documents in standard Odoo: sales the sale side and the
    # costs shown on the quotation, purchase the vendor side, sales managers and accounting everything (ADR-005).
    invoice_ids = fields.Many2many("account.move", compute="_compute_documents", compute_sudo=True,
                                   string="Customer invoices", groups=SALE_GROUPS)
    bill_ids = fields.Many2many("account.move", compute="_compute_documents", compute_sudo=True,
                                string="Vendor bills", groups=COST_GROUPS)
    sale_count = fields.Integer(compute="_compute_documents", compute_sudo=True)
    purchase_count = fields.Integer(compute="_compute_documents", compute_sudo=True)
    invoice_count = fields.Integer(compute="_compute_documents", compute_sudo=True, groups=SALE_GROUPS)
    bill_count = fields.Integer(compute="_compute_documents", compute_sudo=True, groups=COST_GROUPS)
    quote_difference = fields.Text("Differences with the quotation", compute="_compute_quote_difference",
                                   compute_sudo=True)
    # profitability, company currency, untaxed, from posted documents and open purchase needs
    amount_sale = fields.Monetary("Agreed sale", compute="_compute_amounts", compute_sudo=True, groups=SALE_GROUPS,
                                  help="Untaxed total of the confirmed sales of the file, services added later included.")
    amount_sale_accepted = fields.Monetary("Accepted sale", compute="_compute_amounts", compute_sudo=True,
                                           groups=SALE_GROUPS, help="Sale of the lines accepted with the quotation.")
    amount_sale_added = fields.Monetary("Added after acceptance", compute="_compute_amounts", compute_sudo=True,
                                        groups=SALE_GROUPS)
    amount_sale_own = fields.Monetary("of which BOSS services", compute="_compute_amounts", compute_sudo=True,
                                      groups=SALE_GROUPS)
    amount_on_behalf = fields.Monetary("of which paid on behalf", compute="_compute_amounts", compute_sudo=True,
                                       groups=SALE_GROUPS,
                                       help="Amounts paid in the customer's name and re-invoiced at cost.")
    amount_cost_accepted = fields.Monetary(
        "Expected cost at acceptance", compute="_compute_amounts", compute_sudo=True, groups=ACCEPTED_GROUPS,
        help="Supplier cost of the accepted lines, as shown on the quotation when it was accepted.")
    amount_committed = fields.Monetary("Committed purchases", compute="_compute_amounts", compute_sudo=True,
                                       groups=COST_GROUPS,
                                       help="Untaxed total of the confirmed purchase orders of the file.")
    amount_cost_actual = fields.Monetary("Actual cost", compute="_compute_amounts", compute_sudo=True,
                                         groups=COST_GROUPS,
                                         help="Posted vendor bills minus vendor credit notes on the file.")
    amount_cost_pending = fields.Monetary("Cost still expected", compute="_compute_amounts", compute_sudo=True,
                                          groups=COST_GROUPS, help="Ordered or expected costs not billed yet.")
    amount_cost_forecast = fields.Monetary("Forecast final cost", compute="_compute_amounts", compute_sudo=True,
                                           groups=COST_GROUPS, help="Actual cost + cost still expected.")
    amount_margin_accepted = fields.Monetary("Margin at acceptance", compute="_compute_amounts", compute_sudo=True,
                                             groups=SALE_GROUPS,
                                             help="Accepted sale minus expected cost at acceptance.")
    amount_margin_forecast = fields.Monetary(
        "Forecast margin after external costs", compute="_compute_amounts", compute_sudo=True, groups=MARGIN_GROUPS,
        help="Agreed sale minus the forecast final cost. Not final while a cost is unknown or not billed. BOSS's own "
        "work (staff, office) is not a cost here: this is not the net profit.")
    amount_margin_final = fields.Monetary(
        "Final margin after external costs", compute="_compute_amounts", compute_sudo=True, groups=MARGIN_GROUPS,
        help="Only when every external cost is billed or closed: agreed sale minus actual cost.")
    amount_invoiced = fields.Monetary("Invoiced", compute="_compute_amounts", compute_sudo=True, groups=SALE_GROUPS,
                                      help="Posted customer invoices minus credit notes, untaxed.")
    amount_to_invoice = fields.Monetary("To invoice", compute="_compute_amounts", compute_sudo=True,
                                        groups=SALE_GROUPS)
    amount_collected = fields.Monetary("Collected (with taxes)", compute="_compute_amounts", compute_sudo=True,
                                       groups=SALE_GROUPS)
    amount_paid = fields.Monetary("Paid to suppliers (with taxes)", compute="_compute_amounts", compute_sudo=True,
                                  groups=COST_GROUPS)
    amount_draft_invoices = fields.Monetary("Draft customer invoices (not counted)", compute="_compute_amounts",
                                            compute_sudo=True, groups=SALE_GROUPS)
    amount_draft_rfqs = fields.Monetary("RFQs not confirmed (not counted)", compute="_compute_amounts",
                                        compute_sudo=True, groups=COST_GROUPS)
    amount_draft_bills = fields.Monetary("Draft vendor bills (not counted)", compute="_compute_amounts",
                                         compute_sudo=True, groups=COST_GROUPS)
    cost_complete = fields.Boolean("Costs complete", compute="_compute_amounts", compute_sudo=True,
                                   help="Every external cost is billed or closed: the margin is final.")
    profit_explanation = fields.Text("Where the figures come from", compute="_compute_amounts", compute_sudo=True,
                                     groups=MARGIN_GROUPS)
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
        for file in files.filtered(lambda f: not f.handler_id and len(f.handler_candidate_ids) == 1):
            file.handler_id = file.handler_candidate_ids  # the only handler known for the airline at the airport
        return files

    def _boss_create_analytic_account(self):
        plan = self.env.ref("boss_expediente.analytic_plan_files")
        for file in self.filtered(lambda f: not f.analytic_account_id):
            file.analytic_account_id = self.env["account.analytic.account"].sudo().create({
                "name": file.name, "plan_id": plan.id, "partner_id": file.partner_id.commercial_partner_id.id,
                "company_id": file.company_id.id,
            })

    @api.depends("order_link_ids", "allocation_ids.order_id")
    def _compute_sale_order_ids(self):
        for file in self:
            file.sale_order_ids = file.order_link_ids | file.allocation_ids.order_id

    def _search_sale_order_ids(self, operator, value):
        if operator not in ("in", "not in", "any", "not any"):
            return NotImplemented
        positive = operator in ("in", "any")
        domain = ["|", ("order_link_ids", "any" if operator in ("any", "not any") else "in", value),
                  ("allocation_ids.order_id", "any" if operator in ("any", "not any") else "in", value)]
        return domain if positive else ["!"] + domain

    def _boss_link_orders(self, orders):
        """Accepted orders of the file: what is not in another file yet is allocated to this one, the analytic
        distribution of each line follows its allocation, and each service bought from a supplier gets its purchase
        need for the quantity of this file. Idempotent: a line already in this file is skipped."""
        self.ensure_one()
        digits = self.env["decimal.precision"].precision_get("Product Unit")
        lines = orders.order_line.filtered(lambda l: not l.display_type and not l.is_downpayment)
        Allocation = self.env["boss.expediente.allocation"]
        for line in lines - self.allocation_ids.sale_line_id:
            free = line.product_uom_qty - sum(line.boss_allocation_ids.mapped("quantity"))
            if float_compare(free, 0.0, precision_digits=digits) > 0:
                Allocation.create({"expediente_id": self.id, "sale_line_id": line.id, "quantity": free})
        lines._boss_sync_file_analytic()
        known = self.cost_ids.sale_line_id | self.cost_ids.rebill_line_id
        bought = self.allocation_ids.filtered(
            lambda a: a.sale_line_id in lines and a.sale_line_id.boss_execution == "supplier"
            and a.sale_line_id not in known)
        if bought:
            Cost = self.env["boss.expediente.cost"]
            Cost.create([Cost._values_from_sale_line(a.sale_line_id, self, a.quantity) for a in bought])

    def _boss_copy_values(self):
        """A second file of the same shipment agreement: same customer, parties and route; its own cargo, references
        and dates are entered on it."""
        self.ensure_one()
        fields_to_copy = ["partner_id", "user_id", "company_id", "shipper_id", "consignee_id", "notify_id", "agent_id",
                          "carrier_id", "haulier_id", "customs_broker_id", "direction", "transport_mode", "load_type",
                          "incoterm_id", "port_id", "country_id", "inland_state_id", "origin_place",
                          "destination_place", "goods_description", *[f"scope_{scope}" for scope in SCOPES]]
        values = {}
        for fname in fields_to_copy:
            value = self[fname]
            values[fname] = value.id if isinstance(value, models.BaseModel) else value
        return values

    def action_split(self):
        self.ensure_one()
        return {"type": "ir.actions.act_window", "res_model": "boss.expediente.split", "view_mode": "form",
                "views": [(False, "form")], "target": "new", "name": self.env._("Move services to another file"),
                "context": {"default_expediente_id": self.id}}

    # --- pricing inputs from the file's actual data (same names and engine as the quotation) ----------------------

    def _boss_pricing_date(self):
        """Actual date when known (ATA / ATD), else the estimate, else the quotation's planned date: it chooses the
        version of each supplier tariff."""
        self.ensure_one()
        if self.direction == "export":
            day = self.atd and self.atd.date() or self.etd
        else:
            day = self.ata and self.ata.date() or self.eta
        order = self.sale_order_ids.filtered(lambda o: o.state == "sale").sorted("date_order")[:1]
        return day or order.boss_planned_date or fields.Date.context_today(self)

    def _boss_quantity(self, source, size=False, ctype=False):
        self.ensure_one()
        return shipment_quantity(source, [(c.size, c.container_type_id, 1) for c in self.container_ids],
                                 self.gross_kg, self.volume_m3, self.pallets, self.awb_kg, size, ctype)

    def _boss_inputs(self):
        """Shipment inputs of boss.pricing taken from the file (what really happens), like
        sale.order._boss_shipment_inputs() takes them from the quotation (what was agreed)."""
        self.ensure_one()
        order = self.sale_order_ids.filtered(lambda o: o.state == "sale").sorted("date_order")[:1]
        partner = self.partner_id.commercial_partner_id
        containers = defaultdict(int)
        for row in self.container_ids:
            containers[(row.size, row.container_type_id.id)] += 1
        day = self._boss_pricing_date()
        return {
            "direction": self.direction, "transport_mode": self.transport_mode, "load_type": self.load_type,
            "carrier_id": self.carrier_id.id, "port_id": self.port_id.id, "country_id": self.country_id.id,
            "state_id": self.inland_state_id.id, "customer_id": partner.id,
            "tariff_use": "demo" if partner.boss_demo else "real",
            "containers": [{"size": size, "type_id": type_id, "quantity": quantity}
                           for (size, type_id), quantity in containers.items()],
            "gross_kg": self.gross_kg or None, "awb_kg": self.awb_kg or None, "volume_m3": self.volume_m3 or None,
            "pallets": self.pallets or None, "goods_value": order.boss_goods_value or None,
            "duties_amount": order.boss_duties_amount or None, "storage_days": None,
            "start_weekday": day.weekday() if day else None,
        }

    # Handler of the airline at the airport (Hoja1 B9/C9/C10)
    @api.depends("carrier_id", "port_id", "transport_mode")
    def _compute_handler_candidate_ids(self):
        Rel = self.env["boss.airline.handler"]
        for file in self:
            file.handler_candidate_ids = (Rel._handlers_for(file.carrier_id, file.port_id)
                                          if file.transport_mode == "air" else self.env["res.partner"])

    @api.onchange("carrier_id", "port_id", "transport_mode")
    def _onchange_handler_proposal(self):
        """One known handler for the airline at the airport: proposed. Several: the user chooses among them (the
        field only offers those). None recorded: free choice among handling agents."""
        for file in self:
            candidates = file.handler_candidate_ids
            if file.handler_id and candidates and file.handler_id not in candidates:
                file.handler_id = False  # the handler of the previous airline or airport
            if len(candidates) == 1 and not file.handler_id:
                file.handler_id = candidates

    def _boss_handler_needs(self):
        """Needs bought from the handler (air handling services) not ordered yet: they follow the handler chosen on
        the file, whichever supplier priced them on the quotation."""
        return self.cost_ids.filtered(
            lambda n: n.product_id.default_code in HANDLER_SERVICE_CODES
            and not n.purchase_line_ids and n.state not in ("closed", "billed", "performed"))

    # Actual period of the time-based services, from the file's dates (Cristina, 26/10/2026)
    PERIOD_FIELDS = ("ata", "noa", "foh", "atd", "pickup_date")

    def _boss_period_bounds(self):
        """(start, end) of the actual period of a time-based service of this file, from its dates. Import: arrival
        (NOA when the handler counts from it, else ATA) → pickup. Export: goods in the terminal (FOH) → actual
        departure. None while a bound is not known: the service keeps its estimate of days."""
        self.ensure_one()
        if self.direction == "export":
            return self.foh, self.atd
        return self.noa or self.ata, self.pickup_date

    def write(self, vals):
        res = super().write(vals)
        if any(f in vals for f in self.PERIOD_FIELDS):
            self._boss_apply_dates()
        if vals.get("handler_id"):
            for file in self:
                needs = file._boss_handler_needs().filtered(lambda n: n.partner_id != file.handler_id)
                if needs:
                    needs.write({"partner_id": file.handler_id.id})
                    file.with_context(boss_reason=self.env._("Handler changed")).action_recompute_costs()
        return res

    def _boss_apply_dates(self):
        """The time-based services whose period is not set by hand follow the file's dates; a milestone records
        it and the expected cost is recomputed (the sale never changes)."""
        for file in self:
            start, end = file._boss_period_bounds()
            needs = file.cost_ids.filtered(
                lambda n: n.product_id.boss_cost_method == "time" and not n.period_manual and not n.closed
                and (n.period_start != start or n.period_end != end))
            if not needs:
                continue
            needs.with_context(boss_period_from_file=True).write({"period_start": start, "period_end": end})
            fmt = lambda d: fields.Datetime.context_timestamp(file, d).strftime("%d/%m/%Y %H:%M") if d else "—"  # noqa: E731
            file.event_ids.create({
                "expediente_id": file.id, "kind": "milestone",
                "name": self.env._("Period of %(services)s from the file dates: %(start)s → %(end)s",
                                   services=", ".join(needs.mapped("product_id.default_code")),
                                   start=fmt(start), end=fmt(end))})
            file.with_context(boss_reason=self.env._("File dates changed")).action_recompute_costs()

    def action_recompute_costs(self):
        """Expected cost again with the file's current data. Sale prices and the acceptance snapshot do not change."""
        for file in self:
            revisions = file.cost_ids._boss_recompute(self.env.context.get("boss_reason"))
            changed = revisions.filtered("applied")
            not_priced = revisions.filtered(lambda r: r.status not in ("ok", "manual"))
            if revisions:
                lines = [f"{r.cost_id.display_name}: {r.old_quantity:g} x {r.old_unit_cost:.2f} → "
                         f"{r.new_quantity:g} x {r.new_unit_cost:.2f} {r.currency_id.name}" for r in changed]
                lines += [f"{r.cost_id.display_name}: {r.explanation or r.status}" for r in not_priced]
                file.message_post(body=Markup("<br/>").join(
                    [self.env._("Expected cost recomputed with the file data:")] + lines))
        return True

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

    def _boss_own_order_invoices(self):
        """Invoices of the orders that belong to this file only; an order shared by several files reaches each file
        through the analytic account of its invoice lines."""
        self.ensure_one()
        return self.sale_order_ids.filtered(lambda o: len(o.boss_expediente_ids) <= 1).invoice_ids

    @api.depends("sale_order_ids", "purchase_order_ids")
    def _compute_documents(self):
        Move = self.env["account.move"]
        for file in self:
            invoices, bills = file._boss_own_order_invoices(), file.purchase_order_ids.invoice_ids
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
            actual_date = actual_date and actual_date.date()
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

    def _boss_user_can(self, groups):
        user = self.env.user
        return any(user.has_group(group) for group in groups.split(","))

    def _compute_amounts(self):
        """Every figure from documents, company currency, untaxed unless stated. Posted documents, confirmed orders,
        drafts and forecasts are kept apart; the margin is called final only when every external cost is billed or
        closed (ADR-005)."""
        _ = self.env._
        for file in self:
            company = file.company_id
            currency = company.currency_id
            today = fields.Date.context_today(file)

            def money(amount):
                return formatLang(self.env, amount, currency_obj=currency)

            def company_amount(amount, from_currency, date):
                return from_currency._convert(amount, currency, company, fields.Date.to_date(date) or today)

            # the part of each accepted line that is in this file (one quotation may feed several files)
            allocations = file.allocation_ids.filtered(lambda a: a.order_id.state == "sale")
            orders = allocations.order_id
            line_amount = {a: company_amount(a.amount, a.currency_id, a.order_id.date_order) for a in allocations}
            added = allocations.filtered("sale_line_id.boss_added_after_acceptance")
            amount_sale = sum(line_amount.values())
            amount_added = sum(line_amount[a] for a in added)
            own = sum(amount for a, amount in line_amount.items() if a.sale_line_id.boss_execution == "boss")
            on_behalf = sum(amount for a, amount in line_amount.items() if a.product_id.boss_paid_on_behalf)

            purchase_lines = file.purchase_order_ids.filtered(lambda p: p.state == "purchase").order_line.filtered(
                lambda l: not l.display_type)
            committed = sum(company_amount(l.price_subtotal, l.currency_id, l.order_id.date_order)
                            for l in purchase_lines)
            draft_rfqs = file.purchase_order_ids.filtered(lambda p: p.state in ("draft", "sent", "to approve"))
            account = file.analytic_account_id
            cost_items = file._boss_journal_items(("in_invoice", "in_refund", "in_receipt"))
            revenue_items = file._boss_journal_items(("out_invoice", "out_refund"))
            actual = sum(item.balance * account_share(item, account) for item in cost_items)
            invoiced = -sum(item.balance * account_share(item, account) for item in revenue_items)
            # cost still expected: open needs, and confirmed purchase lines entered without a need
            needs = file.cost_ids
            accepted_needs = needs.filtered(
                lambda n: n.kind == "sale" and not n.sale_line_id.boss_added_after_acceptance)
            pending = sum(needs.mapped("pending_amount_company"))
            billed_by_line = needs._boss_billed_by_purchase_line(purchase_lines)
            loose = purchase_lines.filtered(lambda l: not l.boss_cost_id)
            for line in loose:
                ordered = company_amount(line.price_subtotal, line.currency_id, line.order_id.date_order)
                pending += max(ordered - billed_by_line.get(line.id, 0.0), 0.0)
            unknown = needs.filtered("cost_unknown")
            complete = not unknown and currency.is_zero(pending)
            accepted_sale = amount_sale - amount_added
            accepted_cost = sum(accepted_needs.mapped("accepted_amount_company"))

            invoices = (file._boss_own_order_invoices() | revenue_items.move_id).filtered(
                lambda m: m.move_type in ("out_invoice", "out_refund"))
            bills = (file.purchase_order_ids.invoice_ids | cost_items.move_id).filtered(
                lambda m: m.move_type in ("in_invoice", "in_refund", "in_receipt"))
            posted_invoices, posted_bills = (invoices | bills).filtered(lambda m: m.state == "posted") & invoices, \
                (invoices | bills).filtered(lambda m: m.state == "posted") & bills
            draft_invoices = invoices.filtered(lambda m: m.state == "draft")
            draft_bills = bills.filtered(lambda m: m.state == "draft")
            file.update({
                "amount_sale": amount_sale, "amount_sale_accepted": accepted_sale, "amount_sale_added": amount_added,
                "amount_sale_own": own, "amount_on_behalf": on_behalf,
                "amount_cost_accepted": accepted_cost,
                "amount_committed": committed, "amount_cost_actual": actual, "amount_cost_pending": pending,
                "amount_cost_forecast": actual + pending,
                "amount_margin_accepted": accepted_sale - accepted_cost,
                "amount_margin_forecast": amount_sale - actual - pending,
                "amount_margin_final": amount_sale - actual if complete else 0.0,
                "amount_invoiced": invoiced, "amount_to_invoice": amount_sale - invoiced,
                "amount_collected": sum(m.amount_total_signed - m.amount_residual_signed for m in posted_invoices),
                "amount_paid": -sum(m.amount_total_signed - m.amount_residual_signed for m in posted_bills),
                "amount_draft_invoices": sum(draft_invoices.mapped("amount_untaxed_signed")),
                "amount_draft_rfqs": sum(company_amount(p.amount_untaxed, p.currency_id, p.date_order)
                                         for p in draft_rfqs),
                "amount_draft_bills": -sum(draft_bills.mapped("amount_untaxed_signed")),
                "cost_complete": complete,
            })

            # Where each figure comes from (the summary must be checkable by hand).
            rows = [
                _("Agreed sale %(total)s = accepted %(accepted)s (%(orders)s) + added after acceptance %(added)s",
                  total=money(amount_sale), accepted=money(accepted_sale), orders=", ".join(orders.mapped("name")),
                  added=money(amount_added)),
            ]
            rows += [f"   + {a.product_id.default_code or a.product_id.name}: {money(line_amount[a])}" for a in added]
            rows.append(_("Expected cost at acceptance %s (supplier services of the accepted lines):",
                          money(accepted_cost)))
            rows += [f"   {n.product_id.default_code or n.product_id.name}: {money(n.accepted_amount_company)}"
                     for n in accepted_needs]
            rows.append(_("Margin at acceptance %(margin)s = %(sale)s - %(cost)s",
                          margin=money(accepted_sale - accepted_cost), sale=money(accepted_sale),
                          cost=money(accepted_cost)))
            rows.append(_("Forecast final cost %(total)s = actual cost (posted vendor bills and credit notes) %(actual)s "
                          "+ cost still expected %(pending)s:", total=money(actual + pending), actual=money(actual),
                          pending=money(pending)))
            for need in needs:
                basis = (_("closed") if need.closed else _("billed") if need.state == "billed"
                         else _("order to review") if need.po_to_review
                         else _("confirmed order") if need.qty_ordered else _("expected"))
                unknown_text = " · " + _("COST UNKNOWN") if need.cost_unknown else ""
                rows.append(f"   {need.product_id.default_code or need.product_id.name} ({basis}): "
                            f"{money(need.pending_amount_company)}{unknown_text}")
            if loose:
                rows.append(_("   purchase lines without file service: %s", money(sum(
                    max(company_amount(l.price_subtotal, l.currency_id, l.order_id.date_order)
                        - billed_by_line.get(l.id, 0.0), 0.0) for l in loose))))
            if complete:
                rows.append(_("Final margin %(margin)s = %(sale)s - actual cost %(actual)s",
                              margin=money(amount_sale - actual), sale=money(amount_sale), actual=money(actual)))
            else:
                rows.append(_("Forecast margin %(margin)s = %(sale)s - %(cost)s. NOT FINAL: %(n)s services not billed "
                              "yet or with unknown cost.", margin=money(amount_sale - actual - pending),
                              sale=money(amount_sale), cost=money(actual + pending),
                              n=len(needs.filtered(lambda n: not n.closed and n.state != "billed"))))
            rows.append(_("Not counted in the figures: draft customer invoices %(inv)s, RFQs not confirmed %(rfq)s, "
                          "draft vendor bills %(bills)s.", inv=money(file.amount_draft_invoices),
                          rfq=money(file.amount_draft_rfqs), bills=money(file.amount_draft_bills)))
            file.profit_explanation = "\n".join(rows)

            # To do, limited to what the user may see (sales: sale side; purchase / accounting: cost side).
            sees_cost = file._boss_user_can(COST_GROUPS)
            sees_sale = file._boss_user_can(SALE_GROUPS)
            todo = []
            checks = [
                (sees_cost or sees_sale, _("services with unknown cost"), unknown),
                (True, _("services without supplier"), needs.filtered(lambda n: n.state == "no_supplier")),
                (True, _("services to order (RFQ)"), needs.filtered(lambda n: n.state == "to_order")),
                (True, _("RFQs to confirm"), draft_rfqs),
                (True, _("extra costs to decide"), needs.filtered(
                    lambda n: n.extra_class in ("approval", "disputed") and not n.closed)),
                (sees_cost, _("cost variances to review"), needs.filtered("variance_to_review")),
                (sees_cost, _("purchase orders to review after a cost recalculation"), needs.filtered("po_to_review")),
                (sees_sale, _("draft customer invoices"), draft_invoices),
                (sees_cost, _("draft vendor bills"), draft_bills),
            ]
            todo += [f"{len(records)} {label}" for visible, label, records in checks if visible and records]
            if sees_sale and float_compare(file.amount_to_invoice, 0.0, precision_rounding=currency.rounding) > 0:
                todo.append(_("%s to invoice", money(file.amount_to_invoice)))
            if sees_cost and not currency.is_zero(pending):
                todo.append(_("%s of cost not billed yet", money(pending)))
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
        for need in self.cost_ids.filtered(lambda n: not n.closed and not n.without_order):
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

    def action_add_service(self):
        """A service sold after acceptance, added to the accepted order of the file (explicit change, reason)."""
        self.ensure_one()
        order = self.sale_order_ids.filtered(lambda o: o.state == "sale").sorted("date_order")[:1]
        if not order:
            raise UserError(self.env._("%s has no accepted order yet.", self.name))
        return order.action_boss_add_service()

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
