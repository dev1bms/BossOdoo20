from odoo import fields, models

CONTAINER_SIZES = [("20", "20'"), ("40", "40'"), ("45", "45'")]


class BossContainerType(models.Model):
    """Container equipment type (dry, high cube, reefer...). A price CONDITION, never a unit."""

    _name = "boss.container.type"
    _description = "Container type"
    _order = "sequence, code"

    name = fields.Char(required=True, translate=True)
    code = fields.Char(required=True, help="E.g. DV, HC, RF, OT, FR, TK.")
    sequence = fields.Integer(default=10)
    active = fields.Boolean(default=True)

    _code_unique = models.Constraint("UNIQUE(code)", "This container type code already exists.")

    def _compute_display_name(self):
        for ctype in self:
            ctype.display_name = f"{ctype.code} - {ctype.name}"
