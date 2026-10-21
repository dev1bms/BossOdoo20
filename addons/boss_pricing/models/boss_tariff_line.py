from odoo import api, fields, models
from odoo.exceptions import ValidationError

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
    free_days = fields.Integer()
    free_hours = fields.Integer(help="Free period in hours. In a quotation (days only) it counts as whole days.")
    free_mode = fields.Selection([("deduct", "Free days are deducted"),
                                  ("threshold", "Once exceeded, every day is charged from day 1")],
                                 default="deduct")
    tier_mode = fields.Selection([("positional", "Each day at the tier of its position"),
                                  ("whole_stay", "Every day at the tier reached by the whole stay")],
                                 default="positional")
    friday_extra_day = fields.Boolean(help="One more free day when the period starts on a Friday.")
    saturday_until_monday = fields.Boolean(help="Free until Monday when the period starts on a Saturday.")
    min_amount = fields.Float("Minimum", min_display_digits="Product Price",
                              help="Minimum of the line total (all units of this charge together).")
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
            size = f" {line.container_size}'" if line.container_size else ""
            line.display_name = (f"{tariff.name} v{tariff.version} - {line.product_id.default_code} / "
                                 f"{line.uom_id.name}{size}")

    def _engine_params(self):
        self.ensure_one()
        params = {name: self[name] for name in (
            "basis", "volumetric_factor", "unit_size", "round_up", "unit_price", "basis_2", "unit_price_2",
            "b2_unit_size", "b2_round_up", "floor_previous", "per_container", "percent_base", "rate",
            "free_days", "free_hours", "free_mode", "tier_mode", "friday_extra_day", "saturday_until_monday",
            "min_amount", "max_amount")}
        params["brackets"] = [{"up_to": b.up_to, "fixed_amount": b.fixed_amount, "unit_price": b.unit_price}
                              for b in self.bracket_ids]
        params["base_product_ids"] = self.base_product_ids.ids
        params["supplier_id"] = self.tariff_id.partner_id.id
        params["currency"] = self.tariff_id.currency_id.name
        return params

    def _to_engine_rule(self):
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
            approved=tariff.state == "approved", on_request=self.on_request, priority=tariff.priority,
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
