from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError

from ..engine import METHODS, Rule
from .boss_container_type import CONTAINER_SIZES

METHOD_SELECTION = [
    ("per_unit", "Price per unit"),
    ("max_of_bases", "Larger of two bases"),
    ("brackets", "Brackets"),
    ("percent", "Percentage of a base"),
    ("time", "Per day with free period"),
]
BASES = [
    ("line", "Quantity of the quotation line"),
    ("containers", "Containers of the line"),
    ("teu", "TEU of the line's containers"),
    ("gross_kg", "Gross weight (kg)"),
    ("gross_ton", "Gross weight (tonnes)"),
    ("volume_m3", "Volume (m³)"),
    ("wm", "W/M: larger of tonnes and m³"),
    ("chargeable_kg", "Chargeable kg (volumetric factor of the document)"),
    ("awb_kg", "Chargeable kg of the air waybill (entered)"),
    ("pallets", "Pallets"),
    ("km", "Kilometres"),
]
PERCENT_BASES = [
    ("goods_value", "Goods value"),
    ("duties_amount", "Customs duties of the declaration"),
    ("services", "Cost of other services of the same supplier"),
]


class BossTariffLine(models.Model):
    _name = "boss.tariff.line"
    _description = "Supplier price"
    _order = "tariff_id, product_id, uom_id, container_size"

    tariff_id = fields.Many2one("boss.tariff", required=True, ondelete="cascade", index=True)
    product_id = fields.Many2one(
        "product.product", "Service", required=True, index=True,
        domain="[('boss_pricing_mode', '=', 'tariff')]")
    allowed_uom_ids = fields.Many2many("uom.uom", compute="_compute_allowed_uom_ids")
    uom_id = fields.Many2one(
        "uom.uom", "Charge basis", required=True,
        domain="[('id', 'in', allowed_uom_ids), ('boss_quantity_source', '!=', False)]",
        help="The unit of the quotation line this price serves: container, B/L, shipment, kg... "
        "There is no conversion between charge bases.")
    container_size = fields.Selection(CONTAINER_SIZES, help="Only for containers of this size. Empty: any size.")
    container_type_ids = fields.Many2many("boss.container.type", string="Container types",
                                          help="Only for these container types. Empty: any type.")
    method = fields.Selection(METHOD_SELECTION, required=True, default="per_unit")
    basis = fields.Selection(BASES, "Priced on", default="line", required=True,
                             help="What the supplier document charges on.")
    volumetric_factor = fields.Float(help="kg per m³ stated by the supplier document (e.g. 167 air).")
    unit_size = fields.Float(default=1.0, help="Size of one priced unit, e.g. 100 for 'per 100 kg'.")
    round_up = fields.Boolean("Or fraction", help="Round up to whole units ('per 100 kg or fraction').")
    round_undecided = fields.Boolean(
        "Or fraction not decided", help="Time-based prices: the document says «per 100 kg» without «or fraction» and "
        "the business has not decided: both readings are computed and the price is automatic only when they agree.")
    unit_price = fields.Float(min_display_digits="Product Price")
    basis_2 = fields.Selection(BASES, "Second basis")
    unit_price_2 = fields.Float("Second unit price", min_display_digits="Product Price")
    b2_unit_size = fields.Float("Second unit size", default=1.0)
    b2_round_up = fields.Boolean("Second basis or fraction")
    bracket_ids = fields.One2many("boss.tariff.bracket", "line_id", "Brackets / day tiers", copy=True)
    floor_previous = fields.Boolean("Not below the previous bracket",
                                    help="The amount is never lower than the top of the previous bracket.")
    per_container = fields.Boolean("Bracket price per container")
    percent_base = fields.Selection(PERCENT_BASES)
    rate = fields.Float("Rate (%)", digits=(12, 4))
    base_product_ids = fields.Many2many("product.product", string="Base services",
                                        help="Services of the same supplier the percentage applies to.")
    free_days = fields.Integer(help="Free period in calendar days.")
    free_hours = fields.Integer(
        help="Free period in hours, compared with the exact hours of the actual period. An estimate in days is "
        "free only when its whole days fit (48 h: up to 2 days; 36 h: 1 day).")
    free_mode = fields.Selection([("deduct", "Free days are deducted"),
                                  ("threshold", "Once exceeded, every day is charged from day 1")],
                                 default="deduct")
    period_unit = fields.Selection(
        [("24h", "Periods of 24 hours from the start"),
         ("calendar", "Calendar days (entry and exit days counted)"),
         ("undecided", "Not decided: 24-hour periods or calendar days (no automatic price when they differ)")],
        "Days counted as", default="calendar", required=True,
        help="How the actual period is counted. «Por 24 horas»: every started period of 24 hours from the start "
        "event (a part counts as a whole period). «Por día» / «días naturales»: calendar days from the entry date "
        "to the exit date, both included. 'Not decided' while the business has not confirmed the reading.")
    tier_mode = fields.Selection([("positional", "Day number since the start (\"day 5 to 7\")"),
                                  ("relative", "Days after the free period (\"5 days at X, then Y\")"),
                                  ("whole_stay", "Every day at the tier reached by the whole stay"),
                                  ("undecided", "Not decided: day by day or whole stay (no automatic price "
                                                "when they differ)")],
                                 default="positional",
                                 help="How the 'Up to' of the day tiers is read. 'Not decided' when the document "
                                 "does not say: stays where both readings give the same amount are priced, longer "
                                 "ones show both amounts and need a manual cost until the business decides.")
    friday_extra_day = fields.Boolean(
        "Friday +1 free day", help="One more free day (or 24 h) whenever the period starts on a Friday, whatever "
        "the exit day.")
    friday_monday_free = fields.Integer(
        "Free if Friday to Monday",
        help="Free period (in the unit of the franchise: hours, or days) when the period starts on a Friday and "
        "ends on the following Monday, e.g. 72 h. It needs the actual exit date: never assumed in an estimate.")
    saturday_until_monday = fields.Boolean(
        help="Free until the following Monday included when the period starts on a Saturday, whatever the hours. "
        "It needs the actual exit date: never assumed in an estimate.")
    min_amount = fields.Float("Minimum", min_display_digits="Product Price",
                              help="Minimum of the line total (all units of this charge together).")
    min_per_day = fields.Boolean(
        "Minimum per day", help="The minimum applies to each charged day or period (document: «mínimo … AWB/día», "
        "«/expedición/día»), not to the whole stay.")
    max_amount = fields.Float("Maximum", min_display_digits="Product Price",
                              help="Maximum of the line total. Empty: no maximum.")
    on_request = fields.Boolean(
        help="The document says 'on request': there is no amount; the quotation shows it as pending.")
    document_page = fields.Char("Page", help="Page of the supplier document where this price is.")
    note = fields.Char()
    currency_id = fields.Many2one(related="tariff_id.currency_id")
    state = fields.Selection(related="tariff_id.state")
    partner_id = fields.Many2one(related="tariff_id.partner_id", store=True)

    @api.depends("product_id")
    def _compute_allowed_uom_ids(self):
        for line in self:
            line.allowed_uom_ids = line.product_id.product_tmpl_id._boss_charge_bases() if line.product_id else False

    @api.onchange("product_id")
    def _onchange_product_id(self):
        if self.product_id:
            self.uom_id = self.product_id.uom_id
            if self.product_id.boss_cost_method in dict(METHOD_SELECTION):
                self.method = self.product_id.boss_cost_method

    @api.constrains("product_id", "uom_id")
    def _check_charge_basis(self):
        for line in self:
            if line.uom_id not in line.product_id.product_tmpl_id._boss_charge_bases():
                raise ValidationError(self.env._(
                    "'%(uom)s' is not a charge basis of %(service)s.",
                    uom=line.uom_id.name, service=line.product_id.display_name))

    @api.constrains("unit_price", "unit_price_2", "min_amount", "max_amount", "rate")
    def _check_amounts(self):
        for line in self:
            if min(line.unit_price, line.unit_price_2, line.min_amount, line.max_amount, line.rate) < 0:
                raise ValidationError(self.env._("Supplier prices cannot be negative."))
            if line.max_amount and line.max_amount < line.min_amount:
                raise ValidationError(self.env._("The maximum is lower than the minimum."))

    @api.constrains("method", "basis", "volumetric_factor", "basis_2", "percent_base", "bracket_ids")
    def _check_method_parameters(self):
        for line in self.filtered(lambda l: not l.on_request):
            if "chargeable_kg" in (line.basis, line.basis_2) and not line.volumetric_factor:
                raise ValidationError(self.env._("Chargeable kg needs the volumetric factor stated by the document."))
            if line.method == "max_of_bases" and not line.basis_2:
                raise ValidationError(self.env._("The larger of two bases needs a second basis."))
            if line.method == "percent" and not line.percent_base:
                raise ValidationError(self.env._("A percentage needs its base."))
            if line.method in ("brackets", "time") and not line.bracket_ids:
                raise ValidationError(self.env._("Brackets and day tiers need at least one row."))

    def _compute_display_name(self):
        for line in self:
            tariff = line.tariff_id
            if not tariff or not line.product_id:
                line.display_name = self.env._("New supplier price")
                continue
            size = f" {line.container_size}'" if line.container_size else ""
            line.display_name = (f"{tariff.name} v{tariff.version} - {line.product_id.default_code} / "
                                 f"{line.uom_id.name}{size}")

    def _engine_params(self):
        self.ensure_one()
        params = {name: self[name] for name in (
            "basis", "volumetric_factor", "unit_size", "round_up", "unit_price", "basis_2", "unit_price_2",
            "b2_unit_size", "b2_round_up", "floor_previous", "per_container", "percent_base", "rate",
            "free_days", "free_hours", "free_mode", "period_unit", "tier_mode", "friday_extra_day",
            "friday_monday_free", "saturday_until_monday", "min_amount", "min_per_day", "max_amount",
            "round_undecided")}
        params["brackets"] = [{"up_to": b.up_to, "fixed_amount": b.fixed_amount, "unit_price": b.unit_price}
                              for b in self.bracket_ids]
        params["base_product_ids"] = self.base_product_ids.ids
        params["supplier_id"] = self.tariff_id.partner_id.id
        params["currency"] = self.tariff_id.currency_id.name
        return params

    def _to_engine_rule(self, simulate=None):
        """simulate: draft tariffs counted as approved for this call only (test panel, never a quotation)."""
        self.ensure_one()
        tariff = self.tariff_id
        conditions = tariff._engine_conditions()
        if self.container_size:
            conditions["container_size"] = {self.container_size}
        if self.container_type_ids:
            conditions["container_type_id"] = set(self.container_type_ids.ids)
        return Rule(
            id=self.id, product_id=self.product_id.id, uom_id=self.uom_id.id, method=self.method,
            currency=tariff.currency_id.name, lineage_id=tariff.lineage_id.id or tariff.id,
            version=tariff.version, valid_from=tariff.valid_from, valid_to=tariff.valid_to or None,
            approved=tariff.state == "approved" or tariff in (simulate or ()), on_request=self.on_request, priority=tariff.priority,
            conditions=conditions, params=self._engine_params(),
        )


