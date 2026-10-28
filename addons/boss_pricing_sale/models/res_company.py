from odoo import api, fields, models

from .product_pricelist_item import BOSS_LINE_COST

FX_POLICIES = [
    ("none", "Do not convert: the cost stays pending"),
    ("rate_quotation", "Odoo exchange rate of the quotation date"),
]


class ResCompany(models.Model):
    _inherit = "res.company"

    # ADR-002 §Currency: amounts in different currencies are never added without a policy.
    # The policy is a business decision (docs/preguntas-abiertas.md P03): default = no conversion.
    boss_fx_policy = fields.Selection(FX_POLICIES, string="Supplier cost in another currency",
                                      default="none", required=True)
    # ADR-004: the Odoo tax of each VAT case is in the BOSS VAT table (boss.vat.tax), by class and customer zone.


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    boss_fx_policy = fields.Selection(related="company_id.boss_fx_policy", readonly=False)
    boss_tariff_document_required = fields.Boolean(related="company_id.boss_tariff_document_required", readonly=False)
    boss_spot_rate_auto_approve = fields.Boolean(related="company_id.boss_spot_rate_auto_approve", readonly=False)
    # Default sale price = expected cost + this percentage (Belal, 27/10/2026, after Ángel: a surcharge on the cost,
    # not a margin on the sale). It lives as one standard rule on the default pricelist: a customer with an agreed
    # price keeps it, a price typed on the line is never overwritten, and 0 removes the rule (switched off).
    boss_default_markup = fields.Float(
        "Default sale price: expected cost + %", digits=(16, 2),
        help="Sale price proposed on every service line whose cost is known: cost + this percentage, as a rule of "
        "the default pricelist. Agreed prices of a customer's own pricelist and prices typed on the line come first. "
        "0 switches it off (the rule is removed).")

    def _boss_default_markup_rules(self):
        """The global «expected cost + %» rules of the company's pricelists (normally one, on the default one)."""
        return self.env["product.pricelist.item"].search([
            ("base", "=", BOSS_LINE_COST), ("applied_on", "=", "3_global"), ("compute_price", "=", "markup"),
            ("pricelist_id.active", "=", True), ("pricelist_id.company_id", "in", [self.env.company.id, False]),
        ], order="pricelist_id, id")

    @api.model
    def _boss_get_default_markup(self):
        rule = self._boss_default_markup_rules()[:1]
        return rule.price_markup if rule else 0.0

    @api.model
    def _boss_set_default_markup(self, markup):
        """0 or less removes the rule; otherwise the rule is updated, or created on the pricelist a customer gets by
        default (country group, generic default, else the first one)."""
        rules = self._boss_default_markup_rules()
        if markup <= 0:
            rules.unlink()
            return
        if rules:
            rules.filtered(lambda r: r.price_markup != markup).write({"price_markup": markup})
            rules.filtered(lambda r: not r.price_round).write({"price_round": 0.01})
            return
        partner = self.env.company.partner_id
        pricelist = self.env["product.pricelist"]._get_partner_pricelist_multi([partner.id])[partner.id]
        if pricelist:
            self.env["product.pricelist.item"].create({
                "pricelist_id": pricelist.id, "applied_on": "3_global", "base": BOSS_LINE_COST,
                "compute_price": "markup", "price_markup": markup,
                "price_round": 0.01,  # a sale price in cents: two decimals (Ángel, 27/10/2026)
            })

    @api.model
    def get_values(self):
        res = super().get_values()
        res["boss_default_markup"] = self._boss_get_default_markup()
        return res

    def set_values(self):
        super().set_values()
        self._boss_set_default_markup(self.boss_default_markup or 0.0)
