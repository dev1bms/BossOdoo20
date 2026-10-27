from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError

# ADR-002: the scope of a tariff = conditions shared by every line. Each one maps to a shipment
# input of the same name in boss.pricing (one place, one meaning).
SCOPE_FIELDS = ("direction", "transport_mode", "load_type", "carrier_id", "port_ids", "foreign_port_ids",
                "country_ids", "state_ids", "customer_id")
# Approved = evidence: these fields never change; a change is a new version.
GOVERNED_FIELDS = SCOPE_FIELDS + (
    "partner_id", "currency_id", "valid_from", "valid_to", "document", "document_reference", "is_demo",
)
# Engine condition of demonstration tariffs: they price only demonstration customers (input `tariff_use`).
DEMO_USE = "demo"
# Only set by the workflow methods (never by create, import, RPC or a form).
WORKFLOW_FIELDS = ("state", "approved_by_id", "approved_date", "version", "lineage_id")

# Cross-trade: neither side in Spain; national: both sides in Spain (Odoo 17 x_traficos I/E/X/N; ADR-006 §3).
DIRECTIONS = [("import", "Import"), ("export", "Export"), ("cross", "Cross-trade"), ("national", "National")]
TRANSPORT_MODES = [("sea", "Sea"), ("air", "Air"), ("road", "Road")]
LOAD_TYPES = [("fcl", "FCL (full container)"), ("lcl", "LCL (groupage)"), ("air", "Air cargo"),
              ("road", "Road cargo")]