class BossTariffBracket(models.Model):
    _name = "boss.tariff.bracket"
    _description = "Bracket or day tier of a supplier price"
    _order = "line_id, up_to_is_open, up_to"

    line_id = fields.Many2one("boss.tariff.line", required=True, ondelete="cascade", index=True)
    up_to = fields.Float("Up to", help="Upper bound, included (kg, km, value, day number...). 0 = no limit.")
    up_to_is_open = fields.Boolean(compute="_compute_up_to_is_open", store=True)
    fixed_amount = fields.Float(min_display_digits="Product Price", help="Amount of the bracket.")
    unit_price = fields.Float(min_display_digits="Product Price",
                              help="Price per unit (whole quantity), or price per day for day tiers.")

    @api.depends("up_to")
    def _compute_up_to_is_open(self):
        for bracket in self:
            bracket.up_to_is_open = not bracket.up_to


assert set(dict(METHOD_SELECTION)) == set(METHODS), "every engine method has a label"


# --- Workspace «Tarifas y proveedores»: read-only helpers on a supplier price (no second calculation) --------

VALIDITY_STATES = [("draft", "Draft"), ("to_approve", "Waiting for approval"), ("future", "Not valid yet"),
                   ("current", "Valid"), ("expiring", "Expires soon"), ("expired", "Expired"),
                   ("replaced", "Replaced by a newer version")]
