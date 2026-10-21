from odoo import api, fields, models
from odoo.exceptions import ValidationError

from ..engine import Rule


class BossTariffLine(models.Model):
    _name = "boss.tariff.line"
    _description = "Supplier price"
    _order = "tariff_id, product_id, uom_id"

    tariff_id = fields.Many2one("boss.tariff", required=True, ondelete="cascade", index=True)
    product_id = fields.Many2one(
        "product.product", "Service", required=True, index=True,
        domain="[('boss_pricing_mode', '=', 'tariff')]")
    allowed_uom_ids = fields.Many2many("uom.uom", compute="_compute_allowed_uom_ids")
    uom_id = fields.Many2one(
        "uom.uom", "Charge basis", required=True,
        domain="[('id', 'in', allowed_uom_ids), ('boss_quantity_source', '!=', False)]",
        help="What the price is per: container 40', B/L, shipment, chargeable kg... Each basis is "
        "priced on its own; there is no conversion between bases.")
    method = fields.Selection([("per_unit", "Price per unit")], required=True, default="per_unit",
                              help="Price per unit: unit price x quantity in the charge basis, then "
                              "minimum and maximum on the line total.")
    unit_price = fields.Float(min_display_digits="Product Price")
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

    _service_basis_unique = models.Constraint(
        "UNIQUE(tariff_id, product_id, uom_id)",
        "A tariff has one price per service and charge basis.",
    )

    @api.depends("product_id")
    def _compute_allowed_uom_ids(self):
        for line in self:
            line.allowed_uom_ids = line.product_id.product_tmpl_id._boss_charge_bases() if line.product_id else False

    @api.constrains("product_id", "uom_id")
    def _check_charge_basis(self):
        for line in self:
            if line.uom_id not in line.product_id.product_tmpl_id._boss_charge_bases():
                raise ValidationError(self.env._(
                    "'%(uom)s' is not a charge basis of %(service)s.",
                    uom=line.uom_id.name, service=line.product_id.display_name))

    @api.constrains("unit_price", "min_amount", "max_amount")
    def _check_amounts(self):
        for line in self:
            if min(line.unit_price, line.min_amount, line.max_amount) < 0:
                raise ValidationError(self.env._("Supplier prices cannot be negative."))
            if line.max_amount and line.max_amount < line.min_amount:
                raise ValidationError(self.env._("The maximum is lower than the minimum."))

    def _compute_display_name(self):
        for line in self:
            tariff = line.tariff_id
            line.display_name = f"{tariff.name} v{tariff.version} - {line.product_id.default_code} / {line.uom_id.name}"

    def _to_engine_rule(self):
        self.ensure_one()
        tariff = self.tariff_id
        return Rule(
            id=self.id, product_id=self.product_id.id, uom_id=self.uom_id.id, method=self.method,
            currency=tariff.currency_id.name, lineage_id=tariff.lineage_id.id or tariff.id,
            version=tariff.version, valid_from=tariff.valid_from, valid_to=tariff.valid_to or None,
            approved=tariff.state == "approved", on_request=self.on_request, priority=tariff.priority,
            conditions=tariff._engine_conditions(),
            params={"unit_price": self.unit_price, "min_amount": self.min_amount,
                    "max_amount": self.max_amount},
        )
