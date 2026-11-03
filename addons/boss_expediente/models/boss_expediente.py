from collections import defaultdict
from datetime import datetime, time

from markupsafe import Markup
from psycopg2 import errors as pg_errors

from odoo import Command, api, fields, models
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.tools import float_compare, float_round
from odoo.tools.misc import formatLang

from odoo.addons.boss_pricing.models.boss_container_type import CONTAINER_SIZES
from odoo.addons.boss_pricing.models.boss_tariff import DIRECTIONS, LOAD_TYPES, TRANSPORT_MODES
from odoo.addons.boss_pricing_sale.models.boss_shipment_container import shipment_quantity
from odoo.addons.boss_pricing_sale.models.sale_order import MIN_MARGIN_RATE, MIN_MARGIN_TOLERANCE
from odoo.addons.boss_pricing_sale.models.boss_shipment_route import (BUSINESSES, chargeable_by_mode, chargeable_kg,
                                                                      abroad_side, key_date, spanish_side, traffic_code)

from .boss_airline_handler import HANDLER_SERVICE_CODES

FILE_EVENT_FIELDS = {"ata": "ata", "discharge": "discharge_date", "noa": "noa", "foh": "foh", "departure": "atd",
                     "pickup": "pickup_date", "delivery": "delivery_date", "emptying": "emptying_date"}
CONTAINER_EVENT_FIELDS = {"container_empty_out": "empty_out_date", "container_gate_in": "gate_in_date",
                          "container_full_out": "pickup_date", "container_empty_return": "return_date"}
# Period of a time-based service when its supplier price states no events (or it has no supplier price yet).
# Sources: Cristina e-mail 25/09/2026 (ALM: air import NOA -> pickup, air export delivery -> ETD; BossOdoo19
# DECISIONS.md:139) and the MSC local charges of 01/09/2026 (demurrage p.18 «llegada buque hasta devolución del vacío»,
# occupancy p.17 «llegada buque hasta fecha entrega», export p.9-10 «entrada lleno», detention «salida vacío ->
# entrada lleno»). Export storage ends at the ACTUAL departure (Cristina says ETD: the actual one is used once known,
# the estimate of days until then). DET is only an export charge in the MSC documents (import: inside DEM, Hapag).
DEFAULT_PERIOD_EVENTS = {
    ("ALM", "import", "lcl"): ("emptying", "pickup"),  # Cristina 25/09: LCL import emptying -> pickup
    ("ALM", "export", "lcl"): (False, False),  # Cristina 25/09: LCL export, none
    ("ALM", "import"): ("noa_or_ata", "pickup"),
    ("ALM", "export"): ("foh", "departure"),
    ("DEM", "import"): ("ata", "container_empty_return"),
    ("DEM", "export"): ("container_gate_in", "departure"),
    ("OCU", "import"): ("ata", "container_full_out"),
    ("OCU", "export"): ("container_gate_in", "departure"),
    ("DET", "export"): ("container_empty_out", "container_gate_in"),
}

STATES = [
    ("open", "Open"),
    ("in_transit", "In transit"),
    ("arrived", "Arrived"),
    ("delivered", "Delivered"),
    ("closed", "Operations closed"),
    ("cancel", "Cancelled"),
]
# Suggested next step of a file, in BOSS's order of work (docs/hoja-de-ruta.md, item 1). A guide computed from the
# file's documents: it blocks nothing and decides no business rule; «To do» keeps listing everything that is open.
NEXT_STEPS = [
    ("link_quotation", "Link the accepted quotation"),
    ("choose_supplier", "Choose the missing suppliers"),
    ("type_cost", "Type the unknown costs"),
    ("order", "Create the requests for quotation"),
    ("confirm_rfq", "Confirm the requests for quotation with the suppliers"),
    ("in_transit", "Put the file in transit"),
    ("arrived", "Record the arrival (ATA)"),
    ("delivered", "Mark the file delivered"),
    ("perform", "Mark the ordered services performed"),
    ("invoice", "Invoice the customer"),
    ("close_operations", "Close operations"),
    ("bills", "Record the supplier bills"),
    ("review", "Review the pending items"),
    ("close_financial", "Close financially"),
    ("done", "Nothing left to do"),
]
SCOPES = ("pickup", "origin_customs", "main", "destination_customs", "delivery")
# Shipment data frozen when operations close (plan-expediente-completo (10); Odoo 17 froze about 140 fields of the
# file at its close): parties, route, cargo, references, dates and customs. Not frozen: the services, costs and late
# supplier bills (Cristina closes against the forecast and records the bills later without reopening, F0-C60), the
# containers (their return dates drive demurrage and detention), notes, ratings and the financial close.
FROZEN_FIELDS = (
    "partner_id", "business", "shipper_id", "consignee_id", "notify_id", "agent_id", "carrier_id", "handler_id",
    "haulier_id", "customs_broker_id", "direction", "transport_mode", "load_type", "incoterm_id", "origin_country_id",
    "origin_port_id", "pickup_address_id", "origin_place", "destination_country_id", "destination_port_id",
    "delivery_address_id", "destination_place", "port_id", "country_id", "inland_state_id", "scope_pickup",
    "scope_origin_customs", "scope_main", "scope_destination_customs", "scope_delivery", "goods_description",
    "packages", "package_type", "hs_code", "gross_kg", "volume_m3", "awb_kg", "pallets", "goods_value", "duties_amount",
    "booking_ref", "mbl_ref", "hbl_ref", "mawb_ref", "hawb_ref", "vessel", "voyage", "customs_ref", "etd", "eta", "atd",
    "ata", "noa", "foh", "emptying_date", "discharge_date", "pickup_date", "delivery_date", "delivered_date",
    "customs_channel", "customs_admission_date", "customs_release_date", "customs_guarantee",
    "customs_docs_received_date", "customs_docs_sent_date", "hbl_release", "master_id",
)
FROZEN_STATES = ("closed", "cancel")
# Charges Cristina sends to the customs broker for the customs value (A37): freight, THC, T3 and insurance, by
# service code and its variants (FMI-LCL, THC-LCL, T3-PAD). By code, not by service group: the freight group also
# holds QBR and the insurance group the courier (MEN).
CUSTOMS_VALUE_CHARGES = (("freight", ("FMI", "FME", "FAI", "FAE")), ("THC", ("THC",)), ("T3", ("T3",)),
                         ("insurance", ("SEG",)))
# Transport data of a consolidation that belongs to the master (MBL / MAWB) and is copied to its houses (ADR-013).
MASTER_FIELDS = ("carrier_id", "vessel", "voyage", "booking_ref", "mbl_ref", "mawb_ref", "etd", "eta", "atd", "ata",
                 "discharge_date")
# Case and route copied from a master to a new house (the house keeps its own parties, cargo and customs).
HOUSE_FROM_MASTER = ("business", "direction", "transport_mode", "load_type", "incoterm_id", "origin_country_id",
                     "origin_port_id", "origin_place", "destination_country_id", "destination_port_id",
                     "destination_place", "agent_id", "handler_id",
                     *(f"scope_{scope}" for scope in SCOPES))
ALLOCATION_BASES = [("chargeable", "Chargeable weight (W/M)"), ("gross", "Gross weight"), ("volume", "Volume"),
                    ("equal", "Equal parts"), ("manual", "Manual share")]
# Type of unit of the cargo: the Odoo 17 taxonomy of a partida (x_studio_unit_type), as Ángel asked (27/10/2026).
PACKAGE_TYPES = [("CT", "Cartons"), ("PL", "Pallets"), ("CR", "Crates"), ("PC", "Packages"), ("BT", "Bottles"),
                 ("BG", "Bags")]