EXPIRING_DAYS = 30
# Parameters that only mean something for one method: cleared when the method changes, so that a hidden value
# never takes part in the calculation or the matching.
METHOD_FIELDS = {
    "max_of_bases": ("basis_2", "unit_price_2", "b2_unit_size", "b2_round_up"),
    "brackets": ("floor_previous", "per_container"),
    "percent": ("percent_base", "rate", "base_product_ids"),
    "time": ("free_days", "free_hours", "free_mode", "tier_mode", "friday_extra_day", "friday_monday_free",
             "saturday_until_monday", "min_per_day", "round_undecided"),
}
EXAMPLE_INPUTS = {"gross_kg": 500.0, "volume_m3": 2.0, "awb_kg": 500.0, "pallets": 4.0, "km": 100.0,
                  "goods_value": 10000.0, "duties_amount": 2000.0, "storage_days": 10, "start_weekday": 2}
EXAMPLE_QTY = {"container": 2, "teu": 4, "gross_kg": 500, "gross_ton": 0.5, "volume_m3": 2, "wm": 2, "pallets": 4,
               "awb_kg": 500}


class BossTariffLineWorkspace(models.Model):
    _inherit = "boss.tariff.line"

    tariff_state = fields.Selection(related="tariff_id.state", store=True, string="Approval")
    tariff_active = fields.Boolean(related="tariff_id.active", store=True)
    valid_from = fields.Date(related="tariff_id.valid_from", store=True)
    valid_to = fields.Date(related="tariff_id.valid_to", store=True)
    direction = fields.Selection(related="tariff_id.direction", store=True)
    transport_mode = fields.Selection(related="tariff_id.transport_mode", store=True)
    load_type = fields.Selection(related="tariff_id.load_type", store=True)
    port_ids = fields.Many2many(related="tariff_id.port_ids", string="Ports")
    version = fields.Integer(related="tariff_id.version")
    document_reference = fields.Char(related="tariff_id.document_reference")
    company_id = fields.Many2one(related="tariff_id.company_id", store=True)
    service_code = fields.Char(related="product_id.default_code", string="Code")
    service_name = fields.Char(related="product_id.name", string="Service")
    validity_state = fields.Selection(VALIDITY_STATES, "Validity", compute="_compute_workspace_display")
    price_display = fields.Char("Price", compute="_compute_workspace_display",
                                help="Price with its unit (never the total of the service).")
    scope_display = fields.Char("Applies to", compute="_compute_workspace_display")
    calc_display = fields.Char("Calculation", compute="_compute_workspace_display")
    example_text = fields.Text("Example", compute="_compute_example_text",
                               help="Illustrative shipment computed with the engine and these values.")
    is_demo = fields.Boolean(related="tariff_id.is_demo", store=True, string="Demo")
    free_of_charge = fields.Boolean(
        "No cost (confirmed zero)",
        help="The supplier document says this service costs nothing. Without it, a price without amount is "
        "'missing', never 'free'.")
    ws_is_empty = fields.Boolean("Without amount", compute="_compute_ws_amount_labels",
                                 help="No amount entered and not marked 'On request' or 'No cost'.")
    ws_price_unit_label = fields.Char("Price per", compute="_compute_ws_amount_labels")
    ws_price2_unit_label = fields.Char("Second price per", compute="_compute_ws_amount_labels")
    ws_bounds_label = fields.Char("Minimum / maximum on", compute="_compute_ws_amount_labels")
    ws_brackets_label = fields.Char("Brackets in", compute="_compute_ws_amount_labels")

    @api.depends("method", "basis", "unit_size", "basis_2", "b2_unit_size", "uom_id", "currency_id",
                 "percent_base", "unit_price", "unit_price_2", "rate", "bracket_ids.unit_price",
                 "bracket_ids.fixed_amount", "on_request", "free_of_charge", "min_per_day")
    @api.depends_context("lang")
    def _compute_ws_amount_labels(self):
        """What each amount of the form is charged on, in words (from the line's own basis and unit)."""
        _ = self.env._
        for line in self:
            cur = line.currency_id.name or ""
            unit = line._ws_unit(line.basis, line.unit_size) if line.basis else ""
            line.ws_price_unit_label = _("%(cur)s per %(unit)s", cur=cur, unit=unit)
            line.ws_price2_unit_label = _("%(cur)s per %(unit)s", cur=cur,
                                          unit=line._ws_unit(line.basis_2, line.b2_unit_size) if line.basis_2 else "")
            if line.method == "time" and line.min_per_day:
                line.ws_bounds_label = _("%(cur)s per charged day (minimum) · whole quotation line (maximum)", cur=cur)
            else:
                line.ws_bounds_label = _("%(cur)s on the cost of the whole quotation line (%(uom)s)", cur=cur,
                                         uom=line.uom_id.name or "-")
            if line.method == "time":
                line.ws_brackets_label = _("'Up to' = day number (0 = no limit) · price in %(cur)s per %(unit)s and day",
                                           cur=cur, unit=unit)
            else:
                line.ws_brackets_label = _("'Up to' in %(unit)s (0 = no limit) · fixed amount in %(cur)s for the "
                                           "bracket · unit price in %(cur)s per %(unit)s", cur=cur, unit=unit)
            if line.on_request or line.free_of_charge:
                empty = False
            elif line.method in ("per_unit", "max_of_bases"):
                empty = not (line.unit_price or line.unit_price_2)
            elif line.method == "percent":
                empty = not line.rate
            else:
                empty = not any(b.unit_price or b.fixed_amount for b in line.bracket_ids)
            line.ws_is_empty = empty

    def _ws_label(self, fname, value, record=None):
        record = record or self
        return dict(record._fields[fname]._description_selection(self.env)).get(value, value or "")

    def _ws_unit(self, basis, unit_size):
        # per container the unit of the line says it best («Contenedor»); other bases name their measure
        unit = (self.uom_id.name or "…") if basis in ("line", "containers") else self._ws_label("basis", basis)
        size = unit_size if unit_size and unit_size != 1 else None
        return f"{self.env['boss.pricing']._num(size)} {unit}" if size else unit

    @api.depends("method", "basis", "unit_size", "unit_price", "basis_2", "unit_price_2", "b2_unit_size",
                 "bracket_ids.up_to", "bracket_ids.unit_price", "bracket_ids.fixed_amount", "rate", "percent_base",
                 "free_days", "free_hours", "tier_mode", "period_unit", "round_undecided", "min_amount",
                 "min_per_day", "max_amount", "on_request",
                 "uom_id", "tariff_id.state",
                 "tariff_id.valid_from", "tariff_id.valid_to", "tariff_id.direction", "tariff_id.transport_mode",
                 "tariff_id.load_type", "tariff_id.port_ids", "tariff_id.state_ids", "tariff_id.customer_id",
                 "container_size", "container_type_ids", "tariff_id.currency_id")
    @api.depends_context("lang")
    def _compute_workspace_display(self):
        _ = self.env._
        num = self.env["boss.pricing"]._num
        today = fields.Date.context_today(self)
        newest = {}  # lineage -> newest approved version already started
        for tariff in self.env["boss.tariff"].search([("lineage_id", "in", self.tariff_id.lineage_id.ids),
                                                     ("state", "=", "approved"), ("valid_from", "<=", today)]):
            newest[tariff.lineage_id.id] = max(newest.get(tariff.lineage_id.id, 0), tariff.version)
        for line in self:
            cur = line.currency_id.name or ""
            if line.on_request:
                price = _("On request")
            elif line.method == "per_unit":
                price = f"{num(line.unit_price)} {cur} / {line._ws_unit(line.basis, line.unit_size)}"
            elif line.method == "max_of_bases":
                price = _("max(%(a)s; %(b)s)",
                          a=f"{num(line.unit_price)} {cur} / {line._ws_unit(line.basis, line.unit_size)}",
                          b=f"{num(line.unit_price_2)} {cur} / {line._ws_unit(line.basis_2, line.b2_unit_size)}")
            elif line.method == "percent":
                price = f"{num(line.rate)} % · {line._ws_label('percent_base', line.percent_base)}"
            else:
                parts = []
                for bracket in line.bracket_ids[:3]:
                    limit = _("up to %s", num(bracket.up_to)) if bracket.up_to else _("more")
                    values = []
                    if bracket.fixed_amount:
                        values.append(f"{num(bracket.fixed_amount)} {cur}")
                    if bracket.unit_price:
                        values.append(num(bracket.unit_price))
                    parts.append(f"{limit}: {' + '.join(values) or '0'}")
                more = "…" if len(line.bracket_ids) > 3 else ""
                if line.method == "time":
                    per = _("%(cur)s per %(unit)s and day", cur=cur, unit=line._ws_unit(line.basis, line.unit_size))
                else:
                    per = f"{cur} / {line._ws_unit(line.basis, line.unit_size)}"
                price = f"{'; '.join(parts)}{more} ({per})"
                if line.method == "time":
                    free = (_("%s h free", line.free_hours) if line.free_hours
                            else _("%s days free", line.free_days))
                    price += f" · {free}"
                    undecided = [label for label, flag in ((_("day count"), line.period_unit == "undecided"),
                                                           (_("tiers"), line.tier_mode == "undecided"),
                                                           (_("or fraction"), line.round_undecided)) if flag]
                    if undecided:
                        price += " · " + _("not decided: %s", ", ".join(undecided))
            if line.min_amount:
                price += " · " + (_("min. %s per day", f"{num(line.min_amount)} {cur}")
                                  if line.method == "time" and line.min_per_day
                                  else _("min. %s", f"{num(line.min_amount)} {cur}"))
            if line.max_amount:
                price += " · " + _("max. %s", f"{num(line.max_amount)} {cur}")
            line.price_display = price
            tariff = line.tariff_id
            scope = [line._ws_label("direction", tariff.direction, tariff) or _("Import/export"),
                     line._ws_label("transport_mode", tariff.transport_mode, tariff) or _("any mode")]
            if tariff.load_type:
                scope.append(line._ws_label("load_type", tariff.load_type, tariff))
            if tariff.port_ids:
                scope.append(", ".join(tariff.port_ids.mapped("code")))
            if tariff.state_ids:
                scope.append(", ".join(tariff.state_ids.mapped("name")))
            if line.container_size or line.container_type_ids:
                size = f"{line.container_size}'" if line.container_size else ""
                scope.append(f"{size} {'/'.join(line.container_type_ids.mapped('code'))}".strip())
            if tariff.customer_id:
                scope.append(_("only %s", tariff.customer_id.name))
            line.scope_display = " · ".join(s for s in scope if s)
            line.calc_display = f"{line._ws_label('method', line.method)} · {line._ws_label('basis', line.basis)}"
            if tariff.state != "approved":
                line.validity_state = tariff.state
            elif tariff.valid_from and tariff.valid_from > today:
                line.validity_state = "future"
            elif tariff.valid_to and tariff.valid_to < today:
                line.validity_state = "expired"
            elif tariff.version < newest.get(tariff.lineage_id.id, 0):
                line.validity_state = "replaced"
            elif tariff.valid_to and (tariff.valid_to - today).days <= EXPIRING_DAYS:
                line.validity_state = "expiring"
            else:
                line.validity_state = "current"

    def _example_inputs(self):
        """Illustrative shipment: 2 containers of the line's size and type, 500 kg, 2 m³, 10 days, Wednesday."""
        self.ensure_one()
        source = self.uom_id.boss_quantity_source
        ctype = self.container_type_ids[:1].id or self.env.ref("boss_pricing.container_type_dv").id
        inputs = dict(EXAMPLE_INPUTS, containers=[{"size": self.container_size or "40", "type_id": ctype,
                                                   "quantity": 2}])
        inputs["line_qty"] = EXAMPLE_QTY.get(source, 500 if self.uom_id.boss_quantity_source == "input"
                                             and self.uom_id == self.env.ref("boss_services.uom_kg_road") else 1)
        if self.method == "percent" and self.percent_base == "services":
            base = self.base_product_ids[:1]
            inputs["related_costs"] = [{"product_id": base.id, "supplier_id": self.tariff_id.partner_id.id,
                                        "amount": 100.0, "currency": self.currency_id.name}] if base else []
        return inputs

    @api.depends("method", "basis", "unit_size", "round_up", "unit_price", "basis_2", "unit_price_2",
                 "b2_unit_size", "b2_round_up", "bracket_ids", "bracket_ids.up_to", "bracket_ids.unit_price",
                 "bracket_ids.fixed_amount", "floor_previous", "per_container", "percent_base", "rate",
                 "base_product_ids", "free_days", "free_hours", "free_mode", "period_unit", "tier_mode",
                 "friday_extra_day", "friday_monday_free", "saturday_until_monday", "min_amount", "min_per_day",
                 "round_undecided", "max_amount", "volumetric_factor", "uom_id",
                 "container_size", "container_type_ids", "on_request")
    @api.depends_context("lang")
    def _compute_example_text(self):
        from .. import engine  # noqa: PLC0415
        from .boss_pricing import _plain  # noqa: PLC0415
        _ = self.env._
        pricing = self.env["boss.pricing"]
        for line in self:
            if line.on_request or not line.method or not line.uom_id:
                line.example_text = False
                continue
            inputs = line._example_inputs()
            try:
                amount, steps = engine.METHODS[line.method](line._engine_params(), inputs)
            except engine.MissingInput as exc:
                line.example_text = _("Example not possible yet, missing: %s", ", ".join(exc.names))
                continue
            except engine.OutOfRange:
                line.example_text = _("The example quantity is above the last bracket: no price (ask the supplier).")
                continue
            except engine.Undecided as exc:
                readings = dict(exc.steps).get("readings_undecided", {})
                line.example_text = _(
                    "Illustrative shipment of 500 kg and 10 days: the readings not decided give between %(low)s and "
                    "%(high)s, so such a stay is not priced automatically.",
                    low=pricing._num(float(readings.get("low", 0)), line.currency_id),
                    high=pricing._num(float(readings.get("high", 0)), line.currency_id))
                continue
            except Exception:  # noqa: BLE001 (values still being typed)
                line.example_text = _("Complete the values to see an example.")
                continue
            head = _("Illustrative shipment: 2 containers of %(size)s', 500 kg, 2 m³, 10 days from a Wednesday; "
                     "quantity of the line %(qty)s.", size=line.container_size or "40",
                     qty=pricing._num(inputs["line_qty"]))
            text = [pricing._explain_step(code, {k: _plain(v) for k, v in values.items()}, line.currency_id,
                                          line.uom_id) for code, values in steps]
            line.example_text = "\n".join([head] + [t for t in text if t] +
                                          [_("Result: %s", pricing._num(float(amount), line.currency_id))])

    @api.onchange("method")
    def _onchange_method_clear(self):
        """Values of another method never stay hidden in the calculation; the user is told what was cleared."""
        cleared = []
        for method, names in METHOD_FIELDS.items():
            if self.method == method:
                continue
            for name in names:
                field = self._fields[name]
                default = [(5,)] if field.type == "many2many" else (field.default(self) if field.default else False)
                current = self[name]
                if current and current != (field.default(self) if field.default else False):
                    cleared.append(field.get_description(self.env)["string"])
                self[name] = default
        if self.method not in ("brackets", "time") and self.bracket_ids:
            cleared.append(self._fields["bracket_ids"].get_description(self.env)["string"])
            self.bracket_ids = [(5,)]
        if cleared:
            return {"warning": {"title": self.env._("Values cleared"), "message": self.env._(
                "These values belong to another calculation method and were cleared: %s. Discard the changes to "
                "get them back.", ", ".join(cleared))}}

    def action_ws_open(self):
        self.ensure_one()
        return {"type": "ir.actions.act_window", "res_model": "boss.tariff.line", "res_id": self.id,
                "view_mode": "form", "views": [(self.env.ref("boss_pricing.boss_tariff_line_view_form").id, "form")],
                "target": "new", "name": self.display_name}

    def action_ws_duplicate(self):
        """Copy a price of a draft tariff (another container size, a close condition); the copy opens to change
        what differs. Approved tariffs never change: create a new version first."""
        self.ensure_one()
        if self.tariff_id.state != "draft":
            raise UserError(self.env._(
                "Prices are copied inside a draft tariff: create a new version of '%s' first.", self.tariff_id.name))
        return self.copy({"tariff_id": self.tariff_id.id}).action_ws_open()

    def action_ws_document(self):
        self.ensure_one()
        return self.tariff_id.action_ws_document()