class BossTariff(models.Model):
    _name = "boss.tariff"
    _description = "Supplier tariff"
    _inherit = ["mail.thread"]
    _order = "partner_id, lineage_id, version desc"

    name = fields.Char(required=True, tracking=True, help="E.g. MSC local charges import 2026.")
    partner_id = fields.Many2one("res.partner", "Supplier", required=True, tracking=True,
                                 help="Who invoices BOSS for these services.")
    state = fields.Selection(
        [("draft", "Draft"), ("to_approve", "Waiting for approval"), ("approved", "Approved")],
        default="draft", required=True, readonly=True, copy=False, tracking=True,
        help="Only approved tariffs price quotations.",
    )
    active = fields.Boolean(default=True, tracking=True)
    company_id = fields.Many2one("res.company", required=True, default=lambda self: self.env.company)
    currency_id = fields.Many2one("res.currency", required=True, tracking=True,
                                  default=lambda self: self.env.company.currency_id)
    valid_from = fields.Date(required=True, tracking=True, default=fields.Date.today)
    valid_to = fields.Date(tracking=True, help="Empty: valid until a newer version starts.")
    version = fields.Integer(default=1, readonly=True, copy=False)
    lineage_id = fields.Many2one("boss.tariff", "First version", readonly=True, copy=False, index=True,
                                 help="All versions of the same supplier tariff share it.")
    priority = fields.Integer(
        default=10, tracking=True,  # an approver may change it on an approved tariff (resolves conflicts)
        help="Lower wins when two tariffs apply to the same shipment. Set it on purpose to resolve "
        "a conflict; equal priorities with the same scope are reported as a conflict.",
    )
    document = fields.Binary("Supplier document", attachment=True, copy=False,
                             help="The PDF (or file) received from the supplier.")
    document_name = fields.Char()
    document_reference = fields.Char(tracking=True, help="Title and edition of the document, e.g. "
                                     "'DRY - Gastos locales 2026 (09/2026)'.")
    direction = fields.Selection(DIRECTIONS, tracking=True, help="Empty: any direction (import, export, cross-trade, national).")
    transport_mode = fields.Selection(TRANSPORT_MODES, tracking=True, help="Empty: any mode.")
    load_type = fields.Selection(LOAD_TYPES, tracking=True, help="Empty: any load type.")
    carrier_id = fields.Many2one("res.partner", "Carrier", tracking=True,
                                 help="Shipping line, airline or haulier the prices apply to. Empty: any.")
    port_ids = fields.Many2many("boss.port", string="Ports", help="Empty: any port.")
    foreign_port_ids = fields.Many2many(
        "boss.port", "boss_tariff_foreign_port_rel", "tariff_id", "port_id", "Ports / airports abroad",
        help="Origin port of an import or destination port of an export (freight rates are per route, e.g. "
        "Shanghai → Valencia). Empty: any.")
    country_ids = fields.Many2many(
        "res.country", string="Countries abroad",
        help="Origin country of an import or destination country of an export. Empty: any.")
    state_ids = fields.Many2many(
        "res.country.state", string="Provinces (inland)", domain="[('country_id.code', '=', 'ES')]",
        help="Province of the pickup or delivery place in Spain (e.g. a haulier's zone). Empty: any.")
    customer_id = fields.Many2one("res.partner", "Customer", tracking=True,
                                  help="Prices agreed for this customer only. They win over general prices.")
    is_demo = fields.Boolean(
        "Demo tariff", tracking=True,
        help="Training or demonstration prices: they only price customers marked as demo customers, never a "
        "real customer (even when no other price exists).")
    scope_confirmed = fields.Boolean(
        "Scope reviewed",  # a new version keeps the reviewed scope it was copied from
        help="Tick it once the scope matches the supplier document: the fields left empty then mean "
        "'applies to any', not 'not filled in yet'. Required to send the tariff for approval.")
    scope_summary = fields.Char("Applies to", compute="_compute_scope_summary")
    line_ids = fields.One2many("boss.tariff.line", "tariff_id", "Prices", copy=True)
    line_count = fields.Integer("Number of prices", compute="_compute_scope_summary")
    approved_by_id = fields.Many2one("res.users", readonly=True, copy=False)
    approved_date = fields.Datetime(readonly=True, copy=False)
    note = fields.Text()

    @api.depends(*SCOPE_FIELDS, "is_demo", "line_ids")
    @api.depends_context("lang")
    def _compute_scope_summary(self):
        _ = self.env._
        for tariff in self:
            label = lambda name, t=tariff: dict(t._fields[name]._description_selection(self.env)).get(t[name])  # noqa: E731
            parts = [label("direction") or _("any direction"), label("transport_mode") or _("any mode")]
            if tariff.load_type:
                parts.append(label("load_type"))
            for names in (tariff.port_ids.mapped("code"), tariff.foreign_port_ids.mapped("code"),
                          tariff.country_ids.mapped("name"), tariff.state_ids.mapped("name")):
                if names:
                    parts.append(", ".join(names))
            if tariff.carrier_id:
                parts.append(_("carrier %s", tariff.carrier_id.name))
            parts.append(_("only %s", tariff.customer_id.name) if tariff.customer_id else _("any customer"))
            if tariff.is_demo:
                parts.append(_("DEMO: demo customers only"))
            tariff.scope_summary = " · ".join(parts)
            tariff.line_count = len(tariff.line_ids)

    @api.constrains(*SCOPE_FIELDS)
    def _check_lines_scope(self):
        self.line_ids._check_line_scope()

    @api.constrains("valid_from", "valid_to")
    def _check_dates(self):
        for tariff in self:
            if tariff.valid_to and tariff.valid_to < tariff.valid_from:
                raise ValidationError(self.env._("The end of validity is before its start."))

    @api.model_create_multi
    def create(self, vals_list):
        # Every tariff starts as a draft of its own lineage, whatever the caller sends (form, import, RPC).
        for vals in vals_list:
            if (vals.get("state") or "draft") != "draft" or any(
                    vals.get(f) for f in ("approved_by_id", "approved_date", "lineage_id")):
                raise UserError(self.env._("A supplier tariff is always created as a draft and approved by a person."))
            vals.pop("version", None)
        tariffs = super().create(vals_list)
        for tariff in tariffs:
            tariff._workflow_write({"lineage_id": tariff.id})
        return tariffs

    def write(self, vals):
        if set(vals) & set(WORKFLOW_FIELDS):
            raise UserError(self.env._("Status, approval and version of a tariff change only through its buttons."))
        if ("priority" in vals and self.filtered(lambda t: t.state != "draft")
                and not self.env.user.has_group("boss_pricing.group_tariff_approver")):
            raise UserError(self.env._("Only a tariff approver can change the priority of a submitted tariff."))
        if set(vals) & set(GOVERNED_FIELDS) and self.filtered(lambda t: t.state != "draft"):
            raise UserError(self.env._(
                "A tariff that was sent for approval cannot change. Set it back to draft, or create a "
                "new version if it is approved."))
        return super().write(vals)

    def _workflow_write(self, vals):
        """The only path that changes WORKFLOW_FIELDS (skips the guard of write())."""
        return super(BossTariff, self).write(vals)

    def action_submit(self):
        for tariff in self:
            if tariff.state != "draft":
                continue
            if not tariff.line_ids:
                raise UserError(self.env._("Add at least one price before sending '%s'.", tariff.name))
            if not tariff.document:
                raise UserError(self.env._(
                    "Attach the supplier document of '%s': every price must be traceable to it.",
                    tariff.name))
            if not tariff.scope_confirmed:
                raise UserError(self.env._(
                    "Review the scope of '%(tariff)s' and tick 'Scope reviewed': empty fields mean the prices apply "
                    "to any %(fields)s.", tariff=tariff.name, fields=tariff.ws_open_scope or "-"))
            empty = tariff.line_ids.filtered("ws_is_empty")
            if empty:
                raise UserError(self.env._(
                    "These prices have no amount: %s. Enter the amount from the document, mark 'On request', or "
                    "tick 'No cost (confirmed zero)' if the supplier really charges nothing.",
                    ", ".join(empty.mapped("display_name"))))
            tariff._workflow_write({"state": "to_approve"})

    def action_approve(self):
        if not self.env.user.has_group("boss_pricing.group_tariff_approver"):
            raise UserError(self.env._("Only a tariff approver can approve supplier prices."))
        for tariff in self.filtered(lambda t: t.state == "to_approve"):
            tariff._workflow_write({"state": "approved", "approved_by_id": self.env.uid,
                                    "approved_date": fields.Datetime.now()})

    def action_back_to_draft(self):
        self.filtered(lambda t: t.state == "to_approve")._workflow_write({"state": "draft"})

    def action_new_version(self):
        self.ensure_one()
        if self.state != "approved":
            raise UserError(self.env._("Only an approved tariff gets new versions; edit the draft instead."))
        latest = self.search([("lineage_id", "=", self.lineage_id.id)], order="version desc", limit=1)
        new = self.copy({"name": self.name, "valid_from": fields.Date.today(), "valid_to": False})
        new._workflow_write({"lineage_id": self.lineage_id.id, "version": latest.version + 1})
        return new._get_form_action()

    def _get_form_action(self):
        return {"type": "ir.actions.act_window", "res_model": "boss.tariff", "res_id": self.id,
                "view_mode": "form", "views": [(False, "form")], "target": "current"}

    # Load types that exist in each transport mode: changing the mode clears a load type of another mode.
    MODE_LOADS = {"sea": ("fcl", "lcl"), "air": ("air",), "road": ("road",)}

    ws_checklist = fields.Text("Before sending", compute="_compute_ws_checklist")
    ws_open_scope = fields.Char("Applies to any", compute="_compute_ws_checklist",
                                help="Scope left empty: the prices apply to every value of these fields.")

    @api.depends("line_ids", "line_ids.product_id", "line_ids.uom_id", "line_ids.container_size",
                 "line_ids.container_type_ids", "line_ids.ws_is_empty", "document", "document_reference",
                 "line_ids.line_direction", "line_ids.line_transport_mode", "line_ids.line_load_type",
                 "line_ids.line_port_ids", "line_ids.line_foreign_port_ids", "line_ids.line_country_ids",
                 "line_ids.line_state_ids", "scope_confirmed", *SCOPE_FIELDS)
    @api.depends_context("lang")
    def _compute_ws_checklist(self):
        _ = self.env._
        for tariff in self:
            todo = []
            if not tariff.line_ids:
                todo.append(_("Add at least one price."))
            if not tariff.document:
                todo.append(_("Attach the supplier document."))
            if not tariff.document_reference:
                todo.append(_("Write the document reference (title and edition)."))
            if not tariff.scope_confirmed:
                todo.append(_("Review the scope and tick 'Scope reviewed' (empty = applies to any)."))
            for line in tariff.line_ids.filtered("ws_is_empty"):
                todo.append(_("%s has no amount: enter it, or mark 'On request' or 'No cost (confirmed zero)'.",
                              line.product_id.display_name))
            lines = list(tariff.line_ids)
            for i, line in enumerate(lines):
                for other in lines[i + 1:]:
                    if (line.product_id == other.product_id and line.uom_id == other.uom_id
                            and line._ws_overlaps(other)):
                        todo.append(_("Two prices for %(svc)s in %(uom)s apply to the same shipments (same unit, "
                                      "container and scope): they would conflict. Narrow «Applies to» on one of them.",
                                      svc=line.product_id.display_name, uom=line.uom_id.name))
            tariff.ws_checklist = "\n".join(todo) or False
            tariff.ws_open_scope = ", ".join(
                tariff._fields[name].get_description(self.env)["string"]
                for name in SCOPE_FIELDS if not tariff[name]) or False

    @api.onchange("transport_mode")
    def _onchange_transport_mode_load(self):
        if self.transport_mode and self.load_type and self.load_type not in self.MODE_LOADS[self.transport_mode]:
            self.load_type = False

    def action_ws_document(self):
        self.ensure_one()
        if not self.document:
            raise UserError(self.env._("'%s' has no supplier document attached.", self.name))
        return {"type": "ir.actions.act_url", "target": "new",
                "url": f"/web/content/boss.tariff/{self.id}/document/{self.document_name or 'document.pdf'}"}

    def _engine_conditions(self):
        """Scope as engine conditions: name -> accepted values (only the scope that is set)."""
        self.ensure_one()
        conditions = {}
        for name in ("direction", "transport_mode", "load_type"):
            if self[name]:
                conditions[name] = {self[name]}
        for name in ("carrier_id", "customer_id"):
            if self[name]:
                conditions[name] = {self[name].id}
        if self.port_ids:
            conditions["port_id"] = set(self.port_ids.ids)
        if self.foreign_port_ids:
            conditions["foreign_port_id"] = set(self.foreign_port_ids.ids)
        if self.country_ids:
            conditions["country_id"] = set(self.country_ids.ids)
        if self.state_ids:
            conditions["state_id"] = set(self.state_ids.ids)
        if self.is_demo:
            conditions["tariff_use"] = {DEMO_USE}
        return conditions
