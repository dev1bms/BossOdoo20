from odoo import fields, models


class BossPort(models.Model):
    _name = "boss.port"
    _description = "Port or airport"
    _order = "kind, code"
    _rec_names_search = ["code", "name"]

    name = fields.Char(required=True, translate=True)
    code = fields.Char(required=True, help="UN/LOCODE for sea ports, IATA code for airports.")
    kind = fields.Selection([("sea", "Sea port"), ("air", "Airport")], required=True, default="sea")
    country_id = fields.Many2one("res.country", required=True)
    canary_islands = fields.Boolean(help="Port in the Canary Islands (own VAT zone).")
    active = fields.Boolean(default=True)

    _code_kind_unique = models.Constraint("UNIQUE(code, kind)", "This code already exists.")

    def _compute_display_name(self):
        for port in self:
            port.display_name = f"{port.code} - {port.name}"