# Shipment data copied ONCE from the accepted quotation (file field: quotation field). From then on the file holds
# the actual data and the quotation keeps what was agreed; differences are shown, never synchronised.
FROM_ORDER = {
    "business": "boss_business", "direction": "boss_direction", "transport_mode": "boss_transport_mode",
    "load_type": "boss_load_type", "carrier_id": "boss_carrier_id", "port_id": "boss_port_id",
    "country_id": "boss_country_id", "inland_state_id": "boss_inland_state_id", "incoterm_id": "incoterm",
    "origin_country_id": "boss_origin_country_id", "origin_port_id": "boss_origin_port_id",
    "pickup_address_id": "boss_pickup_address_id", "origin_place": "boss_origin_place",
    "destination_country_id": "boss_destination_country_id", "destination_port_id": "boss_destination_port_id",
    "delivery_address_id": "boss_delivery_address_id", "destination_place": "boss_destination_place",
    "etd": "boss_etd", "eta": "boss_eta", "shipper_id": "boss_shipper_id",
    "consignee_id": "boss_consignee_id", "goods_description": "boss_goods_description", "packages": "boss_packages",
    "package_type": "boss_package_type", "hs_code": "boss_hs_code",
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


def settled_part(moves, items, account):
    """Amount already paid of the moves that belongs to the file: each move counts in proportion to its product
    lines on the file's analytic account (an invoice of several files is collected in proportion, like «invoiced»).
    A move of the file's own order without analytic lines counts in full."""
    part = defaultdict(float)
    for item in items:
        part[item.move_id.id] += item.balance * account_share(item, account)
    total = 0.0
    for move in moves:
        paid = move.amount_total_signed - move.amount_residual_signed
        if move.id in part:
            base = sum(move.line_ids.filtered(lambda l: l.display_type == "product").mapped("balance"))
            total += paid * (part[move.id] / base if base else 0.0)
        else:
            total += paid
    return total


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
        "res.partner", "Ordered by", required=True, tracking=True, index=True, check_company=True,
        help="Who orders the shipment and is invoiced: a BOSS client, or an agent (a forwarder abroad) for its own "
        "client.")
    business = fields.Selection(BUSINESSES, "Business of", default="boss", tracking=True)
    traffic_code = fields.Char("Traffic", compute="_compute_traffic_code", store=True,
                               help="Direction (I/E), mode (M sea, A air, T road) and whose client (B BOSS, A agent).")
    user_id = fields.Many2one("res.users", "Responsible", default=lambda self: self.env.user, tracking=True)
    state = fields.Selection(STATES, default="open", required=True, tracking=True, copy=False)
    rating_ids = fields.One2many("boss.expediente.rating", "expediente_id", "Ratings", copy=False)
    rating_missing = fields.Char("Still to rate", compute="_compute_rating_missing",
                                 help="Parties of the file without a rating (customer and suppliers bought from).")
    preliminary = fields.Boolean(
        compute="_compute_preliminary",
        help="Opened before an accepted quotation (pre-alert, documents received). Link the quotation when it is "
        "accepted.")
    # parties
    shipper_id = fields.Many2one("res.partner", "Shipper", tracking=True)
    consignee_id = fields.Many2one("res.partner", "Consignee", tracking=True)
    notify_id = fields.Many2one("res.partner", "Notify party")
    agent_id = fields.Many2one("res.partner", "Agent abroad", tracking=True)
    carrier_id = fields.Many2one("res.partner", "Main carrier", tracking=True, help="Shipping line or airline.")
    handler_id = fields.Many2one(
        "res.partner", "Handler", tracking=True,
        help="Air handling agent of the airline at the airport (HAN, ALM, AWB, ETX, X-R are bought from it). "
             "Proposed from «Airlines and handlers» when one handler is known; with several, choose among them.")
    handler_candidate_ids = fields.Many2many(
        "res.partner", compute="_compute_handler_candidate_ids",
        string="Handlers known for this airline at this airport")
    haulier_id = fields.Many2one("res.partner", "Inland carrier (haulier)", tracking=True,
                                 help="Road transport supplier of the pickup or delivery; from the accepted quotation.")
    customs_broker_id = fields.Many2one("res.partner", "Customs broker")
    # route and scope
    direction = fields.Selection(DIRECTIONS, tracking=True)
    transport_mode = fields.Selection(TRANSPORT_MODES, "Transport mode", tracking=True)
    load_type = fields.Selection(LOAD_TYPES, "Load type", tracking=True)
    incoterm_id = fields.Many2one("account.incoterms", "Incoterm", tracking=True)
    # origin and destination (ADR-006); the Spanish port, country abroad and province are derived from them
    port_kind = fields.Char(compute="_compute_port_kind")
    origin_country_id = fields.Many2one("res.country", "Origin country", tracking=True)
    origin_port_id = fields.Many2one("boss.port", "Origin port / airport", tracking=True,
                                     domain="[('country_id', '=?', origin_country_id), ('kind', '=?', port_kind)]")
    pickup_address_id = fields.Many2one("res.partner", "Pickup address", tracking=True)
    origin_place = fields.Char("Origin place", compute="_compute_places", store=True, readonly=False)
    destination_country_id = fields.Many2one("res.country", "Destination country", tracking=True)
    destination_port_id = fields.Many2one(
        "boss.port", "Destination port / airport", tracking=True,
        domain="[('country_id', '=?', destination_country_id), ('kind', '=?', port_kind)]")
    delivery_address_id = fields.Many2one("res.partner", "Delivery address", tracking=True)
    destination_place = fields.Char("Destination place", compute="_compute_places", store=True, readonly=False)
    port_id = fields.Many2one("boss.port", "Spanish port / airport", tracking=True, compute="_compute_pricing_route",
                              store=True, readonly=False,
                              help="The destination of an import, the origin of an export.")
    country_id = fields.Many2one("res.country", "Country abroad", tracking=True, compute="_compute_pricing_route",
                                 store=True, readonly=False)
    inland_state_id = fields.Many2one("res.country.state", "Inland province", domain="[('country_id.code', '=', 'ES')]",
                                      compute="_compute_inland_state", store=True, readonly=False,
                                      help="Province of the delivery (import) or pickup (export) address in Spain.")
    scope_pickup = fields.Boolean("Pickup")
    scope_origin_customs = fields.Boolean("Customs at origin")
    scope_main = fields.Boolean("Main carriage")
    scope_destination_customs = fields.Boolean("Customs at destination")
    scope_delivery = fields.Boolean("Delivery")
    # cargo
    goods_description = fields.Char("Goods")
    packages = fields.Integer()
    package_type = fields.Selection(PACKAGE_TYPES, "Type of unit")
    hs_code = fields.Char("Goods code (HS)", help="Customs tariff code of the goods: it decides the duties.")
    gross_kg = fields.Float("Gross weight (kg)", digits=(12, 2), tracking=True)
    volume_m3 = fields.Float("Volume (m³)", digits=(12, 3), tracking=True)
    awb_kg = fields.Float("Chargeable weight (AWB, kg)", digits=(12, 2))
    volume_weight_kg = fields.Float("Volume weight (kg)", digits=(12, 2), compute="_compute_chargeable_kg", store=True,
                                    help="Volume × factor of the mode: air 167, road 333, sea 1000 kg per m³.")
    chargeable_kg = fields.Float("Chargeable weight (kg)", digits=(12, 2), compute="_compute_chargeable_kg",
                                 store=True, help="The higher of the gross weight and the volume weight (both needed).")
    pallets = fields.Integer()
    goods_value = fields.Monetary("Goods value", currency_field="currency_id", tracking=True,
                                  help="Commercial value of the goods, when known (often only after the quotation).")
    duties_amount = fields.Monetary("Customs duties (estimate)", currency_field="currency_id")
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
    # Customs of the file (the customs unit of Odoo 17 «partida»: channel, admission and release «levante», guarantee;
    # Cristina, «Nuevo Odoo» › OPS- exptes A32-A36). Roadmap item 5.
    customs_channel = fields.Selection(
        [("green", "Green (automatic release)"), ("orange", "Orange (documentary check)"),
         ("red", "Red (physical inspection)")], "Customs channel", tracking=True,
        help="Channel given by customs to the declaration (DUA).")
    customs_admission_date = fields.Datetime("Admitted by customs", tracking=True)
    customs_release_date = fields.Datetime(
        "Customs release (levante)", tracking=True,
        help="The goods are released by customs. Needed to mark the file delivered when BOSS clears customs (Odoo 17: "
             "every partida cleared by BOSS has its release date before delivery).")
    customs_guarantee = fields.Selection(
        [("boss", "BOSS guarantee (aval)"), ("customer", "Customer's guarantee"), ("payment", "Duties paid (form 031)")],
        "Duties paid or guaranteed by",
        help="How the duties of the declaration are paid or guaranteed (Cristina, «Nuevo Odoo» › OPS- exptes A33).")
    customs_docs_received_date = fields.Date("Customer documents complete",
                                             help="Every document of the customer for the declaration received (A35).")
    customs_docs_sent_date = fields.Date("Documents sent to the customs broker", help="(A36)")
    customs_broker_text = fields.Text(
        "Data for the customs broker", compute="_compute_customs_broker_text",
        help="What the customs broker needs to clear the goods (Cristina, «Nuevo Odoo» › OPS- exptes A37): parties, "
             "transport documents, containers, goods and the freight, THC, T3 and insurance sold for the customs value. "
             "Copied and sent by the operator; Odoo never sends it.")
    hbl_release = fields.Selection(
        [("pending", "Originals, not released yet"), ("released", "Released (telex or originals surrendered)"),
         ("swb", "Sea waybill (no originals)")], "House B/L release", tracking=True,
        help="Cristina («Nuevo Odoo» › OPS- exptes A39, A73): before the cargo is delivered and its transport order is "
             "given, the house B/L is released or is a sea waybill.")
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
    emptying_date = fields.Datetime("Emptying (LCL)", tracking=True,
                                    help="Sea groupage import: the container is emptied at the warehouse (CFS). Start of "
                                         "the LCL storage (Cristina 25/09/2026: emptying -> pickup).")
    discharge_date = fields.Datetime("Vessel discharge", tracking=True,
                                     help="Sea: discharge of the vessel. Start of the carrier periods that count from "
                                          "it (Hapag-Lloyd demurrage and detention «DIFU»).")
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
        help="Only when every external cost is billed or closed and the agreed sale is invoiced: invoiced (credit "
        "notes deducted) minus actual cost.")
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
                                   help="Every external cost is billed or closed.")
    margin_final = fields.Boolean("Margin final", compute="_compute_amounts", compute_sudo=True,
                                  help="Costs complete and nothing left to invoice: the margin is final. A credited "
                                  "service stays to invoice until it is invoiced again or re-priced (Re-price).")
    profit_explanation = fields.Text("Where the figures come from", compute="_compute_amounts", compute_sudo=True,
                                     groups=MARGIN_GROUPS)
    completeness = fields.Text("To do", compute="_compute_amounts", compute_sudo=True)
    next_step = fields.Selection(NEXT_STEPS, "Next step", compute="_compute_amounts", compute_sudo=True,
                                 search="_search_next_step",
                                 help="Suggested next step in BOSS's order of work. A guide: it blocks nothing.")
    next_step_detail = fields.Char("Next step detail", compute="_compute_amounts", compute_sudo=True)
    has_to_order = fields.Boolean(compute="_compute_amounts", compute_sudo=True)
    has_to_invoice = fields.Boolean(compute="_compute_amounts", compute_sudo=True)
    financial_closed = fields.Boolean("Financially closed", readonly=True, copy=False, tracking=True)
    summary_html = fields.Html("Buying and selling by service group", compute="_compute_summary_html",
                               compute_sudo=True, sanitize=False, groups=MARGIN_GROUPS)
    financial_closed_date = fields.Date(readonly=True, copy=False)
    financial_closed_by = fields.Many2one("res.users", readonly=True, copy=False)
    delivered_date = fields.Date(
        "Delivered on", readonly=True, copy=False, tracking=True,
        help="Day the file was marked delivered. Cristina: every delivered file closes operations within a week («Nuevo "
             "Odoo» › OPS- exptes A69).")
    # Consolidation (roadmap item 8, ADR-013): a master file (the MBL / MAWB and the shared purchases) with house files
    # (one per HBL / HAWB: its own customer, cargo, customs, delivery, sale and invoices). A file with neither is a
    # single shipment, as every file was before.
    master_id = fields.Many2one(
        "boss.expediente", "Master file", index=True, tracking=True, check_company=True, copy=False,
        domain="[('id', '!=', id), ('master_id', '=', False), ('state', '!=', 'cancel')]",
        help="The file of the master B/L or AWB this house travels under. The master's transport data (carrier, "
             "vessel, booking, master B/L or AWB, dates) is copied here, and its shared costs give this file its share.")
    house_ids = fields.One2many("boss.expediente", "master_id", "Houses")
    house_count = fields.Integer(compute="_compute_consolidation")
    consolidation_role = fields.Selection(
        [("single", "Single shipment"), ("master", "Master"), ("house", "House")], "Consolidation",
        compute="_compute_consolidation")
    allocation_basis = fields.Selection(
        ALLOCATION_BASES, "Shared costs split by", default="chargeable", tracking=True,
        help="How the costs of this master are shared among its houses: by chargeable weight (W/M: the higher of "
             "weight and volume, the basis the carriers charge on), gross weight, volume, equal parts, or a share "
             "typed on each house. Odoo 19 offered the same choices; the industry splits by weight or volume.")
    master_allocation_basis = fields.Selection(related="master_id.allocation_basis")
    master_share = fields.Float(
        "Share of the master's costs (%)", digits=(16, 2), compute="_compute_master_share", store=True,
        readonly=False, tracking=True, copy=False,
        help="Part of the master's costs that this house bears, from the master's basis (typed when the basis is "
             "manual).")
    amount_master_cost = fields.Monetary(
        "Share of the master's costs", compute="_compute_amounts", compute_sudo=True, groups=COST_GROUPS,
        help="This house's share of the forecast cost of its master (counted in its cost and margin).")
    amount_master_cost_actual = fields.Monetary("of which billed on the master", compute="_compute_amounts",
                                                compute_sudo=True, groups=COST_GROUPS)
    amount_houses_sale = fields.Monetary("Sale of the houses", compute="_compute_consolidated", compute_sudo=True,
                                         groups=SALE_GROUPS)
    amount_houses_cost = fields.Monetary("Own costs of the houses", compute="_compute_consolidated",
                                         compute_sudo=True, groups=COST_GROUPS)
    amount_consolidated_margin = fields.Monetary(
        "Consolidated margin", compute="_compute_consolidated", compute_sudo=True, groups=MARGIN_GROUPS,
        help="Sale of the master and its houses minus the costs of the master and the own costs of the houses.")
    margin_exception_reason = fields.Char(
        "Closed with a low margin because", tracking=True, copy=False, groups="sales_team.group_sale_manager",
        help="Odoo 17 practice: a margin below the minimum stops the operational close until a manager unlocks it. "
             "Sales managers type the reason here.")

    # --- creation ------------------------------------------------------------------------------------------------

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("name", "/") == "/":
                vals["name"] = self.env["ir.sequence"].next_by_code("boss.expediente") or "/"
        files = super().create(vals_list)
        files._boss_create_analytic_account()
        files._boss_propose_operator()
        files.filtered("master_id").master_id._boss_sync_houses()
        for file in files.filtered(lambda f: not f.handler_id and len(f.handler_candidate_ids) == 1):
            file.handler_id = file.handler_candidate_ids  # the only handler known for the airline at the airport
        return files

    def _boss_propose_operator(self):
        """The operator of the customer for the file's traffic («Operators by customer and traffic», the Odoo 17
        practice) becomes the responsible when the file opens; without one the responsible stays who opened it (the
        salesman of the accepted quotation). It can be changed on the file at any time."""
        Assignment = self.env["boss.operator.assignment"].sudo()
        for file in self.sudo():  # who opens it may no longer see it once another user is responsible (own files)
            operator = Assignment._operator_for(file.partner_id, file.traffic_code)
            if operator and operator != file.user_id:
                file.user_id = operator
                file.message_post(body=self.env._(
                    "Responsible proposed from «Operators by customer and traffic»: %(operator)s (%(traffic)s).",
                    operator=operator.name, traffic=file.traffic_code))

    def _search_next_step(self, operator, value):
        """Files whose suggested next step is (not) one of the values. The step is not stored (it follows every
        document of the file): it is computed on the files not closed financially, which is the work in progress."""
        if operator not in ("in", "not in"):
            return NotImplemented
        values = {value} if isinstance(value, str) or not value else set(value)
        files = self.search([("state", "!=", "cancel"), ("financial_closed", "=", False)])
        ids = [file.id for file in files if file.next_step in values]
        if "done" in values:
            ids += self.search([("financial_closed", "=", True)]).ids
        return [("id", "in" if operator == "in" else "not in", ids)]

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
        self._boss_check_active()
        if self.state == "closed":
            raise UserError(self.env._("%s: operations are closed, reopen the file first.", self.name))
        return {"type": "ir.actions.act_window", "res_model": "boss.expediente.split", "view_mode": "form",
                "views": [(False, "form")], "target": "new", "name": self.env._("Move services to another file"),
                "context": {"default_expediente_id": self.id}}

    # --- pricing inputs from the file's actual data (same names and engine as the quotation) ----------------------

    def _boss_pricing_date(self):
        """Actual date when known (ATA / ATD), else the estimate, else the quotation's planned date: it chooses the
        version of each supplier tariff."""
        self.ensure_one()
        if key_date(self.direction) == "etd":
            day = self.atd and self.atd.date() or self.etd
        else:
            day = self.ata and self.ata.date() or self.eta
        order = self.sale_order_ids.filtered(lambda o: o.state == "sale").sorted("date_order")[:1]
        return day or order.boss_planned_date or fields.Date.context_today(self)

    def _boss_quantity(self, source, size=False, ctype=False):
        self.ensure_one()
        return shipment_quantity(source, [(c.size, c.container_type_id, 1) for c in self.container_ids],
                                 self.gross_kg, self.volume_m3, self.pallets, self.awb_kg or self.chargeable_kg,
                                 size, ctype, chargeable_kg=self.chargeable_kg,
                                 chargeable_by_mode=chargeable_by_mode(self.gross_kg, self.volume_m3))

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
            "carrier_id": self.carrier_id._boss_carrier_family().id if self.carrier_id else False,
            "port_id": self.port_id.id, "country_id": self.country_id.id,
            "foreign_port_id": (self[f"{abroad_side(self.direction)}_port_id"].id if abroad_side(self.direction)
                                else False),
            "state_id": self.inland_state_id.id, "customer_id": partner.id,
            "tariff_use": "demo" if partner.boss_demo else "real",
            "containers": [{"size": size, "type_id": type_id, "quantity": quantity}
                           for (size, type_id), quantity in containers.items()],
            "gross_kg": self.gross_kg or None, "awb_kg": self.awb_kg or self.chargeable_kg or None,
            "chargeable_kg": self.chargeable_kg or None,
            "chargeable_kg_by_mode": {m: kg or None for m, kg in chargeable_by_mode(self.gross_kg, self.volume_m3).items()},
            "volume_m3": self.volume_m3 or None, "pallets": self.pallets or None,
            "goods_value": self.goods_value or order.boss_goods_value or None,
            "duties_amount": self.duties_amount or order.boss_duties_amount or None, "storage_days": None,
            "start_weekday": day.weekday() if day else None,
        }

    # Route (ADR-006): same rules as the quotation (boss.shipment.route)
    @api.depends("direction", "transport_mode", "business")
    def _compute_traffic_code(self):
        for file in self:
            file.traffic_code = traffic_code(file.direction, file.transport_mode, file.business)

    @api.depends("transport_mode")
    def _compute_port_kind(self):
        for file in self:
            file.port_kind = {"sea": "sea", "air": "air"}.get(file.transport_mode, False)

    @api.depends("pickup_address_id.city", "delivery_address_id.city")
    def _compute_places(self):
        for file in self:
            file.origin_place = file.pickup_address_id.city or file.origin_place
            file.destination_place = file.delivery_address_id.city or file.destination_place

    @api.depends("direction", "origin_country_id", "origin_port_id", "destination_country_id", "destination_port_id")
    def _compute_pricing_route(self):
        for file in self:
            side, abroad = spanish_side(file.direction), abroad_side(file.direction)
            known = file.origin_country_id or file.origin_port_id or file.destination_country_id or file.destination_port_id
            if not file.direction or not known:
                file.port_id, file.country_id = file.port_id, file.country_id
                continue
            file.port_id = file[f"{side}_port_id"] if side else False
            file.country_id = file[f"{abroad}_country_id"] if abroad else False

    @api.depends("direction", "pickup_address_id.state_id", "delivery_address_id.state_id")
    def _compute_inland_state(self):
        for file in self:
            side = spanish_side(file.direction)
            address = file.delivery_address_id if side == "destination" else file.pickup_address_id
            spanish = side and address.state_id.country_id.code == "ES"
            file.inland_state_id = address.state_id if spanish else file.inland_state_id

    @api.depends("transport_mode", "gross_kg", "volume_m3")
    def _compute_chargeable_kg(self):
        for file in self:
            file.volume_weight_kg, file.chargeable_kg = chargeable_kg(file.transport_mode, file.gross_kg,
                                                                      file.volume_m3)

    @api.onchange("partner_id", "direction", "business")
    def _onchange_orderer_party(self):
        """BOSS business: who orders is the consignee of an import or the shipper of an export (Ángel, 27/10/2026)."""
        if not self.partner_id:
            return
        party = self.partner_id.commercial_partner_id
        if self.business != "boss":
            if self.consignee_id == party:
                self.consignee_id = False
            if self.shipper_id == party:
                self.shipper_id = False
            return
        if self.direction == "import" and not self.consignee_id:
            self.consignee_id = party
        elif self.direction == "export" and not self.shipper_id:
            self.shipper_id = party

    @api.onchange("direction")
    def _onchange_direction_spain(self):
        """Import and export: the Spanish side is Spain and the side abroad cannot be. National: both sides are Spain.
        Cross-trade: nothing is proposed or cleared."""
        spain = self.env.ref("base.es")
        if self.direction == "national":
            for side in ("origin", "destination"):
                if not self[f"{side}_country_id"]:
                    self[f"{side}_country_id"] = spain
            return
        side, abroad = spanish_side(self.direction), abroad_side(self.direction)
        if not side or not abroad:
            return
        if not self[f"{side}_country_id"]:
            self[f"{side}_country_id"] = spain
        if self[f"{abroad}_country_id"] == spain:
            self[f"{abroad}_country_id"] = False

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
            candidates = file.handler_candidate_ids._origin  # on the form the candidates are new-id copies
            if file.handler_id and candidates and file.handler_id._origin not in candidates:
                file.handler_id = False  # the handler of the previous airline or airport
            if len(candidates) == 1 and not file.handler_id:
                file.handler_id = candidates

    def _boss_handler_needs(self):
        """Needs bought from the handler (air handling services) not ordered yet: they follow the handler chosen on
        the file, whichever supplier priced them on the quotation."""
        return self.cost_ids.filtered(
            lambda n: n.product_id.default_code in HANDLER_SERVICE_CODES
            and not n.purchase_line_ids and n.state not in ("closed", "billed", "performed"))

    # Actual period of the time-based services, from the file's and containers' dates (Cristina 26/10/2026: ATA and
    # pickup with date and time, the system computes the dates). Each service follows the events of the supplier price
    # that prices it (PERIOD_EVENTS on the tariff line, as the supplier document states them), else its default below.
    PERIOD_FIELDS = ("ata", "noa", "foh", "atd", "pickup_date", "delivery_date", "discharge_date", "emptying_date")

    def _boss_event_date(self, event, container=None):
        """Datetime (UTC) of an event of this file, or of one of its containers for the per-container events.
        Container dates are days: taken at noon UTC so that the calendar day is the same in every Spanish time zone."""
        self.ensure_one()
        if event.startswith("container_"):
            day = container and container[CONTAINER_EVENT_FIELDS[event]]
            return day and datetime.combine(day, time(12, 0))
        if event == "noa_or_ata":
            return self.noa or self.ata
        return self[FILE_EVENT_FIELDS[event]] or None

    def write(self, vals):
        self._boss_check_frozen(vals)
        res = super().write(vals)
        if vals.get("ata") and "state" not in vals:
            arriving = self.filtered(lambda f: f.state == "in_transit")
            if arriving:
                arriving.action_arrived()
        if vals.get("master_id"):
            linked = self.filtered("master_id")
            linked.master_id._boss_sync_houses()
            linked._boss_cover_house_services()
        if any(f in vals for f in MASTER_FIELDS):
            self._boss_sync_houses(vals)
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
        """The time-based services whose period is not set by hand follow the file's dates, each with the events of
        its own supplier price; a milestone records it and the expected cost is recomputed (the sale never changes)."""
        fmt = lambda file, d: fields.Datetime.context_timestamp(file, d).strftime("%d/%m/%Y %H:%M") if d else "—"  # noqa: E731
        for file in self:
            changed = []
            for need in file.cost_ids.filtered(lambda n: n.product_id.boss_cost_method == "time" and not n.period_manual
                                               and not n.closed):
                start, end = need._boss_period_bounds()
                if (need.period_start, need.period_end) != (start, end):
                    need.with_context(boss_period_from_file=True).write({"period_start": start, "period_end": end})
                    changed.append(need)
            if not changed:
                continue
            file.event_ids.create({
                "expediente_id": file.id, "kind": "milestone",
                "name": self.env._("Period from the file dates: %s", "; ".join(
                    f"{n.product_id.default_code} {fmt(file, n.period_start)} → {fmt(file, n.period_end)}"
                    for n in changed))})
            file.with_context(boss_reason=self.env._("File dates changed")).action_recompute_costs()

    def action_recompute_costs(self):
        """Expected cost again with the file's current data. Sale prices and the acceptance snapshot do not change."""
        self._boss_check_active()
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

    @api.depends("house_ids", "master_id")
    def _compute_consolidation(self):
        for file in self:
            file.house_count = len(file.house_ids)
            file.consolidation_role = "master" if file.house_ids else "house" if file.master_id else "single"

    @api.depends("master_id", "master_id.allocation_basis", "master_id.house_ids", "master_id.house_ids.gross_kg",
                 "master_id.house_ids.volume_m3", "master_id.house_ids.chargeable_kg", "master_id.house_ids.state")
    def _compute_master_share(self):
        """Share of each house in its master's costs, by the master's basis; the shares of a master add up to 100
        (largest remainder). A manual basis keeps what was typed."""
        for master in self.master_id:
            houses = master.house_ids.filtered(lambda h: h.state != "cancel")
            basis = master.allocation_basis
            if basis == "manual":
                continue
            weight = {"chargeable": "chargeable_kg", "gross": "gross_kg", "volume": "volume_m3"}.get(basis)
            values = {h: (h[weight] if weight else 1.0) or 0.0 for h in houses}
            total = sum(values.values())
            if not total:
                values, total = {h: 1.0 for h in houses}, float(len(houses))  # no cargo data yet: equal parts
            exact = {h: 100.0 * v / total for h, v in values.items()}
            shares = {h: float_round(exact[h], precision_digits=2, rounding_method="DOWN") for h in houses}
            remainder = round(100.0 - sum(shares.values()), 2)
            for h in sorted(houses, key=lambda h: (exact[h] - shares[h], h.id), reverse=True):
                if remainder <= 0:
                    break
                shares[h] = round(shares[h] + 0.01, 2)
                remainder = round(remainder - 0.01, 2)
            for house in houses:
                house.master_share = shares[house]
            (master.house_ids - houses).master_share = 0.0
        self.filtered(lambda f: not f.master_id).master_share = 0.0

    def _compute_consolidated(self):
        """Consolidated view of a master: the sale of its houses, their own costs, and the margin of the whole."""
        for file in self:
            houses = file.house_ids.filtered(lambda h: h.state != "cancel")
            houses_sale = sum(houses.mapped("amount_sale"))
            houses_cost = sum(h.amount_cost_forecast - h.amount_master_cost for h in houses)
            file.amount_houses_sale = houses_sale
            file.amount_houses_cost = houses_cost
            file.amount_consolidated_margin = (file.amount_sale + houses_sale) - (file.amount_cost_forecast + houses_cost)

    @api.constrains("master_id", "house_ids")
    def _check_consolidation(self):
        for file in self:
            if file.master_id and (file.master_id == file or file.master_id.master_id):
                raise ValidationError(self.env._("A house hangs from a master file, and a master is not a house itself."))
            if file.master_id and file.house_ids:
                raise ValidationError(self.env._("%s has houses: it cannot be a house of another file.", file.name))

    def _boss_sync_houses(self, vals=None):
        """The master's transport data is the houses' data: copied to them (one carrier, one vessel, one master
        document, one set of dates for the whole consolidation)."""
        for master in self.filtered("house_ids"):
            values = {f: (master[f].id if isinstance(master[f], models.BaseModel) else master[f])
                      for f in MASTER_FIELDS if vals is None or f in vals}
            if values:
                master.house_ids.filtered(lambda h: h.state not in FROZEN_STATES).write(values)

    def _boss_cover_house_services(self):
        """A house sells services the master buys (freight, local charges…): their purchase needs on the house are
        covered by the master (no second order), and the house takes its share of the master's cost instead."""
        for house in self.filtered("master_id"):
            # by service group: the master buys the freight per container (FMI), the house sells it per W/M (FMI-LCL)
            shared = {house._boss_service_group(p) for p in house.master_id.cost_ids.filtered(lambda n: not n.closed).product_id}
            needs = house.cost_ids.filtered(lambda n: n.kind == "sale" and not n.closed and not n.purchase_line_ids
                                            and house._boss_service_group(n.product_id) in shared)
            if needs:
                needs.write({"closed": True, "master_covered": True,
                             "reason": self.env._("Bought on the master file %s", house.master_id.name)})
                house.message_post(body=self.env._("Services bought on the master %(master)s, not ordered here: %(codes)s.",
                                                   master=house.master_id.name,
                                                   codes=", ".join(needs.mapped("product_id.default_code"))))

    def action_cover_house_services(self):
        self.ensure_one()
        self.house_ids._boss_cover_house_services()

    def action_new_house(self):
        """A house of this master: same case and route, the master's customer by default (changed on the house when
        the consolidation carries several customers), linked at once."""
        self.ensure_one()
        values = {f: (self[f].id if isinstance(self[f], models.BaseModel) else self[f]) for f in HOUSE_FROM_MASTER}
        values.update({"partner_id": self.partner_id.id, "master_id": self.id, "company_id": self.company_id.id,
                       "user_id": self.user_id.id})
        house = self.create(values)
        return {"type": "ir.actions.act_window", "res_model": "boss.expediente", "view_mode": "form",
                "views": [(False, "form")], "res_id": house.id}

    def action_open_houses(self):
        return self._boss_action("boss.expediente", self.house_ids, self.env._("Houses of %s", self.name))

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
            actual_date = file.ata if key_date(file.direction) == "eta" else file.atd
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

    def _boss_check_group(self, group):
        """The buttons of the financial close are limited by group in the view; the method checks it too, so that a
        call over RPC (or from another screen) cannot skip it."""
        if not self.env.su and not self.env.user.has_group(group):
            raise AccessError(self.env._("Only %s can do this on a file.",
                                         self.env.ref(group).sudo().display_name))

    def _boss_user_can(self, groups):
        user = self.env.user
        return any(user.has_group(group) for group in groups.split(","))

    @staticmethod
    def _boss_customs_value_charge(product):
        """Which charge of the customs value (A37) a service is, or None."""
        code = product.default_code or ""
        for key, codes in CUSTOMS_VALUE_CHARGES:
            if any(code == c or code.startswith(c + "-") for c in codes):
                return key
        return None

    @api.depends("name", "customs_ref", "customs_broker_id.lang", "shipper_id", "consignee_id", "incoterm_id",
                 "origin_country_id", "origin_port_id", "destination_port_id", "vessel", "voyage", "mbl_ref", "hbl_ref",
                 "mawb_ref", "hawb_ref", "container_ids.number", "container_ids.seal", "goods_description", "hs_code",
                 "packages", "gross_kg", "volume_m3", "goods_value", "customs_guarantee", "order_link_ids",
                 "allocation_ids")
    @api.depends_context("uid")
    def _compute_customs_broker_text(self):
        """One text the operator copies to the broker, in the broker's language (Spanish by default). The amounts are
        the services sold to the customer (what the importer pays for the transport), shown only to users who see
        the sale; nothing is judged here, the broker declares."""
        for file in self:
            lang = file.customs_broker_id.lang or "es_ES"
            env = file.with_context(lang=lang).env
            _ = env._
            na = "—"
            lines = [_("File %s: data for the customs clearance", file.name)]
            if file.customs_ref:
                lines.append(_("Declaration (DUA): %s", file.customs_ref))
            for label, party in ((_("Importer / consignee"), file.consignee_id),
                                 (_("Exporter / shipper"), file.shipper_id)):
                partner = party.commercial_partner_id
                ids = ", ".join(x for x in (partner.vat and _("tax ID %s", partner.vat),
                                            partner.boss_eori and _("EORI %s", partner.boss_eori)) if x)
                lines.append(f"{label}: {partner.name or na}" + (f" ({ids})" if ids else ""))
            lines.append(_("Incoterm: %s", file.incoterm_id.code or na))
            origin = ", ".join(x for x in (file.origin_port_id.display_name, file.origin_country_id.with_env(env).name)
                               if x)
            lines.append(_("From %(origin)s to %(destination)s", origin=origin or na,
                           destination=file.destination_port_id.display_name or na))
            transport = " ".join(x for x in (file.vessel, file.voyage) if x)
            if transport:
                lines.append(_("Vessel / flight: %s", transport))
            documents = [f"{label} {ref}" for label, ref in (("MBL", file.mbl_ref), ("HBL", file.hbl_ref),
                                                             ("MAWB", file.mawb_ref), ("HAWB", file.hawb_ref)) if ref]
            if documents:
                lines.append(_("Transport documents: %s", ", ".join(documents)))
            containers = [" ".join(x for x in (c.number, c.seal and _("seal %s", c.seal)) if x)
                          for c in file.container_ids if c.number]
            if containers:
                lines.append(_("Containers: %s", "; ".join(containers)))
            goods = [x for x in (file.goods_description, file.hs_code and _("HS %s", file.hs_code),
                                 file.packages and _("%s packages", file.packages),
                                 file.gross_kg and _("%s kg gross", formatLang(env, file.gross_kg, digits=2)),
                                 file.volume_m3 and _("%s m³", formatLang(env, file.volume_m3, digits=3))) if x]
            lines.append(_("Goods: %s", ", ".join(goods) or na))
            if file.goods_value:
                lines.append(_("Goods value: %s", formatLang(env, file.goods_value, currency_obj=file.currency_id)))
            if file._boss_user_can(SALE_GROUPS):
                sold = defaultdict(lambda: defaultdict(float))
                orders = file.sudo().sale_order_ids.filtered(lambda o: o.state == "sale")
                for line in orders.order_line.filtered(lambda l: not l.display_type):
                    key = file._boss_customs_value_charge(line.product_id)
                    if key:
                        sold[key][line.currency_id] += line.price_subtotal
                lines.append(_("Charges for the customs value (sold to the customer):"))
                labels = {"freight": _("Freight"), "THC": "THC", "T3": "T3", "insurance": _("Insurance")}
                for key, _codes in CUSTOMS_VALUE_CHARGES:
                    amounts = [formatLang(env, amount, currency_obj=currency) for currency, amount in sold[key].items()]
                    lines.append(f"  {labels[key]}: {' + '.join(amounts) or na}")
            if file.customs_guarantee:
                selection = dict(file._fields["customs_guarantee"]._description_selection(env))
                lines.append(_("Duties paid or guaranteed by: %s", selection[file.customs_guarantee]))
            file.customs_broker_text = "\n".join(lines)

    # --- ratings (F0-C66) and freeze at the operational close ------------------------------------------------------

    def _boss_rating_parties(self):
        """Who is rated on this file: the customer, and every supplier the file bought from (confirmed purchase orders
        and posted bills), each by its legal entity. [(partner, role)]"""
        self.ensure_one()
        suppliers = (self.purchase_order_ids.filtered(lambda p: p.state == "purchase").partner_id
                     | self.bill_ids.filtered(lambda m: m.state == "posted").partner_id).commercial_partner_id
        customer = self.partner_id.commercial_partner_id
        return [(customer, "customer")] * bool(customer) + [(supplier, "supplier") for supplier in suppliers]

    # Not stored: computed when read. Only stored fields trigger it (bill_ids is itself computed, so a bill posted
    # elsewhere must not search files through it).
    @api.depends("rating_ids.rating", "partner_id", "purchase_order_ids.state")
    def _compute_rating_missing(self):
        for file in self:
            rated = {(r.partner_id, r.role) for r in file.rating_ids if r.rating}
            missing = [partner.name for partner, role in file._boss_rating_parties() if (partner, role) not in rated]
            file.rating_missing = ", ".join(missing) or False

    def _boss_sync_ratings(self):
        """Add a line to rate for each party not listed yet (nothing is removed: a rating stays)."""
        for file in self:
            listed = {(r.partner_id, r.role) for r in file.rating_ids}
            new = [{"expediente_id": file.id, "partner_id": partner.id, "role": role}
                   for partner, role in file._boss_rating_parties() if (partner, role) not in listed]
            if new:  # listing who to rate is the system's; the rating itself is the user's
                self.env["boss.expediente.rating"].sudo().create(new)

    def action_rate_parties(self):
        self._boss_sync_ratings()

    def _boss_frozen_fields(self):
        """Fields that cannot change once operations are closed (extended by the documents module)."""
        return FROZEN_FIELDS

    def _boss_check_frozen(self, vals):
        frozen = set(vals) & set(self._boss_frozen_fields())
        if not frozen or self.env.context.get("boss_unfreeze"):
            return
        closed = self.filtered(lambda f: f.state in FROZEN_STATES)
        if closed:
            labels = ", ".join(sorted(self._fields[f].get_description(self.env)["string"] for f in frozen))
            raise UserError(self.env._(
                "%(files)s: operations are closed, so its shipment data is frozen (%(fields)s). Reopen the file to "
                "change it.", files=", ".join(closed.mapped("name")), fields=labels))

    @api.model
    def _get_view(self, view_id=None, view_type="form", **options):
        """The frozen fields are read-only on the form of a closed or cancelled file (the server refuses them too)."""
        arch, view = super()._get_view(view_id, view_type, **options)
        if view_type == "form":
            frozen = set(self._boss_frozen_fields())
            condition = "state in %s" % (FROZEN_STATES,)
            for node in arch.xpath("//field[@name]"):
                if node.get("name") not in frozen or node.xpath("ancestor::field"):
                    continue
                current = node.get("readonly")
                if current in ("1", "True", "true"):
                    continue
                node.set("readonly", f"({current}) or {condition}" if current and current not in ("0", "False")
                         else condition)
        return arch, view

    def _boss_service_group(self, product):
        """Name of the service group of a product: its category under «BOSS services», else «Other»."""
        root = self.env.ref("boss_services.product_category_services", raise_if_not_found=False)
        category = product.categ_id
        return category.name if category and category != root else self.env._("Other")

    def _boss_summary_rows(self):
        """Buying and selling by service group (the product category of each service), like the Odoo 17 «Resumen»
        (Ángel, 27/10/2026): agreed sale, invoiced to the customer and still to invoice; cost still expected, actual
        (posted vendor bills and credit notes) and forecast; forecast margin. Company currency, untaxed; the same
        documents and rules as the figures above, so the total row equals them. Returns [(group, figures)] with a
        last («Total») row."""
        self.ensure_one()
        company, currency = self.company_id, self.company_id.currency_id
        today = fields.Date.context_today(self)
        account = self.analytic_account_id

        def company_amount(amount, from_currency, date):
            return from_currency._convert(amount, currency, company, fields.Date.to_date(date) or today)

        rows = defaultdict(lambda: {"sale": 0.0, "invoiced": 0.0, "pending": 0.0, "actual": 0.0})
        for allocation in self.allocation_ids.filtered(lambda a: a.order_id.state == "sale"):
            rows[self._boss_service_group(allocation.product_id)]["sale"] += company_amount(
                allocation.amount, allocation.currency_id, allocation.order_id.date_order)
        for item in self._boss_journal_items(("out_invoice", "out_refund")):
            rows[self._boss_service_group(item.product_id)]["invoiced"] -= item.balance * account_share(item, account)
        for item in self._boss_journal_items(("in_invoice", "in_refund", "in_receipt")):
            rows[self._boss_service_group(item.product_id)]["actual"] += item.balance * account_share(item, account)
        for need in self.cost_ids:
            rows[self._boss_service_group(need.product_id)]["pending"] += need.pending_amount_company
        purchase_lines = self.purchase_order_ids.filtered(lambda p: p.state == "purchase").order_line.filtered(
            lambda l: not l.display_type)
        billed_by_line = self.cost_ids._boss_billed_by_purchase_line(purchase_lines)
        for line in purchase_lines.filtered(lambda l: not l.boss_cost_id):
            ordered = company_amount(line.price_subtotal, line.currency_id, line.order_id.date_order)
            rows[self._boss_service_group(line.product_id)]["pending"] += max(
                ordered - billed_by_line.get(line.id, 0.0), 0.0)
        order = [self.env.ref(xmlid, raise_if_not_found=False).name for xmlid in (
            "boss_services.product_category_freight", "boss_services.product_category_inland",
            "boss_services.product_category_local", "boss_services.product_category_customs",
            "boss_services.product_category_storage", "boss_services.product_category_insurance",
            "boss_services.product_category_profit_share", "boss_services.product_category_duties")]
        ordered_rows = sorted(rows.items(), key=lambda kv: (order.index(kv[0]) if kv[0] in order else len(order), kv[0]))
        total = {"sale": 0.0, "invoiced": 0.0, "pending": 0.0, "actual": 0.0}
        result = []
        for group, figures in ordered_rows:
            figures["to_invoice"] = figures["sale"] - figures["invoiced"]
            figures["forecast"] = figures["actual"] + figures["pending"]
            figures["margin"] = figures["sale"] - figures["forecast"]
            for key in total:
                total[key] += figures[key]
            result.append((group, figures))
        total.update({"to_invoice": total["sale"] - total["invoiced"], "forecast": total["actual"] + total["pending"]})
        total["margin"] = total["sale"] - total["forecast"]
        result.append((self.env._("Total"), total))
        return result

    def _compute_summary_html(self):
        _ = self.env._
        headers = (_("Service group"), _("Agreed sale"), _("Invoiced"), _("To invoice"), _("Cost still expected"),
                   _("Actual cost (bills)"), _("Forecast cost"), _("Forecast margin"))
        keys = ("sale", "invoiced", "to_invoice", "pending", "actual", "forecast", "margin")
        for file in self:
            currency = file.company_id.currency_id
            money = lambda amount: formatLang(self.env, amount, currency_obj=currency)  # noqa: E731
            rows = file._boss_summary_rows()
            head = Markup("").join(Markup("<th class=\"%s\">%s</th>") % ("text-end" if i else "", h) for i, h in enumerate(headers))
            body = Markup("").join(
                Markup("<tr class=\"%s\"><td>%s</td>%s</tr>") % (
                    "fw-bold table-active" if i == len(rows) - 1 else "", group,
                    Markup("").join(Markup("<td class=\"text-end\">%s</td>") % money(figures[k]) for k in keys))
                for i, (group, figures) in enumerate(rows))
            file.summary_html = Markup(
                "<table class=\"table table-sm o_boss_summary\"><thead><tr>%s</tr></thead><tbody>%s</tbody></table>"
                "<p class=\"text-muted small mb-0\">%s</p>") % (
                head, body, _("Company currency, without taxes. Actual cost = posted vendor bills and credit notes; "
                              "cost still expected = services not billed yet (forecast); invoiced = posted customer "
                              "invoices less credit notes. Services without a group: «Other»."))

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
            # a house bears its share of the master's costs (ADR-013): forecast and billed, like its own
            master = file.master_id
            share = (file.master_share or 0.0) / 100.0 if master else 0.0
            allocated_actual = share * master.amount_cost_actual if master else 0.0
            allocated_pending = share * master.amount_cost_pending if master else 0.0
            actual += allocated_actual
            pending += allocated_pending
            unknown = needs.filtered("cost_unknown")
            complete = not unknown and currency.is_zero(pending) and (not master or master.cost_complete)
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
            # final only when the sale side is settled too: a credit note leaves its service to invoice (D-8)
            final = complete and float_compare(amount_sale - invoiced, 0.0, precision_rounding=currency.rounding) <= 0
            file.update({
                "amount_sale": amount_sale, "amount_sale_accepted": accepted_sale, "amount_sale_added": amount_added,
                "amount_sale_own": own, "amount_on_behalf": on_behalf,
                "amount_cost_accepted": accepted_cost,
                "amount_committed": committed, "amount_cost_actual": actual, "amount_cost_pending": pending,
                "amount_cost_forecast": actual + pending,
                "amount_margin_accepted": accepted_sale - accepted_cost,
                "amount_margin_forecast": amount_sale - actual - pending,
                "amount_margin_final": invoiced - actual if final else 0.0,
                "amount_invoiced": invoiced, "amount_to_invoice": amount_sale - invoiced,
                "amount_collected": settled_part(posted_invoices, revenue_items, account),
                "amount_paid": -settled_part(posted_bills, cost_items, account),
                "amount_draft_invoices": sum(draft_invoices.mapped("amount_untaxed_signed")),
                "amount_draft_rfqs": sum(company_amount(p.amount_untaxed, p.currency_id, p.date_order)
                                         for p in draft_rfqs),
                "amount_draft_bills": -sum(draft_bills.mapped("amount_untaxed_signed")),
                "cost_complete": complete, "margin_final": final,
                "amount_master_cost": allocated_actual + allocated_pending,
                "amount_master_cost_actual": allocated_actual,
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
            if master:
                rows.append(_("   share of the master %(master)s: %(share)s %% of its forecast cost = %(amount)s",
                              master=master.name, share=file.master_share,
                              amount=money(allocated_actual + allocated_pending)))
            if loose:
                rows.append(_("   purchase lines without file service: %s", money(sum(
                    max(company_amount(l.price_subtotal, l.currency_id, l.order_id.date_order)
                        - billed_by_line.get(l.id, 0.0), 0.0) for l in loose))))
            if final:
                rows.append(_("Final margin %(margin)s = invoiced (credit notes deducted) %(invoiced)s - actual cost "
                              "%(actual)s", margin=money(invoiced - actual), invoiced=money(invoiced),
                              actual=money(actual)))
            else:
                rows.append(_("Forecast margin %(margin)s = %(sale)s - %(cost)s. NOT FINAL:",
                              margin=money(amount_sale - actual - pending), sale=money(amount_sale),
                              cost=money(actual + pending)))
                if not complete:
                    rows.append(_("   %s services not billed yet or with unknown cost",
                                  len(needs.filtered(lambda n: not n.closed and n.state != "billed"))))
                if float_compare(amount_sale - invoiced, 0.0, precision_rounding=currency.rounding) > 0:
                    rows.append(_("   %(todo)s of the agreed sale not invoiced (invoiced %(invoiced)s, credit notes "
                                  "deducted): invoice it, or re-price the service if it will not be invoiced",
                                  todo=money(amount_sale - invoiced), invoiced=money(invoiced)))
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
                (sees_cost, _("supplier bills paid before their services were invoiced (P30)"), posted_bills.filtered(
                    lambda b: b.boss_paid_before_invoice and b._boss_bill_order_problems())),
            ]
            todo += [f"{len(records)} {label}" for visible, label, records in checks if visible and records]
            if sees_sale and float_compare(file.amount_to_invoice, 0.0, precision_rounding=currency.rounding) > 0:
                todo.append(_("%s to invoice", money(file.amount_to_invoice)))
            if sees_cost and not currency.is_zero(pending):
                todo.append(_("%s of cost not billed yet", money(pending)))
            file.completeness = "\n".join(todo) or False

            # Next step: the first open one in BOSS's order of work; the same for every role (the detail shows only
            # the figures the user may see).
            no_supplier = needs.filtered(lambda n: n.state == "no_supplier")
            to_order = needs.filtered(lambda n: n.state == "to_order")
            ordered = needs.filtered(lambda n: n.state == "ordered")
            to_invoice = float_compare(amount_sale - invoiced, 0.0, precision_rounding=currency.rounding) > 0
            review = len(needs.filtered(lambda n: n.variance_to_review or n.po_to_review or (
                n.extra_class in ("approval", "disputed") and not n.closed))) + len(
                draft_invoices | draft_bills
                | posted_bills.filtered(lambda b: b.boss_paid_before_invoice and b._boss_bill_order_problems()))
            step, detail = False, False
            if file.state == "cancel":
                pass
            elif file.financial_closed:
                step = "done"
            elif file.preliminary and not file.house_ids:  # a master usually sells nothing itself
                step = "link_quotation"
            elif no_supplier:
                step, detail = "choose_supplier", _("%s services", len(no_supplier))
            elif unknown:
                step, detail = "type_cost", _("%s services", len(unknown))
            elif to_order:
                step, detail = "order", _("%s services", len(to_order))
            elif draft_rfqs:
                step, detail = "confirm_rfq", _("%s requests for quotation", len(draft_rfqs))
            elif file.state == "open":
                transit_missing = file._boss_transit_missing()
                step = "in_transit"
                detail = _("still without: %s", ", ".join(transit_missing)) if transit_missing else False
            elif file.state == "in_transit":
                step = "arrived"
                detail = False if file.ata else _("type the ATA in «References and dates»")
            elif file.state == "arrived":
                delivery_missing = file._boss_delivery_missing()
                step = "delivered"
                detail = _("first: %s", ", ".join(delivery_missing)) if delivery_missing else False
            elif ordered:
                step, detail = "perform", _("%s services", len(ordered))
            elif to_invoice:
                step, detail = "invoice", money(amount_sale - invoiced) if sees_sale else False
            elif file.state == "delivered":
                step = "close_operations"
                if file.rating_missing and file.company_id.boss_ratings_to_close:
                    detail = _("rate first: %s", file.rating_missing)
                elif file.delivered_date:
                    days = (today - file.delivered_date).days
                    detail = (_("delivered %s days ago: Cristina asks to close within a week", days) if days > 7
                              else _("delivered %s days ago", days))
            elif not currency.is_zero(pending):
                step, detail = "bills", money(pending) if sees_cost else False
            elif review:
                step, detail = "review", _("%s items", review)
            else:
                step = "close_financial"
            file.update({"next_step": step, "next_step_detail": detail, "has_to_order": bool(to_order),
                         "has_to_invoice": to_invoice})

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
        self._boss_check_open_financially()
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

    def _boss_check_open_financially(self):
        closed = self.filtered("financial_closed")
        if closed:
            raise UserError(self.env._("%s is financially closed: an accounting manager reopens it first.",
                                       ", ".join(closed.mapped("name"))))

    def _boss_check_active(self):
        """The actions of the «Actions» menu of the file never run on a cancelled or financially closed file."""
        self._boss_check_open_financially()
        cancelled = self.filtered(lambda f: f.state == "cancel")
        if cancelled:
            raise UserError(self.env._("%s is cancelled.", ", ".join(cancelled.mapped("name"))))

    def action_invoice_services(self):
        self._boss_check_open_financially()
        self.ensure_one()
        return {
            "type": "ir.actions.act_window", "res_model": "boss.invoice.services", "view_mode": "form",
            "views": [(False, "form")], "target": "new", "name": self.env._("Invoice services"),
            "context": {"default_expediente_id": self.id},
        }

    def action_new_quotation(self):
        """A service sold later: a new quotation of the same customer, linked to this file, with its shipment data."""
        self.ensure_one()
        self._boss_check_active()
        context = {"default_partner_id": self.partner_id.id, "default_boss_expediente_id": self.id,
                   "default_origin": self.name}
        for fname, order_field in FROM_ORDER.items():
            value = self[fname]
            context[f"default_{order_field}"] = value.id if isinstance(value, models.BaseModel) else value
        return {"type": "ir.actions.act_window", "res_model": "sale.order", "view_mode": "form",
                "views": [(False, "form")], "name": self.env._("New quotation"), "context": context}

    def action_add_service(self):
        """A service sold after acceptance, added to the accepted order of the file (explicit change, reason)."""
        self.ensure_one()
        self._boss_check_active()
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
                        "boss_default_analytic": {str(self.analytic_account_id.id): 100.0},
                        "boss_default_file": self.id},
        }

    def _boss_transit_missing(self):
        """Data a file has when it leaves (Odoo 17 practice, F0-C31 and F0-C38 in docs/decisiones-f0.md): actual
        departure, booking and master B/L or AWB (sea, air), container numbers of an FCL. A warning, never a condition:
        package 3 of docs/paquetes-aprobacion-f0.md enforces only what Cristina wrote down."""
        self.ensure_one()
        _ = self.env._
        missing = [] if self.atd else [_("ATD (actual departure)")]
        if self.transport_mode in ("sea", "air") and not self.booking_ref:
            missing.append(_("booking"))
        if self.transport_mode == "air" and not self.mawb_ref:
            missing.append(_("master AWB"))
        if self.transport_mode == "sea" and not self.mbl_ref:
            missing.append(_("master B/L"))
        if self.load_type == "fcl" and self.container_ids.filtered(lambda c: not c.number):
            missing.append(_("container numbers"))
        return missing

    def _boss_delivery_missing(self):
        """What the file lacks to be marked delivered. Cristina wrote it («Nuevo Odoo» › OPS- exptes A42: the date and
        time of a pickup or delivery made by BOSS; A73: the house B/L released or a sea waybill before delivering) and
        Odoo 17 enforced it («Check Update 3-4»: arrival and vessel discharge on an import, the customs release of every
        declaration cleared by BOSS)."""
        self.ensure_one()
        _ = self.env._
        missing = []
        importing = self.direction == "import"
        if importing and not self.ata:
            missing.append(_("ATA (actual arrival)"))
        if importing and self.transport_mode == "sea" and not self.discharge_date:
            missing.append(_("vessel discharge"))
        if (self.scope_origin_customs or self.scope_destination_customs) and not self.customs_release_date:
            missing.append(_("customs release (levante)"))
        if self.scope_pickup and not self.pickup_date:
            missing.append(_("pickup date and time"))
        if self.scope_delivery and not self.delivery_date:
            missing.append(_("delivery date and time"))
        if (importing and self.transport_mode == "sea" and self.scope_delivery
                and self.hbl_release not in ("released", "swb")):
            missing.append(_("house B/L released or sea waybill"))
        return missing

    def action_in_transit(self):
        files = self | self.house_ids.filtered(lambda h: h.state == "open")  # the houses leave with their master
        for file in files:
            missing = file._boss_transit_missing()
            if missing:
                file.message_post(body=self.env._(
                    "In transit without: %s. A warning: complete them when they are known.", ", ".join(missing)))
        files.write({"state": "in_transit"})

    def action_arrived(self):
        """Arrived (Odoo 17 stage «Llegado», F0-C22): the actual arrival (ATA) is known. Typing the ATA of a file in
        transit does it by itself (see write); the houses arrive with their master, whose ATA they share."""
        for file in self:
            if not file.ata:
                raise UserError(self.env._("%s has no ATA yet: type the actual arrival in «References and dates» and "
                                           "the file is marked arrived.", file.name))
        files = self | self.house_ids.filtered(lambda h: h.state in ("open", "in_transit") and h.ata)
        files.filtered(lambda f: f.state in ("open", "in_transit")).write({"state": "arrived"})

    def action_delivered(self):
        for file in self:
            missing = file._boss_delivery_missing()
            if missing:
                raise UserError(self.env._(
                    "%(file)s cannot be marked delivered yet, it lacks: %(missing)s. Fill them in «References and "
                    "dates» and «Customs».", file=file.name, missing=", ".join(missing)))
        self.write({"state": "delivered", "delivered_date": fields.Date.context_today(self)})
        self._boss_sync_ratings()  # the parties to rate before closing are listed in «Ratings»

    def _boss_margin_warnings(self):
        """Service groups of the file below the minimum margin: the base rule of Odoo 17 also used on the quotation
        (10 % of the forecast cost, 10 of tolerance), amounts paid on behalf re-invoiced exactly."""
        self.ensure_one()
        _ = self.env._
        currency = self.company_id.currency_id
        duties = self.env.ref("boss_services.product_category_duties", raise_if_not_found=False)
        money = lambda amount: formatLang(self.env, amount, currency_obj=currency)  # noqa: E731
        warnings = []
        for group, figures in self.sudo()._boss_summary_rows()[:-1]:
            sale, cost, margin = figures["sale"], figures["forecast"], figures["margin"]
            if duties and group == duties.name:
                if not currency.is_zero(sale - cost):
                    warnings.append(_("%(group)s re-invoiced %(sale)s for %(cost)s paid", group=group, sale=money(sale),
                                      cost=money(cost)))
            elif cost and margin + MIN_MARGIN_TOLERANCE < MIN_MARGIN_RATE * cost:
                warnings.append(_("%(group)s margin %(margin)s, minimum %(minimum)s", group=group,
                                  margin=money(margin), minimum=money(MIN_MARGIN_RATE * cost)))
        return warnings

    def action_close_operations(self):
        """Operational close as Cristina wrote it and Odoo 17 enforced it (F0-C60; F0-A07, Belal): every service
        invoiced, no margin below the minimum unless a sales manager wrote why. Costs still to be billed do not stop
        it: the file is closed against its forecast and the late bills are taken without reopening (OPS- exptes A69)."""
        _ = self.env._
        for file in self:
            sudo = file.sudo()
            currency = file.company_id.currency_id
            problems = []
            if float_compare(sudo.amount_to_invoice, 0.0, precision_rounding=currency.rounding) > 0:
                problems.append(_("%s still to invoice: invoice the services first",
                                  formatLang(self.env, sudo.amount_to_invoice, currency_obj=currency)))
            warnings = file._boss_margin_warnings()
            if warnings and not sudo.margin_exception_reason:
                problems.append(_("margin below the minimum (%s): a sales manager writes why in «Closed with a low "
                                  "margin because»", "; ".join(warnings)))
            if problems:
                raise UserError(_("%(file)s cannot close operations yet: %(problems)s.", file=file.name,
                                  problems="; ".join(problems)))
        # Ratings (F0-C66, Odoo 17 since 01/03/2025; a setting): the lines to rate are added and kept, and the user is
        # sent to them instead of an error that would undo them.
        to_rate = self.filtered(lambda f: f.company_id.boss_ratings_to_close)
        to_rate._boss_sync_ratings()
        missing = to_rate.filtered("rating_missing")
        if missing:
            return {"type": "ir.actions.client", "tag": "display_notification", "params": {
                "type": "warning", "sticky": True, "title": _("Rate the parties before closing"),
                "message": "; ".join(_("%(file)s: %(parties)s", file=f.name, parties=f.rating_missing) for f in missing)
                + ". " + _("Give each one a rating from 0 to 10 in the «Ratings» tab, then close operations."),
                "next": {"type": "ir.actions.client", "tag": "soft_reload"}}}
        self.write({"state": "closed"})
        return True

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
        self._boss_check_group("account.group_account_invoice")
        for file in self:
            problems = []
            if file.state not in ("closed", "cancel"):
                problems.append(self.env._("operations are not closed"))
            open_houses = file.house_ids.filtered(lambda h: h.state != "cancel" and not h.financial_closed)
            if open_houses:
                problems.append(self.env._("its houses are not closed financially: %s",
                                           ", ".join(open_houses.mapped("name"))))
            if file.completeness:
                problems.append(file.completeness)
            if problems:
                raise UserError(self.env._("%(file)s cannot be closed financially:\n%(problems)s", file=file.name,
                                           problems="\n".join(problems)))
        self.write({"financial_closed": True, "financial_closed_date": fields.Date.context_today(self),
                    "financial_closed_by": self.env.uid})
        self.env["boss.margin.report"]._boss_refresh(self)

    def action_reopen_financial(self):
        self._boss_check_group("account.group_account_manager")
        self.write({"financial_closed": False, "financial_closed_date": False, "financial_closed_by": False})
        self.env["boss.margin.report"]._boss_refresh(self)

    def _boss_open_needs(self, needs, name):
        """The services of the file a step is about, in a list where they are completed in place."""
        view = self.env.ref("boss_expediente.boss_expediente_cost_view_list_todo")
        return {"type": "ir.actions.act_window", "res_model": "boss.expediente.cost", "name": name,
                "view_mode": "list", "views": [(view.id, "list")], "domain": [("id", "in", needs.ids)],
                "context": {"default_expediente_id": self.id}}

    def action_next_step(self):
        """Do the suggested next step when it is one click (a state change, the RFQs, the invoice wizard), otherwise
        open exactly the records it is about. Every action keeps its own rights and checks."""
        self.ensure_one()
        _ = self.env._
        step = self.next_step
        needs = self.cost_ids
        if step == "link_quotation":
            customer = self.partner_id.commercial_partner_id
            orders = self.env["sale.order"].search([("partner_id", "child_of", customer.id),
                                                    ("state", "in", ("draft", "sent"))])
            return self._boss_action("sale.order", orders, _("Open quotations of %s", self.partner_id.display_name))
        if step == "choose_supplier":
            return self._boss_open_needs(needs.filtered(lambda n: n.state == "no_supplier"),
                                         _("Services without supplier"))
        if step == "type_cost":
            return self._boss_open_needs(needs.filtered("cost_unknown"), _("Services with unknown cost"))
        if step == "order":
            return self.action_create_rfqs()
        if step == "confirm_rfq":
            rfqs = self.purchase_order_ids.filtered(lambda p: p.state in ("draft", "sent", "to approve"))
            return self._boss_action("purchase.order", rfqs, _("Requests for quotation to confirm"))
        if step == "in_transit":
            return self.action_in_transit()
        if step == "arrived":
            return self.action_arrived()
        if step == "delivered":
            return self.action_delivered()
        if step == "perform":
            return self._boss_open_needs(needs.filtered(lambda n: n.state == "ordered"), _("Ordered services"))
        if step == "invoice":
            return self.action_invoice_services()
        if step == "close_operations":
            return self.action_close_operations()
        if step == "bills":
            orders = self.purchase_order_ids.filtered(
                lambda p: p.state == "purchase" and p.invoice_status == "to invoice")
            if orders:
                return self._boss_action("purchase.order", orders, _("Purchase orders to bill"))
            return self.action_new_bill()
        if step == "review":
            to_review = needs.filtered(lambda n: n.variance_to_review or n.po_to_review or (
                n.extra_class in ("approval", "disputed") and not n.closed))
            if to_review:
                return self._boss_open_needs(to_review, _("Services to review"))
            documents = self.sudo()
            moves = (documents.invoice_ids | documents.bill_ids).filtered(lambda m: m.state == "draft" or (
                m.state == "posted" and m.boss_paid_before_invoice and m._boss_bill_order_problems()))
            return self._boss_action("account.move", self.env["account.move"].browse(moves.ids),
                                     _("Documents to review"))
        if step == "close_financial":
            return self.action_close_financial()
        return False


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
    empty_out_date = fields.Date("Empty pickup", help="Export: empty container picked up (start of the detention).")
    gate_in_date = fields.Date("Full in terminal", help="Export: full container delivered to the port terminal.")
    pickup_date = fields.Date("Full pickup", help="Import: full container out of the terminal.")
    return_date = fields.Date("Empty return", help="Import: empty container returned to the carrier.")

    DATE_FIELDS = ("empty_out_date", "gate_in_date", "pickup_date", "return_date")

    @api.model_create_multi
    def create(self, vals_list):
        containers = super().create(vals_list)
        dated = containers.filtered(lambda c: any(c[f] for f in self.DATE_FIELDS))
        dated.expediente_id._boss_apply_dates()
        return containers

    def write(self, vals):
        res = super().write(vals)
        if any(f in vals for f in self.DATE_FIELDS):
            self.expediente_id._boss_apply_dates()
        return res


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
