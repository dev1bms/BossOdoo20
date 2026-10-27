from odoo import fields, models


class SaleOrderTemplate(models.Model):
    """What BOSS handles in the case of the template (ADR-006): copied to the quotation with the case."""
    _inherit = "sale.order.template"

    boss_scope_pickup = fields.Boolean("Pickup")
    boss_scope_origin_customs = fields.Boolean("Customs at origin")
    boss_scope_main = fields.Boolean("Main carriage")
    boss_scope_destination_customs = fields.Boolean("Customs at destination")
    boss_scope_delivery = fields.Boolean("Delivery")
