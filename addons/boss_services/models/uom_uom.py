from odoo import fields, models


class UomUom(models.Model):
    _inherit = "uom.uom"

    # ADR-002: a charge basis is an independent unit; its quantity comes from the shipment
    # inputs named here, never from a conversion between units.
    boss_quantity_source = fields.Selection(
        [
            ("container_20", "Containers 20'"),
            ("container_40", "Containers 40'"),
            ("container_45", "Containers 45'"),
            ("teu", "TEU of the containers"),
            ("shipment", "One per shipment"),
            ("input", "Entered on the line"),
        ],
        string="BOSS quantity",
        help="Where the quantity of a quotation line in this charge basis comes from. "
        "Empty: not a BOSS charge basis.",
    )
