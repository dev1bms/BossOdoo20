from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError

# ADR-002: the scope of a tariff = conditions shared by every line. Each one maps to a shipment
# input of the same name in boss.pricing (one place, one meaning).
SCOPE_FIELDS = ("direction", "transport_mode", "load_type", "carrier_id", "port_ids", "country_ids",
                "state_ids", "customer_id")
# Approved = evidence: these fields never change; a change is a new version.
GOVERNED_FIELDS = SCOPE_FIELDS + (
    "partner_id", "currency_id", "valid_from", "valid_to", "document", "document_reference",
)
# Only set by the workflow methods (never by create, import, RPC or a form).
WORKFLOW_FIELDS = ("state", "approved_by_id", "approved_date", "version", "lineage_id")

DIRECTIONS = [("import", "Import"), ("export", "Export")]
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
    direction = fields.Selection(DIRECTIONS, tracking=True, help="Empty: import and export.")
    transport_mode = fields.Selection(TRANSPORT_MODES, tracking=True, help="Empty: any mode.")
    load_type = fields.Selection(LOAD_TYPES, tracking=True, help="Empty: any load type.")
    carrier_id = fields.Many2one("res.partner", "Carrier", tracking=True,
                                 help="Shipping line, airline or haulier the prices apply to. Empty: any.")
    port_ids = fields.Many2many("boss.port", string="Ports", help="Empty: any port.")
    country_ids = fields.Many2many(
        "res.country", string="Countries abroad",
        help="Origin country of an import or destination country of an export. Empty: any.")
    state_ids = fields.Many2many(
        "res.country.state", string="Provinces (inland)", domain="[('country_id.code', '=', 'ES')]",
        help="Province of the pickup or delivery place in Spain (e.g. a haulier's zone). Empty: any.")
    customer_id = fields.Many2one("res.partner", "Customer", tracking=True,
                                  help="Prices agreed for this customer only. They win over general prices.")
    line_ids = fields.One2many("boss.tariff.line", "tariff_id", "Prices", copy=True)
    approved_by_id = fields.Many2one("res.users", readonly=True, copy=False)
    approved_date = fields.Datetime(readonly=True, copy=False)
    note = fields.Text()

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
                 "line_ids.container_type_ids", "document", "document_reference", *SCOPE_FIELDS)
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
            seen = {}
            for line in tariff.line_ids:
                key = (line.product_id.id, line.uom_id.id, line.container_size, frozenset(line.container_type_ids.ids))
                if key in seen:
                    todo.append(_("Two prices for %(svc)s with the same unit and container: they would conflict.",
                                  svc=line.product_id.display_name))
                seen[key] = line
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
        if self.country_ids:
            conditions["country_id"] = set(self.country_ids.ids)
        if self.state_ids:
            conditions["state_id"] = set(self.state_ids.ids)
        return conditions
