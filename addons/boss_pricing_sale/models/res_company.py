from odoo import fields, models

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
    # ADR-004: Ángel's VAT rules give a class per line (NS / EX / NR); the Odoo tax used for each class
    # is his decision (B02). Until it is set, the line VAT is "pending" and the quotation is not ready.
    boss_tax_nr_id = fields.Many2one("account.tax", "Sale tax for NR lines", domain=[("type_tax_use", "=", "sale")])
    boss_tax_ex_id = fields.Many2one("account.tax", "Sale tax for EX lines (exempt)",
                                     domain=[("type_tax_use", "=", "sale")])
    boss_tax_ns_id = fields.Many2one("account.tax", "Sale tax for NS lines (not subject)",
                                     domain=[("type_tax_use", "=", "sale")])


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    boss_fx_policy = fields.Selection(related="company_id.boss_fx_policy", readonly=False)
    boss_tax_nr_id = fields.Many2one(related="company_id.boss_tax_nr_id", readonly=False)
    boss_tax_ex_id = fields.Many2one(related="company_id.boss_tax_ex_id", readonly=False)
    boss_tax_ns_id = fields.Many2one(related="company_id.boss_tax_ns_id", readonly=False)
