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


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    boss_fx_policy = fields.Selection(related="company_id.boss_fx_policy", readonly=False)
